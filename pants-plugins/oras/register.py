"""
Build files into Oras Artifacts for publication.

Targets:
┌────────────┐
│OrasArtifact│
└────────────┘
      ├────────────────────────┐
      ▼        satisfies       ▼
┌───────────────────┐┌───────────────────┐
│OrasPublishFieldSet││OrasPackageFieldSet│
└───────────────────┘└───────────────────┘

Rules:                
┌───────────────────┐  ┌────────────┐
│OrasPackageFieldSet│─►│BuiltPackage│
└───────────────────┘  └────────────┘
                              │
┌───────────────────┐         │
│OrasPublishFieldSet│         ?
└───────────────────┘         │
      ▲                       │
      │  has a                ▼
┌──────────────────┐  ┌────────────────┐
│PublishOrasRequest│─►│PublishProcesses│
└──────────────────┘  └────────────────┘
"""
import logging
import dataclasses
import pants.core.goals.publish
import pants.engine.rules
import pants.engine.target
import pants.engine.process
import pants.engine.console
import pants.core.goals.package
import pants.engine.unions
import pants.util.logging
import pants.engine.fs

logger = logging.getLogger(__name__)

# Fields =

class OrasArtifactSourcesField(pants.engine.target.MultipleSourcesField):
    alias = "sources"

class OrasArtifactTagField(pants.engine.target.StringField):
    required =  True
    alias = "tag"

# Targets =

class OrasArtifact(pants.engine.target.Target):
    alias = "oras_artifact"
    core_fields = (
            *pants.engine.target.COMMON_TARGET_FIELDS,
            OrasArtifactSourcesField,
            OrasArtifactTagField,
        )

# Intermediate steps =

class BuiltOrasArtifact(pants.core.goals.package.BuiltPackageArtifact):
    sha: str = ""
    tag: str = ""

class PublishOrasRequest(pants.core.goals.publish.PublishRequest):
    ...

# Fieldsets =

@dataclasses.dataclass(frozen = True)
class OrasArtifactFieldset(pants.engine.target.FieldSet):
    required_fields = (
            OrasArtifactSourcesField,
            OrasArtifactTagField
            )

    sources: OrasArtifactSourcesField
    tag: OrasArtifactTagField

@dataclasses.dataclass(frozen = True)
class OrasPublishFieldSet(OrasArtifactFieldset, pants.core.goals.publish.PublishFieldSet):
    publish_request_type = PublishOrasRequest
    sources: OrasArtifactSourcesField

    def get_output_data(self) -> pants.core.goals.publish.PublishOutputData:
        return pants.core.goals.publish.PublishOutputData({
                "publisher": "oras",
                **super().get_output_data(),
            })

class OrasArtifactPackageFieldSet(OrasArtifactFieldset, pants.core.goals.package.PackageFieldSet):
    ...

# Rules =

@pants.engine.rules.rule(desc = "Package files into an ORAS artifact", level = pants.util.logging.LogLevel.WARN)
async def package_oras_artifact(fieldset: OrasArtifactPackageFieldSet) -> pants.core.goals.package.BuiltPackage:
    if (tag := fieldset.tag.value) is None:
        raise pants.engine.target.InvalidTargetException("Must provide a value to tag.")
    result = await pants.engine.rules.Get(
            pants.engine.process.ProcessResult,
            pants.engine.process.Process(["/bin/echo",tag], description = "do nothing"))
    ls = await pants.engine.rules.Get(
            pants.engine.process.ProcessResult,
            pants.engine.process.Process(["/bin/ls"], description = "do nothing"))
    logger.critical(ls.stdout)
    pwd = await pants.engine.rules.Get(
            pants.engine.process.ProcessResult,
            pants.engine.process.Process(["/bin/pwd"], description = "do nothing"))
    logger.critical(pwd.stdout)
    return pants.core.goals.package.BuiltPackage(
            digest = result.output_digest,
            artifacts = (BuiltOrasArtifact(relpath = None),)
        )


@pants.engine.rules.rule(desc = "Publish ORAS Artifact to OCI registries", level = pants.util.logging.LogLevel.WARN)
async def publish_test(request: PublishOrasRequest) -> pants.core.goals.publish.PublishProcesses:
    logger.critical(request.packages)
    return pants.core.goals.publish.PublishProcesses([
        pants.core.goals.publish.PublishPackages(
            names = (request.field_set.tag,),
            description = "Not publishing anything!")
        ])

# Register =

def rules():
    return [
        *pants.engine.rules.collect_rules(),
        *OrasPublishFieldSet.rules(),
        pants.engine.unions.UnionRule(pants.core.goals.package.PackageFieldSet, OrasArtifactPackageFieldSet),
    ]

def target_types():
    return [
        OrasArtifact,
    ]

