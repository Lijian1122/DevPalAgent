# -*- coding: utf-8 -*-
"""
DevPal MVP - 最小可用 Agent 版本
完整工具系统：file_reader、file_writer、command_executor
"""
import anthropic
import os
import sys
from pathlib import Path

# 修复 Windows 终端编码问题
if sys.platform == "win32":
    os.system("chcp 65001 >nul")
    sys.stdout.reconfigure(encoding='utf-8')

# 导入配置系统
try:
    from .config import get_config
except ImportError:
    # 直接运行脚本时使用绝对导入
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from devpal.config import get_config

# 导入工具系统
try:
    from .tools import registry
except ImportError:
    from devpal.tools import registry

config = get_config()

ANTHROPIC_AUTH_TOKEN = config.anthropic_auth_token
ANTHROPIC_BASE_URL = config.anthropic_base_url

if not ANTHROPIC_AUTH_TOKEN:
    print("[ERROR] 未找到 Anthropic API Token")
    print("[INFO] 请使用以下任意一种方式配置：")
    print("   1. 在 config/config.yaml 中填写 anthropic.auth_token")
    print("   2. 设置环境变量: set ANTHROPIC_AUTH_TOKEN=your-token")
    print()
    print("[TIP] 复制 config/config.yaml.example 为 config/config.yaml 然后填写你的配置")
    exit(1)

# 初始化 Anthropic 客户端，支持自定义 base_url
# 火山引擎标准格式: https://ark.cn-beijing.volces.com/api/v3
# 火山引擎需要 Bearer 认证方式，不是 x-api-key
if "volces.com" in ANTHROPIC_BASE_URL or "ark.cn" in ANTHROPIC_BASE_URL:
    # 火山引擎 Bearer 认证
    if ANTHROPIC_AUTH_TOKEN.startswith("apikey-"):
        print(f"[DEBUG] 使用火山引擎 x-api-key 认证 (apikey- 格式)")
        client = anthropic.Anthropic(
            api_key=ANTHROPIC_AUTH_TOKEN,
            base_url=ANTHROPIC_BASE_URL
        )
    else:
        print(f"[DEBUG] 使用火山引擎 Bearer 认证 (UUID 格式)")
        client = anthropic.Anthropic(
            api_key="",
            base_url=ANTHROPIC_BASE_URL,
            default_headers={
                "Authorization": f"Bearer {ANTHROPIC_AUTH_TOKEN}"
            }
        )
else:
    # 官方 Claude
    print(f"[DEBUG] 使用官方 Claude x-api-key 认证方式")
    client = anthropic.Anthropic(
        api_key=ANTHROPIC_AUTH_TOKEN,
        base_url=ANTHROPIC_BASE_URL
    )

print(f"[INFO] API 地址: {ANTHROPIC_BASE_URL}")
print(f"[INFO] 使用模型: {config.anthropic_model}")
print(f"[INFO] 已注册工具: {[tool.name for tool in registry.list_tools()]}")

# 从工具注册表获取工具描述
tools = registry.get_tool_descriptions()


def run_agent(query: str):
    """Agent 主循环"""
    messages = [{"role": "user", "content": query}]

    print(f"\n[OK] DevPal 收到任务: {query}")
    print(f"{'='*60}")

    for i in range(config.max_iterations):
        print(f"\n[INFO] 第 {i+1} 轮思考...")

        response = client.messages.create(
            model=config.anthropic_model,
            max_tokens=config.max_tokens,
            messages=messages,
            tools=tools
        )

        # 调试：打印 response 完整结构
        print(f"[DEBUG] response.model: {response.model}")
        print(f"[DEBUG] response.role: {response.role}")
        print(f"[DEBUG] response.type: {response.type}")
        print(f"[DEBUG] response.stop_reason: {response.stop_reason}")
        print(f"[DEBUG] response.usage: {response.usage}")
        print(f"[DEBUG] response.content blocks ({len(response.content)}):")
        for idx, block in enumerate(response.content):
            print(f"  [{idx}] type={block.type}")
            if block.type == "text":
                print(f"       text={block.text[:100]}..." if len(block.text) > 100 else f"       text={block.text}")
            elif block.type == "tool_use":
                print(f"       id={block.id}")
                print(f"       name={block.name}")
                print(f"       input={block.input}")

        # 构建 assistant 消息（Claude 要求的精确格式）
        assistant_content = []
        for block in response.content:
            if block.type == "thinking":
                # 火山引擎特有：thinking 块，跳过，不需要发给 LLM
                continue
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        messages.append({"role": "assistant", "content": assistant_content})

        # 检查是否有工具调用
        has_tool_call = False
        for block in response.content:
            if block.type == "tool_use":
                has_tool_call = True
                print(f"[TOOL] 调用工具: {block.name}")
                print(f"       参数: {block.input}")

                # 使用工具注册表执行
                result = registry.execute_tool(block.name, block.input)

                if result.success:
                    print(f"       结果: 成功，{len(result.content)} 字符")
                else:
                    print(f"       错误: {result.error_message}")

                # 返回工具结果给 LLM
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result.content if result.success else result.error_message
                        }
                    ]
                })

        # 没有工具调用 = 任务完成
        if not has_tool_call:
            print(f"\n{'='*60}")
            print("[DONE] 最终回答:")
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "简单介绍一下自己，说明你能做什么"

    run_agent(query)
