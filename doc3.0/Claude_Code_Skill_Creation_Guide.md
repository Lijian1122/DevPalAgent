# Claude Code Skill 创建与使用完整指南

**文档版本**: 1.0  
**创建日期**: 2026-05-20  
**适用范围**: Claude Code CLI / Desktop / VS Code Extension

---

## 📚 目录

1. [Skill 概述](#skill-概述)
2. [Skill 类型与目录结构](#skill-类型与目录结构)
3. [创建 Skill 的完整流程](#创建-skill-的完整流程)
4. [实战案例：Write File Correctly](#实战案例write-file-correctly)
5. [Skill 调试与验证](#skill-调试与验证)
6. [最佳实践](#最佳实践)
7. [常见问题](#常见问题)

---

## Skill 概述

### 什么是 Skill？

Skill 是 Claude Code 的扩展机制，允许你：
- 创建可复用的提示词模板
- 封装常用的工作流程
- 提供自动化的检查清单
- 集成外部工具和脚本

### Skill 的三种形式

| 类型 | 位置 | 调用方式 | 用途 |
|---|---|---|---|
| **Command** | `~/.claude/commands/` | `/skill-name` | 快速调用的提示词 |
| **Skill** | `~/.claude/skills/` | 系统识别 | 完整的工具包（文档+脚本） |
| **Project Rule** | `项目根目录/CLAUDE.md` | 自动加载 | 项目级规则和约定 |

---

## Skill 类型与目录结构

### 1. Command（命令型 Skill）

**位置**: `~/.claude/commands/skill-name.md`

**特点**:
- 单个 Markdown 文件
- 通过 `/skill-name` 调用
- 内容作为提示词注入对话

**目录结构**:
```
~/.claude/commands/
├── commit-message.md
├── write-file-correctly.md
└── your-skill.md
```

**文件格式**:
```markdown
# Skill 标题

这里是提示词内容，会被注入到对话中。

## 使用说明

详细的使用指导...

## 示例

具体的示例...
```

### 2. Skill（工具包型 Skill）

**位置**: `~/.claude/skills/skill-name/`

**特点**:
- 包含多个文件（文档+脚本）
- 可以包含可执行脚本
- 支持复杂的工作流

**目录结构**:
```
~/.claude/skills/skill-name/
├── README.md    # 主文档（必需）
├── skill.py      # Python 脚本（可选）
├── skill.sh           # Bash 脚本（可选）
└── config.json        # 配置文件（可选）
```

**README.md 格式**:
```markdown
---
name: skill-name
description: 简短描述（一句话）
---

# Skill 名称

详细的使用文档...
```

### 3. Project Rule（项目级规则）

**位置**: `项目根目录/CLAUDE.md`

**特点**:
- 项目打开时自动加载
- 优先级最高
- 适合项目特定规则

**文件格式**:
```markdown
# 项目名称

## Critical Development Rules

### 规则 1

**IMPORTANT**: 重要规则说明

### 规则 2

详细说明...
```

---

## 创建 Skill 的完整流程

### 步骤 1: 确定 Skill 类型

**决策树**:

```
需要创建 Skill？
│
├─ 只是简单的提示词？
│  └─ 是 → 创建 Command
│     位置: ~/.claude/commands/name.md
│
├─ 需要可执行脚本？
│  └─ 是 → 创建 Skill
│     位置: ~/.claude/skills/name/
│
└─ 项目特定规则？
   └─ 是 → 创建 CLAUDE.md
      位置: 项目根目录/CLAUDE.md
```

### 步骤 2: 创建目录和文件

#### 方案 A: 创建 Command

```bash
# 1. 创建文件
touch ~/.claude/commands/your-skill.md

# 2. 编辑内容
cat > ~/.claude/commands/your-skill.md << 'EOF'
# Your Skill Title

提示词内容...

## 使用说明

详细说明...
EOF

# 3. 验证
ls -la ~/.claude/commands/your-skill.md
```

#### 方案 B: 创建 Skill

```bash
# 1. 创建目录
mkdir -p ~/.claude/skills/your-skill

# 2. 创建 README.md
cat > ~/.claude/skills/your-skill/README.md << 'EOF'
---
name: your-skill
description: 简短描述
---

# Your Skill

详细文档...
EOF

# 3. 创建脚本（可选）
cat > ~/.claude/skills/your-skill/skill.py << 'EOF'
#!/usr/bin/env python3
# 脚本内容...
EOF
chmod +x ~/.claude/skills/your-skill/skill.py

# 4. 验证
ls -la ~/.claude/skills/your-skill/
```

#### 方案 C: 创建 CLAUDE.md

```bash
# 1. 在项目根目录创建
cd /path/to/your/project

# 2. 创建文件
cat > CLAUDE.md << 'EOF'
# 项目名称

## Critical Development Rules

### 规则 1

**IMPORTANT**: 重要规则

### 规则 2

详细说明...
EOF

# 3. 验证
cat CLAUDE.md
```

### 步骤 3: 编写内容

#### Command 内容模板

```markdown
# [Skill 名称]

[一句话说明这个 skill 的用途]

## 📋 使用清单

### ✅ 检查项

- [ ] 检查项 1
- [ ] 检查项 2
- [ ] 检查项 3

### ✅ 正确做法

```[language]
# 示例代码
正确的做法...
```
### ❌ 常见错误

```[language]
# 错误示例
错误的做法...
```

## 🎯 关键原则

1. 原则 1
2. 原则 2
3. 原则 3

## 📚 示例

### 示例 1: [场景名称]

```[language]
具体示例...
```

## 🔗 相关资源

- 资源 1
- 资源 2
```

#### Skill README 模板

```markdown
---
name: skill-name
description: 一句话描述
---

# Skill 名称

## 问题描述

这个 skill 解决什么问题？

## 解决方案

如何解决这个问题？

## 使用方法

### 方式 1: 命令行

```bash
python ~/.claude/skills/skill-name/skill.py [args]
```

### 方式 2: 在对话中

```
请参考 skill-name skill
```

## 配置选项

| 选项 | 说明 | 默认值 |
|---|---|---|
| option1 | 说明 | default |

## 示例

### 示例 1

```bash
# 命令
python skill.py example

# 输出
Expected output...
```

## 故障排除

### 问题 1

**症状**: 描述问题

**解决**: 解决方法

## 相关资源

- 链接 1
- 链接 2
```

### 步骤 4: 测试 Skill

#### 测试 Command

```bash
# 1. 检查文件是否存在
ls -la ~/.claude/commands/your-skill.md

# 2. 查看内容
cat ~/.claude/commands/your-skill.md

# 3. 在 Claude Code 中测试
# 输入: /your-skill
# 预期: 显示 skill 内容
```

#### 测试 Skill
```bash
# 1. 检查目录结构
ls -la ~/.claude/skills/your-skill/

# 2. 测试脚本
python ~/.claude/skills/your-skill/skill.py --help

# 3. 验证系统识别
# Claude Code 会在 system-reminder 中列出
```

#### 测试 CLAUDE.md

```bash
# 1. 确认文件在项目根目录
ls -la CLAUDE.md

# 2. 打开项目
# Claude Code 会自动加载

# 3. 验证加载
# 在对话中问："项目有什么开发规则？"
# Claude 应该能回答 CLAUDE.md 中的内容
```

### 步骤 5: 文档化

创建使用文档：

```bash
# 在项目 doc 目录创建说明
cat > doc/skills/your-skill-guide.md << 'EOF'
# Your Skill 使用指南

## 快速开始

...

## 详细说明

...

## 示例

...
EOF
```

---

## 实战案例：Write File Correctly

### 背景

**问题**: Claude 连续 5 次调用 Write 工具但都缺少参数

**目标**: 创建一个 skill 来防止这个错误

### 解决方案架构

```
多层防护体系:
├── 自动层: CLAUDE.md（项目打开自动生效）
├── 命令层: /write-file-correctly（手动提醒）
├── 工具层: Skill 文档和脚本
└── 验证层: Python 验证脚本
```

### 实施步骤

#### 1. 创建 CLAUDE.md（自动提醒）

```bash
cat > c:/code/DevPalAgent/CLAUDE.md << 'EOF'
# DevPalAgent

## Critical Development Rules

### File Writing Protocol

**IMPORTANT**: Before using the Write tool, ALWAYS follow this checklist:

1. ✅ **Prepare content completely**
2. ✅ **Verify parameters**
3. ✅ **Check length**
4. ✅ **Single call**

❌ **NEVER do this**:
```python
Write()  # Missing parameters!
```

✅ **ALWAYS do this**:
```python
content = """..."""
Write(file_path="path.md", content=content)
```
EOF
```

#### 2. 创建 Command（手动提醒）

```bash
cat > ~/.claude/commands/write-file-correctly.md << 'EOF'
# Write File Correctly Command

## 📋 Write 工具使用清单

### ✅ 必需检查项

- [ ] 内容已完整准备
- [ ] file_path 已确定
- [ ] content 已准备
- [ ] 长度已检查

### ✅ 正确的调用方式

```python
content = """..."""
Write(file_path="path.md", content=content)
```

### ❌ 常见错误

```python
Write()  # ❌ 缺少参数
```
EOF
```

#### 3. 创建 Skill（完整工具包）

```bash
# 创建目录
mkdir -p ~/.claude/skills/write-file-correctly

# 创建 README
cat > ~/.claude/skills/write-file-correctly/README.md << 'EOF'
---
name: write-file-correctly
description: Correctly use Write tool to avoid missing parameter errors
---

# Write File Correctly Skill

## Problem
Repeatedly calling Write tool without providing required parameters.

## Solution
Follow 4-step checklist before calling Write.

## Usage
```bash
python ~/.claude/skills/write-file-correctly/skill.py "path" "content"
```
EOF

# 创建验证脚本
cat > ~/.claude/skills/write-file-correctly/skill.py << 'EOF'
#!/usr/bin/env python3
import sys

def validate_write_params(file_path=None, content=None):
    errors = []
    if not file_path:
        errors.append("[X] file_path is missing")
    if not content:
        errors.append("[X] content is missing")
    
    if errors:
      print("Write Tool Validation Failed:")
        for error in errors:
            print(f"  {error}")
        return False
    
    print("[OK] Write tool parameters are valid")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python skill.py <file_path> <content>")
        sys.exit(1)
    
    validate_write_params(sys.argv[1], sys.argv[2])
EOF

chmod +x ~/.claude/skills/write-file-correctly/skill.py
```

#### 4. 创建快速命令脚本

```bash
cat > ~/.claude/skills/write-file-correctly/check-write.sh << 'EOF'
#!/bin/bash
echo "=== Write Tool Checklist ==="
echo ""
echo "✓ Before calling Write, ensure:"
echo "  1. Content is completely prepared"
echo "  2. file_path is determined"
echo "  3. content is ready"
echo "  4. Length checked (>150 lines needs chunking)"
echo ""
echo "Correct usage:"
echo '  Write(file_path="path/to/file.md", content="...")'
EOF

chmod +x ~/.claude/skills/write-file-correctly/check-write.sh
```

#### 5. 验证效果

```bash
# 测试 Command
# 在 Claude Code 中输入: /write-file-correctly

# 测试验证脚本
python ~/.claude/skills/write-file-correctly/skill.py "" ""
# 预期输出: [X] file_path is missing, [X] content is missing

python ~/.claude/skills/write-file-correctly/skill.py "test.md" "content"
# 预期输出: [OK] Write tool parameters are valid

# 测试快速命令
~/.claude/skills/write-file-correctly/check-write.sh
# 预期输出: 显示清单
```

### 效果验证

**测试场景**: 要求 Claude 创建一个文件

**之前**:
```python
Write()  # 失败
Write()  # 失败
Write()  # 失败（连续 5 次）
```

**之后**:
```python
# Claude 自动遵循协议
content = """..."""
Write(file_path="test.md", content=content)
# ✅ 一次成功
```

---

## Skill 调试与验证

### 调试清单

## 1. 文件存在性检查

```bash
# Command
ls -la ~/.claude/commands/your-skill.md

# Skill
ls -la ~/.claude/skills/your-skill/
ls -la ~/.claude/skills/your-skill/README.md

# CLAUDE.md
ls -la CLAUDE.md
```

#### 2. 内容格式检查

```bash
# 查看文件内容
cat ~/.claude/commands/your-skill.md

# 检查 frontmatter（Skill）
head -10 ~/.claude/skills/your-skill/README.md

# 检查 CLAUDE.md 结构
head -30 CLAUDE.md
```

#### 3. 系统识别检查

**Command 识别**:
- 在 Claude Code 中输入 `/`
- 查看是否列出你的 skill

**Skill 识别**:
- 查看 system-reminder 消息
- 应该列出你的 skill

**CLAUDE.md 识别**:
- 在对话中问："项目有什么规则？"
- Claude 应该能回答 CLAUDE.md 中的内容

#### 4. 功能测试

```bash
# 测试脚本执行
python ~/.claude/skills/your-skill/skill.py --help

# 测试 bash 脚本
~/.claude/skills/your-skill/skill.sh

# 测试 Command
# 在 Claude Code 中: /your-skill
```

### 常见问题排查

#### 问题 1: Command 不显示

**症状**: 输入 `/` 看不到 skill

**排查**:
```bash
# 1. 检查文件是否存在
ls -la ~/.claude/commands/your-skill.md

# 2. 检查文件名
# 确保是 .md 后缀

# 3. 重启 Claude Code
```

#### 问题 2: Skill 脚本无法执行

**症状**: 运行脚本报错 "Permission denied"

**解决**:
```bash
# 添加执行权限
chmod +x ~/.claude/skills/your-skill/skill.py
chmod +x ~/.claude/skills/your-skill/skill.sh
```

#### 问题 3: CLAUDE.md 没有自动加载

**症状**: Claude 不知道项目规则

**排查**:
```bash
# 1. 确认文件在项目根目录
ls -la CLAUDE.md

# 2. 确认文件名正确（大写）
# 必须是 CLAUDE.md，不是 claude.md
# 3. 重新打开项目
```

#### 问题 4: Python 脚本编码错误

**症状**: Windows 下 emoji 显示错误

**解决**:
```python
# 在脚本开头添加
# -*- coding: utf-8 -*-

# 避免使用 emoji，改用 ASCII
# ✅ → [OK]
# ❌ → [X]
# ⚠️ → [!]
```

---

## 最佳实践

### 1. 命名规范

#### Command 命名

```bash
# 好的命名（kebab-case）
write-file-correctly.md
commit-message.md
code-review.md

# 不好的命名
WriteFileCorrectly.md  # 不要用 PascalCase
write_file_correctly.md  # 不要用 snake_case
```

#### Skill 命名

```bash
# 好的命名（kebab-case）
~/.claude/skills/write-file-correctly/
~/.claude/skills/commit-message/

# 不好的命名
~/.claude/skills/WriteFileCorrectly/
~/.claude/skills/write_file_correctly/
```

### 2. 文档结构

#### 清晰的层次

```markdown
# 标题（H1）- 只有一个

## 主要章节（H2）

### 子章节（H3）

#### 细节（H4）- 谨慎使用
```

#### 使用清单

```markdown
## 检查清单

- [ ] 检查项 1
- [ ] 检查项 2
- [ ] 检查项 3
```

#### 代码示例

````markdown
### 正确做法

```python
# 好的示例
correct_code()
```

### 错误做法

```python
# 错误示例
wrong_code()
```
````

### 3. 脚本编写

#### Python 脚本模板

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill 名称

简短描述
"""
import sys
import os

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python skill.py <args>")
        sys.exit(1)
    
    # 主要逻辑
    pass

if __name__ == "__main__":
    main()
```

#### Bash 脚本模板

```bash
#!/bin/bash
# Skill 名称
# 简短描述

set -e  # 遇到错误立即退出
# 主要逻辑
main() {
    echo "Skill 输出"
}

# 执行
main "$@"
```

### 4. 版本控制

#### 包含在 Git 中

```bash
# 项目级 CLAUDE.md
git add CLAUDE.md
git commit -m "docs: add project rules"

# 项目级 skill 文档
git add doc/skills/
git commit -m "docs: add skill documentation"
```

#### 不包含在 Git 中

```bash
# 全局 Command 和 Skill
# ~/.claude/commands/
# ~/.claude/skills/
# 这些是用户级配置，不应提交到项目仓库
```

### 5. 文档维护

#### 保持更新

```markdown
# Skill 名称

**版本**: 1.0  
**更新日期**: 2026-05-20  
**状态**: 稳定

## 更新日志

### v1.0 (2026-05-20)
- 初始版本
- 添加基础功能
```

#### 添加示例

```markdown
## 示例

### 示例 1: 基础用法

**场景**: 描述场景

**命令**:
```bash
command here
```

**输出**:
```
expected output
```

**说明**: 解释说明
```

---

## 常见问题

### Q1: Command 和 Skill 有什么区别？

**A**: 
- **Command**: 单个 .md 文件，通过 `/` 调用，适合简单提示词
- **Skill**: 完整目录，包含文档+脚本，适合复杂工具包

### Q2: 什么时候用 CLAUDE.md？

**A**: 
- 项目特定的规则和约定
- 需要自动加载的重要规则
- 优先级最高的提示

### Q3: Skill 可以跨项目使用吗？

**A**: 
- **Command**: ✅ 全局可用（`~/.claude/commands/`）
- **Skill**: ✅ 全局可用（`~/.claude/skills/`）
- **CLAUDE.md**: ❌ 仅当前项目

### Q4: 如何让 Claude 自动遵循 Skill？

**A**: 
1. 将规则写入 `CLAUDE.md`（最有效）
2. 在 CLAUDE.md 中引用 Skill 位置
3. 用户可以用 `/skill-name` 手动提醒

### Q5: Skill 脚本可以用其他语言吗？

**A**: 
可以，只要：
- 添加 shebang（如 `#!/usr/bin/env python3`）
- 添加执行权限（`chmod +x`）
- 系统中安装了对应的解释器

### Q6: 如何分享 Skill？

**A**: 
```bash
# 打包 Skill
tar -czf my-skill.tar.gz -C ~/.claude/skills my-skill/

# 分享给他人
# 他人解压到 ~/.claude/skills/
tar -xzf my-skill.tar.gz -C ~/.claude/skills/
```

### Q7: Skill 可以调用其他 Skill 吗？

**A**: 
可以，在脚本中调用：
```bash
# 在 skill.sh 中
~/.claude/skills/other-skill/skill.py
```

### Q8: 如何调试 Skill 不生效的问题？

**A**: 
按顺序检查：
1. 文件是否存在？`ls -la`
2. 文件名是否正确？（大小写、后缀）
3. 权限是否正确？`chmod +x`
4. 内容格式是否正确？`cat` 查看
5. 重启 Claude Code

---

## 附录

### A. 完整的 Skill 模板

#### Command 模板

```markdown
# [Skill 名称]

[一句话说明]

## 📋 使用清单

### ✅ 检查项

- [ ] 项 1
- [ ] 项 2

### ✅ 正确做法

```[language]
正确示例
```

### ❌ 错误做法

```[language]
错误示例
```

## 🎯 关键原则

1. 原则 1
2. 原则 2

## 📚 示例

### 示例 1

```[language]
示例代码
```

## 🔗 相关资源

- 资源 1
- 资源 2
```

#### Skill 完整模板

**目录结构**:
```
~/.claude/skills/skill-name/
├── README.md
├── skill.py
├── skill.sh
└── config.json
```

**README.md**:
```markdown
---
name: skill-name
description: 简短描述
---

# Skill 名称

## 问题描述

## 解决方案

## 使用方法

## 配置选项

## 示例

## 故障排除

## 相关资源
```

**skill.py**:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Skill 名称"""
import sys

def main():
    if len(sys.argv) < 2:
      print("Usage: python skill.py <args>")
        sys.exit(1)
    # 主要逻辑
    pass

if __name__ == "__main__":
    main()
```

**skill.sh**:
```bash
#!/bin/bash
set -e
# 主要逻辑
echo "Skill 输出"
```

### B. 参考资源

- **Claude Code 文档**: https://claude.ai/code
- **本项目示例**: 
  - `~/.claude/commands/write-file-correctly.md`
  - `~/.claude/skills/write-file-correctly/`
  - `c:\code\DevPalAgent\CLAUDE.md`
- **验证报告**: `doc3.0/Write_File_Protocol_Verification_Report.md`

---

**文档维护**: 本文档应随 Claude Code 版本更新而更新  
**反馈**: 如有问题或建议，请更新本文档
