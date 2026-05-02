# -*- coding: utf-8 -*-
"""
DevPal MVP - 最小可用 Agent 版本
直接运行就能看到效果
"""
import anthropic
import os
import subprocess
import sys

# 修复 Windows 终端编码问题
if sys.platform == "win32":
    os.system("chcp 65001 >nul")
    sys.stdout.reconfigure(encoding='utf-8')

# 导入配置系统
try:
    from .config import get_config
except ImportError:
    # 直接运行脚本时使用绝对导入
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from devpal.config import get_config

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

# 调试：显示 Token 来源和前几位（安全显示）
print(f"[DEBUG] Token 前 15 位: {ANTHROPIC_AUTH_TOKEN[:15]}...")
print(f"[DEBUG] Token 总长度: {len(ANTHROPIC_AUTH_TOKEN)}")
print(f"[DEBUG] 环境变量 ANTHROPIC_AUTH_TOKEN: {'已设置' if 'ANTHROPIC_AUTH_TOKEN' in os.environ else '未设置'}")
print(f"[DEBUG] 环境变量 ANTHROPIC_API_KEY: {'已设置' if 'ANTHROPIC_API_KEY' in os.environ else '未设置'}")

# 初始化 Anthropic 客户端，支持自定义 base_url
# 火山引擎标准格式: https://ark.cn-beijing.volces.com/api/v3
# 火山引擎需要 Bearer 认证方式，不是 x-api-key

if "volces.com" in ANTHROPIC_BASE_URL or "ark.cn" in ANTHROPIC_BASE_URL:
    # 火山引擎 Bearer 认证
    # 检测 Token 格式：apikey-xxx 可能需要特殊处理
    if ANTHROPIC_AUTH_TOKEN.startswith("apikey-"):
        print(f"[DEBUG] 使用火山引擎 Bearer 认证 (apikey- 格式)")
        # 有些 apikey 格式需要加上 Bearer 前缀，有些不需要
        # 尝试直接用 api_key 参数（SDK 会自动加 x-api-key 头，不行就手动设置）
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


def execute_command(cmd: str) -> str:
    """执行命令行工具（修复 Windows 编码问题）"""
    try:
        # 指定 encoding='utf-8'，错误时自动替换避免崩溃
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # 遇到无法解码的字符时替换而不是崩溃
            timeout=config.command_timeout
        )
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        return f"命令执行成功 (exit_code={result.returncode}):\nstdout:\n{stdout}\nstderr:\n{stderr}"
    except subprocess.TimeoutExpired:
        return f"命令执行超时（{config.command_timeout}秒）"
    except Exception as e:
        return f"命令执行失败: {str(e)}"


# 工具定义（Claude 格式）
tools = [
    {
        "name": "execute_command",
        "description": "执行命令行命令，例如编译代码、查看文件列表等",
        "input_schema": {
            "type": "object",
            "properties": {
                "cmd": {"type": "string", "description": "要执行的 shell 命令"}
            },
            "required": ["cmd"]
        }
    }
]


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

        # 构建 assistant 消息（Claude 要求的精确格式）
        assistant_content = []
        for block in response.content:
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

                # 执行工具
                if block.name == "execute_command":
                    result = execute_command(**block.input)
                else:
                    result = f"未知工具: {block.name}"

                print(f"       结果: {len(result)} 字符")

                # 返回工具结果给 LLM
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
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
    import sys

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "帮我看看当前目录下有什么文件"

    run_agent(query)
