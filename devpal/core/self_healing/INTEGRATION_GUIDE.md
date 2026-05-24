# Self-Healing 根因分析集成说明

## 已完成的实现

### 1. 核心模块

已创建以下核心模块：

- **devpal/core/self_healing/models.py** - 数据模型
  - ErrorContext, ErrorType, ErrorSeverity
  - RootCause, TraceNode
  - HealingStrategy, StrategyType
  - HealingRecord

- **devpal/core/self_healing/root_cause_analyzer.py** - 根因分析器
  - 错误分类（语法/逻辑/环境）
  - 追溯链路分析
  - 影响范围分析
  - 根因推断
  - 修复建议生成

- **devpal/core/self_healing/strategy_selector.py** - 策略选择器
  - 策略匹配
  - 历史学习
  - 置信度评分
  - 策略排序

- **devpal/core/self_healing/healing_history.py** - 修复历史管理器
  - 记录管理
  - 相似错误查询
  - 统计分析
  - 持久化存储

- **devpal/core/self_healing/report_generator.py** - 报告生成器
  - 根因分析报告生成
  - 错误概览
  - 详细分析
  - 统计信息

- **devpal/core/openspec_phases/enhanced_test_self_healer.py** - 增强的测试自愈器
  - 集成根因分析
  - 策略选择
  - 历史学习
  - 向后兼容

### 2. Phase 10 集成

已更新 `devpal/core/openspec_phases/phase10_run_tests.py`：
- 导入 EnhancedTestSelfHealer
- 支持增强模式配置

## 使用方法

### 启用增强的 Self-Healer

在 OpenSpecContext 中设置：

```python
context.use_enhanced_self_healer = True  # 默认启用
```

### 禁用增强模式（使用传统 Self-Healer）

```python
context.use_enhanced_self_healer = False
```

### 查看修复统计

```python
if hasattr(self_healer, 'get_healing_statistics'):
    stats = self_healer.get_healing_statistics()
    print(f"总修复记录: {stats['total_records']}")
    print(f"修复成功率: {stats['success_rate']:.1%}")
```

### 生成根因分析报告

```python
from devpal.core.self_healing import RootCauseReportGenerator

generator = RootCauseReportGenerator(
    healing_history=self_healer.healing_history,
    output_path=project_dir / "docs"
)

report_path = generator.generate_report(self_healer.healing_history.records)
print(f"报告已生成: {report_path}")
```

## 核心特性

### 1. 三层智能分析

- **错误分类**: 自动识别语法/逻辑/环境错误
- **追溯链路**: 代码 → Phase → Prompt → 需求
- **影响范围**: 使用 ArtifactGraph 分析依赖

### 2. 学习型修复系统

- 记录每次修复的策略和结果
- 相似错误快速应用历史成功策略
- 策略成功率统计和优化

### 3. 可观测性

- 详细的根因分析日志
- 追溯链路可视化
- 修复历史持久化
- 统计报告生成

## 数据存储

修复历史存储在：
```
<project_dir>/.spec/healing_history/healing_history.jsonl
```

每条记录包含：
- 错误上下文
- 根因分析结果
- 修复策略
- 执行结果和时间

## 面试价值

### 技术亮点

1. **智能自愈**: 不是简单 Retry，而是基于 Traceability 的根因分析
2. **学习机制**: 记录修复历史，相似错误快速应用
3. **可观测性**: 生成根因分析报告，透明化修复过程
4. **系统性思维**: 识别错误分类，追溯到需求/Prompt/Phase

### 面试话术

> "DevPalAgent 的 Self-Healing 实现了三层智能：错误分类（语法/逻辑/环境）、追溯链路（代码→Phase→Prompt→需求）、学习机制（记录修复历史，相似错误快速应用）。这展示了 Self-Correction 的智能化水平，不是简单的 Retry。"

## 下一步

### 待完成任务

1. **Phase 10 完整集成** - 需要手动修改初始化代码
2. **端到端测试** - 验证完整流程
3. **报告生成集成** - 在 Phase 11 中生成根因分析报告
4. **单元测试** - 为核心模块添加测试

### Phase 10 集成代码示例

在 `phase10_run_tests.py` 的第 154-164 行替换为：

```python
        # 初始化自愈器（带错误处理）
        # 支持增强模式（集成根因分析）
        use_enhanced_healer = getattr(self.context, 'use_enhanced_self_healer', True)
        
        try:
            llm_client = get_llm_client()
      
         if use_enhanced_healer:
                self.log("  [INFO] Initializing Enhanced Self-Healer (with Root Cause Analysis)")
                try:
                 # 尝试使用增强版本
             self.self_healer = EnhancedTestSelfHealer(
                  project_dir=project_dir,
                        llm_client=llm_client,
                    context=self.context,
                artifact_graph=getattr(self.context, 'artifact_graph', None),
                     logger=self.log
              )
                    self.log("  [OK] Enhanced Self-Healer initialized successfully")
                except Exception as e:
                    self.log(f"  [WARN] Failed to initialize Enhanced Self-Healer: {e}")
                    self.log("  [INFO] Falling back to standard Self-Healer")
                 self.self_healer = TestSelfHealer(
              project_dir=project_dir,
                   llm_client=llm_client,
                     logger=self.log
                    )
         else:
                self.log("  [INFO] Initializing standard Self-Healer")
                self.self_healer = TestSelfHealer(
            project_dir=project_dir,
                    llm_client=llm_client,
              logger=self.log
                )
        except Exception as exc:
          self.log(f"  [WARN] Failed to initialize self-healer: {exc}")
            self.log("  [INFO] Self-healing will be disabled for this run")
            self.self_healer = None
```

## 文件清单

### 新增文件

1. `devpal/core/self_healing/__init__.py`
2. `devpal/core/self_healing/models.py`
3. `devpal/core/self_healing/root_cause_analyzer.py`
4. `devpal/core/self_healing/strategy_selector.py`
5. `devpal/core/self_healing/healing_history.py`
6. `devpal/core/self_healing/report_generator.py`
7. `devpal/core/openspec_phases/enhanced_test_self_healer.py`
8. `plan_doc/plan_0524_Self_Healing_Root_Cause.md` (技术文档)

### 修改文件

1. `devpal/core/openspec_phases/phase10_run_tests.py` (导入 EnhancedTestSelfHealer)

## 验收标准

### 功能验收

- ✅ 核心数据模型完整
- ✅ RootCauseAnalyzer 实现完整
- ✅ HealingStrategySelector 实现完整
- ✅ HealingHistory 实现完整
- ✅ RootCauseReportGenerator 实现完整
- ✅ EnhancedTestSelfHealer 实现完整
- ⏳ Phase 10 完整集成（需手动完成）
- ⏳ 端到端测试验证

### 质量验收

- ✅ 代码结构清晰
- ✅ 类型注解完整
- ✅ 文档字符串完整
- ⏳ 单元测试（待添加）
- ⏳ 集成测试（待添加）

---

**实施状态**: 核心功能已完成 90%，待完成 Phase 10 完整集成和端到端测试

**创建时间**: 2026-05-24  
**作者**: DevPalAgent Team
