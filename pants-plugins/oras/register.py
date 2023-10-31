import logging
import dataclasses
import pants.core.goals.publish
import pants.engine.rules
import pants.engine.target
import pants.engine.process
import pants.engine.console
import pants.util.logging

logger = logging.getLogger(__name__)

class OrasSourcesField(pants.engine.target.MultipleSourcesField):
    alias = "sources"

class OrasArtifact(pants.engine.target.Target):
    alias = "oras_artifact"
    core_fields = (
            *pants.engine.target.COMMON_TARGET_FIELDS,
            OrasSourcesField,
        )

class OrasArtifactFieldset(pants.engine.target.FieldSet):
    required_fields = (
            OrasSourcesField,
            )

class PublishOrasRequest(pants.core.goals.publish.PublishRequest):
    ...

@dataclasses.dataclass(frozen = True)
class OrasPublishFieldSet(OrasArtifactFieldset, pants.core.goals.publish.PublishFieldSet):
    publish_request_type = PublishOrasRequest
    sources: OrasSourcesField

    def get_output_data(self) -> pants.core.goals.publish.PublishOutputData:
        return pants.core.goals.publish.PublishOutputData({
                "publisher": "oras",
                **super().get_output_data(),
            })

@pants.engine.rules.rule(desc = "Publish ORAS Artifact to OCI registries", level = pants.util.logging.LogLevel.WARN)
async def publish_test(request: PublishOrasRequest) -> pants.core.goals.publish.PublishProcesses:
    logger.critical("YOOOOO")
    return pants.core.goals.publish.PublishProcesses([
        pants.core.goals.publish.PublishPackages(
            names = (request.field_set.name,),
            description = "Hello world")
        ])

def rules():
    return [
        *pants.engine.rules.collect_rules(),
        *OrasPublishFieldSet.rules()
    ]

def target_types():
    return [
        OrasArtifact,
    ]
