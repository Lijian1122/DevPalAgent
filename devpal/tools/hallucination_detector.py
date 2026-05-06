# -*- coding: utf-8 -*-
"""
幻觉检测工具 - AI 幻觉自动防御体系的核心工具
检测并防止 LLM 产生的各类幻觉：编造信息、错误参数、不存在的工具等
"""
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field
from difflib import SequenceMatcher

from .base import BaseTool, ToolResult


class HallucinationDetectorTool(BaseTool):
    """幻觉检测工具 - 自动检测和防御 AI 幻觉"""

    name = "hallucination_detector"
    description = "检测 LLM 输出中的幻觉：编造信息、错误参数、不存在的工具等，并提供修正建议"

    class Parameters(BaseModel):
        check_type: str = Field(
            default="all",
            description="检测类型: tool_call(工具调用校验), plan(计划校验), code(代码校验), fact(事实校验), all(全部)"
        )
        content_to_check: str = Field(
            description="需要检测的内容：LLM 输出、计划步骤、工具调用参数等"
        )
        context: Optional[str] = Field(
            default=None,
            description="上下文信息：可用工具列表、真实代码内容等"
        )
        tool_name: Optional[str] = Field(
            default=None,
            description="待检测的工具名称（仅 check_type=tool_call 时需要）"
        )
        tool_args: Optional[Dict[str, Any]] = Field(
            default=None,
            description="待检测的工具参数（仅 check_type=tool_call 时需要）"
        )

    # 幻觉信号关键词 - 出现这些词时需要警惕
    HALLUCINATION_SIGNALS = [
        "可能", "大概", "也许", "应该", "我猜", "可能是",
        "我记得", "据我所知", "根据我的知识库",
        "你可以试试", "应该可以", "理论上"
    ]

    # 危险操作关键词 - 需要特别校验
    DANGEROUS_OPERATIONS = [
        'delete', 'remove', 'rm -rf', 'format', 'del', 'deltree',
        'drop', 'truncate', 'alter', 'delete from'
    ]

    def _execute(self, params: Parameters) -> ToolResult:
        issues = []
        risk_level = "low"

        if params.check_type in ["all", "tool_call"]:
            tool_issues = self._check_tool_call(params)
            issues.extend(tool_issues)

        if params.check_type in ["all", "plan"]:
            plan_issues = self._check_plan(params)
            issues.extend(plan_issues)

        if params.check_type in ["all", "code"]:
            code_issues = self._check_code(params)
            issues.extend(code_issues)

        if params.check_type in ["all", "fact"]:
            fact_issues = self._check_fact(params)
            issues.extend(fact_issues)

        # 计算风险等级
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for issue in issues:
            severity_counts[issue.get('severity', 'low')] += 1

        if severity_counts["high"] > 0:
            risk_level = "high"
        elif severity_counts["medium"] > 0 or severity_counts["high"] > 1:
            risk_level = "medium"

        result = {
            "risk_level": risk_level,
            "total_issues": len(issues),
            "issues": issues,
            "needs_human_verification": risk_level in ["high", "medium"],
            "recommendation": self._get_recommendation(risk_level, issues)
        }

        result_content = self._format_result(result)

        return ToolResult.ok(
            result_content,
            risk_level=risk_level,
            issues=issues,
            needs_human_verification=result["needs_human_verification"]
        )

    def _check_tool_call(self, params: Parameters) -> List[Dict]:
        """检测工具调用幻觉"""
        issues = []
        tool_name = params.tool_name
        tool_args = params.tool_args
        context = params.context or ""

        if not tool_name:
            return issues

        # 1. 检测工具是否存在
        available_tools = self._extract_available_tools(context)
        if available_tools and tool_name not in available_tools:
            # 找最相似的工具
            similar = self._find_similar_tool(tool_name, available_tools)
            issues.append({
                "type": "tool_not_exist",
                "severity": "high",
                "message": f"工具 '{tool_name}' 不存在",
                "suggestion": f"最相似的工具是: {similar}" if similar else "请检查工具名称"
            })

        # 2. 检测参数是否为 None 或空
        if tool_args:
            for key, value in tool_args.items():
                if value is None or value == "":
                    issues.append({
                        "type": "null_parameter",
                        "severity": "high",
                        "message": f"参数 '{key}' 值为 None 或空",
                        "suggestion": "请从用户输入中提取真实参数值，不要使用占位符"
                    })
                elif isinstance(value, str) and len(value) > 1000:
                    issues.append({
                        "type": "parameter_too_long",
                        "severity": "medium",
                        "message": f"参数 '{key}' 过长 ({len(value)} 字符)",
                        "suggestion": "检查参数是否被错误填充"
                    })

        # 3. 检测危险操作
        if tool_name and any(op in tool_name.lower() for op in self.DANGEROUS_OPERATIONS):
            issues.append({
                "type": "dangerous_operation",
                "severity": "high",
                "message": "检测到危险操作",
                "suggestion": "执行前需要人工确认，建议先备份"
            })

        return issues

    def _check_plan(self, params: Parameters) -> List[Dict]:
        """检测计划步骤幻觉"""
        issues = []
        content = params.content_to_check
        context = params.context or ""
        available_tools = self._extract_available_tools(context)

        lines = content.split('\n')
        for i, line in enumerate(lines):
            # 检测计划中引用了不存在的工具
            if available_tools:
                for tool in available_tools:
                    if tool in line and "Tool:" in line:
                        break
                else:
                    # 如果提到了某个工具但不在可用列表中
                    tool_match = re.search(r'Tool:\s*(\w+)', line)
                    if tool_match:
                        mentioned_tool = tool_match.group(1)
                        if mentioned_tool not in available_tools:
                            similar = self._find_similar_tool(mentioned_tool, available_tools)
                            issues.append({
                                "type": "plan_wrong_tool",
                                "severity": "high",
                                "line": i + 1,
                                "message": f"计划步骤中引用了不存在的工具: {mentioned_tool}",
                                "suggestion": f"建议替换为: {similar}" if similar else "请检查工具名称"
                            })

            # 检测过于模糊的步骤描述
            if len(line.strip()) > 0 and len(line.strip()) < 10 and "Step" not in line:
                issues.append({
                    "type": "plan_too_vague",
                    "severity": "low",
                    "line": i + 1,
                    "message": "步骤描述过于模糊",
                    "suggestion": "建议增加更具体的操作描述"
                })

        # 检测可行性评分过高但内容很简单
        if "feasibility" in content.lower() and "1.0" in content and len(lines) < 3:
            issues.append({
                "type": "overconfident_feasibility",
                "severity": "medium",
                "message": "可行性评分过高但计划过于简单",
                "suggestion": "建议重新评估任务复杂度"
            })

        return issues

    def _check_code(self, params: Parameters) -> List[Dict]:
        """检测代码生成幻觉"""
        issues = []
        content = params.content_to_check
        context = params.context or ""

        # 1. 检测 TODO/FIXME 标记（可能是 LLM 不知道怎么写留的占位符）
        if 'TODO' in content or 'FIXME' in content:
            issues.append({
                "type": "code_todo_marker",
                "severity": "medium",
                "message": "代码中包含 TODO/FIXME 标记，可能是未完成的实现",
                "suggestion": "请检查这部分代码逻辑是否完整"
            })

        # 2. 检测 placeholder 变量名
        placeholder_patterns = [r'your_\w+', r'my_\w+', r'test_\w+', r'example_\w+', r'sample_\w+']
        for pattern in placeholder_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append({
                    "type": "placeholder_variable",
                    "severity": "low",
                    "message": f"检测到可能的占位符变量名 (pattern: {pattern})",
                    "suggestion": "请替换为真实的业务变量名"
                })

        # 3. 检测语法错误迹象
        if context and "file_path" in context:
            context_file = re.search(r'file_path[=:]\s*([^\s,]+)', context)
            if context_file:
                file_path = context_file.group(1).strip('\'"')
                if os.path.exists(file_path):
                    # 简单检查生成的函数是否在原文件中存在
                    func_match = re.search(r'def\s+(\w+)\s*\(|class\s+(\w+)\s*[:\(]', content)
                    if func_match:
                        func_name = func_match.group(1) or func_match.group(2)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            orig_content = f.read()
                        if func_name not in orig_content:
                            issues.append({
                                "type": "code_function_not_exist",
                                "severity": "medium",
                                "message": f"生成的函数/类 '{func_name}' 在原文件中不存在",
                                "suggestion": "请确认是新增功能还是拼写错误"
                            })

        return issues

    def _check_fact(self, params: Parameters) -> List[Dict]:
        """检测事实性陈述幻觉"""
        issues = []
        content = params.content_to_check

        # 1. 检测幻觉信号词
        for signal in self.HALLUCINATION_SIGNALS:
            if signal in content:
                issues.append({
                    "type": "uncertain_statement",
                    "severity": "low",
                    "message": f"检测到不确定性表述: '{signal}'",
                    "suggestion": "建议通过工具调用确认事实后再下结论"
                })
                break

        # 2. 检测过于肯定的数字陈述
        number_pattern = r'(\d+(?:\.\d+)?)\s*%(?:\s+|$)'
        numbers = re.findall(number_pattern, content)
        if len(numbers) > 3:
            issues.append({
                "type": "too_many_numbers",
                "severity": "medium",
                "message": "包含大量数字陈述，请确认数据来源",
                "suggestion": "建议通过工具获取真实数据，不要依赖模型记忆"
            })

        # 3. 检测引用了具体的论文、研究、数据来源
        citation_patterns = [
            r'根据.*研究', r'据.*报道', r'论文.*表明', r'研究.*表明',
            r'[A-Z][a-z]+ et al\.', r'\(\d{4}\)'
        ]
        for pattern in citation_patterns:
            if re.search(pattern, content):
                issues.append({
                    "type": "citation_claim",
                    "severity": "high",
                    "message": "检测到引用了研究/论文/报道",
                    "suggestion": "LLM 可能编造引用，请人工核实来源的真实性"
                })
                break

        return issues

    def _extract_available_tools(self, context: str) -> List[str]:
        """从上下文中提取可用工具列表"""
        tools = []
        # 匹配常见的工具列表格式
        tool_patterns = [
            r'可用工具[：:]\s*([^\n]+)',
            r'tools:\s*([^\n]+)',
            r'You can use the following tools:\s*([^\n]+)'
        ]
        for pattern in tool_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                tools_str = match.group(1)
                tools = [t.strip() for t in tools_str.split(',')]
                break
        return tools

    def _find_similar_tool(self, tool_name: str, available_tools: List[str]) -> Optional[str]:
        """找最相似的工具名"""
        best_match = None
        best_score = 0
        for tool in available_tools:
            score = SequenceMatcher(None, tool_name.lower(), tool.lower()).ratio()
            if score > best_score and score > 0.5:
                best_score = score
                best_match = tool
        return best_match

    def _get_recommendation(self, risk_level: str, issues: List[Dict]) -> str:
        """根据检测结果给出建议"""
        if risk_level == "high":
            high_issues = [i for i in issues if i.get('severity') == 'high']
            return f"检测到高风险幻觉 ({len(high_issues)} 个)，建议：1) 重新生成工具调用/计划 2) 人工核对关键信息 3) 不要自动执行"
        elif risk_level == "medium":
            return "存在中度风险，建议检查后再执行，关键步骤需要人工确认"
        else:
            return "未检测到明显幻觉，可以继续执行，但仍需关注执行结果"

    def _format_result(self, result: Dict) -> str:
        """格式化输出结果"""
        lines = [
            "=" * 60,
            "🔍 幻觉检测结果",
            "=" * 60,
            f"风险等级: {'🔴 高' if result['risk_level'] == 'high' else '🟡 中' if result['risk_level'] == 'medium' else '🟢 低'}",
            f"发现问题: {result['total_issues']} 个",
            f"需要人工确认: {'是' if result['needs_human_verification'] else '否'}",
            ""
        ]

        if result['issues']:
            lines.append("问题详情:")
            for i, issue in enumerate(result['issues'], 1):
                severity_icon = "🔴" if issue['severity'] == 'high' else "🟡" if issue['severity'] == 'medium' else "🔵"
                lines.append(f"  {severity_icon} [{i}] {issue['type']}")
                lines.append(f"      描述: {issue['message']}")
                lines.append(f"      建议: {issue['suggestion']}")
        else:
            lines.append("✅ 未检测到明显幻觉信号")

        lines.append("")
        lines.append(f"建议: {result['recommendation']}")
        lines.append("=" * 60)

        return "\n".join(lines)
