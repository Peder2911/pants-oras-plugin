"""
ORAS targets.

The ORAS plugin exposes two kinds of targets:
    * OrasArtifact (oras_artifact): Publish a set of files to an ORAS repository
    * OrasAttachment (oras_attachment): Attach a set of files to an ORAS repository
"""
import dataclasses
import pants.engine.target
import pants.engine.rules

class OrasArtifactDependencies(pants.engine.target.Dependencies):
    alias = "dependencies"


class OrasArtifactLayersField(pants.engine.target.DictStringToStringField):
    alias = "layers"


class OrasArtifactRepositoryField(pants.engine.target.StringField):
    alias = "repository"

class OrasArtifactTypeField(pants.engine.target.StringField):
    alias = "artifact_type"
    default = "application/vnd.unknown.artifact.v1"

class OrasArtifactAnnotationsField(pants.engine.target.DictStringToStringField):
    alias = "annotations"

class OrasArtifact(pants.engine.target.Target):
    alias = "oras_artifact"
    core_fields = (
        *pants.engine.target.COMMON_TARGET_FIELDS,
        OrasArtifactAnnotationsField,
        OrasArtifactDependencies,
        OrasArtifactLayersField,
        OrasArtifactRepositoryField,
        OrasArtifactTypeField,
    )

@dataclasses.dataclass(frozen=True)
class OrasArtifactFieldset(pants.engine.target.FieldSet):
    required_fields = (OrasArtifactLayersField, OrasArtifactRepositoryField, OrasArtifactRepositoryField)
    annotations: OrasArtifactAnnotationsField
    artifact_type: OrasArtifactTypeField
    layers: OrasArtifactLayersField
    repository: OrasArtifactRepositoryField

class OrasAttachment(pants.engine.target.Target):
    alias = "oras_attachment"
    core_fields = (
        *pants.engine.target.COMMON_TARGET_FIELDS,
        OrasArtifactLayersField,
        OrasArtifactDependencies,
        OrasArtifactRepositoryField,
        OrasArtifactTypeField,
        OrasArtifactAnnotationsField,
    )

def rules():
    return [
        *pants.engine.rules.collect_rules()
    ]

def target_types():
    return [
        OrasArtifact,
        OrasAttachment,
    ]
