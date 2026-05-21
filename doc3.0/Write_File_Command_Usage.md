# Write File Correctly - Command Usage Guide

## ✅ 已完成的封装

### 1. Skill 目录结构

```
~/.claude/skills/write-file-correctly/
├── README.md          # 完整的使用指南和清单
├── skill.py           # Python 验证脚本
└── check-write.sh     # Bash 快速命令
```

### 2. 可用命令

#### 方式 1: 直接查看清单（最快）

```bash
check-write
# 或
write-checklist
```

**输出**：
```
=== Write Tool Checklist ===

✓ Before calling Write, ensure:
  1. Content is completely prepared
  2. file_path is determined
  3. content is ready
  4. Length checked (>150 lines needs chunking)

Correct usage:
  Write(file_path="path/to/file.md", content="...")

Common mistakes:
  ✗ Write()  # Missing parameters
  ✗ Calling Write multiple times without fixing errors
```

#### 方式 2: 验证参数

```bash
check-write validate "path/to/file.md" "content here"
# 或
validate-write "path/to/file.md" "content here"
```

**输出示例（成功）**：
```
[OK] Write tool parameters are valid
```

**输出示例（失败）**：
```
Write Tool Validation Failed:
  [X] file_path is missing
  [X] content is missing

Correct usage:
  Write(file_path="path/to/file.md", content="...")
```

#### 方式 3: 查看完整文档

```bash
cat ~/.claude/skills/write-file-correctly/README.md
```

#### 方式 4: 在对话中调用

虽然 `/write-file-correctly` 命令可能还不能直接调用，但你可以：

```
请显示 write-file-correctly skill 的内容
```

或

```
参考 ~/.claude/skills/write-file-correctly/README.md
```

---

## 🎯 使用场景

### 场景 1: 写文件前快速检查

```bash
# 在终端运行
check-write

# 看到清单后，在 Claude 对话中写文件
Write(
    file_path="doc/guide.md",
    content="..."
)
```

### 场景 2: 验证参数是否正确

```bash
# 测试参数
check-write validate "test.md" "Hello World"
# 输出: [OK] Write tool parameters are valid

# 测试空参数
check-write validate "" ""
# 输出: [X] file_path is missing, [X] content is missing
```

### 场景 3: 提醒 Claude 遵循规则

在对话中说：
```
请先运行 check-write 命令查看清单，然后再写文件
```

或

```
遵循 write-file-correctly skill 的规则
```

---

## 📊 集成效果

| 方法 | 命令 | 自动程度 | 状态 |
|---|---|:---:|:---:|
| **CLAUDE.md** | 自动加载 | 🟢 自动 | ✅ 已完成 |
| **Bash 命令** | `check-write` | 🟡 手动 | ✅ 已完成 |
| **验证脚本** | `validate-write` | 🟡 手动 | ✅ 已完成 |
| **Skill 文档** | `cat ~/.claude/skills/...` | 🟡 手动 | ✅ 已完成 |
| **对话提醒** | "参考 skill" | 🟡 手动 | ✅ 可用 |

---

## 🚀 快速开始

### 1. 测试命令是否可用

```bash
# 重新加载 bashrc
source ~/.bashrc

# 测试命令
check-write
```

### 2. 在写文件前使用

```bash
# 步骤 1: 查看清单
check-write

# 步骤 2: 在 Claude 中写文件
# （确保遵循清单）
```

### 3. 验证参数（可选）

```bash
# 验证你准备的参数
check-write validate "my-file.md" "my content"
```

---

## 📝 示例工作流

### 完整的写文件流程

```bash
# 1. 在终端查看清单
$ check-write

=== Write Tool Checklist ===
✓ Before calling Write, ensure:
  1. Content is completely prepared
  2. file_path is determined
  3. content is ready
  4. Length checked (>150 lines needs chunking)

# 2. 在 Claude 对话中
User: "请创建一个 AI Agent 面试文档"

Claude: 
# 我会先准备完整内容
content = """
# AI Agent Interview Guide
## Question 1: ...
## Question 2: ...
...
"""

# 然后一次性调用 Write
Write(
    file_path="doc3.0/AI_Agent_Interview_Guide.md",
    content=content
)

# 3. 验证（可选）
$ check-write validate "doc3.0/AI_Agent_Interview_Guide.md" "content..."
[OK] Write tool parameters are valid
```

---

## 🔧 故障排除

### 问题 1: 命令不存在

```bash
# 解决方案：重新加载 bashrc
source ~/.bashrc

# 或者直接运行脚本
~/.claude/skills/write-file-correctly/check-write.sh
```

### 问题 2: Python 脚本报错

```bash
# 检查 Python 是否可用
python --version

# 手动运行脚本
python ~/.claude/skills/write-file-correctly/skill.py "test" "content"
```

### 问题 3: Claude 没有遵循规则

**原因**: CLAUDE.md 可能没有被加载

**解决方案**:
1. 确认 `c:\code\DevPalAgent\CLAUDE.md` 存在
2. 重新打开项目
3. 在对话中明确提醒："请遵循 CLAUDE.md 中的 File Writing Protocol"

---

## 📚 相关文档

- **Skill 文档**: `~/.claude/skills/write-file-correctly/README.md`
- **项目规则**: `c:\code\DevPalAgent\CLAUDE.md`
- **集成指南**: `c:\code\DevPalAgent\doc3.0/Write_File_Skill_Integration_Guide.md`
- **验证脚本**: `~/.claude/skills/write-file-correctly/skill.py`
- **快速命令**: `~/.claude/skills/write-file-correctly/check-write.sh`

---

## 🎉 总结

现在你有 **5 种方式** 查看和使用这个 skill：

1. ✅ **自动提醒**: CLAUDE.md 自动加载（最重要）
2. ✅ **快速命令**: `check-write` 查看清单
3. ✅ **参数验证**: `validate-write "path" "content"`
4. ✅ **完整文档**: `cat ~/.claude/skills/write-file-correctly/README.md`
5. ✅ **对话提醒**: "参考 write-file-correctly skill"

**推荐工作流**: 
- 写文件前在终端运行 `check-write`
- 在 Claude 对话中遵循清单
- 必要时用 `validate-write` 验证参数
