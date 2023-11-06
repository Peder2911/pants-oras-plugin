"""
Package ORAS artifacts.

Pants does not currently allow "empty" publications. Each publication needs an
associated build, even though ORAS is only a storage layer and thus does not
have an associated internal build step.

This module defines the mock intermediate steps and goals needed to perform publish.
"""
import oras.targets
import pants.core.goals.package
import pants.engine.fs
import pants.engine.rules
import pants.engine.unions
import pants.util.logging


class BuiltOrasArtifact(pants.core.goals.package.BuiltPackageArtifact):
    sha: str = ""
    tag: str = ""


class OrasArtifactPackageFieldSet(
    oras.targets.OrasArtifactFieldset, pants.core.goals.package.PackageFieldSet
):
    ...


@pants.engine.rules.rule(
    desc="Package files into an ORAS artifact", level=pants.util.logging.LogLevel.WARN
)
async def package_oras_artifact(
    _: OrasArtifactPackageFieldSet,
) -> pants.core.goals.package.BuiltPackage:
    return pants.core.goals.package.BuiltPackage(
        digest=pants.engine.fs.EMPTY_DIGEST, artifacts=tuple()
    )


def rules():
    return [
        *pants.engine.rules.collect_rules(),
        pants.engine.unions.UnionRule(
            pants.core.goals.package.PackageFieldSet, OrasArtifactPackageFieldSet
        ),
    ]
