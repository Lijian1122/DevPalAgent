# -*- coding: utf-8 -*-
"""
Self Improvement Tool
Agent 自我修复和自我改进的工具
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class SelfImproveTool(BaseTool):
    """Agent 自我修复和自我改进工具"""

    name = "self_improve"
    description = "Agent 自我修复 bug 和自我改进代码的工具"

    class Parameters(BaseModel):
        action: str = Field(
            default="analyze_issue",
            description="操作类型: analyze_issue(分析问题), apply_fix(应用修复), create_backup(创建备份), list_backups(列出备份), restore_backup(恢复备份), run_self_test(自检)"
        )
        target_file: Optional[str] = Field(
            default=None,
            description="目标文件路径（相对于 devpal 根目录）"
        )
        new_content: Optional[str] = Field(
            default=None,
            description="新的文件内容（用于应用修复）"
        )
        backup_name: Optional[str] = Field(
            default=None,
            description="备份名称（用于恢复备份）"
        )
        description: Optional[str] = Field(
            default=None,
            description="变更描述"
        )
        test_command: Optional[str] = Field(
            default=None,
            description="自检命令"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        base_path = Path(__file__).parent.parent
        backup_path = base_path.parent / ".devpal_backups"
        backup_path.mkdir(exist_ok=True)

        try:
            if params.action == "create_backup":
                return self._create_backup(base_path, backup_path, params.description)
            elif params.action == "list_backups":
                return self._list_backups(backup_path)
            elif params.action == "restore_backup":
                return self._restore_backup(base_path, backup_path, params.backup_name)
            elif params.action == "analyze_issue":
                return self._analyze_issue(base_path, params.target_file, params.description)
            elif params.action == "apply_fix":
                return self._apply_fix(base_path, params.target_file, params.new_content, params.description)
            elif params.action == "run_self_test":
                return self._run_self_test(base_path, params.test_command)
            else:
                return ToolResult.error(f"不支持的操作类型: {params.action}")
        except Exception as e:
            return ToolResult.error(f"操作失败: {str(e)}", error_type="self_improve_error")

    def _create_backup(self, base_path: Path, backup_path: Path, description: Optional[str]) -> ToolResult:
        """创建当前代码的备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        if description:
            backup_name += f"_{description[:30].replace(' ', '_')}"

        backup_dir = backup_path / backup_name
        backup_dir.mkdir(parents=True)

        # 复制 devpal 目录
        shutil.copytree(base_path, backup_dir / "devpal")

        # 创建说明文件
        with open(backup_dir / "info.txt", "w", encoding="utf-8") as f:
            f.write(f"Backup created: {datetime.now()}\n")
            f.write(f"Description: {description or 'No description'}\n")

        return ToolResult.ok(
            f"✅ 备份创建成功: {backup_name}\n路径: {backup_dir}",
            backup_name=backup_name,
            backup_path=str(backup_dir)
        )

    def _list_backups(self, backup_path: Path) -> ToolResult:
        """列出所有备份"""
        if not backup_path.exists():
            return ToolResult.ok("暂无备份")

        backups = sorted([d.name for d in backup_path.iterdir() if d.is_dir()])

        output = f"可用备份列表（共 {len(backups)} 个）:\n\n"
        for b in backups:
            info_file = backup_path / b / "info.txt"
            desc = ""
            if info_file.exists():
                with open(info_file, encoding="utf-8") as f:
                    content = f.read()
                    if "Description:" in content:
                        desc_line = [l for l in content.split("\n") if "Description:" in l][0]
                        desc = desc_line.split("Description:", 1)[1].strip()

            output += f"  - {b}"
            if desc and desc != "No description":
                output += f" ({desc[:50]})"
            output += "\n"

        return ToolResult.ok(output, backups=backups)

    def _restore_backup(self, base_path: Path, backup_path: Path, backup_name: Optional[str]) -> ToolResult:
        """从备份恢复"""
        if not backup_name:
            return ToolResult.error("请指定要恢复的备份名称")

        backup_dir = backup_path / backup_name
        if not backup_dir.exists():
            return ToolResult.error(f"备份不存在: {backup_name}")

        # 创建当前状态的备份（预防恢复失败）
        safety_backup = self._create_backup(base_path, backup_path, "pre_restore_safety")
        if not safety_backup.success:
            return safety_backup

        # 恢复代码
        shutil.rmtree(base_path)
        shutil.copytree(backup_dir / "devpal", base_path)

        return ToolResult.ok(
            f"✅ 从备份恢复成功: {backup_name}\n"
            f"安全备份已保存: {safety_backup.metadata.get('backup_name')}"
        )

    def _analyze_issue(self, base_path: Path, target_file: Optional[str], description: Optional[str]) -> ToolResult:
        """分析潜在的代码问题"""
        issues = []

        if target_file:
            # 分析单个文件
            file_path = base_path / target_file
            if not file_path.exists():
                return ToolResult.error(f"文件不存在: {target_file}")

            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # 简单的问题检测
            for i, line in enumerate(lines, 1):
                # 检测 TODO/FIXME
                if "TODO" in line and "#" in line.split("TODO")[0]:
                    issues.append({
                        "type": "todo",
                        "file": target_file,
                        "line": i,
                        "content": line.strip(),
                        "severity": "info"
                    })
                # 检测 FIXME
                if "FIXME" in line and "#" in line.split("FIXME")[0]:
                    issues.append({
                        "type": "fixme",
                        "file": target_file,
                        "line": i,
                        "content": line.strip(),
                        "severity": "warning"
                    })
                # 检测 print 调试语句
                if "print(" in line and "#" not in line.split("print(")[0] and target_file.endswith('.py'):
                    if "__main__" not in content.split("\n")[max(0, i-10):i]:
                        issues.append({
                            "type": "debug_code",
                            "file": target_file,
                            "line": i,
                            "content": line.strip(),
                            "severity": "info"
                        })
        else:
            # 扫描整个代码库
            for py_file in base_path.rglob("*.py"):
                rel_path = py_file.relative_to(base_path)
                try:
                    content = py_file.read_text(encoding="utf-8")
                    if "FIXME" in content:
                        issues.append({
                            "type": "fixme_found",
                            "file": str(rel_path),
                            "severity": "info"
                        })
                except Exception:
                    pass

        output = f"代码分析结果（发现 {len(issues)} 个潜在问题）:\n\n"
        for issue in issues:
            output += f"  [{issue['severity']}] {issue['file']}"
            if 'line' in issue:
                output += f":{issue['line']}"
            output += f" - {issue['type']}\n"
            if 'content' in issue:
                output += f"      {issue['content']}\n"

        return ToolResult.ok(output, issues=issues, issue_count=len(issues))

    def _apply_fix(self, base_path: Path, target_file: Optional[str], new_content: Optional[str], description: Optional[str]) -> ToolResult:
        """应用代码修复"""
        if not target_file:
            return ToolResult.error("请指定目标文件")

        if not new_content:
            return ToolResult.error("请提供新的文件内容")

        file_path = base_path / target_file
        if not file_path.exists():
            return ToolResult.error(f"文件不存在: {target_file}")

        # 先创建备份
        backup_result = self._create_backup(base_path, base_path.parent / ".devpal_backups", f"pre_fix_{Path(target_file).stem}")
        if not backup_result.success:
            return backup_result

        # 应用修改
        old_content = file_path.read_text(encoding="utf-8")
        file_path.write_text(new_content, encoding="utf-8")

        output = f"✅ 代码修复已应用到: {target_file}\n"
        output += f"备份已创建: {backup_result.metadata.get('backup_name')}\n"
        if description:
            output += f"变更描述: {description}\n"
        output += f"\n原文件大小: {len(old_content)} 字节\n"
        output += f"新文件大小: {len(new_content)} 字节\n"
        output += f"差异: {abs(len(new_content) - len(old_content))} 字节"

        return ToolResult.ok(
            output,
            target_file=target_file,
            backup_created=backup_result.metadata.get('backup_name'),
            description=description
        )

    def _run_self_test(self, base_path: Path, test_command: Optional[str]) -> ToolResult:
        """运行自检"""
        # 简单的导入测试
        results = []
        passed = 0
        failed = 0

        # 测试 1: 工具导入
        try:
            from devpal.tools import (
                FileReaderTool, FileWriterTool, CommandExecutorTool,
                CodeSearchTool, CompilerAnalyzerTool, LinkedListTool,
                GitTool, StaticAnalyzer, CodeReviewTool,
                MsvcAsanCompilerTool, SelfSourceReaderTool, SelfImproveTool
            )
            results.append(("工具导入测试", "PASS", ""))
            passed += 1
        except Exception as e:
            results.append(("工具导入测试", "FAIL", str(e)))
            failed += 1

        # 测试 2: 核心模块导入
        try:
            from devpal.core import AgentEngine, AgentConfig
            results.append(("核心模块导入测试", "PASS", ""))
            passed += 1
        except Exception as e:
            results.append(("核心模块导入测试", "FAIL", str(e)))
            failed += 1

        # 测试 3: 工具注册表
        try:
            from devpal.tools import registry
            tools = registry.list_tool_names()
            results.append(("工具注册表测试", "PASS", f"已注册 {len(tools)} 个工具"))
            passed += 1
        except Exception as e:
            results.append(("工具注册表测试", "FAIL", str(e)))
            failed += 1

        # 测试 4: 内存模块
        try:
            from devpal.memory import MemoryManager
            results.append(("内存模块测试", "PASS", ""))
            passed += 1
        except Exception as e:
            results.append(("内存模块测试", "FAIL", str(e)))
            failed += 1

        # 生成报告
        output = "=" * 60 + "\n"
        output += "DevPal Agent 自检报告\n"
        output += "=" * 60 + "\n\n"

        for test_name, status, detail in results:
            status_icon = "✅" if status == "PASS" else "❌"
            output += f"{status_icon} {test_name}: {status}\n"
            if detail:
                output += f"   {detail}\n"
            output += "\n"

        output += "=" * 60 + "\n"
        output += f"总计: {passed} 通过, {failed} 失败\n"
        output += "=" * 60 + "\n"

        if failed == 0:
            output += "\n🎉 所有测试通过！Agent 运行正常。"
        else:
            output += f"\n⚠️  有 {failed} 个测试失败，建议检查。"

        return ToolResult.ok(output, passed=passed, failed=failed)
