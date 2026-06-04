# Interview Q&A: Project Architecture

## 面试专题：DevPalAgent 整体架构设计

---
## Q1: DevPalAgent 的整体架构是什么？

**核心回答**:
DevPalAgent 采用**双链路架构**：经典 Agent 链路（Plan-Act-Reflect）+ OpenSpec Runtime 链路（11-Phase Pipeline）。两条链路互补，前者处理交互式任务，后者处理端到端生成。

**架构图**:
```
┌───────────────────────────────┐
│     User / CLI / Web                │
│  chat request / requirements.md     │
└──────────────┬─────────────────┘
               │
      ┌────────┴─────────┐
      │                │
      ▼             ▼
┌──────────┐      ┌──────────────┐
│ Agent    │      │ OpenSpec     │
│ Engine   │    │ Workflow     │
└────┬─────┘      └──────┬───────┘
     │                   │
     ▼              ▼
┌────────┐      ┌──────────────┐
│ Planner  │      │ Enhanced     │
│          │      │ Scheduler    │
└────┬─────┘      └──────┬───────┘
     │                 │
     ▼                   ▼
┌──────────┐      ┌──────────────┐
│ Executor │      │ Phase 1-11   │
│          │      │ + Multi-Agent│
└────┬─────┘      └──────┬───────┘
   │                   │
     ▼                   ▼
┌──────────┐      ┌──────────────┐
│ Reflector│    │ Context +    │
│          │ EventBus     │
└──────────┘      └──────────────┘
```

---

## Q2: Plan-Act-Reflect 架构如何工作？

**经典 Agent 链路（交互式开发）**:

```python
# devpal/core/agent_engine.py
class AgentEngine:
    """Agent 主引擎"""
    
    def execute_task(self, user_request: str) -> TaskResult:
        """执行用户任务"""
      
        # 1. PLAN: 规划任务
        plan = self.planner.create_plan(user_request)
        # - 解析意图
        # - 识别任务类型
        # - 拆解步骤
        # - 选择工具/Skills
        
        # 2. ACT: 执行任务
        execution_result = self.executor.execute(plan)
        # - 调用 Tools
        # - 调用 Skills
        # - 收集结果
        
        # 3. REFLECT: 反思结果
        reflection = self.reflector.reflect(execution_result, plan)
        # - 验证结果
        # - 分析失败原因
      # - 决定是否重试/调整
        
        if reflection.should_retry:
            # 重新规划并执行
         return self.execute_task(reflection.adjusted_request)
        
        return TaskResult(
          success=reflection.success,
            output=execution_result.output,
            reflection=reflection
        )
```

**三个角色的职责**:

| 角色 | 输入 | 输出 | 核心能力 |
|------|------|---|---------|
| **Planner** | User request | Execution plan | 意图理解、任务分解、工具选择 |
| **Executor** | Plan | Execution result | 工具调用、结果收集、异常处理 |
| **Reflector** | Result + Plan | Reflection | 结果验证、失败分析、改进建议 |

**适用场景**:
- ✅ 代码审查任务
- ✅ 测试编排
- ✅ Bug 修复
- ✅ 代码重构
- ❌ 端到端项目生成（使用 OpenSpec 链路）

---

## Q3: OpenSpec Runtime 架构如何工作？

**OpenSpec 链路（端到端生成）**:

```python
# devpal/core/openspec_executor.py
class OpenSpecExecutor:
    """OpenSpec 工作流执行器"""
    
    def run(self, requirements_file: str) -> WorkflowResult:
        """执行 OpenSpec 11-Phase 流程"""
        
        # 1. 初始化 Context
        context = OpenSpecContext(requirements_file)
        
        # 2. 初始化 Scheduler
        scheduler = EnhancedScheduler(
            requirements_file=requirements_file,
            tool_registry=self.tool_registry,
            enable_timeout=True,
            enable_retry=True,
            enable_checkpoint=True
        )
     
      # 3. 加载 Phases
        phases = self._load_phases()
        # Phase 1: Parse Requirements
        # Phase 2: Create Structure
        # Phase 3: Technical Design
        # Phase 4: Generate Code (Multi-Agent)
        # Phase 5: Generate Tests (Multi-Agent)
      # Phase 6: Build Config
        # Phase 7: Test Docs
        # Phase 8: README
        # Phase 9: Quality Gate
        # Phase 10: Run Tests
        # Phase 11: Final Report
        
        # 4. 执行 Phases
        result = scheduler.run(phases, context)
        
        return WorkflowResult(
            success=result.success,
            final_report=context.final_report,
            generated_files=context.generated_files,
            artifact_graph=context.artifact_graph
        )
```

**核心组件**:

```
OpenSpecExecutor (Facade)
    ↓
EnhancedScheduler (调度层)
  - Timeout 控制
  - Retry 策略
  - Checkpoint/Resume
  - Progress 监控
    ↓
OpenSpecContext (状态层)
  - requirements_content
  - structured_requirements
  - tech_design_content
  - generated_files
  - artifact_graph
  - phase_results
    ↓
Phase 1-11 (执行层)
  - 各 Phase 独立实现
  - 共享 Context
  - 发布 Events
    ↓
EventBus (事件层)
  - 进度监控
  - 性能分析
  - 错误追踪
```

---

## Q4: 两条链路如何协作？

**协作模式**:

```python
# devpal/core/agent_engine.py
class AgentEngine:
    def __init__(self):
        self.planner = Planner()
        self.executor = Executor()
        self.reflector = Reflector()
        self.openspec_executor = OpenSpecExecutor()
    
    def execute_task(self, user_request: str):
        # 1. Planner 识别任务类型
      plan = self.planner.create_plan(user_request)
        
        if plan.task_type == "OPENSPEC_WORKFLOW":
            # 交给 OpenSpec 链路
            return self.openspec_executor.run(plan.requirements_file)
        
        elif plan.task_type == "CODE_REVIEW":
            # 使用 Agent 链路 + Skills
            return self.executor.execute_skill("code_review", plan.params)
        
        elif plan.task_type == "TESTING":
            # 使用 Agent 链路 + Skills
            return self.executor.execute_skill("test_runner", plan.params)
        
        else:
            # 通用 Agent 链路
          return self._execute_plan_act_reflect(plan)
```

**任务路由表**:

| 任务类型 | 链路选择 | 原因 |
|---------|------|------|
| 端到端项目生成 | OpenSpec | 确定性流程，11 阶段标准化 |
| 代码审查 | Agent | 交互式，需要反思和改进 |
| Bug 修复 | Agent | 需要根因分析和迭代修复 |
| 测试执行 | 两者皆可 | Phase 10 或 test_runner Skill |
| 代码重构 | Agent | 交互式，需要多轮确认 |

---

## Q5: 架构的可扩展性如何设计？

**扩展点设计**:

### 1. Tools 扩展
```python
# devpal/tools/registry.py
class ToolRegistry:
    """工具注册表"""
    
    def register_tool(self, tool: Tool):
        ""注册新工具"""
        self._tools[tool.name] = tool
        
# 用户可以注册自定义工具
custom_tool = CustomDatabaseTool()
tool_registry.register_tool(custom_tool)
```

### 2. Skills 扩展
```python
# devpal/skills/custom_skill.py
class CustomAnalysisSkill(BaseSkill):
    """用户自定义 Skill"""
    
    @property
    def name(self) -> str:
      return "custom_analysis"
    
    def execute(self, context, **kwargs):
        # 自定义逻辑
        pass

# 热加载
skill_loader.load_skill(CustomAnalysisSkill())
```

### 3. Phase 扩展
```python
# devpal/core/openspec_phases/phase12_custom.py
class Phase12CustomValidation(Phase):
    """用户自定义 Phase"""
    
    def execute(self, context):
        # 自定义验证逻辑
        pass

# 插入到 workflow
phases = load_phases()
phases.insert(12, Phase12CustomValidation())
```

### 4. EventBus 监控器扩展
```python
# 自定义监控器
class CustomMetricsMonitor:
    def handle_event(self, event: Event):
        # 上报到自定义监控系统
        pass

event_bus.subscribe("phase.*", CustomMetricsMonitor().handle_event)
```

---

## Q6: 架构设计的 Trade-offs 是什么？

**设计决策分析**:

### 1. 双链路 vs 单链路

**选择**: 双链路（Agent + OpenSpec）

| 维度 | 双链路优势 | 单链路问题 |
|------|----------|----------|
| **灵活性** | Agent 链路处理变化任务 | 单一流程不够灵活 |
| **确定性** | OpenSpec 保证端到端质量 | 全依赖 Agent 不可控 |
| **性能** | OpenSpec 可并行优化 | Agent 链路性能优化难 |
| **复杂度** | 两条链路需要协调 | ✅ 单链路简单 |

**Trade-off**: 接受架构复杂度，换取灵活性和确定性。

### 2. 集中式 vs 分布式

**当前选择**: 集中式（单进程）

| 维度 | 集中式 | 分布式 |
|------|-------|-------|
| **部署** | ✅ 简单，单机运行 | 需要分布式协调（Kubernetes） |
| **性能** | 多智能体并行已足够 | 可扩展到 100+ agents |
| **一致性** | ✅ 强一致性 | 分布式事务复杂 |
| **成本** | ✅ 低（单机） | 高（多节点） |

**Trade-off**: 当前选择集中式，未来可扩展到分布式。

### 3. 同步 vs 异步

**选择**: Phase 内同步，Phase 间可异步

```python
# Phase 内同步（保证一致性）
def execute_phase(phase, context):
    result = phase.execute(context)  # 同步等待
    context.set_phase_result(phase.num, result)

# Phase 间可异步（Multi-Agent）
def execute_phase4_parallel(files, context):
    tasks = [agent.generate(file) for file in files]
    results = await asyncio.gather(*tasks)  # 异步并行
```

**Trade-off**: Phase 内保持一致性，Phase 间追求性能。

---
## Q7: 架构如何支持不同语言？

**多语言架构**:

```python
# devpal/core/language_plugin.py
class LanguagePlugin(ABC):
    """语言插件基类"""
    
    @abstractmethod
    def get_project_structure(self) -> dict:
        """返回项目目录结构"""
      pass
    
    @abstractmethod
    def get_build_config(self) -> str:
        """返回构建配置"""
        pass
    
    @abstractmethod
    def get_test_framework(self) -> str:
        """返回测试框架""
        pass
    
    @abstractmethod
    def validate_code(self, code: str) -> List[Issue]:
        """验证代码"""
        pass

# C++ 插件
class CppLanguagePlugin(LanguagePlugin):
    def get_project_structure(self):
        return {
            "include/": "header files",
        "src/": "source files",
          "tests/": "test files",
          "build/": "build output"
      }
    
    def get_build_config(self):
     return "CMakeLists.txt"
    
    def get_test_framework(self):
        return "GoogleTest"
    
    def validate_code(self, code):
        # C++ 静态分析
        return cpp_linter.check(code)

# Python 插件
class PythonLanguagePlugin(LanguagePlugin):
    def get_project_structure(self):
        return {
          "src/": "source files",
            "tests/": "test files",
            "docs/": "documentation"
        }
    
    def get_build_config(self):
        return "setup.py"
    
    def get_test_framework(self):
        return "pytest"
    
    def validate_code(self, code):
     # Python 静态分析
        return pylint.check(code)
```

**语言感知流程**:
```
Phase 1: 识别语言（cpp/python/shell）
    ↓
Phase 2: 使用语言插件创建目录结构
    ↓
Phase 3-4: 使用语言特定 Prompt Template
    ↓
Phase 6: 使用语言特定构建配置
    ↓
Phase 9: 使用语言特定验证器
    ↓
Phase 10: 使用语言特定测试框架
```

---

## 面试展示脚本

**开场**:
"DevPalAgent 采用双链路架构：Agent 链路处理交互式任务，OpenSpec 链路处理端到端生成。这种设计兼顾了灵活性和确定性。"

**技术深度展示**:
1. "Plan-Act-Reflect 循环：Planner 拆解任务 → Executor 执行 → Reflector 验证改进"
2. "OpenSpec 11-Phase Pipeline：从需求到代码到测试到报告的完整流程"
3. "四层扩展点：Tools、Skills、Phases、EventBus 监控器"
4. "语言插件机制：支持 C++、Python、Shell，易于扩展"

**代码展示**:
- `devpal/core/agent_engine.py` - Agent 主引擎
- `devpal/core/openspec_executor.py` - OpenSpec 执行器
- `devpal/core/language_plugin.py` - 语言插件

**亮点总结**:
- 🏗️ **双链路**: Agent + OpenSpec，灵活性与确定性兼顾
- 🔌 **可扩展**: 四层扩展点，易于定制
- 🌍 **多语言**: 语言插件机制，C++/Python/Shell 支持
- 📊 **可观测**: EventBus 贯穿全流程
