# DevPalAgent Skill 接入规划

日期：2026-05-19

## 1. 背景

DevPalAgent 当前已经具备 Agent 主循环、ToolRegistry、插件系统、OpenSpec 工作流、模板系统、语言插件和安装脚本生成能力，但还没有独立的 Skill 系统。

当前最接近 Skill 的机制是 Tool 和 Plugin：

- Tool 负责原子动作，例如文件读写、命令执行、代码搜索、测试执行。
- PluginSystemTool 可以动态加载第三方 BaseTool 子类。
- OpenSpec 负责规范驱动的长流程。
- TemplateRegistry 负责模板生成。
- LanguagePlugin 负责语言级分析能力。

因此，Skill 不应该直接替代 Tool 或 OpenSpec，而应该作为更高一层的任务级能力编排。

## 2. Skill 定位

建议将 Skill 定义为：

> 面向用户意图的任务级能力包，用于编排多个 Tool、OpenSpec 工作流、模板系统和语言插件。

推荐分层：

| 层级 | 职责 | 示例 |
| --- | --- | --- |
| Tool | 原子能力 | 读文件、写文件、执行命令、代码搜索、运行测试 |
| Skill | 任务级编排 | 代码审查、测试生成、安装器生成、OpenSpec 执行 |
| OpenSpec | 规范驱动长流程 | 需求、设计、代码、测试、报告 |
| Template | 静态或半静态产物生成 | 安装脚本、项目骨架、配置文件 |
| LanguagePlugin | 语言理解与分析 | Python、Shell、C++ 分析 |

一句话概括：

> Tool 是原子动作，OpenSpec 是长流程，Skill 是面向用户意图的能力编排层。

## 3. 当前关键代码入口

### Agent 主入口

- `devpal/core/agent_engine.py`
  - `AgentEngine` 是核心执行器。
  - `AgentEngine.run()` 是用户请求入口。
  - SkillRouter 应该接入在 OpenSpec 显式请求检测之后、Planner 之前。

### Tool 系统

- `devpal/tools/base.py`
  - `BaseTool` 定义工具抽象、参数模型、执行入口和 Claude tool schema 生成逻辑。
- `devpal/tools/registry.py`
  - `ToolRegistry` 负责注册和执行所有工具。
  - Skill 内部应该复用 ToolRegistry 调用已有工具。
- `devpal/tools/plugin_system.py`
  - 当前动态插件系统，只支持加载 `BaseTool` 子类。
  - 后续可以参考它实现 Skill 插件加载。

### OpenSpec 系统

- `devpal/core/openspec_executor.py`
  - `OpenSpecWorkflowExecutor` 是 OpenSpec 工作流 facade。
- `devpal/core/openspec_phases/scheduler.py`
  - `OpenSpecPhaseScheduler` 负责任务阶段调度。
- `devpal/core/openspec_phases/phase4_generate_code.py`
  - 当前已经包含 installer 项目的特殊生成逻辑。

### 模板与 installer

- `devpal/core/templates/registry.py`
  - `TemplateRegistry` 负责模板注册和匹配。
- `devpal/core/templates/install_script_generator.py`
  - `InstallScriptGenerator` 负责生成平台安装脚本。
- `devpal/cli/commands/generate_installer.py`
  - installer CLI 命令入口。

### 语言插件

- `devpal/core/schema/languages/base.py`
  - `LanguagePlugin` 和 `LanguagePluginManager` 是语言扩展入口。

## 4. 推荐目录结构

建议新增：

```text
devpal/
  skills/
    __init__.py
    base.py
    registry.py
    router.py
    loader.py
    builtin/
      __init__.py
      code_review.py
      test_generation.py
      installer.py
      openspec.py
```

各文件职责：

| 文件 | 职责 |
| --- | --- |
| `base.py` | 定义 `BaseSkill`、`SkillContext`、`SkillResult` |
| `registry.py` | 管理 Skill 注册、查询、启停 |
| `router.py` | 根据用户请求和上下文选择 Skill |
| `loader.py` | 加载外部 Skill 插件，可后续阶段实现 |
| `builtin/` | 内置 Skill 实现 |

## 5. 核心抽象设计

### 5.1 SkillContext

`SkillContext` 用于传递执行上下文。

建议字段：

```python
class SkillContext(BaseModel):
    user_query: str
    workspace_path: Path
    tool_registry: ToolRegistry
    config: dict = {}
    metadata: dict = {}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `user_query` | 用户原始请求 |
| `workspace_path` | 当前工作区路径 |
| `tool_registry` | 可调用的工具注册表 |
| `config` | Skill 相关配置 |
| `metadata` | 扩展上下文，例如语言、项目类型、OpenSpec 信息 |

### 5.2 SkillResult

`SkillResult` 用于统一 Skill 执行结果。

```python
class SkillResult(BaseModel):
    success: bool
    content: str
    artifacts: list[str] = []
    metadata: dict = {}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `success` | 是否执行成功 |
| `content` | 返回给用户或 Agent 的文本结果 |
| `artifacts` | 生成或修改的产物路径 |
| `metadata` | 额外执行信息 |

### 5.3 BaseSkill

```python
class BaseSkill(ABC):
    name: str
    description: str
    triggers: list[str] = []
    required_tools: list[str] = []

    def can_handle(self, context: SkillContext) -> float:
        return 0.0

    @abstractmethod
    def execute(self, context: SkillContext) -> SkillResult:
        pass
```

字段与方法说明：

| 成员 | 说明 |
| --- | --- |
| `name` | Skill 唯一名称 |
| `description` | Skill 能力说明 |
| `triggers` | 关键词或意图触发规则 |
| `required_tools` | 依赖的 Tool 名称列表 |
| `can_handle()` | 返回匹配置信度，范围 0 到 1 |
| `execute()` | 执行 Skill 编排逻辑 |

## 6. SkillRegistry 设计

`SkillRegistry` 建议放在 `devpal/skills/registry.py`。

职责：

```text
SkillRegistry
  - register(skill)
  - unregister(name)
  - get(name)
  - list_skills()
  - list_skill_names()
  - load_builtin_skills()
  - load_external_skills()
```

原则：

- SkillRegistry 只管理 Skill。
- ToolRegistry 只管理 Tool。
- 不要把 Skill 伪装成 Tool 注册到 ToolRegistry，避免概念混乱。

## 7. SkillRouter 设计

`SkillRouter` 建议放在 `devpal/skills/router.py`。

职责：

```text
SkillRouter
  - 接收 user_query 和上下文
  - 遍历 SkillRegistry 中的 Skill
  - 调用 skill.can_handle(context)
  - 选择置信度最高的 Skill
  - 返回 SkillMatch
```

建议数据结构：

```python
class SkillMatch(BaseModel):
    skill_name: str
    confidence: float
    reason: str = ""
```

路由策略建议分三层。

### 7.1 显式触发

用户明确指定 Skill：

```text
/skill code_review
use skill installer
用 installer skill 生成安装脚本
```

这类请求应该直接命中目标 Skill。

### 7.2 关键词或意图触发

例如：

| 用户请求 | 推荐 Skill |
| --- | --- |
| 帮我审查一下代码 | `code_review_skill` |
| 给这个模块生成测试 | `test_generation_skill` |
| 生成安装脚本 | `installer_skill` |
| 根据需求文档走 OpenSpec | `openspec_skill` |

### 7.3 上下文触发

根据项目上下文自动命中：

- requirements 文档是 installer 项目，命中 `installer_skill`。
- 当前任务是规范驱动开发，命中 `openspec_skill`。
- 当前变更包含测试相关文件，命中 `test_generation_skill` 或 `test_review_skill`。

## 8. AgentEngine 接入方案

Skill 应接入 `AgentEngine`。

### 8.1 初始化接入

在 `AgentEngine.__init__()` 中增加：

```python
self.skill_registry = SkillRegistry()
self.skill_registry.load_builtin_skills()

self.skill_router = SkillRouter(
    skill_registry=self.skill_registry,
    tool_registry=self.tool_registry,
)
```

### 8.2 运行时接入

在 `AgentEngine.run()` 中，推荐执行顺序：

```text
1. 记录 query 统计信息
2. 检测是否是显式 OpenSpec requirements 请求
3. 如果不是强制 OpenSpec 快路径，则尝试 SkillRouter
4. Skill 命中且置信度超过阈值，执行 Skill
5. 未命中则继续走现有 Planner / Tool / Reflector 流程
```

伪代码：

```python
skill_match = self.skill_router.route(user_query)

if skill_match and skill_match.confidence >= self.config.skill_confidence_threshold:
    context = SkillContext(
        user_query=user_query,
        workspace_path=self.workspace_path,
        tool_registry=self.tool_registry,
        config=self.config_obj.get("skills", {}),
    )
    result = skill_match.skill.execute(context)
    return result.content
```

注意：

- 不建议所有请求都强制走 Skill。
- Skill 路由应该是增强能力，不应破坏现有 Plan-Act-Reflect 行为。
- OpenSpec 显式请求优先级应高于普通 Skill 自动路由。

## 9. 内置 Skill 规划

### 9.1 installer_skill

优先级：最高。

原因：

- 现有 `InstallScriptGenerator` 已经成熟。
- `phase4_generate_code.py` 已经有 installer 特殊逻辑。
- 最容易展示 Skill 编排已有能力的价值。

职责：

```text
installer_skill
  - 判断当前任务是否是安装脚本生成
  - 解析目标平台和语言
  - 调用 InstallScriptGenerator
  - 返回生成文件路径和摘要
```

可复用：

- `devpal/core/templates/install_script_generator.py`
- `devpal/cli/commands/generate_installer.py`
- `devpal/core/openspec_phases/phase4_generate_code.py`

### 9.2 code_review_skill

职责：

```text
code_review_skill
  - 搜索相关代码
  - 静态分析
  - 代码审查
  - 幻觉检测
  - 生成审查报告
```

可编排工具：

- `code_search`
- `static_analyzer`
- `code_review`
- `hallucination_detector`
- `code_review_report`

### 9.3 test_generation_skill

职责：

```text
test_generation_skill
  - 分析目标模块
  - 生成测试
  - 运行测试
  - 生成测试文档或报告
```

可编排工具：

- `test_generator`
- `test_runner`
- `test_doc_generator`
- `test_orchestrator`

### 9.4 openspec_skill

职责：

```text
openspec_skill
  - 识别 requirements 文档
  - 委托 OpenSpecWorkflowExecutor
  - 收集各 phase 结果
  - 返回最终执行摘要
```

原则：

- 不在 Skill 内重新实现 OpenSpec 11 阶段。
- Skill 只负责入口识别和委托执行。

可复用：

- `devpal/core/openspec_executor.py`
- `devpal/core/openspec_phases/scheduler.py`

## 10. 配置设计

建议在 `config/config.yaml.example` 中增加：

```yaml
skills:
  enabled: true
  auto_route: true
  confidence_threshold: 0.8
  search_paths:
    - skills
    - plugins/skills
  builtin:
    installer: true
    code_review: true
    test_generation: true
    openspec: true
```

配置含义：

| 配置 | 说明 |
| --- | --- |
| `enabled` | 是否启用 Skill 系统 |
| `auto_route` | 是否自动路由用户请求到 Skill |
| `confidence_threshold` | 自动命中 Skill 的最低置信度 |
| `search_paths` | 外部 Skill 搜索路径 |
| `builtin` | 内置 Skill 开关 |

## 11. CLI 规划

后续可以新增命令：

```text
devpal skill list
devpal skill show <name>
devpal skill run <name> --input <text>
devpal skill validate <path>
devpal skill load <path>
devpal skill unload <name>
```

建议文件位置：

```text
devpal/cli/commands/skill.py
```

CLI 命令可以复用 SkillRegistry 和 SkillRouter，而不是另写一套执行逻辑。

## 12. 外部 Skill 插件规划

当前插件系统只能加载 `BaseTool` 子类。后续可以增加 Skill 插件加载能力。

建议目录：

```text
plugins/
  skills/
    my_skill.py
```

插件示例：

```python
from devpal.skills.base import BaseSkill, SkillContext, SkillResult

class MySkill(BaseSkill):
    name = "my_skill"
    description = "示例 Skill"
    triggers = ["示例", "demo"]
    required_tools = []

    def can_handle(self, context: SkillContext) -> float:
        if "示例" in context.user_query:
            return 0.9
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        return SkillResult(success=True, content="MySkill executed")
```

加载逻辑可参考 `PluginSystemTool._load_plugin()`，但应扫描 `BaseSkill` 子类，而不是 `BaseTool` 子类。

## 13. 测试规划

建议新增目录：

```text
tests/skills/
  test_skill_base.py
  test_skill_registry.py
  test_skill_router.py
  test_builtin_installer_skill.py
  test_builtin_code_review_skill.py
  test_builtin_test_generation_skill.py
  test_builtin_openspec_skill.py
```

测试重点：

1. Skill 可以正常注册。
2. Skill 名称唯一。
3. SkillRouter 可以根据显式名称命中。
4. SkillRouter 可以根据关键词命中。
5. SkillRouter 不应误伤普通请求。
6. Skill 缺少 required tool 时返回明确错误。
7. installer_skill 能复用 InstallScriptGenerator。
8. code_review_skill 能编排现有审查工具。
9. test_generation_skill 能编排测试工具。
10. openspec_skill 能委托 OpenSpecWorkflowExecutor。

## 14. 分阶段落地计划

### Phase 1：Skill 内核

目标：打通最小链路。

新增：

```text
devpal/skills/base.py
devpal/skills/registry.py
devpal/skills/router.py
devpal/skills/__init__.py
```

改造：

```text
devpal/core/agent_engine.py
config/config.yaml.example
```

交付标准：

- SkillRegistry 可注册 Skill。
- SkillRouter 可路由请求。
- AgentEngine 可在命中 Skill 时执行 Skill。
- 未命中 Skill 时保持原有流程不变。

### Phase 2：installer_skill

目标：完成第一个真实 Skill。

新增：

```text
devpal/skills/builtin/installer.py
```

复用：

```text
devpal/core/templates/install_script_generator.py
devpal/cli/commands/generate_installer.py
devpal/core/openspec_phases/phase4_generate_code.py
```

交付标准：

- 用户请求生成安装脚本时可自动命中 installer_skill。
- 能生成目标脚本。
- 返回生成路径和摘要。

### Phase 3：code_review_skill 与 test_generation_skill

目标：把现有工具组合成更高阶能力。

新增：

```text
devpal/skills/builtin/code_review.py
devpal/skills/builtin/test_generation.py
```

交付标准：

- 代码审查请求命中 code_review_skill。
- 测试生成请求命中 test_generation_skill。
- Skill 内部通过 ToolRegistry 调用已有工具。

### Phase 4：openspec_skill

目标：统一 OpenSpec 用户入口。

新增：

```text
devpal/skills/builtin/openspec.py
```

交付标准：

- 用户提供 requirements 文档时，openspec_skill 能委托 OpenSpecWorkflowExecutor。
- Skill 返回清晰的 phase 执行摘要。

### Phase 5：外部 Skill 插件

目标：允许第三方扩展 Skill。

新增：

```text
devpal/skills/loader.py
plugins/skills/
```

可选 CLI：

```text
devpal skill load <path>
devpal skill unload <name>
devpal skill validate <path>
```

交付标准：

- 外部 `.py` 文件可定义 `BaseSkill` 子类。
- SkillRegistry 可动态加载外部 Skill。
- 加载失败时有明确错误。

## 15. 风险与注意事项

### 15.1 不要混淆 Skill 和 Tool

反例：

```text
把 Skill 直接注册到 ToolRegistry
```

这样会导致 Tool 列表膨胀，也会让 LLM 混淆原子动作和任务编排。

推荐：

```text
ToolRegistry 管工具
SkillRegistry 管能力包
Skill 内部调用 ToolRegistry
```

### 15.2 不要让 Skill 抢走所有请求

SkillRouter 应设置置信度阈值。

低置信度请求应继续走现有 Plan-Act-Reflect 流程。

### 15.3 OpenSpec 不要重复实现

`openspec_skill` 应作为入口，不应重写 OpenSpec phase。

### 15.4 插件加载要控制边界

外部 Skill 插件会执行 Python 代码，后续需要考虑：

- 加载路径限制
- 错误隔离
- 插件元数据校验
- 是否允许自动加载

第一阶段可以只支持内置 Skill，外部加载后置。

## 16. 推荐最小可交付版本

建议第一版只做：

```text
Skill 框架 + installer_skill + router 测试
```

原因：

- 改动面可控。
- installer 现有能力最完整。
- 能清楚展示 Skill 编排层价值。
- 不会过早影响 OpenSpec 主流程。

最小文件清单：

```text
devpal/skills/__init__.py
devpal/skills/base.py
devpal/skills/registry.py
devpal/skills/router.py
devpal/skills/builtin/__init__.py
devpal/skills/builtin/installer.py
tests/skills/test_skill_registry.py
tests/skills/test_skill_router.py
tests/skills/test_builtin_installer_skill.py
```

最小改造文件：

```text
devpal/core/agent_engine.py
config/config.yaml.example
```

## 17. 总结

DevPalAgent 引入 Skill 的最佳方式不是新增一批复杂工具，而是在现有架构上增加一个任务级编排层。

推荐架构：

```text
User Query
  -> AgentEngine
  -> SkillRouter
  -> SkillRegistry
  -> BaseSkill
  -> ToolRegistry / OpenSpecWorkflowExecutor / TemplateRegistry / LanguagePluginManager
```

优先落地顺序：

1. 建立 Skill 基础抽象。
2. 建立 SkillRegistry。
3. 建立 SkillRouter。
4. 接入 AgentEngine。
5. 实现 installer_skill。
6. 扩展 code_review_skill、test_generation_skill、openspec_skill。
7. 最后支持外部 Skill 插件和 CLI。

这样可以在不破坏现有 Tool、OpenSpec、Template 和 LanguagePlugin 的前提下，让 DevPalAgent 拥有更清晰的能力组织方式。