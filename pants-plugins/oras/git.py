"""
Rules for producing Git information required to properly tag ORAS artifacts.
"""
import pants.core.util_rules.system_binaries
import pants.base.build_root
import pants.engine.rules
import pants.engine.process
import dataclasses
import typing

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
        #*pants.engine.rules.collect_rules(),
        #*OrasPublishFieldSet.rules(),
        #pants.engine.unions.UnionRule(
        #    pants.core.goals.package.PackageFieldSet, OrasArtifactPackageFieldSet
        #),

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
            git_tags = tuple(git_tags)
        )

def rules():
    return [
        *pants.engine.rules.collect_rules()
    ]
