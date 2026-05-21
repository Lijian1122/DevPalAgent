# Claude CLI 安装脚本生成 - P3.2 集成方案

**日期**：2026-05-17  
**版本**：2.0（基于 P3.2 多语言框架）  
**状态**：设计阶段

---

## 执行摘要

将 Claude Code CLI 安装脚本生成功能集成到 DevPalAgent 的 P3.2 多语言框架中，通过新建统一的 i18n 基础设施和模板系统，生成支持多平台（Bash/Batch/Python）和多语言（中英日韩）的安装脚本。

**核心变化**：
- ❌ 原方案：独立脚本，与 DevPalAgent 无关
- ✅ 新方案：集成到模板系统，共享 P3.2 架构

---

## 1. 架构设计

### 1.1 组件关系图

```
DevPalAgent P3.2 多语言框架
│
├─ 语言插件系统 (devpal/core/schema/languages/)
│  ├─ base.py (LanguagePlugin 抽象类)
│  ├─ cpp_plugin.py (C++ 代码分析)
│  └─ python_plugin.py (Python 代码分析 - 未来)
│  └─ 用途：代码分析（AST、符号、依赖）
│
├─ 模板系统 (devpal/core/templates/)
│  ├─ base.py (BaseTemplate, TemplateContext)
│  ├─ registry.py (模板注册)
│  ├─ cpp_templates.py (C++ 项目模板)
│  ├─ python_templates.py (Python 项目模板)
│  ├─ install_script_templates.py (新增 - 安装脚本模板)
│  └─ 用途：代码生成（脚手架、样板代码）
│
└─ i18n 系统 (devpal/core/templates/i18n/) ← 新增
   ├─ base.py (Locale, MessageCatalog, I18nContext)
   └─ locales/
      ├─ en.py (EnglishMessages)
      ├─ zh.py (ChineseMessages)
      ├─ ja.py (JapaneseMessages)
      └─ ko.py (KoreanMessages)
   └─ 用途：为所有模板提供多语言消息支持
```

### 1.2 文件结构

```
DevPalAgent/
├── devpal/
│   ├── core/
│   │   ├── templates/
│   │   │   ├── base.py                         # 修改 - 扩展 TemplateContext
│   │   │   ├── registry.py                     # 现有
│   │   │   ├── cpp_templates.py                # 现有
│   │   │   ├── python_templates.py             # 现有
│   │   │   ├── install_script_templates.py     # 新增 - 3 个模板类
│   │   │   └── i18n/                           # 新增目录
│   │   │       ├── __init__.py
│   │   │       ├── base.py                     # Locale, MessageCatalog, I18nContext
│   │   │       └── locales/
│   │   │           ├── __init__.py
│   │   │           ├── en.py                   # 20+ 条英文消息
│   │   │           ├── zh.py                   # 20+ 条中文消息
│   │   │           ├── ja.py                   # 可选
│   │   │           └── ko.py                   # 可选
│   │   └── schema/
│   │       └── languages/                      # 现有 - 不修改
│   └── cli/
│       └── commands/
│           └── generate_installer.py           # 新增 - CLI 命令
├── scripts/                                    # 生成输出目录
│   ├── install_claude_cli.sh                  # 生成
│   ├── install_claude_cli.bat                 # 生成
│   ├── install_claude_cli.py                  # 生成
│   └── README_INSTALL.md                      # 生成
└── plan_doc/
    └── install_script_p32_integration_plan_2026-05-17.md  # 本文档
```

---

## 2. 核心实现

### 2.1 i18n 基础设施

#### 2.1.1 核心类（`devpal/core/templates/i18n/base.py`）

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional
from enum import Enum

class Locale(Enum):
    """支持的语言"""
    EN = "en"
    ZH = "zh"
    JA = "ja"
    KO = "ko"

class MessageCatalog(ABC):
    """消息目录基类"""
    
    @abstractmethod
    def get_messages(self) -> Dict[str, str]:
        """返回该语言的所有消息键值对"""
        pass
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        messages = self.get_messages()
        return messages.get(key, default or key)

class I18nContext:
    """i18n 上下文"""
    
    def __init__(self, locale: Locale = Locale.EN):
        self.locale = locale
        self._catalogs: Dict[Locale, MessageCatalog] = {}
    
    def register_catalog(self, locale: Locale, catalog: MessageCatalog):
        self._catalogs[locale] = catalog
    
    def t(self, key: str, **kwargs) -> str:
        """翻译函数（支持 {variable} 变量替换）"""
        catalog = self._catalogs.get(self.locale)
        if not catalog:
            return key
        
        message = catalog.get(key)
        if kwargs:
            try:
                message = message.format(**kwargs)
            except KeyError:
                pass
        return message
```

#### 2.1.2 消息定义（`devpal/core/templates/i18n/locales/en.py`）

```python
from ..base import MessageCatalog

class EnglishMessages(MessageCatalog):
    def get_messages(self) -> dict:
        return {
            "install.welcome": "Welcome to Claude Code CLI One-Click Installer",
            "install.check_node": "Checking Node.js installation...",
            "install.node_found": "✓ Node.js found: {version}",
            "install.node_missing": "✗ Node.js not found",
            "install.node_version_low": "✗ Node.js version too old (requires >= {min_version})",
            "install.npm_missing": "✗ npm not found",
            "install.installing_cli": "Installing Claude Code CLI...",
            "install.success": "✓ Installation successful!",
            "install.failed": "✗ Installation failed: {error}",
            "install.config_api_key_prompt": "Configure API Key now? (y/n)",
            "install.enter_api_key": "Enter your Anthropic API Key",
            "install.api_key_saved": "✓ API Key saved to environment",
            "install.done": "Installation complete! Run 'claude' to start",
            "install.download_node": "Opening Node.js download page...",
            "install.manual_install": "Please install Node.js manually and re-run this script",
            "install.permission_denied": "✗ Permission denied, run as administrator",
            "install.network_error": "✗ Network error, check your connection",
            "install.already_installed": "✓ Claude CLI already installed: {version}",
            "install.upgrade_prompt": "New version available ({new_version}), upgrade? (y/n)",
            "install.usage": "Usage: {script_name} [--lang=zh|en]",
        }
```

#### 2.1.3 中文消息（`devpal/core/templates/i18n/locales/zh.py`）

```python
from ..base import MessageCatalog

class ChineseMessages(MessageCatalog):
    def get_messages(self) -> dict:
        return {
            "install.welcome": "欢迎使用 Claude Code CLI 一键安装脚本",
            "install.check_node": "检查 Node.js 安装状态...",
            "install.node_found": "✓ 已找到 Node.js: {version}",
            "install.node_missing": "✗ 未找到 Node.js",
            "install.node_version_low": "✗ Node.js 版本过低（需要 >= {min_version}）",
            "install.npm_missing": "✗ 未找到 npm",
            "install.installing_cli": "正在安装 Claude Code CLI...",
            "install.success": "✓ 安装成功！",
            "install.failed": "✗ 安装失败: {error}",
            "install.config_api_key_prompt": "是否现在配置 API Key？(y/n)",
            "install.enter_api_key": "请输入您的 Anthropic API Key",
            "install.api_key_saved": "✓ API Key 已保存到环境变量",
            "install.done": "安装完成！运行 'claude' 开始使用",
            "install.download_node": "正在打开 Node.js 下载页面...",
            "install.manual_install": "请手动安装 Node.js 后重新运行此脚本",
            "install.permission_denied": "✗ 权限不足，请使用管理员权限运行",
            "install.network_error": "✗ 网络错误，请检查网络连接",
            "install.already_installed": "✓ Claude CLI 已安装: {version}",
            "install.upgrade_prompt": "发现新版本 ({new_version})，是否升级？(y/n)",
            "install.usage": "用法: {script_name} [--lang=zh|en]",
        }
```

### 2.2 扩展 TemplateContext

```python
# devpal/core/templates/base.py（修改）

from typing import Optional, List
from dataclasses import dataclass, field

@dataclass
class TemplateContext:
    """模板渲染上下文"""
    project_name: str
    project_type: str = "generic"
    language: str = "cpp"
    features: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)
    
    # 新增 - i18n 支持
    i18n_context: Optional['I18nContext'] = None
    target_locales: List[str] = field(default_factory=lambda: ["en", "zh"])
    
    # 运行时数据
    existing_files: List[str] = field(default_factory=list)
    existing_symbols: List[str] = field(default_factory=list)
    
    def t(self, key: str, **kwargs) -> str:
        """翻译快捷方法"""
        if self.i18n_context:
            return self.i18n_context.t(key, **kwargs)
        return key
```

### 2.3 扩展 TemplateCategory

```python
# devpal/core/templates/base.py（修改）

class TemplateCategory(Enum):
    CORE = "core"
    AUTH = "auth"
    DATABASE = "database"
    API = "api"
    WEB = "web"
    CLI = "cli"
    TEST = "test"
    DOCS = "docs"
    BUILD = "build"
    TOOLING = "tooling"        # 新增
    INSTALL = "install"        # 新增
```

### 2.4 安装脚本模板

#### 2.4.1 Bash 模板（`devpal/core/templates/install_script_templates.py`）

```python
from typing import List
from .base import BaseTemplate, TemplateContext, GeneratedFile, TemplateCategory
from .registry import registry
from .i18n.base import I18nContext, Locale
from .i18n.locales.en import EnglishMessages
from .i18n.locales.zh import ChineseMessages

@registry.register
class ClaudeCliInstallBashTemplate(BaseTemplate):
    """Claude CLI Bash 安装脚本模板"""
    
    name = "claude_cli_install_bash"
    description = "Claude Code CLI Bash installation script with i18n"
    category = TemplateCategory.INSTALL
    language = "generic"
    priority = 100
    
    def should_apply(self, context: TemplateContext) -> bool:
        return "claude_cli_installer" in context.features
    
    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        i18n = context.i18n_context or self._create_default_i18n()
        bash_script = self._generate_bash_script(context, i18n)
        
        return [GeneratedFile(
            path="scripts/install_claude_cli.sh",
            content=bash_script,
            description="Claude CLI Bash installation script"
        )]
    
    def _create_default_i18n(self) -> I18nContext:
        i18n = I18nContext(Locale.EN)
        i18n.register_catalog(Locale.EN, EnglishMessages())
        i18n.register_catalog(Locale.ZH, ChineseMessages())
        return i18n
    
    def _generate_bash_script(self, context: TemplateContext, i18n: I18nContext) -> str:
        # 收集所有语言的消息
        messages_by_locale = {}
        for locale in [Locale.EN, Locale.ZH]:
            i18n.locale = locale
            messages_by_locale[locale.value] = {
                key: i18n.t(key)
                for key in self._get_message_keys()
            }
        
        # 生成消息查找函数
        msg_function = self._generate_bash_msg_function(messages_by_locale)
        
        # 完整脚本（省略详细内容，见完整实现）
        script = f'''#!/bin/bash
# Generated by DevPalAgent
set -e

SCRIPT_LANG="en"
detect_language() {{ ... }}

{msg_function}

main() {{
    detect_language "$@"
    echo "$(msg 'install.welcome')"
    # ... 安装逻辑 ...
}}

main "$@"
'''
        return script
```

#### 2.4.2 Windows Batch 模板

```python
@registry.register
class ClaudeCliInstallBatchTemplate(BaseTemplate):
    """Claude CLI Windows Batch 安装脚本模板"""
    
    name = "claude_cli_install_batch"
    description = "Claude Code CLI Windows Batch installation script"
    category = TemplateCategory.INSTALL
    language = "generic"
    priority = 99
    
    def should_apply(self, context: TemplateContext) -> bool:
        return "claude_cli_installer" in context.features
    
    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        # 类似 Bash 模板，生成 .bat 脚本
        pass
```

#### 2.4.3 Python 跨平台模板

```python
@registry.register
class ClaudeCliInstallPythonTemplate(BaseTemplate):
    """Claude CLI Python 跨平台安装脚本模板"""
    
    name = "claude_cli_install_python"
    description = "Claude Code CLI Python cross-platform installation script"
    category = TemplateCategory.INSTALL
    language = "python"
    priority = 98
    
    def should_apply(self, context: TemplateContext) -> bool:
        return "claude_cli_installer" in context.features
    
    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        # 生成 Python 脚本，使用 subprocess 调用 npm
        pass
```

### 2.5 CLI 命令

```python
# devpal/cli/commands/generate_installer.py（新增）

import click
from pathlib import Path
from devpal.core.templates import registry, TemplateContext
from devpal.core.templates.i18n.base import I18nContext, Locale
from devpal.core.templates.i18n.locales.en import EnglishMessages
from devpal.core.templates.i18n.locales.zh import ChineseMessages

@click.command()
@click.option('--lang', multiple=True, default=['en', 'zh'],
              help='Target languages (en, zh, ja, ko)')
@click.option('--output-dir', default='scripts',
              help='Output directory')
def generate_installer(lang, output_dir):
    """Generate Claude CLI installation scripts"""
    
    # 创建 i18n 上下文
    i18n = I18nContext(Locale.EN)
    i18n.register_catalog(Locale.EN, EnglishMessages())
    i18n.register_catalog(Locale.ZH, ChineseMessages())
    
    # 创建模板上下文
    context = TemplateContext(
        project_name="claude_cli_installer",
        project_type="tooling",
        language="generic",
        features=["claude_cli_installer"],
        i18n_context=i18n,
        target_locales=list(lang)
    )
    
    # 生成文件
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    templates = [
        registry.get_template("claude_cli_install_bash"),
        registry.get_template("claude_cli_install_batch"),
        registry.get_template("claude_cli_install_python"),
    ]
    
    for template in templates:
        if template and template.should_apply(context):
            files = template.generate(context)
            for file in files:
                file_path = output_path.parent / file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file.content, encoding='utf-8')
                click.echo(f"✓ Generated: {file_path}")
```

---

## 3. 使用方式

### 3.1 CLI 命令

```bash
# 生成中英文安装脚本
python -m devpal.cli.commands.generate_installer --lang=en --lang=zh

# 生成所有语言
python -m devpal.cli.commands.generate_installer --lang=en --lang=zh --lang=ja --lang=ko

# 指定输出目录
python -m devpal.cli.commands.generate_installer --output-dir=dist/scripts
```

### 3.2 集成到 Phase 2（可选）

```python
# devpal/core/openspec_phases/phase2_create_structure.py（修改）

def execute(self, context: OpenSpecContext) -> PhaseResult:
    # ... 现有逻辑 ...
    
    # 如果需求中包含 "安装脚本" 关键词，生成安装脚本
    if self._should_generate_installer(context):
        self._generate_installer_scripts(context)
    
    return PhaseResult(success=True)

def _should_generate_installer(self, context: OpenSpecContext) -> bool:
    # 检查需求文档中是否提到 "安装脚本"、"installer"、"部署工具" 等关键词
    pass

def _generate_installer_scripts(self, context: OpenSpecContext):
    from devpal.core.templates import registry, TemplateContext
    from devpal.core.templates.i18n.base import I18nContext, Locale
    
    # 创建模板上下文并生成
    pass
```

---

## 4. 实现计划

### 4.1 任务分解

| 任务 | 文件 | 工作量 | 优先级 |
|------|------|--------|--------|
| **P0 - i18n 基础设施** | | | |
| 创建 i18n 核心类 | `devpal/core/templates/i18n/base.py` | 2 小时 | P0 |
| 英文消息定义 | `devpal/core/templates/i18n/locales/en.py` | 1 小时 | P0 |
| 中文消息定义 | `devpal/core/templates/i18n/locales/zh.py` | 1 小时 | P0 |
| 扩展 TemplateContext | `devpal/core/templates/base.py` | 30 分钟 | P0 |
| **P1 - 模板实现** | | | |
| Bash 脚本模板 | `devpal/core/templates/install_script_templates.py` | 4 小时 | P1 |
| Batch 脚本模板 | 同上 | 3 小时 | P1 |
| Python 脚本模板 | 同上 | 3 小时 | P1 |
| README 模板 | 同上 | 1 小时 | P1 |
| **P2 - CLI 集成** | | | |
| CLI 命令实现 | `devpal/cli/commands/generate_installer.py` | 2 小时 | P2 |
| 单元测试 | `tests/templates/test_install_templates.py` | 3 小时 | P2 |
| **P3 - 文档与扩展** | | | |
| 日语消息 | `devpal/core/templates/i18n/locales/ja.py` | 1 小时 | P3 |
| 韩语消息 | `devpal/core/templates/i18n/locales/ko.py` | 1 小时 | P3 |
| 使用文档 | `docs/install_script_generation.md` | 2 小时 | P3 |

**总计**：约 24 小时（3 个工作日）

### 4.2 执行顺序

```
Day 1（8 小时）
├── P0.1  创建 i18n 核心类                [2h]
├── P0.2  英文消息定义                    [1h]
├── P0.3  中文消息定义                    [1h]
├── P0.4  扩展 TemplateContext            [0.5h]
└── P1.1  Bash 脚本模板（部分）           [3.5h]

Day 2（8 小时）
├── P1.1  Bash 脚本模板（完成）           [0.5h]
├── P1.2  Batch 脚本模板                  [3h]
├── P1.3  Python 脚本模板                 [3h]
└── P1.4  README 模板                     [1h]
└── P2.1  CLI 命令实现（部分）            [0.5h]

Day 3（8 小时）
├── P2.1  CLI 命令实现（完成）            [1.5h]
├── P2.2  单元测试                        [3h]
├── P3.1  日语消息                        [1h]
├── P3.2  韩语消息                        [1h]
└── P3.3  使用文档                        [1.5h]
```

---

## 5. 测试计划

### 5.1 单元测试

```python
# tests/templates/test_install_templates.py

def test_i18n_context():
    """测试 i18n 上下文"""
    i18n = I18nContext(Locale.EN)
    i18n.register_catalog(Locale.EN, EnglishMessages())
    i18n.register_catalog(Locale.ZH, ChineseMessages())
    
    # 英文
    assert i18n.t("install.welcome") == "Welcome to Claude Code CLI One-Click Installer"
    
    # 中文
    i18n.locale = Locale.ZH
    assert i18n.t("install.welcome") == "欢迎使用 Claude Code CLI 一键安装脚本"
    
    # 变量替换
    assert i18n.t("install.node_found", version="18.0.0") == "✓ 已找到 Node.js: 18.0.0"

def test_bash_template_generation():
    """测试 Bash 模板生成"""
    context = TemplateContext(
        project_name="test",
        features=["claude_cli_installer"]
    )
    
    template = ClaudeCliInstallBashTemplate()
    files = template.generate(context)
    
    assert len(files) == 1
    assert files[0].path == "scripts/install_claude_cli.sh"
    assert "#!/bin/bash" in files[0].content
    assert "msg()" in files[0].content

def test_batch_template_generation():
    """测试 Batch 模板生成"""
    # 类似 Bash 测试
    pass

def test_python_template_generation():
    """测试 Python 模板生成"""
    # 类似 Bash 测试
    pass
```

### 5.2 集成测试

```bash
# 生成脚本
python -m devpal.cli.commands.generate_installer --lang=en --lang=zh

# 测试 Bash 脚本
cd scripts
chmod +x install_claude_cli.sh

# 英文
./install_claude_cli.sh --lang=en

# 中文
./install_claude_cli.sh --lang=zh

# 测试 Batch 脚本（Windows）
install_claude_cli.bat --lang=zh

# 测试 Python 脚本
python install_claude_cli.py --lang=en
```

---

## 6. 优势与权衡

### 6.1 优势

| 优势 | 说明 |
|------|------|
| **统一架构** | 与 DevPalAgent 现有模板系统无缝集成 |
| **可扩展性** | 添加新语言只需新增 `locales/xx.py` |
| **可复用性** | i18n 框架可供其他模板使用（如 README、文档生成） |
| **类型安全** | 使用 Python 类型提示，IDE 友好 |
| **测试友好** | 纯 Python 实现，易于单元测试 |
| **多平台支持** | 同时生成 Bash/Batch/Python 三种脚本 |

### 6.2 权衡

| 权衡 | 说明 | 缓解措施 |
|------|------|----------|
| **复杂度增加** | 相比独立脚本，架构更复杂 | 清晰的文档和示例 |
| **依赖 DevPalAgent** | 无法独立分发脚本 | 生成的脚本本身是独立的 |
| **学习曲线** | 需要理解模板系统 | 提供 CLI 命令简化使用 |

---

## 7. 未来扩展

### 7.1 短期（1-2 周）

- [ ] 支持更多语言（日语、韩语）
- [ ] 添加 `--mirror` 参数支持国内镜像源
- [ ] 生成 Docker 安装脚本

### 7.2 中期（1-2 月）

- [ ] 将 i18n 框架应用到其他模板（README、文档生成）
- [ ] 支持自定义消息覆盖（用户提供 `custom_messages.json`）
- [ ] 生成 GUI 安装向导（Electron）

### 7.3 长期（3+ 月）

- [ ] 集成到 Phase 2，自动检测需求中的安装脚本需求
- [ ] 支持插件式消息扩展（第三方语言包）
- [ ] 生成 Homebrew/Chocolatey 包管理器配置

---

## 8. 总结

本方案将 Claude CLI 安装脚本生成功能深度集成到 DevPalAgent 的 P3.2 多语言框架中，通过新建统一的 i18n 基础设施，实现了：

1. **架构统一**：与现有模板系统无缝集成
2. **多平台支持**：Bash、Batch、Python 三种脚本
3. **多语言支持**：中英日韩四种语言，可扩展
4. **可复用性**：i18n 框架可供其他模板使用
5. **易用性**：提供 CLI 命令，一键生成

**下一步行动**：
1. 审核本方案
2. 开始实现 P0 任务（i18n 基础设施）
3. 实现 P1 任务（模板）
4. 实现 P2 任务（CLI 集成）
5. 编写测试和文档
