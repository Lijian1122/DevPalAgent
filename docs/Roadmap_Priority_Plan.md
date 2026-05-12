# DevPal Agent 优先级修复计划 v2.2

> **状态**: P0 全部完成 | **最后更新**: 2026-05-12 | **负责人**: DevPal Team

---

## 📋 目录

- [P0: 高优先级 - 立即解决 (2-3 天)](#p0-高优先级---立即解决-2-3-天)
- [P1: 中高优先级 - 核心能力补全 (3-5 天)](#p1-中高优先级---核心能力补全-3-5-天)
- [P2: 中优先级 - 状态持久化 (3-4 天)](#p2-中优先级---状态持久化-3-4-天)
- [P3: 低优先级 - 优化 (2-3 天)](#p3-低优先级---优化-2-3-天)
- [总体路线图](#总体路线图)
- [检查清单 (Checklist)](#检查清单-checklist)
- [风险与缓解](#风险与缓解)

---

## 🔥 P0: 高优先级 - 立即解决 (2-3 天)

> **依赖**: 无 | **前置条件**: None

---

### P0-1: agent_engine.py 模块化重构

**目标**: 2694 行 → 拆分为 < 300 行/文件

**拆分方案:**

```
devpal/core/
├── agent_engine.py                    ← 仅保留核心调度 (~300 行)
├── compiler_detector.py              ← _find_vcvarsall(), find_visual_studio_compiler()
├── test_result_parser.py             ← _parse_test_results()
└── openspec_phases/                  ← 新建 Phase 模块目录
    ├── __init__.py
    ├── phase1_parse_requirements.py
    ├── phase2_create_structure.py
    ├── phase3_technical_design.py
    ├── phase4_generate_code.py
    ├── phase5_generate_tests.py
    ├── phase6_cmake_config.py
    ├── phase7_test_docs.py
    ├── phase8_readme.py
    ├── phase9_code_review.py
    ├── phase10_run_tests.py
    └── phase11_final_report.py
```

**每个 Phase 接口标准:**
```python
class PhaseInterface(ABC):
    @abstractmethod
    def execute(self, context: OpenSpecContext) -> PhaseResult:
        """执行当前阶段"""
        pass
```

**✅ 检查清单:**
- [x] 提取编译器检测工具函数到 `compiler_detector.py`
- [x] 提取测试解析到 `test_result_parser.py`
- [x] 每个 Phase 迁移到独立文件 (11 个 Phase)
- [x] 实现 Phase 接口标准化
- [x] AgentEngine 改为调度器模式
- [x] 所有单元测试通过
- [x] 集成测试验证完整流程

---

### P0-2: CompileDB 符号索引引擎

**目标**: 实现"智能"代码生成的基础设施

**核心职责:**
```python
# devpal/core/schema/compile_db.py

class CompileDB:
    """代码符号数据库 - 代码生成的'眼睛'"""
    
    # 1. 索引整个项目
    def index_project(self, project_path: Path) -> None:
        """扫描所有源文件，构建符号索引"""
        pass
    
    # 2. 符号查询
    def find_symbol(self, name: str) -> Optional[SymbolInfo]:
        """查找函数/类/变量定义位置"""
        pass
    
    def get_file_symbols(self, file_path: Path) -> List[SymbolInfo]:
        """获取单个文件的所有符号"""
        pass
    
    # 3. 依赖分析
    def get_dependencies(self, file_path: Path) -> List[Path]:
        """获取文件的 #include / import 依赖"""
        pass
    
    # 4. 智能代码生成
    def can_insert_function(self, file_path: Path, func_name: str) -> bool:
        """检查函数是否已存在，返回插入位置建议"""
        pass
    
    def get_insert_position(self, file_path: Path, after: str = None) -> int:
        """获取最佳代码插入行号"""
        pass
```

**✅ 检查清单:**
- [x] 实现 C++ 语法解析器 (基于正则)
- [x] 实现 Python 语法解析器 (基于正则)
- [x] 项目索引功能
- [x] 符号查询 API
- [x] 依赖分析功能
- [x] 插入位置智能计算
- [ ] 性能测试: 索引 100 文件 < 5 秒
- [ ] 单元测试覆盖率 > 80%

**实际实现位置**: `devpal/core/compiledb/`

---

### P0-3: 通用模板系统实现

**目标**: 从"认证系统专用"到"通用需求驱动"

**架构设计:**

```
devpal/core/templates/
├── base.py                     ← BaseTemplate 抽象基类
├── registry.py                 ← 模板注册表工厂
├── requirements_parser.py      ← 需求→模板匹配引擎
├── cpp/
│   ├── auth/                   ← 现有认证系统模板
│   ├── database/               ← 数据库访问层
│   └── rest_api/               ← REST API
└── python/
    ├── auth/
    ├── fastapi/
    └── sqlalchemy/
```

**匹配流程:**
```
需求文档 → 关键词提取 → 技术栈识别 → 模板组合 → 代码生成
```

**最小可行模板 (MVP):**
- ✅ C++ 认证系统 (已完成)
- ⏳ C++ 数据库层 (SQLite)
- ⏳ Python FastAPI 骨架
- ⏳ CLI 工具模板

**✅ 检查清单:**
- [x] BaseTemplate 抽象基类设计
- [x] 模板注册表工厂实现
- [x] 需求文档解析器 (关键词 + 意图识别)
- [x] 模板组合引擎 (多模板组合成完整项目)
- [x] C++ 数据库层模板 (SQLite)
- [ ] Python FastAPI 模板
- [ ] 文档: 如何新增自定义模板

**实际实现位置**: `devpal/core/templates/`

---

## ⚡ P1: 中高优先级 - 核心能力补全 (3-5 天)

> **依赖**: P0 全部完成

---

### P1-1: Delta 增量变更引擎集成

**目标**: 实现增量变更而非全量覆盖

**集成点:**
```
Phase 9: Code Review
    ↓ [新增] 生成 Delta 变更序列
    ↓ [新增] 冲突检测
    ↓ [新增] 四层验证
Phase 10: 应用 Delta (逆序应用避免行号偏移)
    ↓ 失败时自动回滚到上一快照
```

**关键实现:**
- 每次代码生成都与现有文件做 diff，生成 Delta
- 从最后一个 Delta 开始逆序应用
- 每个 Delta 原子化，失败自动回滚

**✅ 检查清单:**
- [ ] DeltaSpec 类与 CompileDB 集成
- [ ] diff → Delta 序列生成算法
- [ ] 冲突检测 (行号有效性 + 上下文匹配)
- [ ] 逆序应用算法 (避免行号偏移问题)
- [ ] 原子应用 + 自动回滚
- [ ] Delta 历史记录
- [ ] 与 Phase 9/10 集成

---

### P1-2: 四层验证引擎集成

**目标**: 渐进式代码质量保障

**插入位置 (所有代码生成点后):**
- Phase 4 代码生成后 → 验证
- Phase 5 测试生成后 → 验证
- Phase 6 CMake 生成后 → 验证
- **验证失败 → 进入自动修复循环**

**四层验证:**
1. **Layer 1**: Format Validation (格式验证)
2. **Layer 2**: Semantic Validation (语义验证)
3. **Layer 3**: Parser Validation (解析验证)
4. **Layer 4**: Business Validation (业务规则验证)

**✅ 检查清单:**
- [ ] 现有 validation_engine.py 代码审查与修复
- [ ] Pipeline 执行器实现
- [ ] 每层验证规则的单元测试
- [ ] 与 Phase 4/5/6 集成
- [ ] 失败 → 自动修复 → 重试的循环机制
- [ ] 验证报告生成

---

## ⚙️ P2: 中优先级 - 状态持久化 (3-4 天)

> **依赖**: P1 全部完成

---

### P2-1: 状态快照管理器

```python
class StateManager:
    def create_snapshot(phase: str, context: dict) -> Snapshot
    def restore_snapshot(snapshot_id: str) -> bool
    def list_snapshots() -> List[Snapshot]
    def get_change_log(from_phase, to_phase) -> List[Delta]
```

**快照触发点:**
- 每个 Phase 完成后自动创建
- 编译/测试失败时自动回滚
- 用户可手动触发回滚

**✅ 检查清单:**
- [ ] Snapshot 数据结构设计
- [ ] 快照创建与存储 (文件系统)
- [ ] 快照恢复功能
- [ ] 变更日志 (Delta 历史)
- [ ] 与所有 Phase 集成
- [ ] 回滚后的状态一致性验证

---

### P2-2: 工件依赖图集成

**目标**: 智能影响范围分析

**集成点:**
- Phase 开始时扫描项目建立依赖图
- 每次 Delta 应用后增量更新依赖图
- Phase 11 最终报告中包含影响范围分析
- 智能推荐需要重跑的测试用例

**依赖关系类型:**
1. 代码依赖 (import / #include)
2. 测试覆盖 (test → code)
3. 文档描述 (doc → code)
4. 需求实现 (code → requirements)

**✅ 检查清单:**
- [ ] 现有 artifact_graph.py 代码审查
- [ ] 自动扫描构建依赖图
- [ ] 增量更新机制
- [ ] 影响范围分析 API
- [ ] 与 CompileDB 集成
- [ ] 测试推荐算法
- [ ] 在 Phase 11 报告中展示

---

## 📋 P3: 低优先级 - 优化 (2-3 天)

> **依赖**: P2 全部完成

---

### P3-1: 事件总线完整集成

**目标**: 所有组件通过事件解耦

**7种标准事件类型:**
```python
class EventType(Enum):
    TOOL_EXECUTED = "tool_executed"
    VALIDATION_COMPLETED = "validation_completed"
    DELTA_APPLIED = "delta_applied"
    ARTIFACT_CHANGED = "artifact_changed"
    SNAPSHOT_CREATED = "snapshot_created"
    CONFLICT_DETECTED = "conflict_detected"
    WORKFLOW_PHASE_COMPLETED = "workflow_phase_completed"
```

**✅ 检查清单:**
- [ ] 现有 event_bus.py 代码审查与修复
- [ ] 所有 Phase 完成时发布事件
- [ ] Delta 应用时发布事件
- [ ] 订阅者机制完善
- [ ] 优先级队列
- [ ] 异常隔离 (一个订阅者失败不影响其他)

---

### P3-2: CompileDB 高级功能

- [ ] 跨文件引用解析
- [ ] 函数调用图构建
- [ ] 符号重命名支持
- [ ] 死代码检测
- [ ] 重复代码检测

---

### P3-3: 性能与体验优化

- [ ] 各阶段耗时监控与报告
- [ ] 缓存机制 (避免重复索引)
- [ ] 并行处理支持
- [ ] 更多语言模板 (Rust, Go, Java)
- [ ] 插件系统完善

---

## 🗺️ 总体路线图

| 阶段 | 时间 | 交付物 | 状态 |
|-----|------|-------|------|
| **Week 1** | P0 | agent_engine.py 模块化 + CompileDB + 通用模板系统 | ⏳ 未开始 |
| **Week 2** | P1 | Delta 引擎 + 四层验证集成 | ⏳ 未开始 |
| **Week 3** | P2 | 状态持久化 + 工件依赖图 | ⏳ 未开始 |
| **Week 4** | P3 | 事件总线 + CompileDB 高级功能 + 优化 | ⏳ 未开始 |

---

## ✅ 检查清单 (Checklist)

### 进度总览

- [x] **P0-1**: agent_engine.py 模块化重构 ✅
- [x] **P0-2**: CompileDB 符号索引引擎 ✅
- [x] **P0-3**: 通用模板系统实现 ✅
- [ ] **P1-1**: Delta 增量变更引擎集成
- [ ] **P1-2**: 四层验证引擎集成
- [ ] **P2-1**: 状态快照管理器
- [ ] **P2-2**: 工件依赖图集成
- [ ] **P3-1**: 事件总线完整集成
- [ ] **P3-2**: CompileDB 高级功能
- [ ] **P3-3**: 性能与体验优化

---

## ⚠️ 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|-----|------|------|---------|
| 重构范围扩散 | 高 | 严重 | 严格按拆分方案执行，每个 Phase 独立 PR，先移代码后优化 |
| 模板过度设计 | 中 | 中 | 先支持 3 种核心模板，用真实需求驱动设计 |
| 核心模块 API 不兼容 | 高 | 严重 | 先写集成测试，验证现有 schema 文件的实际可用性 |
| CompileDB 性能问题 | 中 | 中 | 增量索引 + 缓存，性能不达标时切换到 tree-sitter |
| Delta 冲突处理复杂 | 中 | 高 | 先实现检测机制，复杂冲突提示人工处理，不强行自动解决 |

---

## 🔗 相关文档

- [Core_Architecture_Models.md](./Core_Architecture_Models.md) - 核心架构模型详解
- [Core_Engine_Implementation_Guide.md](./Core_Engine_Implementation_Guide.md) - 核心引擎实现指南
- [Anti_Hallucination_Architecture_v2.0.md](./Anti_Hallucination_Architecture_v2.0.md) - v2.0 防幻觉架构

---

**文档维护**: DevPal Agent 开发团队  
**版本**: v2.1  
**下次评审**: 2026-05-19
