"""
ORAS targets.

The ORAS plugin exposes two kinds of targets:
    * OrasArtifact (oras_artifact): Publish a set of files to an ORAS repository
    * OrasAttachment (oras_attachment): Attach a set of files to an ORAS repository
"""
import dataclasses

import pants.engine.rules
import pants.engine.target
import pants.util.strutil


class OrasArtifactDependencies(pants.engine.target.Dependencies):
    alias = "dependencies"
    help = pants.util.strutil.help_text(
        "Target dependencies needed to push this artifact."
    )


class OrasArtifactLayersField(pants.engine.target.DictStringToStringField):
    alias = "layers"
    help = pants.util.strutil.help_text(
        """
        Layers are the blobs you want to store.
        A dictionary where the keys are filenames and the values are media types.
    """
    )


class OrasArtifactRepositoryField(pants.engine.target.StringField):
    alias = "repository"
    help = pants.util.strutil.help_text(
        """
        Name of the repository that you want to push to.
    """
    )


class OrasArtifactTypeField(pants.engine.target.StringField):
    alias = "artifact_type"
    default = "application/vnd.unknown.artifact.v1"
    help = pants.util.strutil.help_text(
        """
        Media type of the artifact. Use the following format:
        application/vnd.autostore.{your media type}.

        The media type should reflect what the artifact contains.
    """
    )


class OrasArtifactAnnotationsField(pants.engine.target.DictStringToStringField):
    alias = "annotations"
    help = pants.util.strutil.help_text(
        """
        Arbitrary mapping of strings t
    """
    )


class OrasArtifact(pants.engine.target.Target):
    alias = "oras_artifact"
    help = pants.util.strutil.help_text(
        """
        ORAS artifacts let you use OCI registries as blob storage.
    """
    )
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
    required_fields = (
        OrasArtifactLayersField,
        OrasArtifactRepositoryField,
        OrasArtifactDependencies,
    )
    annotations: OrasArtifactAnnotationsField
    artifact_type: OrasArtifactTypeField
    layers: OrasArtifactLayersField
    repository: OrasArtifactRepositoryField
    dependencies: OrasArtifactDependencies


# class OrasAttachment(pants.engine.target.Target):
#    alias = "oras_attachment"
#    core_fields = (
#        *pants.engine.target.COMMON_TARGET_FIELDS,
#        OrasArtifactLayersField,
#        OrasArtifactDependencies,
#        OrasArtifactRepositoryField,
#        OrasArtifactTypeField,
#        OrasArtifactAnnotationsField,
#    )


def rules():
    return [*pants.engine.rules.collect_rules()]


def target_types():
    return [
        OrasArtifact,
    ]
