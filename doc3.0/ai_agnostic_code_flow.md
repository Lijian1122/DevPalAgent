# AI-agnostic 协作模式代码逻辑线

**日期**: 2026-06-04  
**目的**: 梳理 AI-agnostic 协作模式的完整代码执行流程  
**范围**: 从 CLI 入口到 Phase 执行的完整链路

---

## 目录

1. [架构概览](#架构概览)
2. [CLI 入口流程](#cli-入口流程)
3. [模式选择与验证](#模式选择与验证)
4. [Scheduler 初始化](#scheduler-初始化)
5. [Phase 执行控制](#phase-执行控制)
6. [Context 恢复机制](#context-恢复机制)
7. [Rule Pack 生成](#rule-pack-生成)
8. [完整流程图](#完整流程图)

---
## 架构概览

### 核心模块关系

```
run_ai_flow.py (CLI)
    ↓
OpenSpecWorkflowExecutor
    ↓
EnhancedOpenSpecScheduler
    ↓
ModePolicy → Phase Skip Logic
    ↓
ChangeLoader → ContextRestorer
    ↓
RulePackGenerator
```

### 模块职责

| 模块 | 职责 | 文件路径 |
|------|------|----------|
| **RunMode** | 定义4种运行模式 | `devpal/collaboration/modes.py` |
| **ModePolicy** | 定义每种模式的执行策略 | `devpal/collaboration/modes.py` |
| **ChangeLoader** | 加载 change artifacts | `devpal/collaboration/change_loader.py` |
| **ContextRestorer** | 恢复 OpenSpecContext | `devpal/collaboration/context_restorer.py` |
| **RulePackGenerator** | 生成 AI 工具规则 | `devpal/collaboration/rule_pack_generator.py` |
| **EnhancedScheduler** | Phase 执行调度 | `devpal/core/openspec_phases/enhanced_scheduler.py` |

---

## CLI 入口流程

### 1. 参数解析 (`run_ai_flow.py`)

**位置**: `run_ai_flow.py:168-225`

```python
def main() -> int:
    parser = argparse.ArgumentParser(...)
    
    # 添加协作模式参数
    parser.add_argument("--propose-only", action="store_true",
                     help="仅生成 OpenSpec Change（Phase 1-3）")
    parser.add_argument("--apply-change",
                        help="从已有 Change 恢复并执行 Phase 4-11")
    parser.add_argument("--validate-change",
            help="从已有 Change 恢复并仅执行验证（Phase 9-11）")
    
    args = parser.parse_args()
```

**关键点**:
- 3个新增 CLI 参数对应3种协作模式
- `--apply-change` 和 `--validate-change` 需要提供 `change_id`
- `--propose-only` 不需要额外参数

### 2. 模式选择逻辑

**位置**: `run_ai_flow.py:233-251`

```python
# 导入 RunMode
from devpal.collaboration.modes import RunMode

# 默认为 FULL 模式
run_mode = RunMode.FULL
change_id = None

# 根据 CLI 参数选择模式
if args.propose_only:
    run_mode = RunMode.PROPOSE_ONLY
    print("[INFO] Mode: PROPOSE_ONLY - Will generate OpenSpec Change and stop at Phase 3")
    
elif args.apply_change:
    run_mode = RunMode.APPLY_ONLY
    change_id = args.apply_change
    print(f"[INFO] Mode: APPLY_ONLY - Will load change '{change_id}' and run Phase 4-11")
    
elif args.validate_change:
    run_mode = RunMode.VALIDATE_ONLY
    change_id = args.validate_change
    print(f"[INFO] Mode: VALIDATE_ONLY - Will load change '{change_id}' and run Phase 9-11")
```

**执行流程**:
1. 检查 `--propose-only` 标志
2. 检查 `--apply-change` 参数
3. 检查 `--validate-change` 参数
4. 默认使用 `RunMode.FULL`
5. 显示选择的模式信息

### 3. 参数传递

**位置**: `run_ai_flow.py:283-304`

```python
executor = OpenSpecWorkflowExecutor(tool_registry)
result = executor.run(
    str(requirements_file),
    OpenSpecRunOptions(
        # ... 其他参数 ...
        run_mode=run_mode,        # 传递运行模式
        change_id=change_id,      # 传递 change ID
    ),
)
```

---

## 模式选择与验证

### RunMode 枚举定义

**位置**: `devpal/collaboration/modes.py:9-15`

```python
class RunMode(str, Enum):
    """OpenSpec workflow run modes."""
    
    FULL = "full"             # Complete Phase 1-11
    PROPOSE_ONLY = "propose_only"    # Phase 1-3 + Change generation
    APPLY_ONLY = "apply_only"        # Phase 4-11 from existing change
    VALIDATE_ONLY = "validate_only"  # Phase 9-11 validation only
```

### ModePolicy 数据类

**位置**: `devpal/collaboration/modes.py:18-43`

```python
@dataclass
class ModePolicy:
    """Policy defining phase execution for each run mode."""
    
    start_phase: int                  # 起始 phase
    stop_after_phase: Optional[int]     # 停止 phase（None = 运行到结束）
    require_existing_change: bool       # 是否需要已有 change
    allow_code_writes: bool             # 是否允许写代码
    allow_test_writes: bool             # 是否允许写测试
    allow_archive: bool                 # 是否允许归档
    generate_rule_pack: bool            # 是否生成 Rule Pack

    def should_run_phase(self, phase_num: int) -> bool:
        """判断是否应该运行某个 phase"""
        if phase_num < self.start_phase:
            return False
        if self.stop_after_phase and phase_num > self.stop_after_phase:
            return False
        return True
```

### 模式策略映射

**位置**: `devpal/collaboration/modes.py:46-84`

```python
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
     stop_after_phase=3,              # 在 Phase 3 后停止
        require_existing_change=False,
        allow_code_writes=False,
        allow_test_writes=False,
        allow_archive=False,
        generate_rule_pack=True,      # 生成 Rule Pack
    ),
    
    RunMode.APPLY_ONLY: ModePolicy(
        start_phase=4,                 # 从 Phase 4 开始
        stop_after_phase=None,
     require_existing_change=True,    # 需要已有 change
        allow_code_writes=True,
        allow_test_writes=True,
      allow_archive=True,
        generate_rule_pack=False,
    ),
    
    RunMode.VALIDATE_ONLY: ModePolicy(
        start_phase=9,               # 从 Phase 9 开始
        stop_after_phase=11,             # 在 Phase 11 后停止
        require_existing_change=True,    # 需要已有 change
        allow_code_writes=False,
        allow_test_writes=False,
      allow_archive=False,
        generate_rule_pack=False,
    ),
}
```

**模式对比表**:

| 模式 | Phase 范围 | 需要 Change | 写代码 | 写测试 | 生成 Rule Pack |
|------|-----------|---------|--------|--------|---------|
| FULL | 1-11 | ❌ | ✅ | ❌ |
| PROPOSE_ONLY | 1-3 | ❌ | ❌ | ❌ | ✅ |
| APPLY_ONLY | 4-11 | ✅ | ✅ | ✅ | ❌ |
| VALIDATE_ONLY | 9-11 | ✅ | ❌ | ❌ | ❌ |

---

## Scheduler 初始化

### OpenSpecRunOptions 增强

**位置**: `devpal/core/openspec_executor.py:11-28`

```python
@dataclass(frozen=True)
class OpenSpecRunOptions:
    # ... 原有参数 ...
    run_mode: RunMode = RunMode.FULL           # 新增: 运行模式
    change_id: Optional[str] = None            # 新增: change ID
```

### EnhancedScheduler 初始化

**位置**: `devpal/core/openspec_phases/enhanced_scheduler.py:307-369`

```python
def __init__(
    self,
    requirements_file: str,
    tool_registry,
    # ... 其他参数 ...
    run_mode: RunMode = RunMode.FULL,         # 新增参数
    change_id: str | None = None,        # 新增参数
):
    # 导入基础 scheduler
    from .scheduler import OpenSpecPhaseScheduler
    
    self.base_scheduler = OpenSpecPhaseScheduler(
        requirements_file, tool_registry, abort_on_critical_failure
    )
    
    self.context = self.base_scheduler.context
    
    # 存储 run mode 和 policy
    self.run_mode = run_mode
    self.mode_policy = get_mode_policy(run_mode)
    self.change_id = change_id
    
    # 验证 change_id 要求
    if self.mode_policy.require_existing_change and not self.change_id:
        raise ValueError(
            f"{self.run_mode} mode requires change_id parameter. "
            "Use --apply-change <change-id> or --validate-change <change-id>"
        )
```

**初始化流程**:
1. 导入并创建 `OpenSpecPhaseScheduler`
2. 获取 context 引用
3. 存储 `run_mode` 和获取对应的 `mode_policy`
4. 存储 `change_id`（如果提供）
5. 验证 change_id 是否满足模式要求

---

## Phase 执行控制

### Workflow Banner 更新

**位置**: `devpal/core/openspec_phases/enhanced_scheduler.py:575-596`

```python
print()
print("=" * 70)
print(" OpenSpec - Requirements-Driven Development Workflow (Enhanced)")
print("=" * 70)
print(f"  Requirements: {context.requirements_file}")
print(f"  Language: {'C++' if context.is_cpp else 'Python'}")
print(f"  Run Mode: {self.run_mode.value}")              # 新增
stop_phase = self.mode_policy.stop_after_phase or 11
print(f"  Phase Range: {self.mode_policy.start_phase} - {stop_phase}")  # 新增
if self.change_id:
    print(f"  Change ID: {self.change_id}")             # 新增
print("=" * 70)
print()
```

**显示效果**:
```
=================================================
 OpenSpec - Requirements-Driven Development Workflow (Enhanced)
==================================================
  Requirements: requirements/simple_login.md
  Language: Python
  Run Mode: propose_only
  Phase Range: 1 - 3
===============================
```

---

### Context 恢复（APPLY/VALIDATE 模式）

**位置**: `devpal/core/openspec_phases/enhanced_scheduler.py:492-516`

```python
# Restore context from existing change (for APPLY/VALIDATE modes)
if self.mode_policy.require_existing_change:
    try:
      from ...collaboration.change_loader import ChangeLoader
        from ...collaboration.context_restorer import ContextRestorer
        
        project_root = self.context.requirements_file.parent
        loader = ChangeLoader(project_root)
        
        # 检查 change 是否存在
        if not loader.change_exists(self.change_id):
            raise FileNotFoundError(
        f"Change '{self.change_id}' not found"
            )
        
        # 加载和恢复
        artifacts = loader.load_change(self.change_id)
        restorer = ContextRestorer()
        restorer.restore_context(project_root, artifacts, self.context)
    except Exception as e:
        print(f"[ERROR] Failed to restore context: {e}")
     raise
```

---

## 完整执行流程总结

整个 AI-agnostic 协作模式通过以下关键机制实现：

1. **模式策略模式**: 统一的 `ModePolicy` 定义各模式行为
2. **Phase 控制**: `should_run_phase()` 方法动态判断执行
3. **Context 恢复**: `ChangeLoader` + `ContextRestorer` 实现状态恢复
4. **Rule Pack 生成**: 模板化生成适配不同 AI 工具的规则
5. **提前终止**: 基于 `stop_after_phase` 的 break 机制

从 CLI 入口到 Phase 执行形成完整的调用链，每个模块职责清晰，易于测试和扩展。

---

**文档版本**: 1.0  
**最后更新**: 2026-06-04  
**作者**: Claude Opus 4.7
