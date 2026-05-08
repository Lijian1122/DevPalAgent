# OpenSpec v2.0 架构图文档

## 概述

本目录包含 OpenSpec v2.0 完整的架构设计图，共 9 张 PNG 格式图片，全面展示了从用户交互到数据流转的整个系统架构。

所有架构图均使用 `graphviz` 自动生成。

---

## 架构图清单

### 01. OpenSpec_Architecture_Overview.png
**整体架构概览图**

展示了 OpenSpec v2.0 的七层架构：

1. **用户交互层** - User / CLI / Web 界面
2. **工作流执行层** - 需求检测 + OpenSpec 执行器 + WorkflowEngine
3. **Schema 核心架构层** - ValidationEngine / DeltaSpec / ArtifactGraph / Requirements / EventBus
4. **深化体验层** - DiagnosticEngine / ConfigPolicy / RolloutEngine / ErrorManager
5. **多语言支持层** - LanguagePluginMgr / C++ Plugin / CompileDB
6. **工具执行层** - 22 个工具的统一执行接口
7. **持久化层** - 文件存储 / 事件日志 / 执行报告

---

### 02. OpenSpec_9_Phase_Workflow.png
**9阶段工作流图**

完整展示了从需求到交付的 9 个阶段：

| 阶段 | 名称 | 主要工作 |
|------|------|----------|
| Phase 1 | 需求文档解析 | 读取 .md、解析 YAML、识别语言、提取验收标准 |
| Phase 2 | 创建项目结构 | include/src/tests/docs/config/data 目录 |
| Phase 3 | 生成核心代码 | User/Session/Authenticator 类实现 |
| Phase 4 | 代码质量审查 | 语法/风格/安全/复杂度分析 |
| Phase 5 | 自动修复 | 备份、自动修正、格式化、修复率计算 |
| Phase 6 | 生成测试文档 | 识别类方法、功能/边界/异常测试用例 |
| Phase 7 | 生成测试代码 | Google Test / pytest 框架集成 |
| Phase 8 | 运行测试 | 编译、执行、统计、生成报告、支持自动重试 |
| Phase 9 | 生成最终报告 | 汇总、计时、文件清单、JSON 报告 |

---

### 03. Schema_Architecture_Layer.png
**Schema 架构层详解图**

展示了 Schema 核心模块及其关系：

- **Schema Core** - ValidationEngine / DeltaSpec / ArtifactGraph
- **Workflow Engine** - YAML 声明式工作流、拓扑排序执行
- **Requirements Manager** - 结构化 Markdown 需求文档管理
- **Event Bus** - 发布订阅系统，7 种标准事件类型

---

### 04. Validation_Engine_Four_Layer.png
**Validation Engine 四层架构图**

四层验证架构，从下往上依次执行：

1. **Format 格式层** - 编码验证、语法检查、括号匹配、换行符统一、BOM 检测
2. **Semantic 语义层** - 逻辑一致性、无幻觉检测、引用有效性、重复检测
3. **Parser 解析层** - 现有代码兼容性、AST 解析、符号表、类型检查
4. **Business 业务层** - 项目规范、命名规范、架构约束、质量门禁、安全策略

任何一层失败都会停止执行，保证代码质量。

---

### 05. ArtifactGraph_Dependency.png
**ArtifactGraph 依赖关系图**

展示工件依赖图的核心概念：

- **工件类型** - 需求 / 代码 / 测试 / 文档 / 配置
- **依赖类型** - IMPLEMENTS / TESTS / REFERENCES / DEPENDS_ON / INCLUDES / EXTENDS
- **示例项目** - 完整展示认证系统需求 → 代码 → 测试 → 文档的依赖链
- **networkx 图计算** - get_affected_artifacts() 影响范围分析

---

### 06. DeltaSpec_Change_Flow.png
**Delta Spec 变更流程图**

增量变更机制完整流程：

1. **原始文件** - 读取、计算哈希、备份
2. **Delta 操作类型** - ADD / MODIFY / REMOVE / RENAMED
3. **DeltaHunk 变更块** - 操作类型、目标路径、新旧内容、行范围、变更原因
4. **冲突检测与验证** - 行范围有效性、内容匹配、重叠检测、语法验证
5. **应用 Delta** - 逆序应用、原子性保证、统一 Diff 格式输出
6. **FileWriter 集成** - delta_mode 开关、show_diff 预览

---

### 07. EventBus_Architecture.png
**EventBus 事件总线架构图**

完整的发布订阅系统架构：

- **事件发布者** - WorkflowEngine / ValidationEngine / DeltaSpec / ArtifactGraph / Tools
- **EventBus 核心** - Priority Queue / Filter / Adapter
- **Event 基类** - event_id / type / timestamp / priority / scope / source / data
- **7 种具体事件类型** - FileChanged / StepExecuted / ValidationCompleted / ArtifactDiscovered / DeltaApplied / WorkflowCompleted / ImpactAnalysis
- **事件订阅者** - EventLogger / ReportGenerator / UI Notifier / MetricsCollector
- **全局单例模式** - get_global_eventbus()

---

### 08. Multilingual_Plugin_System.png
**多语言插件系统架构图**

可扩展的多语言支持架构：

- **LanguagePluginManager** - 插件注册、获取、语言自动检测
- **LanguagePlugin 接口** - parse_ast() / get_symbols() / get_dependencies() / analyze_file() / check_code_quality()
- **数据结构** - ASTNode / SymbolInfo / TypeInfo / DependencyInfo / FileAnalysisResult
- **C++ 插件** - Clang AST（可选）、正则解析、预处理指令、C++11/14/17/20 支持
- **C++ 代码质量规则（12+）** - 命名规范、头文件保护、现代 C++ 特性、代码风格、内存安全
- **编译数据库** - CMake / Makefile / MSVC / Meson 集成
- **未来扩展** - Python / Rust / Go 插件

---

### 09. Complete_Data_Flow.png
**完整数据流转图**

从用户输入到最终输出的完整数据流，展示 7 个阶段：

1. **输入层** - 用户查询 + 需求文件 .md
2. **检测解析层** - 关键词检测 + 需求文档解析
3. **Schema 处理层** - ArtifactGraph 发现 + EventBus 事件流
4. **9阶段工作流执行** - P1-P7 完整执行链
5. **Delta 变更系统** - DeltaSpec + ValidationEngine 四层验证
6. **工具执行层** - file_writer / code_review / auto_fixer / test_doc_generator / test_generator / test_runner
7. **输出层** - 项目源码 + 测试代码 + 文档 + 执行报告 + 事件日志

---

## 生成方式

所有架构图由 `generate_openspec_v2_architecture.py` 自动生成，使用 Python `graphviz` 库。

### 重新生成架构图

```bash
python doc2.0/generate_openspec_v2_architecture.py
```

### 依赖安装

```bash
pip install graphviz
```

注意：需要同时安装 [Graphviz 官方程序](https://graphviz.org/download/) 并添加到 PATH。

---

## 架构设计原则

OpenSpec v2.0 架构设计遵循以下原则：

1. **分层清晰** - 每层职责明确，单向依赖
2. **可扩展性** - 插件化架构、易于添加新语言支持
3. **可靠性** - 四层验证架构确保输出质量
4. **可观测性** - EventBus 完整记录所有事件
5. **增量更新** - DeltaSpec 避免全量文件覆盖
6. **向后兼容** - 不破坏现有工具和工作流

---

## 核心架构组件补充说明

### 重要组件：OpenSpecContext 统一上下文

**位置：** `devpal/core/openspec_context.py`

OpenSpecContext 是 Phase 4 闭环集成的核心架构，作为所有 OpenSpec 组件的统一入口：

```
OpenSpecContext
     │
     ├─ event_bus (EventBus)          ← 所有组件通信枢纽
     ├─ spec_engine (SpecEngine)       ← 规范引擎核心
     ├─ artifact_graph (ArtifactGraph) ← 工件依赖图
     ├─ validation_engine (ValidationEngine) ← 四层验证引擎
     ├─ workflow_engine (WorkflowEngine) ← 工作流执行
     └─ spec_state (SpecStateManager)  ← 状态快照管理
```

**核心能力：**
- 统一管理所有 OpenSpec 组件的生命周期
- 通过 EventBus 实现组件间的解耦通信
- 提供统一的配置和状态持久化
- 支持快照创建和回滚
- `.spec/` 目录作为持久化存储

---

### 重要组件：SpecEngine 规范引擎

**位置：** `devpal/core/schema/spec.py`

SpecEngine 是 "规范优先(Spec-First)" 架构的核心，负责：

1. **需求规范管理** - 解析需求文档 → `SpecRequirement` 对象
2. **工件关联分析** - 自动发现需求与代码/测试/文档的关联
3. **Delta 变更计划** - 生成增量变更计划而非全量覆盖
4. **状态持久化** - `SpecStateManager` 管理 `.spec/` 目录状态
5. **快照管理** - `SpecSnapshot` 支持版本归档和回滚

**状态持久化目录结构：**
```
.spec/
├── state.json          # 当前规范状态
├── snapshots/          # 历史快照归档
│   └── snap_20260508_100000.json
├── deltas/            # Delta 变更历史
└── rules/             # 自定义验证规则
```

---

## 架构图说明与注意事项

### ✅ 已覆盖的架构要点

1. ✅ 7层完整架构概览
2. ✅ 9阶段工作流完整流程
3. ✅ Schema 核心5大模块
4. ✅ Validation Engine 四层验证
5. ✅ ArtifactGraph 工件依赖关系
6. ✅ DeltaSpec 增量变更流程
7. ✅ EventBus 发布订阅架构
8. ✅ 多语言插件系统（C++完整实现）
9. ✅ 端到端完整数据流

### ⚠️ 架构图简化说明（未展开的细节）

为了保持架构图的可读性，以下实现细节未在图中展开：

1. **SpecStateManager** - 状态管理是 SpecEngine 的内部组件，在架构图中作为 SpecEngine 的一部分展示
2. **OpenSpecContext 内部细节** - 统一上下文的6个子组件关系在 `03_Schema_Architecture_Layer.png` 中有体现
3. **各模块的内部类** - 如 `SpecRequirement`、`SpecSnapshot`、`SpecArtifactRef` 等数据类属于内部实现
4. **Phase 5 深化模块** - `DiagnosticEngine`、`RolloutEngine`、`ConfigPolicy`、`ErrorManager` 在 `01_Overview.png` 中展示但未展开

### 📌 建议后续补充的架构图

如果需要更详细的架构文档，可考虑补充以下专项图：

1. **OpenSpecContext 内部组件关系图** - 展示6大组件如何通过 EventBus 通信
2. **SpecEngine 状态机图** - 展示需求状态流转（DRAFT → PROPOSED → APPROVED → IN_PROGRESS → IMPLEMENTED → VERIFIED）
3. **Phase 5 深化架构图** - 展示诊断引擎、渐进式发布、配置策略、错误恢复的协作关系

---

*OpenSpec v2.0 Architecture Documentation*
*Generated: 2026-05-08*
*Last reviewed: 2026-05-08*
