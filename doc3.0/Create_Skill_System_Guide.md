# Create Skill System - 完整指南

**创建日期**: 2026-05-20  
**版本**: 1.0  
**目的**: 将 Skill 创建经验封装为可复用的自动化工具

---

## 📋 系统概述

### 什么是 Create Skill System？

Create Skill System 是一个自动化工具，用于快速创建 Claude Code Skills。它封装了从 write-file-correctly 项目中积累的最佳实践和经验。

### 核心功能

1. **交互式向导**: 引导用户创建 Skill
2. **模板系统**: 提供 5 种预定义模板
3. **自动生成**: 生成完整的文件结构
4. **参数验证**: 检查 Skill 名称和配置
5. **即时测试**: 验证创建的 Skill 是否可用

---

## 🎯 系统组成

### 1. Command 文件

**位置**: `~/.claude/commands/create-skill.md`

**功能**: 
- 提供 `/create-skill` 命令
- 显示交互式向导
- 引导用户提供必要信息

**调用方式**:
```bash
/create-skill
```

### 2. Skill 目录

**位置**: `~/.claude/skills/create-skill/`

**文件结构**:
```
~/.claude/skills/create-skill/
├── README.md              # 完整文档
├── create.py           # Python 自动化脚本
└── QUICK_REFERENCE.md     # 快速参考
```

### 3. 自动化脚本

**位置**: `~/.claude/skills/create-skill/create.py`

**功能**:
- 验证 Skill 名称格式
- 生成文件和目录结构
- 应用模板
- 创建脚本文件
- 验证创建结果

---

## 🎨 可用模板

### 1. checklist - 检查清单型

**适用场景**: 操作前的检查清单

**生成内容**:
- 4 步检查清单
- 正确/错误示例
- 关键原则说明

**真实案例**: write-file-correctly

**使用方式**:
```bash
python ~/.claude/skills/create-skill/create.py \
  --name "my-checklist" \
  --template checklist \
  --description "My operation checklist"
```

### 2. git-commit - Git 提交型

**适用场景**: 规范化 commit message

**生成内容**:
- 7 种 commit 类型表
- 格式规范
- [by AI] 标识
- Co-Authored-By 落款

**真实案例**: commit-message

**使用方式**:
```bash
python ~/.claude/skills/create-skill/create.py \
  --name "my-commit-format" \
  --template git-commit \
  --description "Custom commit message format"
```

### 3. code-review - 代码审查型

**适用场景**: 代码审查检查清单

**生成内容**:
- 审查维度（安全性、性能、可读性）
- 每个维度的检查项
- 评分标准

**使用方式**:
```bash
python ~/.claude/skills/create-skill/create.py \
  --name "code-review" \
  --template code-review \
  --description "Code review checklist"
```

### 4. test-generator - 测试生成型

**适用场景**: 自动生成测试用例

**生成内容**:
- 测试框架配置
- 测试模板
- 覆盖率要求

**使用方式**:
```bash
python ~/.claude/skills/create-skill/create.py \
  --name "test-generator" \
  --template test-generator \
  --with-python \
  --description "Automated test case generator"
```

### 5. custom - 自定义型

**适用场景**: 完全自定义的 Skill

**生成内容**:
- 基础文件结构
- 空白模板

**使用方式**:
```bash
python ~/.claude/skills/create-skill/create.py \
  --name "my-custom-skill" \
  --template custom \
  --description "My custom skill"
```

---

## 🚀 使用方式

### 方式 1: 交互式创建（推荐）

```bash
/create-skill
```

然后回答以下问题：
1. Skill 名称（kebab-case）
2. Skill 类型（command / skill / claude-md）
3. 功能描述
4. 是否需要脚本（Python / Bash）

### 方式 2: 命令行创建

```bash
python ~/.claude/skills/create-skill/create.py \
  --name "my-skill" \
  --type command \
  --description "My skill description"
```

### 方式 3: 基于模板创建

```bash
python ~/.claude/skills/create-skill/create.py \
  --name "my-checklist" \
  --template checklist
```

### 方式 4: 创建完整 Skill（包含脚本）

```bash
python ~/.claude/skills/create-skill/create.py \
  --name "validate-json" \
  --type skill \
  --with-python \
  --with-bash \
  --description "JSON validation tool"
```

---

## 📁 生成的文件结构

### Command 类型

```
~/.claude/commands/
└── skill-name.md
```

**特点**:
- 单个 Markdown 文件
- 通过 `/skill-name` 调用
- 适合简单的提示词模板

### Skill 类型

```
~/.claude/skills/skill-name/
├── README.md         # 主文档
├── skill.py       # Python 脚本（可选）
└── skill.sh         # Bash 脚本（可选）

~/.claude/commands/
└── skill-name.md       # 对应的 Command
```

**特点**:
- 完整的工具包
- 包含可执行脚本
- 支持复杂的工作流

### CLAUDE.md 类型

```
项目根目录/
└── CLAUDE.md           # 项目级规则
```

**特点**:
- 项目级自动加载
- 每次打开项目都生效
- 适合项目特定规则

---

## 🔧 脚本参数

### create.py 完整参数

```bash
python ~/.claude/skills/create-skill/create.py [OPTIONS]

Options:
  --name TEXT          Skill 名称（必需，kebab-case）
  --type TEXT          Skill 类型: command|skill|claude-md (默认: command)
  --description TEXT   Skill 描述
  --template TEXT      使用模板: checklist|git-commit|code-review|test-generator|custom
  --with-python        生成 Python 脚本（仅 skill 类型）
  --with-bash          生成 Bash 脚本（仅 skill 类型）
  --project-path TEXT  项目路径（仅 claude-md 类型）
  --list-templates     列出所有可用模板
  --help               显示帮助信息
```

---

## ✅ 验证流程

创建完成后，脚本会自动验证：

1. ✅ 文件是否创建成功
2. ✅ 文件格式是否正确
3. ✅ 命令是否可调用（Command）
4. ✅ 脚本是否可执行（Skill）
5. ✅ 文档是否完整

**手动验证**:

```bash
# 测试 Command
/skill-name

# 测试 Python 脚本
python ~/.claude/skills/skill-name/skill.py

# 测试 Bash 脚本
~/.claude/skills/skill-name/skill.sh

# 查看文档
cat ~/.claude/skills/skill-name/README.md
```

---

## 📝 命名规范

### ✅ 推荐格式

- **kebab-case**: `write-file-correctly`, `commit-message`, `code-review`
- **动词开头**: `create-`, `check-`, `validate-`, `generate-`
- **描述性**: 名称应清晰表达功能
- **长度适中**: 2-4 个单词

### ❌ 避免

- ❌ 驼峰命名: `writeFileCorrectly`
- ❌ 下划线: `write_file_correctly`
- ❌ 过于简短: `wfc`
- ❌ 过于冗长: `write-file-correctly-and-validate-all-parameters`

---

## 🎯 最佳实践

### 1. 单一职责

每个 Skill 只做一件事，做好一件事。

**好的例子**:
- `write-file-correctly` - 只关注 Write 工具参数验证
- `commit-message` - 只关注 commit message 格式

**不好的例子**:
- `write-and-commit` - 混合了两个功能

### 2. 清晰的文档

README.md 应包含：
- 功能说明
- 使用方式（至少 2 种）
- 示例（至少 2 个）
- 常见问题

### 3. 可执行的脚本

如果包含脚本，确保：
- 有清晰的参数说明
- 有错误处理
- 有使用示例
- 输出格式统一（[OK] / [X] / [!]）

### 4. 自动化测试

创建后立即测试：
- Command 是否可调用
- 脚本是否可执行
- 文档是否完整
- 示例是否正确

### 5. 版本控制

在 README.md 中记录：
- 创建日期
- 版本号
- 更新历史

---

## 📚 真实案例

### 案例 1: write-file-correctly

**需求**: 防止 Write 工具参数缺失错误

**创建过程**:
```bash
# 1. 创建 Command
python create.py --name write-file-correctly --template checklist

# 2. 创建 Skill（包含脚本）
python create.py --name write-file-correctly --type skill --with-python --with-bash

# 3. 创建 CLAUDE.md
# 手动添加到项目根目录
```

**生成文件**:
- `~/.claude/commands/write-file-correctly.md`
- `~/.claude/skills/write-file-correctly/README.md`
- `~/.claude/skills/write-file-correctly/skill.py`
- `~/.claude/skills/write-file-correctly/check-write.sh`
- `c:\code\DevPalAgent\CLAUDE.md`

**结果**: ✅ 成功防止参数缺失错误，验证报告显示 100% 通过

### 案例 2: commit-message

**需求**: 规范化 git commit message

**创建过程**:
```bash
python create.py --name commit-message --template git-commit
```

**生成文件**:
- `~/.claude/commands/commit-message.md`

**结果**: ✅ 统一了 commit message 格式，包含 [by AI] 标识

---

## 🔗 相关资源

### 文档

- **完整指南**: `doc3.0/Claude_Code_Skill_Creation_Guide.md`
- **本文档**: `doc3.0/Create_Skill_System_Guide.md`
- **快速参考**: `~/.claude/skills/create-skill/QUICK_REFERENCE.md`
- **验证报告**: `doc3.0/Write_File_Protocol_Verification_Report.md`
- **使用指南**: `doc3.0/Write_File_Command_Usage.md`

### 文件

- **Command**: `~/.claude/commands/create-skill.md`
- **README**: `~/.claude/skills/create-skill/README.md`
- **脚本**: `~/.claude/skills/create-skill/create.py`

### 案例

- **write-file-correctly**: `~/.claude/skills/write-file-correctly/`
- **commit-message**: `~/.claude/commands/commit-message.md`

---

## 🎉 快速开始

### 1. 查看可用模板

```bash
python ~/.claude/skills/create-skill/create.py --list-templates
```

### 2. 创建你的第一个 Skill

```bash
# 使用交互式向导
/create-skill

# 或使用命令行
python ~/.claude/skills/create-skill/create.py \
  --name "my-first-skill" \
  --template checklist \
  --description "My first skill"
```

### 3. 测试 Skill

```bash
# 调用 Command
/my-first-skill

# 查看文档
cat ~/.claude/commands/my-first-skill.md
```

### 4. 根据需要修改

```bash
# 编辑 Command 文件
code ~/.claude/commands/my-first-skill.md

# 或编辑 Skill 文件
code ~/.claude/skills/my-first-skill/README.md
```

---

## 💡 常见问题

### Q1: 如何选择 Skill 类型？

**A**: 
- **Command**: 简单的提示词模板、检查清单
- **Skill**: 需要脚本的完整工具包
- **CLAUDE.md**: 项目级自动加载规则

### Q2: 如何选择模板？

**A**:
- **checklist**: 操作前检查清单
- **git-commit**: Git 提交格式
- **code-review**: 代码审查
- **test-generator**: 测试生成
- **custom**: 自定义

### Q3: 创建后如何修改？

**A**: 直接编辑生成的文件：
```bash
# Command
code ~/.claude/commands/skill-name.md

# Skill
code ~/.claude/skills/skill-name/README.md
```

### Q4: 如何删除 Skill？

**A**:
```bash
# 删除 Command
rm ~/.claude/commands/skill-name.md

# 删除 Skill
rm -rf ~/.claude/skills/skill-name/
```

### Q5: 如何分享 Skill？

**A**: 
1. 复制文件到其他机器的相同位置
2. 或创建 Git 仓库分享
3. 或打包成 zip 文件

---

## 🔄 更新历史

| 版本 | 日期 | 更新内容 |
|------|------|-------|
| 1.0 | 2026-05-20 | 初始版本，包含 5 种模板 |

---

## 📊 系统架构

```
Create Skill System
├── Command Layer
│   └── /create-skill → 交互式向导
├── Skill Layer
│   ├── README.md → 完整文档
│   ├── create.py → 自动化脚本
│   └── QUICK_REFERENCE.md → 快速参考
├── Template Layer
│   ├── checklist
│   ├── git-commit
│   ├── code-review
│   ├── test-generator
│   └── custom
└── Output Layer
    ├── Command 文件
    ├── Skill 目录
    └── CLAUDE.md
```

---

## 🎯 设计原则

1. **简单易用**: 交互式向导，降低使用门槛
2. **模板驱动**: 预定义模板，快速生成
3. **自动验证**: 创建后自动检查
4. **可扩展**: 易于添加新模板
5. **文档完整**: 每个 Skill 都有完整文档

---

## 🚀 未来计划

### 短期（1-2 周）

- [ ] 添加更多模板（API 文档、性能优化等）
- [ ] 支持从现有 Skill 创建模板
- [ ] 添加 Skill 更新功能

### 中期（1-2 月）

- [ ] Web UI 界面
- [ ] Skill 市场（分享和下载）
- [ ] 版本管理

### 长期（3-6 月）

- [ ] AI 辅助生成 Skill
- [ ] 自动测试框架
- [ ] 社区贡献系统

---

**创建人**: Claude Opus 4.7  
**维护者**: DevPalAgent Team  
**许可证**: MIT  
**联系方式**: 通过 GitHub Issues
