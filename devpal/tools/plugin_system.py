# -*- coding: utf-8 -*-
"""
Plugin System Tool
动态加载和管理第三方插件工具
"""
import os
import sys
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class PluginSystemTool(BaseTool):
    """插件系统 - 动态加载和管理第三方工具"""

    name = "plugin_system"
    description = "插件系统，用于加载、管理和卸载第三方工具插件"

    class Parameters(BaseModel):
        action: str = Field(
            default="list_plugins",
            description="操作类型: list_plugins(列出插件), load_plugin(加载插件), unload_plugin(卸载插件), create_template(生成插件模板), show_help(显示帮助)"
        )
        plugin_path: Optional[str] = Field(
            default=None,
            description="插件文件路径（.py 文件）"
        )
        plugin_name: Optional[str] = Field(
            default=None,
            description="插件名称（用于卸载）"
        )
        template_name: Optional[str] = Field(
            default=None,
            description="模板名称: 'basic'(基础), 'full'(完整)"
        )
        target_dir: Optional[str] = Field(
            default=None,
            description="生成模板的目标目录"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        base_path = Path(__file__).parent
        plugins_dir = base_path.parent.parent / "plugins"
        plugins_dir.mkdir(exist_ok=True)

        # 添加插件目录到 Python 路径
        if str(plugins_dir) not in sys.path:
            sys.path.insert(0, str(plugins_dir))

        try:
            if params.action == "list_plugins":
                return self._list_plugins(plugins_dir)
            elif params.action == "load_plugin":
                return self._load_plugin(params.plugin_path, plugins_dir)
            elif params.action == "unload_plugin":
                return self._unload_plugin(params.plugin_name)
            elif params.action == "create_template":
                return self._create_template(params.template_name, params.target_dir or str(plugins_dir))
            elif params.action == "show_help":
                return self._show_help()
            else:
                return ToolResult.error(f"不支持的操作类型: {params.action}")
        except Exception as e:
            return ToolResult.error(f"插件系统操作失败: {str(e)}", error_type="plugin_error")

    def _list_plugins(self, plugins_dir: Path) -> ToolResult:
        """列出所有已加载和可用的插件"""
        # 已注册的工具
        from devpal.tools import registry
        registered = registry.list_tool_names()

        # 可用的插件文件
        available = []
        if plugins_dir.exists():
            for f in plugins_dir.rglob("*.py"):
                if f.name != "__init__.py":
                    rel_path = f.relative_to(plugins_dir.parent)
                    available.append(str(rel_path))

        # 内置的插件系统工具
        plugin_tools = [name for name in registered if name in ['self_source_reader', 'self_improve', 'plugin_system']]

        output = "=" * 60 + "\n"
        output += "DevPal 插件系统\n"
        output += "=" * 60 + "\n\n"

        output += f"📦 已注册工具: {len(registered)} 个\n"
        output += f"🔌 系统插件: {', '.join(plugin_tools) if plugin_tools else '无'}\n"
        output += f"📁 插件目录: {plugins_dir}\n\n"

        output += "可用的插件文件:\n"
        if available:
            for plugin in available:
                output += f"  - {plugin}\n"
        else:
            output += "  (暂无插件文件)\n"

        output += "\n" + "-" * 60 + "\n"
        output += "所有工具列表:\n"
        for i, name in enumerate(registered, 1):
            from devpal.tools import registry
            tool = registry.get(name)
            desc = tool.description[:50] if tool else ""
            output += f"  {i:2d}. {name} - {desc}...\n"

        return ToolResult.ok(
            output,
            registered_tools=registered,
            available_plugins=available,
            plugin_tools=plugin_tools
        )

    def _load_plugin(self, plugin_path: Optional[str], plugins_dir: Path) -> ToolResult:
        """加载一个插件"""
        if not plugin_path:
            return ToolResult.error("请指定插件文件路径")

        full_path = Path(plugin_path)
        if not full_path.is_absolute():
            full_path = Path.cwd() / plugin_path

        if not full_path.exists():
            # 尝试在插件目录中查找
            full_path = plugins_dir / plugin_path
            if not full_path.exists():
                return ToolResult.error(f"找不到插件文件: {plugin_path}")

        if full_path.suffix != ".py":
            return ToolResult.error("插件必须是 .py 文件")

        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                f"devpal_plugin_{full_path.stem}",
                str(full_path)
            )
            if not spec or not spec.loader:
                return ToolResult.error("无法加载插件模块")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找 BaseTool 的子类
            loaded = []
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, BaseTool) and obj != BaseTool:
                    # 实例化并注册
                    tool_instance = obj()
                    from devpal.tools import registry
                    registry.register(tool_instance)
                    loaded.append(tool_instance.name)

            if loaded:
                output = f"✅ 插件加载成功: {full_path.name}\n"
                output += f"已加载工具: {', '.join(loaded)}\n\n"
                output += "现在可以通过 registry.execute_tool() 调用这些工具了！"
                return ToolResult.ok(output, loaded_tools=loaded)
            else:
                return ToolResult.error(f"插件中没有找到 BaseTool 的子类: {full_path.name}")

        except Exception as e:
            return ToolResult.error(f"加载插件失败: {str(e)}")

    def _unload_plugin(self, plugin_name: Optional[str]) -> ToolResult:
        """卸载一个插件"""
        if not plugin_name:
            return ToolResult.error("请指定要卸载的插件名称")

        from devpal.tools import registry
        if plugin_name not in registry.list_tool_names():
            return ToolResult.error(f"工具未注册: {plugin_name}")

        # 注意：实际从 Python 解释器中卸载模块很复杂
        # 这里只是从注册表中移除
        from devpal.tools import registry
        registry.unregister(plugin_name)

        return ToolResult.ok(
            f"✅ 插件已从注册表中移除: {plugin_name}\n"
            f"注意: Python 模块可能仍保留在内存中，但该工具已不再可用。"
        )

    def _create_template(self, template_type: Optional[str], target_dir: str) -> ToolResult:
        """生成插件模板文件"""
        template_type = template_type or "basic"

        if template_type == "basic":
            template = self._get_basic_template()
        elif template_type == "full":
            template = self._get_full_template()
        else:
            return ToolResult.error(f"不支持的模板类型: {template_type}. 使用 'basic' 或 'full'")

        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        filename = f"my_plugin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        full_path = target_path / filename
        full_path.write_text(template, encoding="utf-8")

        output = f"✅ 插件模板已生成: {full_path}\n\n"
        output += "下一步:\n"
        output += "  1. 编辑这个文件，实现你的工具逻辑\n"
        output += "  2. 调用 plugin_system 的 load_plugin 来加载它\n"
        output += "  3. 然后就可以使用你的新工具了！\n"

        return ToolResult.ok(output, template_file=str(full_path))

    def _get_basic_template(self) -> str:
        """基础插件模板"""
        return '''# -*- coding: utf-8 -*-
"""
DevPal 插件模板 - 基础版
把你的工具逻辑写在这里！
"""
from typing import Optional
from pydantic import BaseModel, Field
from devpal.tools.base import BaseTool, ToolResult


class MyCustomTool(BaseTool):
    """自定义工具 - 在这里实现你的工具逻辑"""

    name = "my_custom_tool"
    description = "在这里写你的工具描述"

    class Parameters(BaseModel):
        param1: str = Field(description="第一个参数")
        param2: Optional[int] = Field(default=0, description="第二个参数（可选）")

    def _execute(self, params: Parameters) -> ToolResult:
        """在这里实现你的工具逻辑"""
        # TODO: 替换成你的实际代码
        result = f"你调用了 my_custom_tool!"
        result += f"\\nparam1 = {params.param1}"
        result += f"\\nparam2 = {params.param2}"

        return ToolResult.ok(result, param1=params.param1)


# 可选：如果有多个工具，可以在这里列出
# __all__ = ["MyCustomTool"]
'''

    def _get_full_template(self) -> str:
        """完整插件模板"""
        return '''# -*- coding: utf-8 -*-
"""
DevPal 插件模板 - 完整版
包含：参数校验、重试机制、元数据、多工具示例
"""
import subprocess
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from devpal.tools.base import BaseTool, ToolResult, retry, ToolSecurity


class FileAnalyzerTool(BaseTool):
    """文件分析工具示例"""

    name = "file_analyzer"
    description = "分析文件内容，统计行数、字符数、代码行数等"

    class Parameters(BaseModel):
        file_path: str = Field(description="要分析的文件路径")
        show_lines: bool = Field(default=False, description="是否显示内容预览")
        max_preview_lines: int = Field(default=10, description="预览行数上限")

    @retry(max_retries=2, delay=0.5)
    def _execute(self, params: Parameters) -> ToolResult:
        """执行文件分析"""
        try:
            with open(params.file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\\n")
            non_empty = sum(1 for l in lines if l.strip())
            comment_lines = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*")))

            result = {
                "file": params.file_path,
                "total_lines": len(lines),
                "non_empty_lines": non_empty,
                "comment_lines": comment_lines,
                "total_chars": len(content),
            }

            output = f"文件分析结果: {params.file_path}\\n"
            output += "=" * 50 + "\\n"
            output += f"总行数: {result['total_lines']}\\n"
            output += f"非空行: {result['non_empty_lines']}\\n"
            output += f"注释行: {result['comment_lines']}\\n"
            output += f"字符数: {result['total_chars']}\\n"

            if params.show_lines and len(lines) <= params.max_preview_lines:
                output += "\\n内容预览:\\n"
                for i, line in enumerate(lines[:params.max_preview_lines], 1):
                    output += f"  {i:3d}. {line}\\n"

            return ToolResult.ok(output, **result)

        except Exception as e:
            return ToolResult.error(f"分析失败: {str(e)}")


class CommandRunnerTool(BaseTool):
    """命令执行工具示例"""

    name = "safe_command_runner"
    description = "安全地执行本地命令（带安全检查）"

    class Parameters(BaseModel):
        command: str = Field(description="要执行的命令")
        timeout: int = Field(default=30, description="超时时间（秒）")

    @retry(max_retries=1, delay=0.0)
    def _execute(self, params: Parameters) -> ToolResult:
        """安全执行命令"""
        # 使用内置的安全检查
        safe, reason = ToolSecurity.check_command_safety(params.command)
        if not safe:
            return ToolResult.error(f"安全检查不通过: {reason}")

        try:
            result = subprocess.run(
                params.command,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=params.timeout
            )

            output = f"命令执行结果 (返回码: {result.returncode})\\n"
            if result.stdout:
                output += f"STDOUT:\\n{result.stdout}\\n"
            if result.stderr:
                output += f"STDERR:\\n{result.stderr}\\n"

            return ToolResult.ok(output, returncode=result.returncode)

        except subprocess.TimeoutExpired:
            return ToolResult.error(f"命令执行超时 ({params.timeout}秒)")
        except Exception as e:
            return ToolResult.error(f"执行失败: {str(e)}")


# 所有需要自动注册的工具类（可选）
# 如果使用 load_plugin，会自动发现所有 BaseTool 子类
# __all__ = ["FileAnalyzerTool", "CommandRunnerTool"]
'''

    def _show_help(self) -> ToolResult:
        """显示帮助信息"""
        output = "=" * 60 + "\n"
        output += "DevPal 插件系统 使用帮助\n"
        output += "=" * 60 + "\n\n"

        output += "📌 快速开始:\n\n"
        output += "  1. 生成插件模板:\n"
        output += '     registry.execute_tool("plugin_system", {\n'
        output += '         "action": "create_template",\n'
        output += '         "template_name": "basic"\n'
        output += "     })\n\n"

        output += "  2. 编辑生成的 .py 文件，实现你的工具逻辑\n\n"

        output += "  3. 加载插件:\n"
        output += '     registry.execute_tool("plugin_system", {\n'
        output += '         "action": "load_plugin",\n'
        output += '         "plugin_path": "plugins/my_plugin.py"\n'
        output += "     })\n\n"

        output += "  4. 使用新工具:\n"
        output += '     registry.execute_tool("my_custom_tool", {...})\n\n'

        output += "-" * 60 + "\n\n"

        output += "🔧 可用操作:\n\n"
        output += "  • list_plugins  - 列出所有已加载的插件和工具\n"
        output += "  • load_plugin   - 加载一个新的插件文件\n"
        output += "  • unload_plugin - 从注册表中移除一个工具\n"
        output += "  • create_template - 生成插件模板 (basic/full)\n"
        output += "  • show_help     - 显示此帮助信息\n\n"

        output += "-" * 60 + "\n\n"

        output += "💡 提示:\n"
        output += "  - 插件必须继承 devpal.tools.base.BaseTool\n"
        output += "  - 使用 @retry 装饰器添加重试功能\n"
        output += "  - 使用 ToolSecurity 做安全检查\n"
        output += "  - 插件目录默认在项目根目录的 plugins/\n"

        return ToolResult.ok(output)
