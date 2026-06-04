# Interview Q&A: Skills System

## 面试专题：Skills 系统设计与实现

---
## Q1: DevPalAgent 的 Skills 系统是什么？为什么需要它？

**核心回答**:
Skills 系统是 DevPalAgent 的可插拔能力扩展机制，类似于 IDE 的插件系统。它允许动态注册和执行领域专属任务，而无需修改核心引擎代码。

**为什么需要**:
1. **可扩展性**: 新增能力不修改核心代码
2. **模块化**: 每个 Skill 独立开发、测试、部署
3. **复用性**: Skill 可跨项目复用
4. **可组合性**: 多个 Skills 可以组合成复杂工作流

**架构位置**:
```
devpal/
├── tools/
│   └── registry.py      # 基础工具注册
├── skills/
│   ├── skill_registry.py    # Skills 注册管理
│   ├── skill_loader.py    # 动态加载
│   └── base_skill.py        # Skill 基类
└── core/
    └── agent_engine.py      # 集成 Skills
```

---

## Q2: Skills 与 Tools 的区别是什么？

**对比表**:

| 维度 | Tools | Skills |
|------|-----|--------|
| **粒度** | 原子操作 (read_file, run_command) | 复合任务 (test_runner, code_review) |
| **状态** | 无状态 | 可以有状态 (context, memory) |
| **依赖** | 独立 | 可以调用多个 Tools |
| **注册** | 静态注册 | 动态加载 |
| **示例** | `file_read`, `git_commit` | `openspec_workflow`, `quality_review` |

**代码对比**:
```python
# Tool: 原子操作
class FileReadTool:
    def execute(self, file_path: str) -> str:
        return Path(file_path).read_text()

# Skill: 复合任务
class CodeReviewSkill(BaseSkill):
    def __init__(self, tool_registry):
        self.tools = tool_registry
        
    def execute(self, target_files: List[str]) -> ReviewReport:
        # 1. 读取文件 (调用 Tool)
        contents = [self.tools.call("file_read", f) for f in target_files]
        
        # 2. 静态分析 (调用 Tool)
        issues = self.tools.call("lint", contents)
        
        # 3. LLM 审查 (调用 Tool)
        ai_feedback = self.tools.call("llm_review", contents)
      
        # 4. 生成报告 (Skill 逻辑)
        return self._generate_report(issues, ai_feedback)
```

**面试话术**:
"Tools 是螺丝刀、锤子；Skills 是完整的家具组装流程。Tools 由 Executor 调用，Skills 由 Agent Engine 调度。"

---

## Q3: Skills 系统的核心设计是什么？

**三层架构**:

```
1. Skill Interface (接口层)
   ↓
2. Skill Registry (注册层)
   ↓
3. Skill Executor (执行层)
```

**核心代码**:
```python
# devpal/skills/base_skill.py
class BaseSkill(ABC):
    """Skill 基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
    """Skill 名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Skill 描述"""
        pass
    
    @abstractmethod
    def execute(self, context: dict, **kwargs) -> SkillResult:
        """执行 Skill"""
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        return True
    
    def on_failure(self, error: Exception) -> None:
      """失败处理"""
        pass

# devpal/skills/skill_registry.py
class SkillRegistry:
    """Skill 注册中心"""
    
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
    
    def register(self, skill: BaseSkill) -> None:
     """注册 Skill"""
        self._skills[skill.name] = skill
        
    def get(self, name: str) -> Optional[BaseSkill]:
        """获取 Skill"""
        return self._skills.get(name)
    
    def list_all(self) -> List[str]:
        """列出所有 Skills"""
        return list(self._skills.keys())
```

**Skill 示例**:
```python
# devpal/skills/openspec_skill.py
class OpenSpecWorkflowSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "openspec_workflow"
    
    @property
    def description(self) -> str:
      return "Execute OpenSpec 11-phase workflow"
    
    def execute(self, context: dict, **kwargs) -> SkillResult:
        requirements_file = kwargs["requirements_file"]
        
        # 调用 OpenSpec Executor
        executor = OpenSpecExecutor(
            requirements_file=requirements_file,
            tool_registry=context["tool_registry"]
        )
        
      result = executor.run()
     
        return SkillResult(
        success=result.success,
            output=result.final_report,
         artifacts=result.generated_files
        )
```

**面试亮点**:
"Skills 系统遵循开闭原则：对扩展开放，对修改封闭。新增 Skill 只需要继承 BaseSkill 并注册，核心引擎零修改。"

---

## Q4: Skills 如何实现动态加载？

**动态加载机制**:

```python
# devpal/skills/skill_loader.py
class SkillLoader:
    """动态加载 Skills"""
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.registry = SkillRegistry()
    
    def load_all(self) -> None:
        """从目录加载所有 Skills"""
        for skill_file in self.skills_dir.glob("*_skill.py"):
        self._load_skill(skill_file)
    
    def _load_skill(self, skill_file: Path) -> None:
        """加载单个 Skill"""
      # 1. 动态导入模块
        module_name = skill_file.stem
      spec = importlib.util.spec_from_file_location(module_name, skill_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 2. 查找 BaseSkill 子类
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseSkill) and obj != BaseSkill:
                # 3. 实例化并注册
           skill_instance = obj()
                self.registry.register(skill_instance)
                print(f"[Skill] Loaded: {skill_instance.name}")
```

**使用方式**:
```python
# devpal/core/agent_engine.py
class AgentEngine:
    def __init__(self):
        self.skill_loader = SkillLoader(Path("devpal/skills"))
        self.skill_loader.load_all()
        
    def execute_skill(self, skill_name: str, **kwargs):
        skill = self.skill_loader.registry.get(skill_name)
        if not skill:
            raise SkillNotFoundError(f"Skill '{skill_name}' not found")
        
        return skill.execute(context=self.context, **kwargs)
```

**热加载支持**:
```python
def reload_skills(self) -> None:
    """热加载 Skills（无需重启）"""
    self.registry.clear()
    self.load_all()
```

**面试话术**:
"Skills 采用热加载机制，支持运行时动态注册。开发者只需将新 Skill 文件放入 `devpal/skills/` 目录，调用 `reload_skills()` 即可生效，无需重启进程。这对持续迭代和 A/B 测试非常友好。"

---

## Q5: Skills 系统如何支持组合和编排？

**Skill Composition**:

```python
# devpal/skills/composite_skill.py
class CompositeSkill(BaseSkill):
    """复合 Skill"""
    
    def __init__(self, sub_skills: List[BaseSkill]):
        self.sub_skills = sub_skills
    
    def execute(self, context: dict, **kwargs) -> SkillResult:
      results = []
      for skill in self.sub_skills:
            result = skill.execute(context, **kwargs)
            if not result.success:
                return result  # 失败则终止
          results.append(result)
            # 将上一个 Skill 的输出作为下一个的输入
            kwargs.update(result.output)
        
        return SkillResult(
          success=True,
            output=self._merge_results(results)
        )

# 示例：端到端工作流
class E2EWorkflowSkill(CompositeSkill):
    def __init__(self, tool_registry):
        sub_skills = [
            RequirementsParseSkill(tool_registry),
            CodeGenerationSkill(tool_registry),
        TestRunnerSkill(tool_registry),
            QualityGateSkill(tool_registry),
            ReportGeneratorSkill(tool_registry)
        ]
     super().__init__(sub_skills)
```

**Pipeline 编排**:
```python
# devpal/skills/skill_pipeline.py
class SkillPipeline:
    """Skill 流水线"""
    
    def __init__(self):
        self.stages: List[SkillStage] = []
    
    def add_stage(self, skill: BaseSkill, condition: Optional[Callable] = None):
        """添加阶段"""
        self.stages.append(SkillStage(skill, condition))
    
    def execute(self, context: dict) -> PipelineResult:
        """执行流水线"""
        for stage in self.stages:
          if stage.condition and not stage.condition(context):
              continue  # 跳过阶段
         
            result = stage.skill.execute(context)
            if not result.success and stage.is_critical:
                return PipelineResult(success=False, failed_stage=stage)
            
            # 更新 context
        context.update(result.output)
     
      return PipelineResult(success=True)

# 使用示例
pipeline = SkillPipeline()
pipeline.add_stage(OpenSpecWorkflowSkill(), condition=lambda ctx: ctx.get("use_openspec"))
pipeline.add_stage(SelfHealingSkill(), condition=lambda ctx: ctx.get("has_errors"))
pipeline.add_stage(DeploymentSkill())

result = pipeline.execute(context)
```

**面试展示**:
"Skills 支持两种组合模式：CompositeSkill（串行）和 SkillPipeline（条件编排）。这使得我们可以构建复杂的 multi-stage workflow，每个 stage 都是可插拔的 Skill。"

---

## Q6: Skills 系统在 DevPalAgent 中的实际应用？

**已实现的 Skills**:

| Skill 名称 | 功能 | 调用场景 |
|-----------|------|-------|
| `openspec_workflow` | 11 阶段 OpenSpec 流程 | 端到端项目生成 |
| `test_runner` | 测试执行和报告 | Phase 10 测试执行 |
| `code_review` | 代码审查 | Phase 9.5 Critique |
| `quality_gate` | 四层质量验证 | Phase 9 Quality Gate |
| `self_healing` | 根因分析和自愈 | 错误恢复 |
| `multi_agent_coordinator` | 多智能体编排 | Phase 4/5 并行生成 |

**代码位置**:
```
devpal/skills/
├── openspec_skill.py
├── test_runner_skill.py
├── code_review_skill.py
├── quality_gate_skill.py
├── self_healing_skill.py
└── multi_agent_skill.py
```

**实际使用示例**:
```python
# 用户请求：端到端生成项目
agent = AgentEngine()

# Agent 解析意图，选择 Skill
skill_name = planner.select_skill(user_request)  # "openspec_workflow"

# 执行 Skill
result = agent.execute_skill(
    skill_name="openspec_workflow",
    requirements_file="requirements/login.md",
    language="cpp"
)

if result.success:
    print(f"项目生成成功: {result.artifacts}")
else:
    # 自动触发 self_healing Skill
    agent.execute_skill(
        skill_name="self_healing",
        error=result.error,
     context=result.context
    )
```

**Skills Metrics**:
```python
# devpal/skills/skill_metrics.py
class SkillMetrics:
    """Skill 执行指标"""
    
    def record_execution(self, skill_name: str, duration: float, success: bool):
        self.metrics[skill_name].append({
            "timestamp": datetime.now(),
         "duration": duration,
       "success": success
        })
    
    def get_stats(self, skill_name: str) -> dict:
        """获取 Skill 统计"""
        executions = self.metrics[skill_name]
        return {
            "total_calls": len(executions),
       "success_rate": sum(e["success"] for e in executions) / len(executions),
            "avg_duration": statistics.mean(e["duration"] for e in executions),
       "p95_duration": statistics.quantiles(e["duration"] for e in executions)[18]
        }
```

**面试话术**:
"DevPalAgent 将核心能力都抽象为 Skills。例如 OpenSpec 11 阶段流程是 `openspec_workflow` Skill，多智能体编排是 `multi_agent_coordinator` Skill。这样设计的好处是：
1. **可测试性**: 每个 Skill 独立单元测试
2. **可监控性**: Skill-level metrics 精确定位性能瓶颈
3. **可替换性**: 例如将 `test_runner` Skill 从 pytest 替换为 Jest"

---

## 面试展示脚本

**开场**:
"DevPalAgent 的 Skills 系统是其可扩展性的核心。它不是简单的函数注册表，而是一个完整的能力编排框架。"

**技术深度展示**:
1. "Skills 与 Tools 的分层设计：Tools 是原子操作，Skills 是复合任务"
2. "动态加载机制：支持热加载，无需重启"
3. "组合模式：CompositeSkill 和 SkillPipeline 支持复杂编排"
4. "实战应用：6 大核心 Skills 支撑端到端流程"

**代码展示**:
- `devpal/skills/base_skill.py` - Skill 基类
- `devpal/skills/skill_loader.py` - 动态加载
- `devpal/skills/openspec_skill.py` - 实战 Skill

**亮点总结**:
- 🔌 **可插拔**: 新 Skill 零侵入
- 🔄 **可组合**: 支持 Pipeline 编排
- 🎯 **可监控**: Skill-level metrics
- 🚀 **生产级**: 6 大 Skills 已在实际项目验证
