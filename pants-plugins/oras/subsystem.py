import pants.core.util_rules.external_tool
import pants.engine.platform
import pants.option.option_types
import pants.option.subsystem
import pants.util.strutil


class Oras(pants.option.subsystem.Subsystem):
    options_scope = "oras"
    help = pants.util.strutil.help_text(
        """
        ORAS is a tool for uploading whatever you want to an OCI registry.
    """
    )
    registries = pants.option.option_types.StrListOption(
        help="A list of registries to push artifacts to.", default=list()
    )

    use_git_commit_hash = pants.option.option_types.BoolOption(
        help="Should pushed artifacts be tagged with the current Git commit hash?",
        default=True,
    )

    use_git_commit_tags = pants.option.option_types.BoolOption(
        help="Should pushed artifacts be tagged with the Git tags associated with the current commit?",
        default=True,
    )


class OrasTool(pants.core.util_rules.external_tool.ExternalTool):
    options_scope = "oras-cli"
    help = "Upload and download things from an OCI registry."
    default_version = "1.1.0"

    default_known_versions = [
        "1.1.0|macos_arm64|d52d3140b0bb9f7d7e31dcbf2a513f971413769c11f7d7a5599e76cc98e45007|3571806",
        "1.1.0|macos_x86_64|f8ac5dea53dd9331cf080f1025f0612e7b07c5af864a4fd609f97d8946508e45|3724034",
        "1.1.0|linux_x86_64|e09e85323b24ccc8209a1506f142e3d481e6e809018537c6b3db979c891e6ad7|3733462",
    ]

    def generate_exe(self, _: pants.engine.platform.Platform) -> str:
        return "./oras"

    def generate_url(self, plat: pants.engine.platform.Platform) -> str:
        platform = plat.value.replace("macos", "darwin").replace("x86_64", "amd64")
        return "/".join(
            (
                "https://github.com/oras-project/oras/releases/download",
                f"v{self.version}",
                f"oras_{self.version}_{platform}.tar.gz",
            )
        )


def rules():
    return [
        *Oras.rules(),
        *OrasTool.rules(),
    ]
