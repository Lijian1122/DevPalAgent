# -*- coding: utf-8 -*-
"""
Agent 核心引擎 - 阶段1完整版本
支持多轮工具Calling、消息历史管理、自动重试
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# 导入配置
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from devpal.config import get_config
from devpal.tools.registry import ToolRegistry, registry
from devpal.memory import MessageHistory


@dataclass
class AgentConfig:
    """Agent 运行配置"""
    max_iterations: int = 5
    verbose: bool = True
    show_tool_output: bool = False
    enable_retry: bool = True


class AgentEngine:
    """Agent 核心引擎"""

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.config = config or AgentConfig()
        self.tool_registry = tool_registry or registry
        self.config_obj = get_config()

        # 系统提示词
        self.system_prompt = self._build_system_prompt()

        # 消息历史
        self.message_history = MessageHistory(
            max_tokens=8000,
            system_prompt=self.system_prompt
        )

        # 初始化 LLM 客户端
        self._init_llm_client()

        # 统计信息
        self.stats = {
            "total_queries": 0,
            "tool_calls": 0,
            "tool_errors": 0,
            "total_tokens": 0,
        }

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tool_names = ", ".join(self.tool_registry.list_tool_names())
        return f"""你是 DevPal，一个专业的 C++/Python 开发助手。

你可以使用以下工具来帮助用户：{tool_names}

工作方式：
1. 如果需要查看文件、执行命令、搜索代码，直接Calling对应的工具
2. 先获取信息，再给出答案，不要编造不存在的信息
3. 工具执行结果会返回给你，你可以继续Calling工具或者给出最终答案
4. 每次可以Calling多 tool(s)，也可以多轮Calling工具
5. 回答要具体、可执行，给出代码示例和操作步骤

记住：不确定的信息就去搜索或查看文件，不要凭空猜测！"""

    def _init_llm_client(self):
        """初始化 LLM 客户端"""
        import anthropic

        base_url = self.config_obj.anthropic_base_url
        api_key = self.config_obj.anthropic_auth_token

        if "volces.com" in base_url or "ark.cn" in base_url:
            # 火山引擎
            self.client = anthropic.Anthropic(
                api_key="",
                base_url=base_url,
                default_headers={"Authorization": f"Bearer {api_key}"}
            )
        else:
            # 官方 Claude
            self.client = anthropic.Anthropic(
                api_key=api_key,
                base_url=base_url
            )

        self.model = self.config_obj.anthropic_model

    def _log(self, message: str, level: str = "INFO"):
        """打印日志"""
        if self.config.verbose:
            print(f"[{level}] {message}")

    def _extract_response_content(self, response) -> tuple[str, List[Dict]]:
        """解析 LLM 响应，提取文本和工具Calling"""
        text_content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "thinking":
                continue  # 跳过火山引擎的 thinking 块
            elif block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        return text_content, tool_calls

    def run(self, user_query: str) -> str:
        """执行用户查询，支持多轮工具Calling"""
        self.stats["total_queries"] += 1

        # 添加用户消息到历史
        self.message_history.add_user(user_query)

        if self.config.verbose:
            print(f"\n{'='*60}")
            print(f" DevPal 收到任务: {user_query}")
            print(f"{'='*60}\n")

        # 主循环 - 最多执行 max_iterations 轮
        for iteration in range(self.config.max_iterations):
            self._log(f" Iteration {iteration + 1} ...")

            # Calling LLM
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.config_obj.max_tokens,
                system=self.system_prompt,
                messages=self.message_history.get_messages(),
                tools=self.tool_registry.get_tool_descriptions()
            )

            # 解析响应
            text_content, tool_calls = self._extract_response_content(response)

            # 没有工具Calling = Done
            if not tool_calls:
                if self.config.verbose:
                    print(f"\n Done\n")
                return text_content

            # 有工具Calling，执行
            self._log(f" Calling {len(tool_calls)}  tool(s)")

            # 构建 assistant 消息（包含 tool_use）
            self.message_history.add_tool_use_message(text_content, tool_calls)

            # 收集所有工具结果（批量发送）
            tool_results = []

            # 执行每 tool(s)
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["input"]
                tool_id = tool_call["id"]

                self.stats["tool_calls"] += 1

                print(f"\n    工具: {tool_name}")
                print(f"      参数: {tool_args}")

                # 执行工具
                result = self.tool_registry.execute_tool(tool_name, tool_args)

                if result.success:
                    print(f"       Success")
                    if self.config.show_tool_output:
                        output = result.content[:1000].replace('\n', '\n      ')
                        truncate_msg = "..." if len(result.content) > 1000 else ""
                        print(f"      输出:\n      {output}{truncate_msg}")
                else:
                    self.stats["tool_errors"] += 1
                    print(f"       Failed: {result.error_message}")

                # 收集工具结果
                tool_results.append({
                    "tool_use_id": tool_id,
                    "content": result.content if result.success else f"错误: {result.error_message}"
                })

            # 批量将所有工具结果返回给 LLM（Claude API 要求多工具结果放在同一条 user 消息）
            self.message_history.add_tool_results(tool_results)

        # 达到最大迭代次数，让 LLM 总结（禁用工具调用）
        self._log("️ Reached max iterations, generating final answer")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.config_obj.max_tokens,
            system=self.system_prompt + "\n请直接给出最终答案，不要调用任何工具。",
            messages=self.message_history.get_messages(),
            tools=[]  # 清空工具列表，强制 LLM 直接回答
        )

        text_content, _ = self._extract_response_content(response)

        # 清理可能残留的火山引擎工具调用标记
        import re
        text_content = re.sub(r'<minimax:tool_call>.*?</minimax:tool_call>', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'<invoke.*?>.*?</invoke>', '', text_content, flags=re.DOTALL)
        text_content = text_content.strip()

        return text_content

    def chat(self):
        """启动交互式聊天"""
        print("=" * 60)
        print(" DevPal Agent - 交互式聊天")
        print("=" * 60)
        print(f" 可用工具: {', '.join(self.tool_registry.list_tool_names())}")
        print(" 输入 'quit' 退出，'help' 查看工具帮助，'stats' 查看统计")
        print()

        while True:
            try:
                user_input = input(" 你: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit", "q"]:
                    print(" 再见！")
                    break

                if user_input.lower() == "help":
                    print("\n" + self.tool_registry.get_tool_help() + "\n")
                    continue

                if user_input.lower() == "stats":
                    print(f"\n 统计信息:")
                    for k, v in self.stats.items():
                        print(f"   {k}: {v}")
                    print()
                    continue

                # 执行查询
                answer = self.run(user_input)

                print(f"\n DevPal:")
                print(answer)
                print()

            except KeyboardInterrupt:
                print("\n\n 再见！")
                break
            except Exception as e:
                print(f"\n 错误: {e}\n")

    def clear_history(self):
        """清空对话历史"""
        self.message_history.clear()
        if self.config.verbose:
            self._log("️ Conversation history cleared")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
