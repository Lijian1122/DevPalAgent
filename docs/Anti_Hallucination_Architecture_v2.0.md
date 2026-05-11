# DevPal Agent v2.0 - 完整架构图

## 🏗️ 整体架构 (7层)

```
┌─────────────────────────────────────┐
│             交互层 (Interface Layer)                │
│  ┌─────────┐  ┌──────────────┐  ┌──────────┐  ┌────────┐ │
│  │  CLI 命令行   │  │   Web UI     │  │  IDE 插件    │  │  API 接口   │ │
│  └──────────────┘  └──────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────┬─────────────────────────┘
                          │
┌──────────────────────────▼──────────────────────────┐
│                  工作流执行层 (Workflow Layer)            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  OpenSpecWorkflowExecutor - 11阶段需求驱动开发引擎                │  │
│  │  Phase 1-11: 需求解析 → 项目结构 → 代码生成 → 审查 → 测试 → 文档  │  │
│  └───────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                                 │
┌─────────────────────────▼─────────────────────────────────┐
│             Agent 核心引擎 (Core Engine)                        │
│  ┌──────────┐      ┌──────────────┐      ┌──────────────┐          │
│  │ Planner  │─────►│  Executor    │─────►│   Reflector     │          │
│  │  规划器   │      │   执行器      │      │    反思器       │          │
│  └──────────┘      └──────┬───────┘      └─────────┘          │
│                      │                                     │
│              ┌────────────▼────────────┐                     │
│              │  ToolRegistry 工具注册表  │                        │
│              │    (26个内置工具)        │                        │
│              └───────┬─────────┘                                │
└─────────────────────────┼───────────────────────────────────┘
                         │
┌─────────────────────▼─────────────────────────────┐
│               规范引擎层 (Spec Engine Layer)                     │
│  ┌───────────┐  ┌───────────────┐  ┌─────────┐   │
│  │ ValidationEngine │  │  DeltaEngine     │  │  ArtifactGraph     │   │
│  │  四层验证流水线   │  │  增量变更引擎    │  │  工件依赖图        │   │
│  │  Format/Semantic │  │  冲突检测/回滚   │  │  影响范围分析      │   │
│  │  Parser/Business │  │  原子应用        │  │  自动关联          │   │
│  └──────────────────┘  └──────────────────┘  └──────────────┘   │
│                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │   EventBus       │  │  StateManager    │  │  CompileDB         │   │
│  │  事件总线      │  │  状态持久化      │  │  编译数据库        │   │
│  │  发布订阅/优先级  │  │  .spec 目录      │  │  符号索引       │   │
│  └──────────────┘  └──────────────────┘  └──────────────────┘   │
└─────────────────┬───────────────────────────────┘
                   │
┌───────────▼───────────────────────────┐
│            防御层 (Anti-Hallucination Layer)                       │
│  ┌─────────────────────────────────┐  │
│  │  HallucinationDetector - 幻觉检测器                    │  │
│  │  • 工具调用校验 (tool_call)                         │  │
│  │  • 计划步骤校验 (plan)                                │  │
│  │  • 代码生成校验 (code)                                      │  │
│  │  • 事实陈述校验 (fact)                                  │  │
│  └───────────────────────────────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────────┐  │
│  │  ValidationEngine - 四层验证流水线                      │  │
│  │  Layer 1: Format Validation (格式/语法/类型)                      │  │
│  │  Layer 2: Semantic Validation (逻辑自洽/语义一致)        │  │
│  │  Layer 3: Parser Validation (与现有代码兼容/符号解析)       │  │
│  │  Layer 4: Business Validation (业务规则/项目规范)                 │  │
│  └───────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                            │
┌───────────────▼──────────────────────────────┐
│                 工具层 (Tools Layer - 26个工具)                  │
│                                              │
│  📁 文件操作 (3)          💻 系统编译 (4)         🌿 代码质量 (4)        │
│  • file_reader           • command_executor      • git_tool          │
│  • file_writer           • compiler_analyzer     • code_review      │
│  • code_search           • msvc_asan_compiler    • code_review_report   │
│                      • static_analyzer       • auto_fixer           │
│                                     │
│  🧪 测试编排 (5)          🚀 OpenSpec (3)        🔄 自我改进 (3)         │
│  • test_orchestrator     • project_generator     • self_source_reader   │
│  • test_doc_generator    • spec_tool             • self_improve         │
│  • test_generator        • openspec_cli          • plugin_system        │
│  • test_runner           │                │            │
│  • code_review_report    │               │              │
│                                                         │
│  🧩 其他工具 (2)                                                 │
│  • linked_list_tool                                        │
│  • hallucination_detector                                         │
└────────────────┬──────────────────────────────┘
                         │
┌─────────────────────────▼──────────────────────────────────┐
│                基础能力层 (Infrastructure Layer)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  ┌────────────┐ │
│  │  LLM SDK     │  │  Memory      │  │  Multimodal  │  │  Plugin    │ │
│  │  大模型封装   │  │  记忆系统     │  │  多模态支持   │  │  插件系统  │ │
│  │  • OpenAI    │  │  • 短期记忆   │  │  • 图片理解   │  │  • 动态加载│ │
│  │  • Claude    │  │  • 长期记忆   │  • 截图分析   │  │  • 热插拔  │ │
│  │  • 本地模型  │  │  • 工作记忆   │  │  • 代码识别   │  │            │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘ │
└──────────────────────────────────────┘
```
---

## 🛡️ 防幻觉架构详解 (Anti-Hallucination Defense)

### 四层防御体系

```
┌───────────────────────────────────────────────────────┐
│            Layer 1: 幻觉检测器 (HallucinationDetector)       │
│  ┌────────────┐  ┌──────────┐  ┌──────────────┐  ┌───────┐ │
│  │ 工具调用校验  │  │ 计划步骤校验  │  │ 代码生成校验  │  │事实校验 │ │
│  │ tool_call    │  │    plan    │  │    code      │  │  fact   │ │
│  │              │  │            │  │              │  │         │ │
│  │• 工具是否存在 │  │• 引用工具正确 │  │• TODO标记    │  │• 不确定 │ │
│  │• 参数非空    │  │• 步骤具体    │  │• 占位符变量  │  │  表述   │ │
│  │• 危险操作    │  │• 可行性评估  │  │• 函数存在性  │  │• 引用   │ │
│  └──────────────┘  └──────────────┘  └────────────┘  └───────┘ │
└─────────────────────────────┬─────────────────────────┘
                          │
┌─────────────────────▼───────────────────────────┐
│              Layer 2: 格式验证 (Format Validation)            │
│  • 语法检查: JSON/YAML/代码语法正确性               │
│  • 类型检查: 参数类型匹配                                     │
│  • 结构检查: 必需字段完整性                            │
└─────────────────┬─────────────────────────┘
                               │
┌───────────────────▼────────────────────────────────────┐
│           Layer 3: 语义验证 (Semantic Validation)           │
│  • 逻辑自洽: 前后矛盾检测                                       │
│  • 依赖关系: 工件依赖完整性                    │
│  • 引用正确: 符号/文件/函数存在性                         │
└───────────────────┬──────────────────────┘
                             │
┌──────────────────────▼───────────────────────┐
│             Layer 4: 业务验证 (Business Validation)             │
│  • 项目规范: 符合代码风格/命名规范                          │
│  • 安全规则: 无SQL注入/XSS/路径遍历                             │
│  • 性能要求: 复杂度/资源使用合理                       │
└─────────────────────────────────────────────────────┘
```

### 检测信号

```python
# 幻觉信号关键词
HALLUCINATION_SIGNALS = [
    "可能", "大概", "也许", "应该", "我猜", "可能是",
    "我记得", "据我所知", "根据我的知识库",
    "你可以试试", "应该可以", "理论上"
]

# 危险操作关键词
DANGEROUS_OPERATIONS = [
    'delete', 'remove', 'rm -rf', 'format', 'del', 'deltree',
    'drop', 'truncate', 'alter', 'delete from'
]
```

### 风险等级

- 🔴 **高风险 (High)**: 工具不存在、参数为空、危险操作、引用编造
- 🟡 **中风险 (Medium)**: 参数过长、TODO标记、过度自信、数字陈述
- 🟢 **低风险 (Low)**: 不确定表述、占位符变量、步骤模糊

---

## 🚀 OpenSpec 11阶段工作流

```
Phase 1: 🔍 需求文档解析
   ↓
Phase 2: 📁 创建项目结构
   ↓
Phase 3: 💻 生成核心代码
   ↓
Phase 4: 📊 代码质量审查 ←─┐
   ↓                      │
Phase 5: 🔧 自动修复 ──────┘
   ↓
Phase 6: 📝 生成测试文档
   ↓
Phase 7: 📚 生成 README + CMakeLists.txt
   ↓
Phase 8: 🔍 生成代码审查报告
   ↓
Phase 9: 🧪 编译并运行测试 (MSVC/MinGW 自动检测)
   ↓
Phase 10: ✅ 生成验证报告
   ↓
Phase 11: 📖 生成技术实现文档
```

---

## 📊 数据流

```
用户输入
   │
   ├─► 需求检测 (detect_requirements_request)
   │      │
   │      ├─ 强触发: "实现需求" + .md 文件
   │      └─ 弱触发: "开发" + .md 文件
   │
   ├─► OpenSpec 工作流
   │      │
   │      ├─► Phase 1-11 执行
   │      │      │
   │      ├─► 工具调用 (ToolRegistry)
   │      │      │      │
   │      │      │      ├─► 幻觉检测 (HallucinationDetector)
   │      │      │      ├─► 四层验证 (ValidationEngine)
   │      │      │      └─► 工具执行
   │      │      │
   │      │      ├─► 增量变更 (DeltaEngine)
   │      │      │      │
   │    │      │   ├─► 冲突检测
   │    │      │      ├─► 原子应用
   │      │      │      └─► 回滚支持
   │      │      │
   │      │      └─► 状态持久化 (.spec/)
   │      │
   │      └─► 最终报告生成
   │
   └─► 输出结果
```

---

## 🔧 核心组件

### 1. ValidationEngine (验证引擎)

```python
class ValidationEngine:
    """四层验证流水线"""
    
    def validate_pipeline(self, content, stages):
        """
        Layer 1: Format Validation
        Layer 2: Semantic Validation
        Layer 3: Parser Validation
        Layer 4: Business Validation
        """
        for stage in stages:
            result = self._execute_stage(stage, content)
            if not result.passed and stage.stop_on_failure:
                return PipelineStatus.FAILED
        return PipelineStatus.SUCCESS
```

### 2. HallucinationDetector (幻觉检测器)

```python
class HallucinationDetector:
    """AI 幻觉自动防御"""
    
    def detect(self, check_type, content, context):
        """
        检测类型:
        - tool_call: 工具调用校验
        - plan: 计划步骤校验
        - code: 代码生成校验
        - fact: 事实陈述校验
        """
        issues = []
        if check_type == "tool_call":
            issues.extend(self._check_tool_call())
        # ... 其他检测
        
        return {
       "risk_level": "high/medium/low",
            "issues": issues,
            "needs_human_verification": bool
        }
```

### 3. DeltaEngine (增量变更引擎)

```python
class DeltaEngine:
    """增量变更而非全量覆盖"""
    
    def apply_delta(self, delta_spec):
        """
        1. 冲突检测
        2. 原子应用
        3. 回滚支持
        """
        if self._detect_conflict(delta_spec):
            return ConflictError
        
      self._backup()
        try:
         self._apply_changes(delta_spec)
        except Exception:
            self._rollback()
```

### 4. ArtifactGraph (工件依赖图)

```python
class ArtifactGraph:
    """代码/测试/文档/需求自动关联"""
    
    def analyze_impact(self, changed_file):
    """
        影响范围分析:
        - 直接依赖
        - 间接依赖
        - 测试覆盖
        - 文档关联
      """
        return {
            "affected_files": [...],
            "affected_tests": [...],
            "affected_docs": [...]
        }
```

---

## 📈 版本演进

| 版本 | 核心特性 | 架构变化 |
|-----|---------|---------|
| **v1.0** | 基础 Agent 能力 | Planner + Executor + Reflector |
| **v1.5** | 自我改进 + 插件系统 | 工具扩展到 22 个 |
| **v1.6** | 测试编排 + MSVC ASAN | 6步测试流程 |
| **v2.0** | **OpenSpec 11阶段工作流** | **规范优先架构 + 四层验证 + 防幻觉** |

---

## 🎯 v2.0 核心创新

1. **规范优先 (Spec-First)**: 需求规范 → 增量变更 → 工件关联
2. **四层验证**: Format → Semantic → Parser → Business
3. **防幻觉体系**: 工具调用/计划/代码/事实 四维检测
4. **11阶段工作流**: 从需求到可交付项目的完整自动化
5. **增量变更**: Delta 而非全量覆盖，支持冲突检测和回滚
6. **工件依赖图**: 自动关联代码/测试/文档，影响范围分析
7. **事件总线**: 发布订阅架构，优先级队列，解耦通信

---

**创建日期**: 2026-05-10  
**版本**: v2.0  
**状态**: ✅ 生产可用
