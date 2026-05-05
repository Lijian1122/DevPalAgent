# -*- coding: utf-8 -*-
"""
Git 自动化工具
提供 Git 仓库操作、代码提交、分支管理、代码 Review 等功能
"""
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


class GitTool(BaseTool):
    """Git 自动化工具"""

    name = "git_tool"
    description = "Git 仓库操作工具，支持查看状态、提交代码、差异比较、分支管理、代码审查等"

    class Parameters(BaseModel):
        action: str = Field(
            default="status",
            description="Git 操作类型: status, add, commit, diff, branch, checkout, log, pull, push, review, stash"
        )
        message: Optional[str] = Field(
            default=None,
            description="提交信息（commit 操作需要）"
        )
        branch: Optional[str] = Field(
            default=None,
            description="分支名称"
        )
        file_path: Optional[str] = Field(
            default=None,
            description="文件路径"
        )
        target_branch: Optional[str] = Field(
            default=None,
            description="目标分支（diff 操作使用）"
        )
        files: Optional[List[str]] = Field(
            default=None,
            description="要操作的文件列表"
        )
        review_scope: Optional[str] = Field(
            default=None,
            description="审查范围: changed, staged, all, file"
        )
        branch_action: Optional[str] = Field(
            default=None,
            description="分支操作类型: list, create, delete"
        )
        stash_action: Optional[str] = Field(
            default=None,
            description="stash 操作: push, pop, list"
        )

    def _execute(self, params: Parameters) -> ToolResult:
        handlers = {
            'status': self._status,
            'commit': self._commit,
            'diff': self._diff,
            'branch': self._branch,
            'checkout': self._checkout,
            'log': self._log,
            'pull': self._pull,
            'push': self._push,
            'review': self._review,
            'add': self._add,
            'stash': self._stash,
        }

        handler = handlers.get(params.action)
        if not handler:
            return ToolResult.error(
                f"不支持的 Git 操作: {params.action}，支持: {list(handlers.keys())}"
            )

        try:
            return handler(params)
        except Exception as e:
            return ToolResult.error(f"Git 操作失败: {str(e)}")

    def _execute_git_command(self, command: str) -> tuple[str, str, int]:
        """执行 git 命令"""
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    def _status(self, params: Parameters) -> ToolResult:
        stdout, stderr, code = self._execute_git_command("git status")
        if code != 0:
            return ToolResult.error(stderr or "获取状态失败")
        return ToolResult.ok(stdout, action="status")

    def _add(self, params: Parameters) -> ToolResult:
        files = params.files if params.files else ['.']
        if isinstance(files, str):
            files = [files]

        file_args = ' '.join(files)
        stdout, stderr, code = self._execute_git_command(f"git add {file_args}")

        if code != 0:
            return ToolResult.error(stderr or "添加文件失败")

        return ToolResult.ok(f"成功添加文件: {', '.join(files)}", files_added=files)

    def _commit(self, params: Parameters) -> ToolResult:
        message = params.message if params.message else 'Update code'
        files = params.files

        if files:
            add_result = self._add(params)
            if not add_result.success:
                return add_result

        stdout, stderr, code = self._execute_git_command(f'git commit -m "{message}"')

        if code != 0:
            if "nothing to commit" in stdout or "nothing to commit" in stderr:
                return ToolResult.ok("没有需要提交的更改", committed=False)
            return ToolResult.error(stderr or "提交失败")

        return ToolResult.ok(stdout, committed=True, message=message)

    def _diff(self, params: Parameters) -> ToolResult:
        target_branch = params.target_branch or ''
        file_path = params.file_path or ''

        if target_branch and file_path:
            cmd = f"git diff {target_branch} -- {file_path}"
        elif target_branch:
            cmd = f"git diff {target_branch}"
        elif file_path:
            cmd = f"git diff HEAD -- {file_path}"
        else:
            cmd = "git diff HEAD"

        stdout, stderr, code = self._execute_git_command(cmd)

        if code != 0:
            return ToolResult.error(stderr or "获取差异失败")

        if not stdout.strip():
            return ToolResult.ok("没有差异", has_changes=False)

        return ToolResult.ok(stdout, has_changes=True)

    def _branch(self, params: Parameters) -> ToolResult:
        branch_name = params.branch or ''
        action = params.branch_action or 'list'

        if action == 'create' and branch_name:
            cmd = f"git checkout -b {branch_name}"
        elif action == 'delete' and branch_name:
            cmd = f"git branch -d {branch_name}"
        else:
            cmd = "git branch -a"

        stdout, stderr, code = self._execute_git_command(cmd)

        if code != 0:
            return ToolResult.error(stderr or "分支操作失败")

        return ToolResult.ok(stdout, action=action)

    def _checkout(self, params: Parameters) -> ToolResult:
        branch = params.branch or 'main'
        stdout, stderr, code = self._execute_git_command(f"git checkout {branch}")

        if code != 0:
            return ToolResult.error(stderr or "切换分支失败")

        return ToolResult.ok(stdout, branch=branch)

    def _log(self, params: Parameters) -> ToolResult:
        stdout, stderr, code = self._execute_git_command("git log --oneline -n 10")

        if code != 0:
            return ToolResult.error(stderr or "获取提交历史失败")

        return ToolResult.ok(stdout)

    def _pull(self, params: Parameters) -> ToolResult:
        branch = params.branch or ''
        cmd = f"git pull origin {branch}" if branch else "git pull"

        stdout, stderr, code = self._execute_git_command(cmd)

        if code != 0:
            return ToolResult.error(stderr or "拉取代码失败")

        return ToolResult.ok(stdout, branch=branch)

    def _push(self, params: Parameters) -> ToolResult:
        branch = params.branch or ''
        cmd = f"git push origin {branch}" if branch else "git push"

        stdout, stderr, code = self._execute_git_command(cmd)

        if code != 0:
            return ToolResult.error(stderr or "推送代码失败")

        return ToolResult.ok(stdout, branch=branch)

    def _stash(self, params: Parameters) -> ToolResult:
        stash_action = params.stash_action or 'push'

        if stash_action == 'push':
            message = params.message or ''
            cmd = f"git stash push -m '{message}'" if message else "git stash push"
        elif stash_action == 'pop':
            cmd = "git stash pop"
        elif stash_action == 'list':
            cmd = "git stash list"
        else:
            return ToolResult.error(f"不支持的 stash 操作: {stash_action}")

        stdout, stderr, code = self._execute_git_command(cmd)

        if code != 0:
            return ToolResult.error(stderr or "stash 操作失败")

        return ToolResult.ok(stdout, stash_action=stash_action)

    def _review(self, params: Parameters) -> ToolResult:
        scope = params.review_scope or 'changed'

        from .code_review import CodeReviewTool
        review_tool = CodeReviewTool()

        if scope == 'file' and params.file_path:
            return review_tool.execute_with_validation({
                'file_path': params.file_path,
                'check_types': ['todo', 'debug', 'style', 'security', 'performance']
            })

        elif scope == 'changed':
            stdout, stderr, code = self._execute_git_command("git diff HEAD --name-only")
            if code == 0 and stdout.strip():
                files = [f for f in stdout.strip().split('\n') if f]
                supported_extensions = ('.cpp', '.h', '.hpp', '.c', '.cc', '.py', '.js', '.ts', '.tsx')
                supported_files = [f for f in files if f.endswith(supported_extensions)]

                if supported_files:
                    return review_tool.execute_with_validation({
                        'files': supported_files,
                        'check_types': ['todo', 'debug', 'style', 'security', 'performance']
                    })
                else:
                    return ToolResult.ok("没有需要审查的代码文件", files_reviewed=files, issues=[])

        return ToolResult.ok("代码审查完成", scope=scope)
