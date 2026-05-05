# DevPal Agent - 个人开发助手

> **基于 Agent 技术的智能开发辅助系统**
>
> **版本：** v1.6
>
> **作者：** 李建
>
> **核心特性：** 测试编排系统 × 19个内置工具 × 自我改进 × 多模态支持
>
> **状态：** ✅ 生产可用

---

## 📋 目录

- [✨ 核心特性](#-核心特性)
- [🏗️ 整体架构](#️-整体架构)
- [🔧 完整工具列表](#-完整工具列表)
- [🎯 核心能力详解](#-核心能力详解)
- [🚀 快速开始](#-快速开始)
- [📖 使用示例](#-使用示例)
- [📁 项目结构](#-项目结构)
- [🧪 测试编排系统](#-测试编排系统-阶段6里程碑)
- [🔄 自我改进系统](#-自我改进系统-阶段5里程碑)
- [🎨 Web 界面](#-web-界面)
- [🔌 插件系统](#-插件系统)
- [📊 架构图](#-架构图)
- [🛠️ 开发指南](#️-开发指南)
- [📈 更新日志](#-更新日志)

---

## ✨ 核心特性

| 特性 | 状态 | 说明 |
|-----|------|------|
| **🤖 智能工具编排** | ✅ v1.0 | 自动决定调用什么工具、什么顺序 |
| **🧠 长短时记忆** | ✅ v1.0 | 记住对话历史、用户偏好、犯过的错误 |
| **📋 任务规划** | ✅ v1.0 | 复杂任务自动拆解成步骤，先规划再执行 |
| **🔍 自我反思** | ✅ v1.0 | 能发现自己的错误并纠正 |
| **🖼️ 多模态理解** | ✅ v1.1 | 能理解图片中的代码、编译报错截图 |
| **🔗 Git 集成** | ✅ v1.1 | Git 操作自动化 |
| **🧪 测试编排系统** | ✅ v1.6 | **一站式自动化测试（6步流程）** |
| **🛠️ 自我改进** | ✅ v1.5 | 代码自修复、自检、自优化 |
| **🔌 插件系统** | ✅ v1.5 | 动态加载第三方插件 |
| **⚡ MSVC ASAN** | ✅ v1.6 | Windows MSVC 编译 + AddressSanitizer |
| **📊 代码审查** | ✅ v1.6 | 自动化代码审查 + 修复建议 |
| **🎯 自动修复** | ✅ v1.6 | 智能修复代码问题 |
| **📝 测试生成** | ✅ v1.6 | 自动生成测试文档 + 测试代码 |
| **🌐 Web UI** | ✅ v1.1 | 现代化 Web 界面 |

---

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        交互层 (Interface)                        │
│   CLI 命令行  /  Web UI 界面  /  IDE 插件                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      Agent 核心引擎 (Core)                       │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────┐       │
│  │ Planner  │    │  Executor    │    │   Reflector     │       │
│  │  规划器   │───►│   执行器     │───►│    反思器       │       │
│  └──────────┘    └──────────────┘    └─────────────────┘       │
│                           │                                       │
│              ┌────────────▼────────────┐                         │
│              │   ToolRegistry 工具注册表   │                         │
│              └────────────┬────────────┘                         │
└───────────────────────────┼──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                    基础能力层 (Infrastructure)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  LLM SDK │  │ Memory   │  │  Tools   │  │ Multimodal│        │
│  │大模型封装 │  │ 记忆系统  │  │ 19个工具  │  │ 多模态    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔧 完整工具列表

### 📁 文件操作 (3个)

| 工具 | 功能 |
|-----|------|
| **file_reader** | 文件读取，支持大文件分页 |
| **file_writer** | 文件写入，安全覆盖保护 |
| **code_search** | 代码搜索，支持正则、文件过滤 |

### 💻 系统与编译 (4个)

| 工具 | 功能 |
|-----|------|
| **command_executor** | 命令行执行，白名单安全过滤 |
| **compiler_analyzer** | 编译错误分析，提取错误位置 |
| **msvc_asan_compiler** | **MSVC + AddressSanitizer**，内存错误检测 |
| **static_analyzer** | 代码静态分析 (clang-tidy/cppcheck) |

### 🌿 Git 与代码质量 (4个)

| 工具 | 功能 |
|-----|------|
| **git_tool** | Git 操作：status/commit/push/review |
| **code_review** | **独立代码审查**，多语言支持 |
| **code_review_report** | 生成详细审查报告 |
| **auto_fixer** | **智能自动修复**代码问题 |

### 🧪 测试编排系统 (5个)

| 工具 | 功能 |
|-----|------|
| **test_orchestrator** | **测试编排核心**，6步一站式流程 |
| **test_doc_generator** | 测试文档生成，结构化用例 |
| **test_generator** | 测试代码生成，多语言模板 |
| **test_runner** | 测试运行器，**MSVC/GCC 双支持** |

### 🔄 自我改进与扩展 (3个)

| 工具 | 功能 |
|-----|------|
| **self_source_reader** | 读取自身源码，AST 结构分析 |
| **self_improve** | **自我修复**，备份 + 修复 + 自检 |
| **plugin_system** | **插件系统**，动态加载第三方工具 |

### 🧩 其他工具 (1个)

| 工具 | 功能 |
|-----|------|
| **linked_list_tool** | 链表操作演示，验证 FunctionCall 机制 |

---

## 🎯 核心能力详解

### Plan-Act-Reflect 执行循环

```
用户输入
    ↓
[Planner 规划器]
    ↓ 生成执行计划
    ├─ 评估计划可行性
    ├─ 检测任务类型（测试/开发/自改进）
    └─ 拆解成步骤
        ↓
[Executor 执行器] ←────────────────┐
    ↓                               │
    ├─ 是否测试任务？→ 直接调用 TestOrchestrator │
    ├─ 是否需要调用工具？→ 调用 ToolRegistry │
    ├─ 执行工具 → 拿到结果          │
    └─ 判断任务完成了吗？            │
           ↓ 否                      │
[Reflector 反思器]                  │
    ↓ 反思刚才的执行               │
    ├─ 刚才做的对吗？               │
    ├─ 哪里错了？                   │
    ├─ 需要调整计划吗？             │
    └─ 把经验存入记忆 ──────────────┘
           ↓ 是
[结果输出 + 经验总结]
```

### 记忆系统三层架构

| 层级 | 类型 | 功能 |
|-----|------|------|
| **L1** | 短期记忆 | 对话上下文，滑动窗口管理 |
| **L2** | 长期记忆 | 用户偏好、任务经验、历史模式 |
| **L3** | 错误记忆 | 错误模式、修正方法、避免重复犯错 |

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- (Windows) Visual Studio 2019/2022 (MSVC 编译器支持)
- (Linux) GCC/Clang

### 安装依赖

```bash
pip install -r requirements.txt
```

### 命令行使用

```python
# 最简启动
from devpal import AgentEngine

agent = AgentEngine()
response = agent.chat("帮我 review 这个代码并生成测试用例")
print(response)
```

### 快速测试编排

```bash
# 测试编排一站式流程
python -c "
from devpal.tools import registry

result = registry.execute_tool('test_orchestrator', {
    'file_path': 'your_code.cpp',
    'project_name': 'MyProject',
    'run_code_review': True,
    'run_auto_fix': True,
    'generate_test_doc': True,
    'generate_test_code': True,
    'run_tests': True
})
print(result.content)
"
```

---

## 📖 使用示例

### 示例 1：完整测试流程

```python
from devpal.tools import registry

# 1. 代码审查
review_result = registry.execute_tool('code_review', {
    'file_path': 'src/buggy_code.cpp'
})

# 2. 自动修复
fix_result = registry.execute_tool('auto_fixer', {
    'file_path': 'src/buggy_code.cpp',
    'create_backup': True
})

# 3. 生成测试文档
doc_result = registry.execute_tool('test_doc_generator', {
    'source_file': 'src/buggy_code.cpp',
    'output_file': 'docs/test_plan.md'
})

# 4. 生成测试代码
code_result = registry.execute_tool('test_generator', {
    'source_file': 'src/buggy_code.cpp',
    'output_file': 'tests/test_buggy.cpp',
    'language': 'cpp'
})

# 5. 运行测试
test_result = registry.execute_tool('test_runner', {
    'test_file': 'tests/test_buggy.cpp',
    'source_file': 'src/buggy_code.cpp'
})
```

### 示例 2：使用 TestOrchestrator 一键完成

```python
from devpal.tools import registry

result = registry.execute_tool('test_orchestrator', {
    'file_path': 'src/buggy_code.cpp',
    'project_name': 'MyProject',
    'run_code_review': True,
    'run_auto_fix': True,
    'generate_test_doc': True,
    'generate_test_code': True,
    'run_tests': True
})

# 输出目录: MyProject/
#   ├── backup_buggy_code.cpp      # 源文件备份
#   ├── code_review.md             # 审查报告
#   ├── test_documentation.md      # 测试文档
#   └── test_buggy_code.cpp        # 测试代码
```

### 示例 3：自我改进

```python
from devpal.tools import registry

# 自我代码审查
result = registry.execute_tool('self_improve', {
    'action': 'self_review',
    'create_backup': True
})

# 自动修复发现的问题
result = registry.execute_tool('self_improve', {
    'action': 'apply_fixes',
    'backup_name': 'backup_20240501_120000'
})
```

---

## 📁 项目结构

```
DevPalAgent/
├── devpal/                          # 主包
│   ├── __init__.py                 # 版本和导出
│   ├── main.py                     # 入口文件
│   ├── cli.py                      # 命令行界面
│   ├── config.py                   # 配置管理
│   │
│   ├── core/                       # 核心引擎层
│   │   ├── __init__.py
│   │   ├── agent_engine.py         # Agent 主引擎
│   │   ├── planner.py              # 规划器
│   │   └── reflector.py            # 反思器
│   │
│   ├── memory/                     # 记忆系统层
│   │   ├── __init__.py
│   │   ├── base.py                 # 记忆基类
│   │   ├── memory_manager.py       # 记忆管理器
│   │   ├── message_history.py      # 消息历史
│   │   ├── short_term.py           # 短期记忆
│   │   ├── long_term.py            # 长期记忆
│   │   └── error_memory.py         # 错误记忆
│   │
│   ├── tools/                      # 工具系统层 (19个工具)
│   │   ├── __init__.py
│   │   ├── base.py                 # Tool 基类
│   │   ├── function_call_base.py   # FunctionCall 抽象层
│   │   ├── registry.py             # 工具注册表
│   │   │
│   │   ├── file_reader.py          # 📁 文件读取
│   │   ├── file_writer.py          # 📁 文件写入
│   │   ├── code_search.py          # 🔍 代码搜索
│   │   ├── command_executor.py     # 💻 命令执行
│   │   ├── compiler_analyzer.py    # 🔧 编译分析
│   │   ├── static_analyzer.py      # 📊 静态分析
│   │   ├── msvc_asan_compiler.py   # ⚡ MSVC ASAN
│   │   ├── git_tool.py             # 🌿 Git 操作
│   │   ├── code_review.py          # 👀 代码审查
│   │   ├── code_review_report.py   # 📋 审查报告
│   │   ├── auto_fixer.py           # 🔧 自动修复
│   │   ├── test_orchestrator.py    # 🧪 测试编排核心 ⭐
│   │   ├── test_doc_generator.py   # 📄 测试文档生成
│   │   ├── test_generator.py       # ✏️ 测试代码生成
│   │   ├── test_runner.py          # 🚀 测试运行器
│   │   ├── self_source_reader.py   # 🔍 自源码读取
│   │   ├── self_improve.py         # 🔄 自我改进
│   │   ├── plugin_system.py        # 🔌 插件系统
│   │   └── linked_list.py          # 🧩 链表演示
│   │
│   ├── multimodal/                 # 多模态层
│   │   ├── __init__.py
│   │   └── image_analyzer.py       # 🖼️ 图片分析
│   │
│   └── web/                        # Web 界面
│       ├── __init__.py
│       └── app.py                  # 🌐 Flask/FastAPI
│
├── docs/                           # 文档与架构图
│   ├── *.png                       # 架构图文件
│   └── generate_architecture_diagrams.py
│
├── plugins/                        # 第三方插件目录
│   └── example_plugin.py
│
├── .devpal_backups/                # 自动备份目录
│   └── backup_timestamp/
│
├── config/                         # 配置文件
│   └── config.yaml
│
├── requirements.txt                # 核心依赖
├── requirements-web.txt            # Web 依赖
│
└── README.md                       # 本文件
```

---

## 🧪 测试编排系统 (阶段6里程碑)

### 6步一站式流程

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 代码审查  CodeReview   │  检测问题、严重程度分级  │
├──────────────────────────────────┼────────────────────────────┤
│  Step 2: 生成审查报告           │  Markdown 详细报告         │
├──────────────────────────────────┼────────────────────────────┤
│  Step 3: 自动修复 AutoFixer     │  智能修复、备份保护       │
├──────────────────────────────────┼────────────────────────────┤
│  Step 4: 测试文档生成           │  结构化用例、边界分析      │
├──────────────────────────────────┼────────────────────────────┤
│  Step 5: 测试代码生成           │  多语言模板、断言覆盖      │
├──────────────────────────────────┼────────────────────────────┤
│  Step 6: 运行测试 + 更新文档     │  MSVC/GCC、结果回填       │
└─────────────────────────────────────────────────────────────┘
```

### MSVC 编译器支持特性

- ✅ Visual Studio 2019/2022 自动检测
- ✅ vswhere.exe 路径探测
- ✅ INCLUDE/LIB 环境变量自动配置
- ✅ AddressSanitizer 内存错误检测
- ✅ 编译错误自动解析
- ✅ 测试结果自动统计

---

## 🔄 自我改进系统 (阶段5里程碑)

### 闭环进化流程

```
┌──────────────────────────────────────────────────────────────┐
│  1. SelfSourceReader → 读取自身源码，分析 AST 结构            │
├──────────────────────────────────────────────────────────────┤
│  2. 问题检测 → TODO/FIXME/print 调试代码/潜在 bug            │
├──────────────────────────────────────────────────────────────┤
│  3. 自动备份 → 备份 + 时间戳命名                               │
├──────────────────────────────────────────────────────────────┤
│  4. 应用修复 → LLM 建议 + 自动修改代码                        │
├──────────────────────────────────────────────────────────────┤
│  5. 自我验证 → 导入测试、注册测试、功能完整性检查              │
└──────────────────────────────────────────────────────────────┘
```

### 安全特性

- ✅ **修改前自动备份**：每次修改前自动创建备份
- ✅ **可回滚**：随时可以恢复到历史版本
- ✅ **沙箱验证**：先验证修改再应用
- ✅ **变更追踪**：所有修改都有记录可查

---

## 🎨 Web 界面

### 功能

- 📊 实时执行状态面板
- 🧰 多标签页工具面板
- 📁 文件浏览器集成
- 📋 代码审查报告可视化
- 📈 测试执行结果展示

### 启动方式

```bash
# 安装 Web 依赖
pip install -r requirements-web.txt

# 启动 Web 服务
python -m devpal.web.app
```

---

## 🔌 插件系统

### 快速创建插件

```python
# plugins/my_custom_tool.py
from devpal.tools.base import BaseTool, ToolResult

class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "我的自定义工具"
    
    class Parameters:
        param1: str = "参数1"
    
    def _execute(self, params):
        # 自定义逻辑
        return ToolResult.ok("执行成功")
```

### 动态加载

```python
from devpal.tools import registry

registry.execute_tool('plugin_system', {
    'action': 'load_plugin',
    'plugin_path': 'plugins/my_custom_tool.py'
})
```

---

## 📊 架构图

所有架构图位于 `docs/` 目录：

| 架构图 | 版本 | 说明 |
|--------|------|------|
| **DevPal_Architecture_Overview_v1.6.png** | v1.6 | 整体架构概览 |
| **Test_Orchestrator_System_Architecture_v1.6.png** | v1.6 | 测试编排系统详情 |
| **Tool_System_Architecture_v1.6.png** | v1.6 | 工具系统架构 |
| **Plan_Act_Reflect_Flowchart_v1.6.png** | v1.6 | 执行流程图 |
| **Complete_Data_Flow_v1.6.png** | v1.6 | 完整数据流 |

---

## 🛠️ 开发指南

### 添加新工具

```python
# 1. 继承 BaseTool
from devpal.tools.base import BaseTool, ToolResult

class MyNewTool(BaseTool):
    name = "my_new_tool"
    description = "新工具的描述"
    
    class Parameters:
        required_param: str
        optional_param: int = 42
    
    def _execute(self, params):
        # 你的实现逻辑
        return ToolResult.ok("执行成功", data=result)

# 2. 在 tools/registry.py 中注册
# from .my_new_tool import MyNewTool
# self.register(MyNewTool())
```

### 调试

```python
# 启用调试模式
from devpal.config import set_config
set_config('DEBUG', True)
```

---

## 📈 更新日志

### v1.6 (2024-05-05) ✅ 最新

- ✨ **新增测试编排系统**（TestOrchestrator）- 6步一站式流程
- ✨ 新增 CodeReview 独立代码审查工具
- ✨ 新增 AutoFixer 智能自动修复工具
- ✨ 新增 TestDocGenerator 测试文档生成器
- ✨ 新增 TestGenerator 测试代码生成器
- ✨ 新增 TestRunner 测试运行器，**MSVC/GCC 双支持**
- ✨ 完善 MSVC ASAN 编译器支持，自动环境配置
- ✨ Planner 增加测试任务自动识别
- ✨ AgentEngine 增加 TestOrchestrator 快捷执行路径
- 📊 新增 v1.6 全套架构图

### v1.5 (2024-05-04)

- ✨ 新增自我改进系统（Self-Source-Reader + Self-Improve）
- ✨ 新增插件系统（PluginSystem）
- ✨ 完善记忆管理器架构
- 📊 新增 v1.5 架构图

### v1.1 (2024-05-02)

- ✨ 多模态支持（ImageAnalyzer）
- ✨ Git 工具集成
- ✨ Web 界面初版
- ✨ 静态分析工具

### v1.0 (2024-05-01)

- 🎉 初始版本发布
- ✅ Plan-Act-Reflect 核心引擎
- ✅ 8 个基础工具
- ✅ 记忆系统三层架构

---

## 📝 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## ⭐ 里程碑

- ✅ v1.0 - 基础 Agent 框架（阶段1）
- ✅ v1.1 - 多模态 + 工具链扩展（阶段4）
- ✅ v1.5 - 自我改进系统（阶段5）
- ✅ **v1.6 - 测试编排系统（阶段6）← 当前版本**
- 🚧 下一阶段：...

---

*本项目采用 DevPal Agent 自我改进系统维护，代码质量持续优化中...*
