# LanguagePlugin 主流程化 + EventBus 接入主流程 实施计划

**创建日期**：2026-05-24  
**目标**：补齐技术债务，完善架构统一性  
**预计工期**：3-4 天  
**优先级**：P2（技术债务）

---

## 一、背景与目标

### 1.1 为什么需要这个改动

**当前问题**：

1. **LanguagePlugin 未被充分利用**
   - 定义了完整的 LanguagePlugin 接口（base.py, cpp_plugin.py, python_plugin.py, shell_plugin.py）
   - 但 Phase 2-11 中几乎没有使用，大量硬编码的 if-elif 链
   - 添加新语言需要修改多个 Phase，维护成本高

2. **双重语言表示混乱**
   - `context.language` (字符串: "cpp", "python", "shell")
   - `context.is_cpp` (布尔值)
   - 两者不同步，导致混淆和冗余

3. **EventBus 未接入主流程**
   - EventBus 已完整实现（696 LOC），支持 8 种事件类型
   - OpenSpecContext 已集成 EventBus
   - 但 Phase 1/4/9/10/11 都没有发布事件
   - 缺少事件驱动的可观测性

**预期收益**：

1. **统一语言抽象**
   - 移除 `is_cpp` 冗余字段
   - 所有语言逻辑通过 LanguagePlugin 接口
   - 添加新语言只需实现一个 Plugin

2. **事件驱动的可观测性**
   - 需求变更、代码生成、质量检查、测试执行全程可追踪
   - 事件日志写入 `.spec/events.jsonl`
   - 支持事件查询、重放、统计

3. **架构一致性**
   - 对标 ArtifactGraph 和 ValidationEngine 的集成方式
   - 统一的扩展模式

---

## 二、当前状态分析

### 2.1 LanguagePlugin 现状

**已实现的文件**：

| 文件 | 状态 | 说明 |
|------|:----:|------|
| `devpal/core/schema/languages/base.py` | ✅ | LanguagePlugin 基类、LanguagePluginManager |
| `devpal/core/schema/languages/language_config.py` | ✅ | 语言特征数据库 |
| `devpal/core/schema/languages/cpp_plugin.py` | ✅ | C++ 插件（完整实现）|
| `devpal/core/schema/languages/python_plugin.py` | ⚠️ | Python 插件（不完整）|
| `devpal/core/schema/languages/shell_plugin.py` | ⚠️ | Shell 插件（不完整）|
| `devpal/core/schema/languages/cpp_rules.py` | ✅ | C++ 代码质量规则 |

**问题清单**：

1. **直接使用 is_cpp 的位置**（应该统一为 language）

| 文件 | 行号 | 问题 | 优先级 |
|------|------|----|--------|
| `base.py` | 75 | `is_cpp: bool = True` - 冗余字段 | 🔴 高 |
| `phase2_create_structure.py` | 73, 77, 93 | 直接检查 is_cpp | 🔴 高 |
| `phase_skip_rules.py` | 21, 40 | 条件判断混合 is_cpp 和 language | 🔴 高 |
| `scheduler.py` | 54-55 | 从 is_cpp 推导 language | 🟡 中 |
| `phase11_final_report.py` | 539, 555, 627 | 混合使用 is_cpp 和 language | 🟡 中 |

2. **硬编码的语言分支**（应该使用 LanguagePlugin 接口）

| 文件 | 模式 | 应该使用 | 优先级 |
|------|------|---------|--------|
| `phase4_generate_code.py` | if language == "cpp/python/shell" | `plugin.get_required_files()` | 🔴 高 |
| `phase5_generate_tests.py` | if language == 'cpp/python/shell' | `plugin.get_test_command()` | 🔴 高 |
| `phase9_quality_gate.py` | if language == 'cpp/python/shell' | `plugin.get_code_smells()` | 🔴 高 |
| `phase10_run_tests.py` | if language == "cpp/python/shell" | `plugin.get_test_command()` | 🔴 高 |
| `phase11_final_report.py` | if language == "cpp/python/shell" | `plugin.get_language_features()` | 🟡 中 |

### 2.2 EventBus 现状

**已实现的功能**：

| 功能 | 状态 | 说明 |
|------|:----:|----|
| EventBus 核心实现 | ✅ | 696 LOC，完整实现 |
| 8 种事件类型 | ✅ | FileChanged, StepExecuted, ValidationCompleted 等 |
| OpenSpecContext 集成 | ✅ | event_bus 和 event_adapter 属性 |
| ToolRegistry 集成 | ✅ | 发布 StepExecutedEvent |
| 事件持久化 | ✅ | `.spec/events.jsonl` |

**未集成的 Phase**：

| Phase | 应该发布的事件 | 当前状态 |
|-------|---------------|---------|
| Phase 1 | RequirementChangedEvent | ❌ 未集成 |
| Phase 4 | FileChangedEvent, ArtifactDiscoveredEvent | ❌ 未集成 |
| Phase 9 | ValidationCompletedEvent | ❌ 未集成 |
| Phase 10 | StepExecutedEvent, ValidationCompletedEvent | ❌ 未集成 |
| Phase 11 | WorkflowCompletedEvent | ❌ 未集成 |

---

## 三、技术方案

### 3.1 LanguagePlugin 主流程化（2 天）

#### 任务 1：统一语言表示（0.5 天）

**目标**：移除 `is_cpp` 冗余字段，统一为 `language`

**步骤**：

1. **修改 OpenSpecContext**（`devpal/core/openspec_phases/base.py`）
   ```python
   # 删除
   is_cpp: bool = True
   
   # 添加属性
   @property
   def is_cpp(self) -> bool:
       """向后兼容的属性"""
       return self.language == "cpp"
   ```

2. **修改 Phase 2**（`phase2_create_structure.py`）
   ```python
   # 替换所有 self.context.is_cpp
   # 改为 self.context.language == "cpp"
   ```

3. **修改 Phase Skip Rules**（`phase_skip_rules.py`）
   ```python
   # 统一使用 language 判断
   def should_skip_phase(phase_id: int, language: str, project_type: str) -> Tuple[bool, str]:
       if project_type in {"installer", "tooling"}:
           # ...
   ```

4. **修改 Scheduler**（`scheduler.py`）
   ```python
   # 删除从 is_cpp 推导 language 的逻辑
   # 直接使用 context.language
   ```

**验收标准**：
- 所有测试通过
- 搜索 `is_cpp` 只出现在属性定义中
- installer e2e 测试通过

---

#### 任务 2：扩展 LanguagePlugin 接口（0.5 天）

**目标**：为 LanguagePlugin 添加 Phase 需要的方法

**修改文件**：`devpal/core/schema/languages/base.py`

**新增方法**：

```python
class LanguagePlugin(abc.ABC):
    # 现有方法...
    
    @abc.abstractmethod
    def get_required_files_template(self) -> Dict[str, str]:
        """获取必需文件模板（Phase 4 使用）"""
        pass
    
    @abc.abstractmethod
    def get_test_command(self, project_dir: Path) -> List[str]:
        """获取测试命令（Phase 10 使用）"""
        pass
    
    @abc.abstractmethod
    def get_build_command(self, project_dir: Path) -> List[str]:
        """获取构建命令（Phase 10 使用）"""
        pass
    
    @abc.abstractmethod
    def get_quality_checks(self) -> List[Callable]:
        """获取质量检查函数列表（Phase 9 使用）"""
        pass
    
    @abc.abstractmethod
    def get_project_structure(self) -> Dict[str, List[str]]:
        """获取项目目录结构（Phase 2 使用）"""
        pass
```

**验收标准**：
- 接口定义清晰
- 所有抽象方法有文档字符串

---

#### 任务 3：完善 Python 和 Shell 插件（0.5 天）

**目标**：实现 Python 和 Shell 插件的缺失方法

**修改文件**：
- `devpal/core/schema/languages/python_plugin.py`
- `devpal/core/schema/languages/shell_plugin.py`

**实现方法**：

```python
# Python Plugin
class PythonLanguagePlugin(LanguagePlugin):
    def get_required_files_template(self) -> Dict[str, str]:
        return {
        "main.py": "# Python main entry",
      "requirements.txt": "",
            "setup.py": "# Setup script",
        }
    
    def get_test_command(self, project_dir: Path) -> List[str]:
        return ["python", "-m", "pytest", "tests/", "-v"]
    
  def get_build_command(self, project_dir: Path) -> List[str]:
        return ["python", "-m", "pip", "install", "-e", "."]
    
    def get_quality_checks(self) -> List[Callable]:
        return [
            self._check_main_py_exists,
            self._check_requirements_txt,
            self._check_test_files,
        ]
    
    def get_project_structure(self) -> Dict[str, List[str]]:
        return {
            "src": [],
            "tests": [],
            "docs": [],
            "data": [],
     }
```

**验收标准**：
- 所有抽象方法实现
- Python 项目可以正常生成和测试

---

#### 任务 4：重构 Phase 2-11 使用 LanguagePlugin（0.5 天）

**目标**：替换硬编码的语言分支为 LanguagePlugin 调用

**Phase 2 - 创建结构**：
```python
# 替换
if not self.context.is_cpp:
    subdirs = [subdir for subdir in subdirs if subdir != 'include']

# 改为
plugin = self.plugin_manager.get_plugin(self.context.language)
if plugin:
    subdirs = list(plugin.get_project_structure().keys())
```

**Phase 4 - 代码生成**：
```python
# 替换
if language == "cpp":
    required_files = """..."""
elif language == "python":
    required_files = """..."""

# 改为
plugin = self.plugin_manager.get_plugin(language)
if plugin:
    required_files = plugin.get_required_files_template()
```

**Phase 9 - 质量门禁**：
```python
# 替换
if language == 'cpp':
    self._register_cpp_validation_checks(engine)
elif language == 'python':
    self._register_python_validation_checks(engine)

# 改为
plugin = self.plugin_manager.get_plugin(language)
if plugin:
    for check in plugin.get_quality_checks():
        engine.register_validator(ValidationLevel.BUSINESS, check)
```

**Phase 10 - 运行测试**：
```python
# 替换
if language == "cpp":
    test_cmd = ["ctest", "--output-on-failure"]
elif language == "python":
    test_cmd = ["python", "-m", "pytest", "tests/", "-v"]

# 改为
plugin = self.plugin_manager.get_plugin(language)
if plugin:
    test_cmd = plugin.get_test_command(project_dir)
```

**验收标准**：
- 所有 Phase 使用 LanguagePlugin 接口
- 搜索 `if language ==` 只出现在 LanguagePlugin 内部
- 所有测试通过

---

### 3.2 EventBus 接入主流程（1 天）

#### 任务 5：Phase 1 集成 EventBus（0.2 天）

**目标**：发布需求变更事件

**修改文件**：`devpal/core/openspec_phases/phase1_parse_requirements.py`

**实现**：

```python
def execute(self) -> PhaseResult:
    # ... 现有逻辑 ...
    
    # 发布需求变更事件
    if self.context.event_adapter:
        self.context.event_adapter.publish_requirement_changed(
            requirement_id="all",
            change_type="parsed",
          old_value=None,
            new_value=structured_requirements,
          impact_score=len(structured_requirements),
        )
    
    return result
```

**验收标准**：
- `.spec/events.jsonl` 包含 RequirementChangedEvent
- 事件包含需求数量信息

---

#### 任务 6：Phase 4 集成 EventBus（0.2 天）

**目标**：发布文件变更和工件发现事件

**修改文件**：`devpal/core/openspec_phases/phase4_generate_code.py`

**实现**：

```python
def execute(self) -> PhaseResult:
    # ... 生成文件 ...
    
    # 发布文件变更事件
    if self.context.event_adapter:
        for file_path in generated_files:
            self.context.event_adapter.publish_file_changed(
                file_path=str(file_path),
             change_type="created",
            old_content=None,
                new_content=file_path.read_text(),
                delta_count=1,
       )
     
        # 发布工件发现事件
        self.context.event_adapter.publish_artifact_discovered(
            artifact_id=f"code-{file_path.stem}",
            artifact_type="source_code",
            artifact_path=str(file_path),
            dependencies=[],
        )
    
    return result
```

**验收标准**：
- `.spec/events.jsonl` 包含 FileChangedEvent
- `.spec/events.jsonl` 包含 ArtifactDiscoveredEvent

---

#### 任务 7：Phase 9 集成 EventBus（0.2 天）

**目标**：发布质量检查完成事件

**修改文件**：`devpal/core/openspec_phases/phase9_quality_gate.py`

**实现**：

```python
def execute(self) -> PhaseResult:
    # ... 质量检查 ...
    
    # 发布验证完成事件
    if self.context.event_adapter:
        self.context.event_adapter.publish_validation_completed(
            passed=result.success,
            issue_count=len(result.issues),
            file_path=None,
            validation_level="quality_gate",
            issues=[str(issue) for issue in result.issues],
        )
    
    return result
```

**验收标准**：
- `.spec/events.jsonl` 包含 ValidationCompletedEvent
- 事件包含问题数量和详情

---

#### 任务 8：Phase 10 集成 EventBus（0.2 天）

**目标**：发布测试执行事件

**修改文件**：`devpal/core/openspec_phases/phase10_run_tests.py`

**实现**：

```python
def execute(self) -> PhaseResult:
    # ... 运行测试 ...
    
    # 发布步骤执行事件
    if self.context.event_adapter:
        self.context.event_adapter.publish_step_executed(
            workflow_name="openspec",
            step_id="phase10_run_tests",
            status="success" if result.success else "failed",
            duration=duration,
      tool_name="pytest" if language == "python" else "ctest",
            error_message=result.error_message if not result.success else None,
        )
        
     # 发布验证完成事件
        self.context.event_adapter.publish_validation_completed(
            passed=test_passed == test_total,
          issue_count=test_failed,
         file_path=None,
      validation_level="test_execution",
            issues=[f"{test_failed} tests failed"],
        )
    
    return result
```

**验收标准**：
- `.spec/events.jsonl` 包含 StepExecutedEvent
- `.spec/events.jsonl` 包含 ValidationCompletedEvent

---

#### 任务 9：Phase 11 集成 EventBus（0.2 天）

**目标**：发布工作流完成事件

**修改文件**：`devpal/core/openspec_phases/phase11_final_report.py`

**实现**：

```python
def execute(self) -> PhaseResult:
    # ... 生成报告 ...
    
    # 发布工作流完成事件
    if self.context.event_adapter:
        self.context.event_adapter.publish_workflow_completed(
            workflow_name="openspec",
            success=all_phases_success,
         duration=total_duration,
            total_steps=11,
            success_steps=success_count,
            failed_steps=failed_count,
        )
    
    return result
```

**验收标准**：
- `.spec/events.jsonl` 包含 WorkflowCompletedEvent
- 事件包含完整的统计信息

---

## 四、时间线

### Week 1（Day 1-2）

**Day 1: LanguagePlugin 重构**（1 天）
- 上午：任务 1 + 任务 2（统一语言表示 + 扩展接口）
- 下午：任务 3 + 任务 4（完善插件 + 重构 Phase）

**Day 2: EventBus 集成**（1 天）
- 上午：任务 5 + 任务 6 + 任务 7（Phase 1/4/9 集成）
- 下午：任务 8 + 任务 9（Phase 10/11 集成）

### Week 2（Day 3-4）

**Day 3: 测试验证**（0.5 天）
- 上午：运行所有单元测试
- 下午：运行 e2e 测试

**Day 4: 文档更新**（0.5 天）
- 上午：更新 README 和架构文档
- 下午：更新面试文档

---

## 五、验收标准

### 5.1 LanguagePlugin 主流程化

| 指标 | 目标 | 验证方式 |
|-----|---|---------|
| 移除 is_cpp 字段 | ✅ | 搜索 `is_cpp` 只出现在属性定义 |
| LanguagePlugin 接口扩展 | ✅ | 5 个新方法全部实现 |
| Python/Shell 插件完善 | ✅ | 所有抽象方法实现 |
| Phase 2-11 重构 | ✅ | 搜索 `if language ==` 只在 Plugin 内部 |
| 所有测试通过 | ✅ | pytest 100% 通过 |

### 5.2 EventBus 接入主流程

| 指标 | 目标 | 验证方式 |
|-----|------|---------|
| Phase 1 集成 | ✅ | `.spec/events.jsonl` 包含 RequirementChangedEvent |
| Phase 4 集成 | ✅ | `.spec/events.jsonl` 包含 FileChangedEvent |
| Phase 9 集成 | ✅ | `.spec/events.jsonl` 包含 ValidationCompletedEvent |
| Phase 10 集成 | ✅ | `.spec/events.jsonl` 包含 StepExecutedEvent |
| Phase 11 集成 | ✅ | `.spec/events.jsonl` 包含 WorkflowCompletedEvent |
| 事件查询功能 | ✅ | `event_bus.query_events()` 正常工作 |

---

## 六、风险与缓解

### 6.1 风险

1. **向后兼容性**
   - 移除 is_cpp 可能影响现有代码
   - **缓解**：保留 is_cpp 作为属性，向后兼容

2. **测试覆盖不足**
   - Python/Shell 插件测试不完整
   - **缓解**：先完善单元测试，再重构

3. **EventBus 性能影响**
   - 大量事件发布可能影响性能
   - **缓解**：EventBus 支持异步队列，默认启用

### 6.2 回滚计划

如果重构失败：
1. 恢复 is_cpp 字段
2. 恢复硬编码的语言分支
3. 禁用 EventBus（`enable_event_bus=False`）

---

## 七、关键文件清单

### 7.1 LanguagePlugin 相关

**需要修改的文件**（10 个）：
1. `devpal/core/openspec_phases/base.py` - 移除 is_cpp
2. `devpal/core/schema/languages/base.py` - 扩展接口
3. `devpal/core/schema/languages/python_plugin.py` - 完善实现
4. `devpal/core/schema/languages/shell_plugin.py` - 完善实现
5. `devpal/core/openspec_phases/phase2_create_structure.py` - 使用 Plugin
6. `devpal/core/openspec_phases/phase4_generate_code.py` - 使用 Plugin
7. `devpal/core/openspec_phases/phase5_generate_tests.py` - 使用 Plugin
8. `devpal/core/openspec_phases/phase9_quality_gate.py` - 使用 Plugin
9. `devpal/core/openspec_phases/phase10_run_tests.py` - 使用 Plugin
10. `devpal/core/openspec_phases/phase11_final_report.py` - 统一语言表示

### 7.2 EventBus 相关

**需要修改的文件**（5 个）：
1. `devpal/core/openspec_phases/phase1_parse_requirements.py` - 发布事件
2. `devpal/core/openspec_phases/phase4_generate_code.py` - 发布事件
3. `devpal/core/openspec_phases/phase9_quality_gate.py` - 发布事件
4. `devpal/core/openspec_phases/phase10_run_tests.py` - 发布事件
5. `devpal/core/openspec_phases/phase11_final_report.py` - 发布事件

---

## 八、总结

**当前状态**：
- ✅ LanguagePlugin 接口已定义
- ✅ EventBus 核心已实现
- ⏳ 主流程集成待完成

**下一步行动**：
1. 统一语言表示（0.5 天）
2. 扩展 LanguagePlugin 接口（0.5 天）
3. 完善 Python/Shell 插件（0.5 天）
4. 重构 Phase 2-11（0.5 天）
5. 集成 EventBus 到 Phase 1/4/9/10/11（1 天）
6. 测试验证（0.5 天）
7. 文档更新（0.5 天）

**预计完成时间**：2026-05-28（4 天）

**技术债务清理度**：100%（2/2 项技术债务）

---

**文档版本**：v1.0  
**创建日期**：2026-05-24  
**负责人**：DevPalAgent Team
