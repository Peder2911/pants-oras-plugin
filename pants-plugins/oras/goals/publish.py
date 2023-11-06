"""
Publish ORAS artifacts and attachments.

Rules:
    get_layers_digest:
    ┌───────────────────────┐           ┌──────────┐
    │OrasArtifactLayersField│──────────►│OrasLayers│
    └───────────────────────┘           └──────────┘

    publish_oras_artifact:
    ┌──────────────────┐
    │PublishOrasRequest│─────────────┐
    └──────────────────┘             │
    ┌───────────────────────┐        │
    │oras.subsystem.OrasTool│────────┤  ┌────────────────┐
    └───────────────────────┘        ├─►│PublishProcesses│
    ┌───────────────────┐            │  └────────────────┘
    │oras.subsystem.Oras│────────────┤
    └───────────────────┘            │
    ┌──────────────────────────────┐ │
    │pants.engine.platform.Platform│─┘
    └──────────────────────────────┘

"""
import dataclasses
import functools
import operator

import oras.git
import oras.subsystem
import oras.targets
import pants.core.goals.publish
import pants.core.util_rules.external_tool
import pants.engine.engine_aware
import pants.engine.fs
import pants.engine.platform
import pants.engine.process
import pants.engine.rules
import pants.engine.target
import pants.util.logging
import pants.core.goals.package
import logging
logger = logging.getLogger(__name__)


class PublishOrasRequest(pants.core.goals.publish.PublishRequest):
    ...


@dataclasses.dataclass(frozen=True)
class OrasPublishFieldSet(
    oras.targets.OrasArtifactFieldset, pants.core.goals.publish.PublishFieldSet
):
    publish_request_type = PublishOrasRequest

    def get_output_data(self) -> pants.core.goals.publish.PublishOutputData:
        return pants.core.goals.publish.PublishOutputData(
            {
                "publisher": "oras",
                **super().get_output_data(),
            }
        )


@dataclasses.dataclass(frozen=True)
class OrasLayers:
    layers: tuple[tuple[str, str], ...]
    digest: pants.engine.fs.Digest


def rules():
    return [
        *pants.engine.rules.collect_rules(),
        *OrasPublishFieldSet.rules(),
    ]


@pants.engine.rules.rule()
async def get_layers_digest(field: oras.targets.OrasArtifactLayersField) -> OrasLayers:
    if field.value is None:
        raise pants.engine.target.InvalidFieldException(
            "Artifact must have at least one layer"
        )
    digest = await pants.engine.rules.Get(
        pants.engine.fs.Digest, pants.engine.fs.PathGlobs(field.value.keys())
    )
    return OrasLayers(
        layers=tuple(field.value.items()),
        digest=digest,
    )


@pants.engine.rules.rule(
    desc="Publish ORAS Artifact to OCI registries",
    level=pants.util.logging.LogLevel.WARN,
)
async def publish_oras_artifact(
    request: PublishOrasRequest,
    oras_tool: oras.subsystem.OrasTool,
    oras_subsystem: oras.subsystem.Oras,
    platform: pants.engine.platform.Platform,
) -> pants.core.goals.publish.PublishProcesses:
    request.packages

    oras_bin = await pants.engine.rules.Get(
        pants.core.util_rules.external_tool.DownloadedExternalTool,
        pants.core.util_rules.external_tool.ExternalToolRequest,
        oras_tool.get_request(platform),
    )

    layers = await pants.engine.rules.Get(
        OrasLayers,
        oras.targets.OrasArtifactLayersField,
        request.field_set.layers,
    )

    request.field_set.dependencies
    deps = await pants.engine.rules.Get(
            pants.engine.target.Targets,
            pants.engine.target.DependenciesRequest(request.field_set.dependencies))
    deps_package_field_sets = await pants.engine.rules.Get(
            pants.engine.target.FieldSetsPerTarget,
            pants.engine.target.FieldSetsPerTargetRequest(pants.core.goals.package.PackageFieldSet, deps))
    deps_packages = await pants.engine.rules.MultiGet(
            pants.engine.rules.Get(pants.core.goals.package.BuiltPackage, pants.core.goals.package.PackageFieldSet, fs) for fs in deps_package_field_sets.field_sets)
    deps_packages_digest = await pants.engine.rules.Get(pants.engine.fs.Digest, pants.engine.fs.MergeDigests([pkg.digest for pkg in deps_packages]))
    logger.critical(deps_packages_digest)

    digest = await pants.engine.rules.Get(
        pants.engine.fs.Digest,
        pants.engine.fs.MergeDigests([layers.digest, oras_bin.digest, deps_packages_digest]),
    )

    layer_args = [f"{k}:{v}" for k, v in layers.layers]

    procs: list[tuple[str, pants.engine.process.Process]] = []

    git_info = await pants.engine.rules.Get(
        oras.git.GitInfo,
        oras.git.GitInfoRequest(
            get_commit_hash=oras_subsystem.use_git_commit_hash,
            get_tags=oras_subsystem.use_git_commit_tags,
        ),
    )

    tags = ["latest"] + git_info.tags
    annotations = request.field_set.annotations.value or dict()
    annotations = functools.reduce(
        operator.add,
        [
            ["--annotation", f"{k}={v}"]
            for k, v in annotations.items()  # request.field_set.annotations.value.items()
        ],
        [],
    )
    for registry in oras_subsystem.registries:
        url = registry.strip("/") + "/" + request.field_set.repository.value
        publish = await pants.engine.rules.Get(
            pants.engine.process.ProcessResult,
            pants.engine.process.Process(
                [
                    oras_bin.exe,
                    "push",
                    "--artifact-type",
                    request.field_set.artifact_type.value,
                    *annotations,
                    url,
                    *layer_args,
                ],
                input_digest=digest,
                description=f"Push to {url}",
                env={"HOME": "~/"},
            ),
        )
        sha = publish.stdout.splitlines()[-1].split()[-1]
        for tag in tags:
            procs.append(
                (
                    f"{url}:{tag}",
                    pants.engine.process.Process(
                        [
                            oras_bin.exe,
                            "tag",
                            url + f"@{sha.decode()}",
                            url + ":" + tag,
                        ],
                        input_digest=oras_bin.digest,
                        description=f"Tag {url} with {tag}",
                        env={"HOME": "~/"},
                    ),
                )
            )

    return pants.core.goals.publish.PublishProcesses(
        [
            pants.core.goals.publish.PublishPackages(
                names=(name,),
                process=pants.engine.process.InteractiveProcess.from_process(proc),
            )
            for name, proc in procs
        ]
    )
