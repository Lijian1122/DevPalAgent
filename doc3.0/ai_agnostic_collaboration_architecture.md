# AI-agnostic Spec-first 协作模式架构设计

**版本**: v2.0  
**日期**: 2026-06-01  
**状态**: 设计阶段  
**优先级**: P1  
**预期工期**: 5-7 天

---

## 执行摘要

DevPalAgent 的 AI-agnostic 协作模式旨在将系统从"单工具闭环"升级为"跨工具协作中枢"。通过 propose-only 和 apply-only 两种运行模式，DevPalAgent 可以与 Claude Code、Cursor、Cline 等外部 AI coding 工具无缝协作，确保所有 AI 工具都围绕同一套 OpenSpec artifacts、tasks 和 traceability 进行工作。

**核心价值**：
- 🎯 **Spec-first 协作协议**：统一的 OpenSpec Change 作为跨工具协作基础
- 🔄 **双向工作流**：propose-only 生成规范，apply-only 验收实现
- 🤝 **工具中立**：支持任何 AI coding 工具，不绑定特定平台
- 📋 **完整追踪**：保持 Requirement → Code → Test → Report 链路

---

## 目录

1. [背景与动机](#1-背景与动机)
2. [架构设计](#2-架构设计)
3. [核心模式](#3-核心模式)
4. [技术实现](#4-技术实现)
5. [Rule Pack 设计](#5-rule-pack-设计)
6. [CLI 接口](#6-cli-接口)
7. [集成方案](#7-集成方案)
8. [实施路线](#8-实施路线)
9. [测试策略](#9-测试策略)
10. [风险与缓解](#10-风险与缓解)
11. [面试价值](#11-面试价值)

---

## 1. 背景与动机

### 1.1 当前状态

**已完成能力** ✅：
- OpenSpec 11 阶段完整流程
- OpenSpec Change artifacts 生成（proposal/spec/tasks/design）
- Archive + Traceability 生命周期闭环
- 并行工具调用优化
- 向量数据库语义检索
- EventBus 可观测性
- Phase 9.5 LLM-as-a-Judge Critique
- Multi-Agent Skills 系统

### 1.2 核心问题

**问题 1：单工具闭环限制**
- 当前 DevPalAgent 默认从 requirements 直接跑完整 11 阶段
- 外部 AI coding 工具难以只接收 spec artifacts 后独立实现
- 人审或其他 AI 工具接手前缺少清晰边界

**问题 2：缺少协作模式**
- 没有 propose-only 模式（只生成规范，不改代码）
- 没有 apply-only 模式（基于已有规范验收实现）
- 外部工具修改代码后，DevPalAgent 无法接管验证

**问题 3：跨工具规则不统一**
- CLAUDE.md 已能生成项目说明，但缺少 spec-first 协作规则
- 缺少 `.cursorrules` / Cline rules 模板
- 外部工具不知道如何读取 changes、如何保持 traceability

### 1.3 设计目标

**目标 1：Propose-only 模式** 🎯
```bash
python run_ai_flow.py -r requirements/simple_login.md --propose-only
```
- 只运行 Phase 1-3（需求解析、项目结构、技术设计）
- 生成 OpenSpec Change artifacts
- 不生成业务代码，不修改 src/tests
- 输出协作指引，告诉外部 AI 如何接手

**目标 2：Apply-only 模式** 🔄
```bash
python run_ai_flow.py --apply-change <change-id>
```
- 读取已有 `openspec/changes/<change-id>/` artifacts
- 基于 change 执行代码生成、质量门禁、测试和报告
- 适合外部 AI 修改后由 DevPalAgent 验收

**目标 3：Validate-only 模式** ✅
```bash
python run_ai_flow.py --validate-change <change-id>
```
- 不生成代码，只验证已有实现
- 运行 Phase 9/9.5/10（Quality Gate + Critique + Tests）
- 生成验证报告

**目标 4：AI-agnostic Rule Pack** 📋
- 生成 CLAUDE.md spec-first 协作章节
- 生成 `.cursorrules` for Cursor
- 生成 `cline-rules.md` for Cline
- 定义 `/opsx:*` 跨工具协作命令

---

## 2. 架构设计

### 2.1 协作模式总览

```text
┌────────────────────────────────┐
│                    DevPalAgent              │
│             (Spec-first Runtime)           │
└─────┬──────────────────────────┬─────────────┘
             │                 │
    ┌────────▼──────┐          ┌───────▼────────┐
    │  Propose-only   │          │  Apply-only    │
    │  Mode           │      │  Mode          │
    └──────┬────────┘          └───────┬────────┘
             │                          │
             │ OpenSpec Change            │ Validation
             │ artifacts             │ + Report
             │                      │
    ┌────────▼───────────────▼────────┐
    │         External AI Coding Tools             │
    │  Claude Code / Cursor / Cline / Others       │
    └───────────────────────┘
```

### 2.2 三种运行模式对比

| 模式 | 输入 | 执行阶段 | 输出 | 适用场景 |
|------|------|---------|------|---------|
| **full-run** | requirements.md | Phase 1-11 | 完整项目 + 报告 | 端到端自动生成 |
| **propose-only** | requirements.md | Phase 1-3 + Change | OpenSpec artifacts | 人审 / 外部 AI 接手 |
| **apply-only** | change-id | Phase 4-11 | 代码 + 验证 + 报告 | 基于规范实现 |
| **validate-only** | change-id | Phase 9-11 | 验证报告 | 验收外部实现 |

### 2.3 数据流

```text
Requirements
    ↓
[Propose-only Mode]
    ↓
OpenSpec Change
├── proposal.md
├── specs/spec.md
├── tasks.md
├── design.md
└── metadata.json (status=PROPOSED)
    ↓
Rule Pack
├── CLAUDE.md (spec-first section)
├── .cursorrules
└── cline-rules.md
    ↓
External AI Tools
(Claude Code / Cursor / Cline)
    ↓
Code Implementation
    ↓
[Apply-only / Validate-only Mode]
    ↓
Quality Gate + Tests + Report
    ↓
Archive
```

---

## 3. 核心模式

### 3.1 Propose-only 模式

**执行流程**：
```text
Phase 1: Parse Requirements
    ↓
Phase 2: Create Project Structure
    ↓
Phase 3: Generate Technical Design
    ↓
OpenSpec Change Builder
    ├─ Generate proposal.md
    ├─ Generate specs/spec.md
    ├─ Generate tasks.md
    ├─ Generate design.md
    └─ Create metadata.json (status=PROPOSED)
    ↓
Rule Pack Generator
    ├─ Update CLAUDE.md
    ├─ Generate .cursorrules
    └─ Generate cline-rules.md
    ↓
Output Collaboration Guide
    └─ Next steps for external AI tools
```

**特点**：
- ✅ 不生成业务代码（src/）
- ✅ 不生成测试代码（tests/）
- ✅ 不运行编译和测试
- ✅ 生成完整的 OpenSpec Change artifacts
- ✅ 输出外部工具协作指引

**适用场景**：
1. 面试展示 spec-first 设计能力
2. 人类先审查 proposal/design
3. 外部 AI 工具接手实现
4. 多人协作前的规范对齐

### 3.2 Apply-only 模式

**执行流程**：
```text
Load existing change
    ↓
openspec/changes/<change-id>/
    ├─ proposal.md
  ├─ specs/spec.md
    ├─ tasks.md
    ├─ design.md
    └─ metadata.json
    ↓
Restore Context
    ├─ Requirements
    ├─ Design decisions
    └─ Task list
    ↓
Phase 4: Generate Code (or verify existing)
    ↓
Phase 5: Generate Tests
    ↓
Phase 9: Quality Gate
    ↓
Phase 9.5: LLM Critique
    ↓
Phase 10: Compile + Test + Self-Healing
    ↓
Phase 11: Final Report
```

**特点**：
- ✅ 基于已有 change artifacts
- ✅ 可以生成新代码
- ✅ 可以验证已有代码
- ✅ 完整的质量门禁和测试
- ✅ 生成 final report

**适用场景**：
1. Cursor/Cline/Claude Code 已修改代码，DevPalAgent 验收
2. DevPalAgent 根据已有 change artifacts 继续实现
3. CI 中对指定 change 执行验证
4. 增量开发和迭代

### 3.3 Validate-only 模式

**执行流程**：
```text
Load existing change + code
    ↓
Phase 9: Quality Gate
    ├─ Format validation
    ├─ Semantic validation
    ├─ Parser validation
    └─ Business rules validation
    ↓
Phase 9.5: LLM Critique
    ├─ Readability
    ├─ Architecture
    ├─ Security
    ├─ Performance
    └─ Maintainability
    ↓
Phase 10: Compile + Test
    ├─ Compilation check
    ├─ Test execution
    └─ Self-healing (if needed)
    ↓
Phase 11: Validation Report
```

**特点**：
- ✅ 不生成代码
- ✅ 只验证已有实现
- ✅ 完整的质量检查
- ✅ 生成验证报告

**适用场景**：
1. 外部 AI 修改后的快速验证
2. PR review 前的自动检查
3. CI/CD 质量门禁
4. 代码审查辅助

---


## 4. 技术实现

### 4.1 模块结构

```text
devpal/collaboration/
├── __init__.py
├── modes.py             # RunMode enum + ModePolicy
├── change_loader.py          # Load existing change artifacts
├── rule_pack_generator.py      # Generate CLAUDE.md/.cursorrules/Cline rules
├── external_commands.py        # /opsx:* command contract
├── context_restorer.py         # Restore context from change artifacts
└── templates/
    ├── claude_code_rules.md    # CLAUDE.md spec-first section template
    ├── cursorrules.txt         # Cursor rules template
    └── cline_rules.md          # Cline rules template
```

### 4.2 RunMode 定义

```python
# devpal/collaboration/modes.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class RunMode(str, Enum):
    """OpenSpec workflow run modes."""
    FULL = "full"                    # Complete Phase 1-11
    PROPOSE_ONLY = "propose_only"    # Phase 1-3 + Change generation
    APPLY_ONLY = "apply_only"        # Phase 4-11 from existing change
    VALIDATE_ONLY = "validate_only"  # Phase 9-11 validation only

@dataclass
class ModePolicy:
    """Policy defining phase execution for each run mode."""
    start_phase: int
    stop_after_phase: Optional[int]
    require_existing_change: bool
    allow_code_writes: bool
    allow_test_writes: bool
    allow_archive: bool
    generate_rule_pack: bool
    
    def should_run_phase(self, phase_num: int) -> bool:
        """Check if a phase should run under this policy."""
        if phase_num < self.start_phase:
        return False
        if self.stop_after_phase and phase_num > self.stop_after_phase:
         return False
        return True

# Mode policies
MODE_POLICIES = {
    RunMode.FULL: ModePolicy(
        start_phase=1,
        stop_after_phase=None,
        require_existing_change=False,
        allow_code_writes=True,
        allow_test_writes=True,
        allow_archive=True,
        generate_rule_pack=False,
    ),
    RunMode.PROPOSE_ONLY: ModePolicy(
        start_phase=1,
        stop_after_phase=3,
        require_existing_change=False,
        allow_code_writes=False,
     allow_test_writes=False,
        allow_archive=False,
     generate_rule_pack=True,
    ),
    RunMode.APPLY_ONLY: ModePolicy(
        start_phase=4,
        stop_after_phase=None,
        require_existing_change=True,
        allow_code_writes=True,
        allow_test_writes=True,
        allow_archive=True,
        generate_rule_pack=False,
    ),
    RunMode.VALIDATE_ONLY: ModePolicy(
        start_phase=9,
        stop_after_phase=11,
        require_existing_change=True,
        allow_code_writes=False,
        allow_test_writes=False,
        allow_archive=False,
        generate_rule_pack=False,
    ),
}
```

### 4.3 ChangeLoader 实现

```python
# devpal/collaboration/change_loader.py

from pathlib import Path
from typing import Dict, Any, Optional
import json

class ChangeLoader:
    """Load existing OpenSpec change artifacts."""
    
    def __init__(self, project_dir: Path):
      self.project_dir = project_dir
        self.changes_dir = project_dir / "openspec" / "changes"
    
    def load_change(self, change_id: str) -> Dict[str, Any]:
        """Load all artifacts for a change."""
        change_dir = self.changes_dir / change_id
      
        if not change_dir.exists():
            raise FileNotFoundError(f"Change not found: {change_id}")
        
        # Load metadata
        metadata_path = change_dir / "metadata.json"
        if not metadata_path.exists():
      raise FileNotFoundError(f"metadata.json not found for change: {change_id}")
        
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        
        # Load artifacts
        artifacts = {
       "change_id": change_id,
            "metadata": metadata,
            "proposal": self._load_file(change_dir / "proposal.md"),
            "tasks": self._load_file(change_dir / "tasks.md"),
            "design": self._load_file(change_dir / "design.md"),
            "spec": self._load_file(change_dir / "specs" / "spec.md"),
        }
        
        return artifacts
    
    def _load_file(self, path: Path) -> Optional[str]:
        """Load file content if exists."""
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None
    
    def list_changes(self, status: Optional[str] = None) -> list[str]:
        """List all changes, optionally filtered by status."""
        if not self.changes_dir.exists():
            return []
        
    changes = []
      for change_dir in self.changes_dir.iterdir():
            if not change_dir.is_dir():
                continue
            
            metadata_path = change_dir / "metadata.json"
            if not metadata_path.exists():
              continue
            
         if status:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
          if metadata.get("status") != status:
               continue
            
            changes.append(change_dir.name)
        
        return sorted(changes)
```

### 4.4 ContextRestorer 实现

```python
# devpal/collaboration/context_restorer.py

from pathlib import Path
from typing import Dict, Any
from devpal.core.openspec_phases.base import OpenSpecContext
class ContextRestorer:
    """Restore OpenSpecContext from change artifacts."""
    
    def restore_context(
        self,
        project_dir: Path,
        change_artifacts: Dict[str, Any],
        context: OpenSpecContext
    ) -> None:
        """Restore context from loaded change artifacts."""
        
        metadata = change_artifacts["metadata"]
      
        # Restore basic info
        context.current_change_id = change_artifacts["change_id"]
        context.project_type = metadata.get("project_type", "unknown")
     context.language = metadata.get("language", "unknown")
        
        # Restore requirements
        if "requirements" in metadata:
            context.structured_requirements = metadata["requirements"]
        
        # Restore design decisions
        if change_artifacts["design"]:
            context.technical_design = change_artifacts["design"]
        
        # Restore task list
        if change_artifacts["tasks"]:
            context.task_list = self._parse_tasks(change_artifacts["tasks"])
        
        # Restore spec
    if change_artifacts["spec"]:
            context.spec_content = change_artifacts["spec"]
    
    def _parse_tasks(self, tasks_md: str) -> list[str]:
        """Parse tasks from tasks.md."""
        tasks = []
        for line in tasks_md.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]") or line.startswith("- [x]"):
          task = line[5:].strip()
                if task:
                tasks.append(task)
    return tasks
```

---


## 5. Rule Pack 设计

### 5.1 CLAUDE.md 增强

在现有 CLAUDE.md 基础上，新增 **Spec-first Collaboration** 章节：

```markdown
## Spec-first Collaboration Rules

### Working with OpenSpec Changes

This project uses DevPalAgent's OpenSpec workflow for spec-first development.
All code changes should be aligned with OpenSpec Change artifacts.

#### Reading a Change

Before implementing, always read the change artifacts:

```bash
# List available changes
ls openspec/changes/

# Read change artifacts
cat openspec/changes/<change-id>/proposal.md
cat openspec/changes/<change-id>/tasks.md
cat openspec/changes/<change-id>/design.md
cat openspec/changes/<change-id>/specs/spec.md
```

#### Implementation Guidelines

1. **Follow tasks.md**: Only implement tasks listed in `tasks.md`
2. **Preserve traceability**: Add requirement IDs in comments when available
3. **Minimal scope**: Do not introduce unrelated refactors
4. **Test coverage**: Ensure tests cover all requirements

#### Validation

After implementation, run DevPalAgent validation:

```bash
# Validate your changes
python run_ai_flow.py --validate-change <change-id>

# If validation passes, archive the change
python -m devpal.openspec archive <change-id>
```

#### Collaboration Commands

- `/opsx:propose <requirements-file>` - Generate OpenSpec Change
- `/opsx:apply <change-id>` - Implement based on change artifacts
- `/opsx:validate <change-id>` - Validate implementation
- `/opsx:archive <change-id>` - Archive completed change

### Do Not

- ❌ Modify code without reading change artifacts
- ❌ Archive changes manually (use DevPalAgent)
- ❌ Skip validation before archiving
- ❌ Introduce features not in tasks.md
```

### 5.2 `.cursorrules` 模板

```text
# DevPalAgent Spec-first Project

You are working in a DevPalAgent Spec-first project.

## Before Editing Code

1. Read `openspec/changes/<change-id>/` artifacts first
2. Understand the requirements from `proposal.md` and `specs/spec.md`
3. Follow the task list in `tasks.md`
4. Review technical decisions in `design.md`

## Implementation Rules

- Only implement tasks listed in `tasks.md`
- Preserve requirement IDs in code comments
- Keep changes minimal and focused
- Do not refactor unrelated code
- Maintain traceability between requirements and code

## After Implementation

Run DevPalAgent validation:
```bash
python run_ai_flow.py --validate-change <change-id>
```

## Archiving

Do not archive manually. Use:
```bash
python -m devpal.openspec archive <change-id>
```

## Questions?

Read CLAUDE.md for detailed collaboration guidelines.
```

### 5.3 `cline-rules.md` 模板

```markdown
# Cline Spec-first Rules

## Overview

This project uses DevPalAgent's OpenSpec workflow. All changes must align with OpenSpec Change artifacts.

## Workflow

### 1. Read Change Artifacts

```bash
# Navigate to change directory
cd openspec/changes/<change-id>/

# Read artifacts
- proposal.md    # High-level proposal
- specs/spec.md  # Detailed specification
- tasks.md       # Task breakdown
- design.md      # Technical design
- metadata.json  # Change metadata
```

### 2. Implement

- Follow tasks in `tasks.md` exactly
- Add requirement IDs in comments: `// REQ-001: User login`
- Keep changes minimal
- Do not modify files outside change scope

### 3. Validate

```bash
python run_ai_flow.py --validate-change <change-id>
```

### 4. Archive

```bash
python -m devpal.openspec archive <change-id>
```

## Best Practices

✅ **Do**:
- Read all change artifacts before coding
- Ask before modifying files outside scope
- Preserve traceability
- Run validation before archiving

❌ **Don't**:
- Skip reading change artifacts
- Introduce unrelated changes
- Archive without validation
- Modify OpenSpec artifacts manually

## Commands

- `python run_ai_flow.py --propose-only -r <requirements>` - Generate change
- `python run_ai_flow.py --apply-change <change-id>` - Implement change
- `python run_ai_flow.py --validate-change <change-id>` - Validate
- `python -m devpal.openspec archive <change-id>` - Archive
```

### 5.4 RulePackGenerator 实现

```python
# devpal/collaboration/rule_pack_generator.py

from pathlib import Path
from typing import Optional
class RulePackGenerator:
    """Generate AI-agnostic collaboration rule packs."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.templates_dir = Path(__file__).parent / "templates"
    
    def generate_all(self, change_id: Optional[str] = None) -> None:
        """Generate all rule pack files."""
        self.update_claude_md(change_id)
        self.generate_cursorrules(change_id)
        self.generate_cline_rules(change_id)
    
    def update_claude_md(self, change_id: Optional[str] = None) -> Path:
        """Update CLAUDE.md with spec-first collaboration section."""
     claude_md_path = self.project_dir / "CLAUDE.md"
        
        # Read template
      template = (self.templates_dir / "claude_code_rules.md").read_text(encoding="utf-8")
        
        # Replace placeholders
        if change_id:
        template = template.replace("<change-id>", change_id)
        
        # Check if section already exists
        if claude_md_path.exists():
         content = claude_md_path.read_text(encoding="utf-8")
            marker_start = "## Spec-first Collaboration Rules"
            marker_end = "### Do Not"
         
          if marker_start in content:
                # Update existing section
                start_idx = content.find(marker_start)
                end_idx = content.find(marker_end, start_idx)
                if end_idx != -1:
          end_idx = content.find("\n##", end_idx)
                    if end_idx == -1:
                        end_idx = len(content)
            content = content[:start_idx] + template + content[end_idx:]
                else:
               content += "\n\n" + template
            else:
                # Append new section
                content += "\n\n" + template
        else:
            content = template
     
        claude_md_path.write_text(content, encoding="utf-8")
        return claude_md_path
    
    def generate_cursorrules(self, change_id: Optional[str] = None) -> Path:
        ""Generate .cursorrules file."""
        cursorrules_path = self.project_dir / ".cursorrules"
        
        template = (self.templates_dir / "cursorrules.txt").read_text(encoding="utf-8")
        
        if change_id:
          template = template.replace("<change-id>", change_id)
        
        cursorrules_path.write_text(template, encoding="utf-8")
        return cursorrules_path
    
    def generate_cline_rules(self, change_id: Optional[str] = None) -> Path:
        """Generate cline-rules.md file."""
        cline_rules_path = self.project_dir / "cline-rules.md"
        
        template = (self.templates_dir / "cline_rules.md").read_text(encoding="utf-8")
    
        if change_id:
            template = template.replace("<change-id>", change_id)
        
        cline_rules_path.write_text(template, encoding="utf-8")
        return cline_rules_path
```

---

## 6. CLI 接口

### 6.1 run_ai_flow.py 参数扩展

```python
# run_ai_flow.py (modifications)

import argparse
from devpal.collaboration.modes import RunMode

def parse_args():
    parser = argparse.ArgumentParser(description="DevPalAgent OpenSpec Workflow")
    
    # Existing arguments
    parser.add_argument("-r", "--requirements", help="Requirements file path")
    parser.add_argument("--project-dir", default=".", help="Project directory")
    
    # New mode arguments
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--propose-only",
     action="store_true",
      help="Propose-only mode: generate OpenSpec Change without code"
    )
    mode_group.add_argument(
        "--apply-change",
        metavar="CHANGE_ID",
        help="Apply-only mode: implement based on existing change"
    )
    mode_group.add_argument(
        "--validate-change",
        metavar="CHANGE_ID",
        help="Validate-only mode: validate existing implementation"
    )
    
    return parser.parse_args()
```

### 6.2 命令示例

**Propose-only 模式**:
```bash
python run_ai_flow.py -r requirements/simple_login.md --propose-only
```

**Apply-only 模式**:
```bash
python run_ai_flow.py --apply-change feature-simple-login-20260602_100000
```

**Validate-only 模式**:
```bash
python run_ai_flow.py --validate-change feature-simple-login-20260602_1000
```

---

## 7. 集成方案

### 7.1 与 Claude Code 集成

通过 CLAUDE.md 和 Skills 两种方式集成。

### 7.2 与 Cursor 集成

通过 `.cursorrules` 文件集成。

### 7.3 与 Cline 集成

通过 `cline-rules.md` 文件集成。

---

## 8. 实施路线

### Day 1：RunMode 与 ModePolicy 基础
### Day 2：ChangeLoader 与 ContextRestorer
### Day 3：Scheduler 集成
### Day 4：RulePackGenerator
### Day 5：Apply-only 与 Validate-only
### Day 6：测试与文档
### Day 7：集成验证与演示

---

## 9. 测试策略

### 9.1 单元测试

- `test_modes.py`: RunMode 和 ModePolicy
- `test_change_loader.py`: ChangeLoader
- `test_context_restorer.py`: ContextRestorer
- `test_rule_pack_generator.py`: RulePackGenerator

### 9.2 集成测试

- `test_propose_only_flow.py`: Propose-only 完整流程
- `test_apply_only_flow.py`: Apply-only 完整流程
- `test_validate_only_flow.py`: Validate-only 完整流程

### 9.3 端到端测试

- `test_collaboration_e2e.py`: 完整协作流程

---

## 10. 风险与缓解

### 风险 1：外部 AI 修改范围失控
**缓解**: Rule Pack 强制读取 tasks.md

### 风险 2：Context 恢复不完整
**缓解**: ContextRestorer 从 metadata 完整恢复

### 风险 3：覆盖用户规则文件
**缓解**: 使用 marker block 增量更新

---

## 11. 面试价值

DevPalAgent 不是替代所有 AI coding 工具，而是提供 spec-first 的工程中枢。它可以 propose-only 生成可审查的 OpenSpec Change，让 Claude Code、Cursor 或 Cline 接手实现；也可以 apply-only 读取已有 change artifacts，对外部 AI 写出的代码执行质量门禁、测试、自愈和报告。

**核心价值**：让任何 AI 写代码都必须围绕同一套 spec、tasks 和 traceability 进行。

---

**文档版本**: v2.0  
**最后更新**: 2026-06-02
