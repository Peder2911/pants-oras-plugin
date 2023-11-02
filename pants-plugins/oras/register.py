"""
Build files into Oras Artifacts for publication.
"""
import typing
import logging
import dataclasses
import pants.core.goals.publish
import pants.engine.rules
import pants.engine.target
import pants.engine.platform
import pants.engine.process
import pants.engine.console
import pants.core.goals.package
import pants.core.util_rules.external_tool
import pants.core.util_rules.system_binaries
import pants.engine.unions
import pants.util.logging
import pants.engine.fs
import pants.base.build_root
import oras.subsystem

logger = logging.getLogger(__name__)

# Fields =


class OrasArtifactDependencies(pants.engine.target.Dependencies):
    alias = "dependencies"


class OrasArtifactLayersField(pants.engine.target.DictStringToStringField):
    alias = "layers"


class OrasArtifactRepositoryField(pants.engine.target.StringField):
    alias = "repository"

class OrasArtifactTypeField(pants.engine.target.StringField):
    alias = "artifact_type"
    default = "application/vnd.unknown.artifact.v1"


# Targets =


class OrasArtifact(pants.engine.target.Target):
    alias = "oras_artifact"
    core_fields = (
        *pants.engine.target.COMMON_TARGET_FIELDS,
        OrasArtifactLayersField,
        OrasArtifactDependencies,
        OrasArtifactRepositoryField,
        OrasArtifactTypeField,
    )


# Intermediate steps =


class BuiltOrasArtifact(pants.core.goals.package.BuiltPackageArtifact):
    sha: str = ""
    tag: str = ""


class PublishOrasRequest(pants.core.goals.publish.PublishRequest):
    ...

@dataclasses.dataclass(frozen = True)
class OrasLayers:
    layers: tuple[tuple[str, str], ...]
    digest: pants.engine.fs.Digest

@dataclasses.dataclass(frozen = True)
class GitInfo:
    commit_hash: typing.Optional[str] = None
    git_tags: tuple[str, ...] = tuple() 

    @property
    def tags(self):
        return list(self.git_tags) + [self.commit_hash] if self.commit_hash else []

@dataclasses.dataclass(frozen = True)
class GitInfoRequest:
    get_commit_hash: bool = True
    get_tags: bool = True

# Fieldsets =


@dataclasses.dataclass(frozen=True)
class OrasArtifactFieldset(pants.engine.target.FieldSet):
    required_fields = (OrasArtifactLayersField, OrasArtifactRepositoryField, OrasArtifactRepositoryField)
    layers: OrasArtifactLayersField
    repository: OrasArtifactRepositoryField
    type: OrasArtifactTypeField

class OrasArtifactPackageFieldSet(
    OrasArtifactFieldset, pants.core.goals.package.PackageFieldSet
):
    ...

@dataclasses.dataclass(frozen=True)
class OrasPublishFieldSet(
    OrasArtifactFieldset, pants.core.goals.publish.PublishFieldSet
):
    publish_request_type = PublishOrasRequest

    def get_output_data(self) -> pants.core.goals.publish.PublishOutputData:
        return pants.core.goals.publish.PublishOutputData(
            {
                "publisher": "oras",
                **super().get_output_data(),
            }
        )

# Rules =

@pants.engine.rules.rule()
async def get_git_info(request: GitInfoRequest, root: pants.base.build_root.BuildRoot) -> GitInfo:
    git_paths = await pants.engine.rules.Get(
            pants.core.util_rules.system_binaries.BinaryPaths,
            pants.core.util_rules.system_binaries.BinaryPathRequest(binary_name = "git", search_path = ["/usr/bin","/bin"])
        )
    git_bin = git_paths.first_path
    if git_bin is None and any([request.get_commit_hash, request.get_tags]):
        raise OSError("The ORAS backend requires `git`.")
    else:
        git_bin = typing.cast(pants.core.util_rules.system_binaries.BinaryPath, git_bin)

    if request.get_commit_hash:
        git_commit_hash_proc = await pants.engine.rules.Get(
            pants.engine.process.ProcessResult,
            pants.engine.process.Process(
                argv=[git_bin.path, "-C", root.path, "log", "-n1", "--format=%H"],
                description="Get current git commit hash.",
                cache_scope=pants.engine.process.ProcessCacheScope.PER_SESSION,
            ),
        )
        git_commit_hash = git_commit_hash_proc.stdout.decode().strip("\n")
    else:
        git_commit_hash = None

    if request.get_tags:
        git_tags_proc = await pants.engine.rules.Get(
            pants.engine.process.ProcessResult,
            pants.engine.process.Process(
                argv=[git_bin.path, "-C", root.path, "tag", "-l"],
                description="Get git tags for current commit.",
                cache_scope=pants.engine.process.ProcessCacheScope.PER_SESSION,
            ),
        )
        git_tags = [
            *[t.strip() for t in git_tags_proc.stdout.decode().split("\n") if t],
        ]

    else:
        git_tags = [] 

    return GitInfo(
            commit_hash=git_commit_hash,
            git_tags = git_tags
        )

@pants.engine.rules.rule()
async def get_layers_digest(field: OrasArtifactLayersField) -> OrasLayers:
    if field.value is None:
        raise pants.engine.target.InvalidFieldException("Artifact must have at least one layer")
    digest = await pants.engine.rules.Get(pants.engine.fs.Digest, pants.engine.fs.PathGlobs(field.value.keys()))
    return OrasLayers(
            layers = tuple(field.value.items()),
            digest = digest,
        )

@pants.engine.rules.rule(
    desc="Package files into an ORAS artifact", level=pants.util.logging.LogLevel.WARN
)
async def package_oras_artifact(
    _: OrasArtifactPackageFieldSet,
) -> pants.core.goals.package.BuiltPackage:
    return pants.core.goals.package.BuiltPackage(digest = pants.engine.fs.EMPTY_DIGEST, artifacts=tuple())


@pants.engine.rules.rule(
    desc="Publish ORAS Artifact to OCI registries",
    level=pants.util.logging.LogLevel.WARN,
)
async def publish_oras_artifact(
    request: PublishOrasRequest,
    oras_tool: oras.subsystem.OrasTool,
    oras: oras.subsystem.Oras,
    platform: pants.engine.platform.Platform,
) -> pants.core.goals.publish.PublishProcesses:

    oras_bin = await pants.engine.rules.Get(
        pants.core.util_rules.external_tool.DownloadedExternalTool,
        pants.core.util_rules.external_tool.ExternalToolRequest,
        oras_tool.get_request(platform),
    )

    layers = await pants.engine.rules.Get(
                OrasLayers,
                OrasArtifactLayersField,
                request.field_set.layers,
            )

    digest = await pants.engine.rules.Get(
            pants.engine.fs.Digest, 
            pants.engine.fs.MergeDigests([layers.digest, oras_bin.digest]))

    layer_args = [f"{k}:{v}" for k,v in layers.layers]

    procs: list[tuple[str, pants.engine.process.Process]] = []

    git_info = await pants.engine.rules.Get(
            GitInfo,
            GitInfoRequest(
                get_commit_hash=oras.use_git_commit_hash,
                get_tags=oras.use_git_commit_tags
            ))

    tags = ["latest"] + git_info.tags
    for registry in oras.registries:
        url = registry.strip("/") + "/" + request.field_set.repository.value
        publish = await pants.engine.rules.Get(
                pants.engine.process.ProcessResult,
                pants.engine.process.Process(
                    [oras_bin.exe, "push", url, *layer_args],
                    input_digest = digest,
                    description = f"Push to {url}",
                    env={"HOME": "~/"},
                ))
        sha = publish.stdout.splitlines()[-1].split()[-1]
        for tag in tags:
            procs.append((f"{url}:{tag}", pants.engine.process.Process(
                    [oras_bin.exe, "tag", url+f"@{sha.decode()}", url+":"+tag],
                    input_digest = oras_bin.digest,
                    description=f"Tag {url} with {tag}",
                    env={"HOME": "~/"},
                )))

    return pants.core.goals.publish.PublishProcesses(
        [
            pants.core.goals.publish.PublishPackages(
                names=(name, ), 
                process =  pants.engine.process.InteractiveProcess.from_process(proc),
            )
            for name,proc in procs 
        ]
    )

# Register =

def rules():
    return [
        *pants.engine.rules.collect_rules(),
        *OrasPublishFieldSet.rules(),
        pants.engine.unions.UnionRule(
            pants.core.goals.package.PackageFieldSet, OrasArtifactPackageFieldSet
        ),
    ]


def target_types():
    return [
        OrasArtifact,
    ]
