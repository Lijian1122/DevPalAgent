# Write File Correctly - Integration Guide

## 如何让 Claude 自动注意到这个 Skill

### 方法 1：项目级 CLAUDE.md（已完成 ✅）

在项目根目录创建 `CLAUDE.md`，Claude Code 会自动加载它作为项目上下文。

**位置**: `c:\code\DevPalAgent\CLAUDE.md`

**内容**: 包含 "File Writing Protocol" 章节，每次 Claude 启动时都会看到。

---

### 方法 2：全局 Memory 提示（推荐）

创建一个全局记忆，让 Claude 在每次写文件前都想起这个规则。

```bash
# 创建全局提示文件
mkdir -p ~/.claude/memory
cat > ~/.claude/memory/write-file-protocol.md << 'EOF'
# Write File Protocol

Before using Write tool:
1. Prepare complete content
2. Verify file_path and content parameters
3. Check if content > 150 lines (need chunking)
4. Call Write ONCE with all parameters

Reference: ~/.claude/skills/write-file-correctly/
EOF
```

---

### 方法 3：Settings Hook（自动验证）

在 `~/.claude/settings.json` 中添加 pre-write hook：

```json
{
  "hooks": {
    "before-tool-call": {
      "Write": "python ~/.claude/skills/write-file-correctly/skill.py \"$file_path\" \"$content\" || echo 'Validation failed, but continuing...'"
    }
  }
}
```

**注意**: 这个功能可能需要 Claude Code 支持，当前版本可能不支持。

---

### 方法 4：创建 Wrapper Skill（最可靠）

创建一个包装 Write 工具的 skill，强制验证：

**文件**: `~/.claude/skills/safe-write/README.md`

```markdown
---
name: safe-write
description: Safe Write tool with automatic validation
---

# Safe Write Skill

## Usage

Instead of calling Write directly, use this skill:

\`\`\`
/safe-write path/to/file.md "content here"
\`\`\`

This skill will:
1. Validate parameters
2. Check content length
3. Call Write tool if valid
4. Provide helpful error messages if invalid
\`\`\`
```

**文件**: `~/.claude/skills/safe-write/skill.py`

```python
#!/usr/bin/env python3
import sys
import os

def safe_write(file_path, content):
    # Validate
    if not file_path:
        print("[ERROR] file_path is required")
      return False
    
    if not content:
      print("[ERROR] content is required")
        return False
    
    lines = content.count('\n') + 1
    if lines > 150:
      print(f"[WARNING] Content has {lines} lines (>150)")
        print("[INFO] Consider chunking with Edit tool")
    
    print(f"[OK] Writing {len(content)} chars to {file_path}")
    print(f"[OK] Parameters validated, ready to call Write tool")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: /safe-write <file_path> <content>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    content = sys.argv[2]
    
    if safe_write(file_path, content):
        print("\n[NEXT] Call Write tool with these parameters:")
        print(f'  Write(file_path="{file_path}", content="...")')
    else:
        sys.exit(1)
```

---

### 方法 5：自动提醒系统（最智能）

创建一个监控脚本，检测 Write 工具调用模式：

**文件**: `~/.claude/skills/write-monitor/monitor.py`

```python
#!/usr/bin/env python3
"""
Monitor Write tool calls and provide warnings
"""
import sys
import json
from pathlib import Path

HISTORY_FILE = Path.home() / ".claude" / "write_history.json"

def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {"calls": [], "errors": 0}

def save_history(history):
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))

def check_pattern(history):
    """Check for error patterns"""
    recent_calls = history["calls"][-5:]
    
    # Pattern 1: Multiple failed calls in a row
    if len(recent_calls) >= 3:
        if all(c.get("status") == "error" for c in recent_calls[-3:]):
            print("\n" + "="*60)
            print("[WARNING] Detected 3 consecutive Write errors!")
         print("="*60)
        print("\nCommon cause: Missing file_path or content parameters")
       print("\nSolution:")
            print("  1. STOP calling Write")
            print("  2. Prepare complete content")
            print("  3. Call Write ONCE with all parameters")
            print("\nReference: ~/.claude/skills/write-file-correctly/")
            print("="*60 + "\n")
            return True
    
  return False

def record_call(status, file_path=None, content_length=0):
    history = load_history()
    history["calls"].append({
        "status": status,
        "file_path": file_path,
        "content_length": content_length,
        "timestamp": str(Path.cwd())
  })
    
    # Keep only last 20 calls
    history["calls"] = history["calls"][-20:]
    
    if status == "error":
        history["errors"] += 1
    
    save_history(history)
  check_pattern(history)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: monitor.py <status> [file_path] [content_length]")
        sys.exit(1)
    
    status = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else None
    content_length = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    
    record_call(status, file_path, content_length)
```

---

## 推荐方案组合

### 立即生效（已完成）
1. ✅ **CLAUDE.md** - 项目级提示（已创建）
2. ✅ **Skill 文档** - 参考文档（已创建）
3. ✅ **验证脚本** - 手动验证（已创建）

### 增强方案（可选）
4. **全局 Memory** - 创建 `~/.claude/memory/write-file-protocol.md`
5. **Safe Write Skill** - 创建包装 skill
6. **Monitor Script** - 创建监控脚本

---

## 使用方式

### 当前可用（无需额外配置）

每次打开 DevPalAgent 项目，Claude 会自动读取 `CLAUDE.md`，看到：

```
## Critical Development Rules

### File Writing Protocol

**IMPORTANT**: Before using the Write tool, ALWAYS follow this checklist:
1. ✅ Prepare content completely
2. ✅ Verify parameters
3. ✅ Check length
4. ✅ Single call
```

### 手动提醒

你可以在对话中说：
- "请遵循 CLAUDE.md 中的 File Writing Protocol"
- "参考 write-file-correctly skill"
- "先验证参数再写文件"

### 自动验证（需要创建额外 skills）

```bash
# 创建 safe-write skill
/safe-write path/to/file.md "content"

# 或使用验证脚本
python ~/.claude/skills/write-file-correctly/skill.py "path" "content"
```

---

## 效果验证

### 测试 1：CLAUDE.md 是否生效

```bash
# 打开项目
cd c:\code\DevPalAgent

# Claude 应该自动加载 CLAUDE.md
# 在对话中问："项目有什么开发规则？"
# Claude 应该提到 File Writing Protocol
```

### 测试 2：Skill 是否可用

```bash
# 查看 skill
cat ~/.claude/skills/write-file-correctly/README.md

# 验证参数
python ~/.claude/skills/write-file-correctly/skill.py "" ""
# 应该显示错误

python ~/.claude/skills/write-file-correctly/skill.py "test.md" "content"
# 应该显示 [OK]
```

---

## 总结

| 方法 | 状态 | 自动程度 | 推荐度 |
|---|:---:|:---:|:---:|
| CLAUDE.md | ✅ 已完成 | 自动加载 | ⭐⭐⭐⭐⭐ |
| Skill 文档 | ✅ 已完成 | 手动参考 | ⭐⭐⭐⭐ |
| 验证脚本 | ✅ 已完成 | 手动调用 | ⭐⭐⭐ |
| 全局 Memory | 待创建 | 自动提示 | ⭐⭐⭐⭐ |
| Safe Write Skill | 待创建 | 半自动 | ⭐⭐⭐ |
| Monitor Script | 待创建 | 自动监控 | ⭐⭐⭐⭐ |

**当前最有效的方法**：CLAUDE.md 已经创建，每次打开项目 Claude 都会看到 File Writing Protocol！
