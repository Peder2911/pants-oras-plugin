"""
Build files into Oras Artifacts for publication.
"""
import oras.targets
import oras.goals.package
import oras.goals.publish
import oras.git

def rules():
    return [
        *oras.targets.rules(),
        *oras.goals.package.rules(),
        *oras.goals.publish.rules(),
        *oras.git.rules(),
    ]


def target_types():
    return [
        *oras.targets.target_types()
    ]
