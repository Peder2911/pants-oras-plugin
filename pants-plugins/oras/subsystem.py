
import pants.option.subsystem
import pants.core.util_rules.external_tool
import pants.option.option_types
import pants.engine.platform

class Oras(pants.option.subsystem.Subsystem):
    ...

class OrasTool(pants.core.util_rules.external_tool.ExternalTool):
    options_scope = "oras"
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
        platform = plat.value.replace("macos","darwin").replace("amd64","x86_64")
        return f"https://github.com/oras-project/oras/releases/download/v{self.version}/oras_{self.version}_{platform}.tar.gz"


def rules():
    return [
        *Oras.rules(),
        *OrasTool.rules(),
    ]
