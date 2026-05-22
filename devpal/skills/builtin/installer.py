"""
InstallerSkill - 安装脚本生成 Skill

生成平台特定的安装脚本（Windows/macOS/Linux）。
"""

from pathlib import Path

from devpal.skills.base import BaseSkill, SkillContext, SkillResult
from devpal.core.templates.install_script_generator import InstallScriptGenerator


class InstallerSkill(BaseSkill):
    """安装脚本生成 Skill"""

    name = "installer_skill"
    description = "生成平台特定的安装脚本（Windows/macOS/Linux）"
    triggers = ["安装脚本", "installer", "部署脚本", "install script", "deployment script"]
    required_tools = []  # 不依赖 tool_registry

    def __init__(self):
        self.generator = InstallScriptGenerator()

    def can_handle(self, context: SkillContext) -> float:
        """判断是否能处理"""
        base_confidence = super().can_handle(context)

        # 检查是否提到平台
        platforms = ["windows", "macos", "linux", "跨平台", "cross-platform", "mac", "win"]
        query_lower = context.user_query.lower()
        for platform in platforms:
            if platform in query_lower:
                return min(base_confidence + 0.15, 1.0)

        return base_confidence

    def execute(self, context: SkillContext) -> SkillResult:
        """执行安装脚本生成"""
        # 1. 识别平台
        platform = self._detect_platform(context.user_query)

        # 2. 生成脚本
        if platform == "windows":
            script_content = self.generator.generate_powershell_script()
            script_path = "install.ps1"
        elif platform in ["macos", "linux", "cross_platform"]:
            script_content = self.generator.generate_bash_script()
            script_path = "install.sh"
        else:
            return SkillResult(
            success=False,
                content=f"不支持的平台: {platform}",
                metadata={"platform": platform}
         )

        # 3. 写入文件
        full_path = context.workspace_path / script_path
        full_path.write_text(script_content, encoding='utf-8')

        # 4. 返回结果
        return SkillResult(
            success=True,
            content=f"安装脚本生成成功: {script_path}",
            artifacts=[str(script_path)],
            metadata={
                "platform": platform,
              "lines": len(script_content.splitlines()),
                "size_bytes": len(script_content.encode('utf-8'))
            }
        )

    def _detect_platform(self, query: str) -> str:
        """检测目标平台"""
        query_lower = query.lower()
        if "windows" in query_lower or "win" in query_lower or "powershell" in query_lower:
            return "windows"
        elif "macos" in query_lower or "mac" in query_lower:
          return "macos"
        elif "linux" in query_lower:
          return "linux"
        elif "跨平台" in query_lower or "cross" in query_lower:
          return "cross_platform"
        else:
        # 默认生成 bash 脚本（适用于 macOS/Linux）
          return "cross_platform"
