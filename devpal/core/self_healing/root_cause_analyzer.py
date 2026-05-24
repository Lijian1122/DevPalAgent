"""
根因分析器

负责分析错误的根本原因，包括错误分类、追溯链路分析和影响范围分析。
"""

import logging
from typing import Optional

from .models import ErrorContext, ErrorType, RootCause


class RootCauseAnalyzer:
    """根因分析器"""

    def __init__(
        self,
        artifact_graph: "ArtifactGraph",
        context: "OpenSpecContext",
        logger: Optional[logging.Logger] = None,
    ):
        self.artifact_graph = artifact_graph
        self.context = context
        self.logger = logger or logging.getLogger(__name__)

        # 错误模式库
        self.error_patterns = self._load_error_patterns()

    def analyze(self, error_context: ErrorContext) -> RootCause:
        """
        执行根因分析

            Args:
              error_context: 错误上下文

            Returns:
                RootCause: 根因分析结果
        """
        self.logger.info(f"[RCA] 开始根因分析: {error_context.error_message[:100]}")

        # Step 1: 错误分类
        error_type = self._classify_error(error_context)
        error_context.error_type = error_type

        # Step 2: 追溯链路分析
        trace_chain = self._build_trace_chain(error_context)

        # Step 3: 影响范围分析
        affected_files = self._analyze_impact(error_context)

        # Step 4: 根因推断
        root_cause_type, description, confidence = self._infer_root_cause(
            error_context, trace_chain
        )

        # Step 5: 生成修复建议
        suggested_fixes = self._generate_fix_suggestions(error_context, root_cause_type)

        root_cause = RootCause(
            error_context=error_context,
            root_cause_type=root_cause_type,
            root_cause_description=description,
            trace_chain=trace_chain,
            affected_files=affected_files,
            confidence=confidence,
            suggested_fixes=suggested_fixes,
        )

        self.logger.info(
            f"[RCA] 根因分析完成: {root_cause_type} (置信度: {confidence:.2f})"
        )
        return root_cause

    def _classify_error(self, error_context: ErrorContext) -> ErrorType:
        """错误分类"""
        import re

        from .models import ErrorType

        error_msg = error_context.error_message.lower()

        # 语法错误模式
        syntax_patterns = [
            r"undefined reference",
            r"syntax error",
            r"import.*error",
            r"no module named",
            r"compilation failed",
            r"parse error",
            r"cannot find",
            r"undeclared identifier",
        ]

        # 逻辑错误模式
        logic_patterns = [
            r"assertion.*failed",
            r"expected.*got",
            r"test.*failed",
            r"incorrect.*result",
            r"assert",
        ]

        # 环境错误模式
        environment_patterns = [
            r"command not found",
            r"permission denied",
            r"file not found",
            r"cannot open.*file",
            r"no such file",
        ]

        for pattern in syntax_patterns:
            if re.search(pattern, error_msg):
                return ErrorType.SYNTAX

        for pattern in logic_patterns:
            if re.search(pattern, error_msg):
                return ErrorType.LOGIC

        for pattern in environment_patterns:
            if re.search(pattern, error_msg):
                return ErrorType.ENVIRONMENT

        return ErrorType.UNKNOWN

    def _build_trace_chain(self, error_context: ErrorContext):
        """构建追溯链路"""
        from .models import TraceNode

        trace_chain = []

        if not error_context.file_path:
            return trace_chain

        # 从 ArtifactGraph 获取追溯信息
        file_path_str = str(error_context.file_path)

        # 1. 代码节点
        trace_chain.append(
            TraceNode(
                node_type="code",
                node_id=file_path_str,
                content=f"错误文件: {error_context.file_path.name}",
                confidence=1.0,
            )
        )

        # 2. Phase 节点
        if error_context.phase:
            trace_chain.append(
                TraceNode(
                    node_type="phase",
                    node_id=error_context.phase,
                    content=f"生成阶段: {error_context.phase}",
                    confidence=1.0,
                )
            )

        # 3. 需求节点（从 ArtifactGraph 查询）
        requirements = self._find_related_requirements(file_path_str)
        for req_id, req_desc in requirements:
            trace_chain.append(
                TraceNode(
                    node_type="requirement",
                    node_id=req_id,
                    content=req_desc,
                    confidence=0.8,
                )
            )

        return trace_chain

    def _analyze_impact(self, error_context: ErrorContext):
        """分析影响范围"""
        from pathlib import Path

        if not error_context.file_path:
            return []

        affected = [error_context.file_path]

        # 使用 ArtifactGraph 查找依赖文件（如果可用）
        try:
            file_path_str = str(error_context.file_path)
            if hasattr(self.artifact_graph, "get_dependencies"):
                dependencies = self.artifact_graph.get_dependencies(file_path_str)
                for dep in dependencies:
                    affected.append(Path(dep))
        except Exception as e:
            self.logger.debug(f"[RCA] 无法获取依赖信息: {e}")
        return affected

    def _infer_root_cause(self, error_context: ErrorContext, trace_chain):
        """推断根因"""
        from .models import ErrorType

        error_type = error_context.error_type
        error_msg = error_context.error_message

        # 基于错误类型和模式推断根因
        if error_type == ErrorType.SYNTAX:
            if (
                "undefined reference" in error_msg.lower()
                or "undeclared" in error_msg.lower()
            ):
                return ("code_generation_error", "代码生成时缺少函数或变量定义", 0.85)
            elif "import" in error_msg.lower() or "no module" in error_msg.lower():
                return ("dependency_missing", "缺少必要的依赖库或模块", 0.90)

        elif error_type == ErrorType.LOGIC:
            if "assertion" in error_msg.lower() or "expected" in error_msg.lower():
                return (
                    "requirement_misunderstanding",
                    "需求理解错误导致逻辑实现不符合预期",
                    0.75,
                )

        elif error_type == ErrorType.ENVIRONMENT:
            return ("configuration_error", "环境配置错误或权限问题", 0.80)

        return ("unknown", "无法确定根本原因", 0.3)

    def _generate_fix_suggestions(
        self, error_context: ErrorContext, root_cause_type: str
    ):
        """生成修复建议"""
        suggestions = []

        if root_cause_type == "code_generation_error":
            suggestions.append("重新生成相关代码文件，明确要求包含缺失的定义")
            suggestions.append("检查 Phase 4 Prompt 是否完整描述了所需功能")

        elif root_cause_type == "dependency_missing":
            suggestions.append("安装缺失的依赖库")
            suggestions.append("更新 requirements.txt 或 CMakeLists.txt")

        elif root_cause_type == "requirement_misunderstanding":
            suggestions.append("重新审查需求文档，确保理解正确")
            suggestions.append("更新测试用例以匹配实际需求")

        elif root_cause_type == "configuration_error":
            suggestions.append("检查环境配置和权限设置")
            suggestions.append("验证必要的工具和路径是否正确")

        return suggestions

    def _find_related_requirements(self, file_path: str):
        """查找相关需求"""
        requirements = []

        # 从 context 获取需求信息
        try:
            if hasattr(self.context, "requirements") and self.context.requirements:
                for req_id, req_data in self.context.requirements.items():
                    # 简化实现：假设所有需求都相关
                    # 实际应该使用 ArtifactGraph 的追踪信息
                    if isinstance(req_data, dict):
                        desc = req_data.get("description", "")[:100]
            else:
                desc = str(req_data)[:100]
                requirements.append((req_id, desc))
        except Exception as e:
            self.logger.debug(f"[RCA] 无法获取需求信息: {e}")

        return requirements

    def _load_error_patterns(self):
        """加载错误模式库"""
        return {
            "syntax": [r"undefined reference", r"syntax error", r"import.*error"],
            "logic": [r"assertion.*failed", r"expected.*got"],
            "environment": [r"command not found", r"permission denied"],
        }
