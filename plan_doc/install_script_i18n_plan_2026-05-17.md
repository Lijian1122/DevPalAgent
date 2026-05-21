# 一键安装 Claude Code CLI 脚本 - 基于 P3.2 多语言框架实现方案

**日期**：2026-05-17  
**作者**：DevPalAgent 规划  
**状态**：设计阶段（已更新为 P3.2 集成方案）

---

## 1. 项目概述

### 1.1 目标

**将安装脚本生成集成到 DevPalAgent 的 P3.2 多语言框架中**，通过模板系统生成跨平台的 Claude Code CLI 一键安装脚本，并提供多语言用户界面支持。

### 1.2 核心需求

| 需求 | 说明 |
|------|------|
| **安装目标** | `@anthropic-ai/claude-code` npm 包（最新版本 2.1.143） |
| **支持平台** | Windows（.bat）、Linux/macOS（.sh）、Python 跨平台脚本 |
| **多语言** | 中文（zh）、英文（en），可扩展日语（ja）、韩语（ko） |
| **集成方式** | 基于 DevPalAgent 的模板系统（`devpal/core/templates/`） |
| **i18n 框架** | 新建统一的 i18n 基础设施，供所有模板使用 |

### 1.3 与 P3.2 的关系（重新定义）

**原方案**：安装脚本与 P3.2 完全独立

**新方案**：安装脚本生成集成到 P3.2 框架中

| 组件 | 用途 | 关系 |
|------|------|------|
| **语言插件** (`devpal/core/schema/languages/`) | 代码分析（AST、符号、依赖） | 用于 Phase 4-10 分析生成的代码 |
| **模板系统** (`devpal/core/templates/`) | 代码生成（脚手架、样板代码） | **安装脚本作为新模板类型** |
| **i18n 系统** (`devpal/core/templates/i18n/`) | **新增**：消息翻译基础设施 | 供所有需要多语言输出的模板使用 |
| **P3.2 多语言支持** | C++/Python/Go 项目生成 | 与安装脚本生成并行，共享 i18n 框架 |

---

## 2. 技术架构

### 2.1 文件结构

```
DevPalAgent/
├── devpal/
│   ├── core/
│   │   ├── templates/
│   │   │   ├── base.py                         # 现有 - 扩展 TemplateContext 支持 i18n
│   │   │   ├── registry.py                     # 现有 - 模板注册系统
│   │   │   ├── cpp_templates.py                # 现有 - C++ 模板
│   │   │   ├── python_templates.py             # 现有 - Python 模板
│   │   │   ├── install_script_templates.py     # 新增 - 安装脚本模板
│   │   │   └── i18n/                           # 新增 - i18n 基础设施
│   │   │       ├── __init__.py
│   │   │       ├── base.py                     # i18n 核心类（Locale, MessageCatalog, I18nContext）
│   │   │       └── locales/                    # 语言包
│   │   │           ├── __init__.py
│   │   │           ├── en.py                   # 英文消息
│   │   │           ├── zh.py                   # 中文消息
│   │   │           ├── ja.py                   # 日语消息（可选）
│   │   │           └── ko.py                   # 韩语消息（可选）
│   │   └── schema/
│   │       └── languages/
│   │           ├── base.py                     # 现有 - 语言插件基类（用于代码分析）
│   │           ├── cpp_plugin.py               # 现有 - C++ 插件
│   │           └── python_plugin.py            # 未来 - Python 插件
│   └── cli/
│       └── commands/
│           └── generate_installer.py           # 新增 - CLI 命令
├── scripts/                                    # 生成输出目录
│   ├── install_claude_cli.sh                  # 生成 - Bash 脚本
│   ├── install_claude_cli.bat                 # 生成 - Batch 脚本
│   ├── install_claude_cli.py                  # 生成 - Python 跨平台脚本
│   └── README_INSTALL.md                      # 生成 - 使用文档
└── plan_doc/
    └── install_script_i18n_plan_2026-05-17.md # 本文档
```

### 2.2 架构设计原则

#### 关注点分离

| 组件 | 职责 | 使用场景 |
|------|------|----------|
| **语言插件** (`languages/`) | 代码分析（AST、符号、依赖） | Phase 4-10 分析生成的 C++/Python 代码 |
| **模板系统** (`templates/`) | 代码生成（脚手架、样板） | Phase 2, 4 生成项目文件 |
| **i18n 系统** (`templates/i18n/`) | 消息翻译 | 所有需要多语言输出的模板 |
| **安装脚本模板** | 生成部署工具 | 独立 CLI 命令或 Phase 2 可选功能 |

#### 扩展 TemplateCategory 枚举

```python
# devpal/core/templates/base.py（修改）

class TemplateCategory(Enum):
    """模板分类"""
    CORE = "core"              # 核心功能
    AUTH = "auth"              # 认证系统
    DATABASE = "database"      # 数据库
    API = "api"                # API 服务
    WEB = "web"                # Web 应用
    CLI = "cli"                # 命令行工具
    TEST = "test"              # 测试
    DOCS = "docs"              # 文档
    BUILD = "build"            # 构建配置
    TOOLING = "tooling"        # 新增 - 开发工具/脚本
    INSTALL = "install"        # 新增 - 安装脚本
```

### 2.3 i18n 基础设施设计

#### 核心类设计

```python
# devpal/core/templates/i18n/base.py（新增）

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
        """获取单条消息"""
        messages = self.get_messages()
        return messages.get(key, default or key)

class I18nContext:
    """i18n 上下文 - 管理当前语言和消息查找"""
    
    def __init__(self, locale: Locale = Locale.EN):
        self.locale = locale
        self._catalogs: Dict[Locale, MessageCatalog] = {}
    
    def register_catalog(self, locale: Locale, catalog: MessageCatalog):
        """注册语言目录"""
        self._catalogs[locale] = catalog
    
    def t(self, key: str, **kwargs) -> str:
        """翻译函数（支持变量替换）"""
        catalog = self._catalogs.get(self.locale)
        if not catalog:
            return key
        
        message = catalog.get(key)
        # 支持 {variable} 格式的变量替换
        if kwargs:
            try:
                message = message.format(**kwargs)
            except KeyError:
                pass
        return message
```

#### 扩展 TemplateContext

```python
# devpal/core/templates/base.py（修改）

from typing import Optional
from .i18n.base import I18nContext

@dataclass
class TemplateContext:
    """模板渲染上下文"""
    project_name: str
    project_type: str = "generic"
    language: str = "cpp"      # cpp, python, rust, go
    features: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)
    
    # 新增 - i18n 支持
    i18n_context: Optional[I18nContext] = None
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

---

## 3. 核心功能模块

### 3.1 语言检测模块

**检测优先级**：
1. 命令行参数：`--lang=zh` 或 `--lang=en`
2. 环境变量：`$LANG`（Linux/macOS）或 `%LANG%`（Windows）
3. 默认值：`en`

**实现逻辑**：
- Bash：正则匹配 `$LANG` 是否以 `zh` 开头
- Batch：字符串分割 `%LANG%` 取第一段

### 3.2 依赖检测模块

| 依赖 | 检测命令 | 安装策略 |
|------|----------|----------|
| **Node.js** | `node --version` | 提示用户下载官方安装包 |
| **npm** | `npm --version` | 随 Node.js 自动安装 |
| **curl/wget** | `which curl` | 用于下载（Linux/macOS） |

**最低版本要求**：
- Node.js >= 18.0.0
- npm >= 8.0.0

**安装策略**：
- **Linux/macOS**：提示使用包管理器（apt/yum/brew）或下载二进制包
- **Windows**：打开 Node.js 官方下载页面（https://nodejs.org）

### 3.3 Claude CLI 安装模块

```bash
# 全局安装
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
```

**错误处理**：
- **权限不足**：提示使用 `sudo`（Linux/macOS）或管理员权限（Windows）
- **网络错误**：提示检查网络连接或使用镜像源
- **版本冲突**：检测已安装版本，提示升级或重新安装

### 3.4 API Key 配置模块（可选）

**交互式配置**：
```bash
# 提示用户输入
read -sp "$(msg 'enter_api_key'): " api_key

# 写入环境变量
echo "export ANTHROPIC_API_KEY=$api_key" >> ~/.bashrc  # Linux/macOS
setx ANTHROPIC_API_KEY "%api_key%"                     # Windows
```

**验证**：
- 提示用户运行 `claude` 命令测试 API Key 是否有效

---

## 4. 消息键值对清单

需要翻译的消息（共 20 条）：

| 消息键 | 中文 | 英文 |
|--------|------|------|
| `welcome` | 欢迎使用 Claude Code CLI 一键安装脚本 | Welcome to Claude Code CLI One-Click Installer |
| `check_node` | 检查 Node.js 安装状态... | Checking Node.js installation... |
| `node_found` | ✓ 已找到 Node.js | ✓ Node.js found |
| `node_missing` | ✗ 未找到 Node.js | ✗ Node.js not found |
| `node_version_low` | ✗ Node.js 版本过低（需要 >= 18.0.0） | ✗ Node.js version too old (requires >= 18.0.0) |
| `npm_missing` | ✗ 未找到 npm | ✗ npm not found |
| `install_cli` | 正在安装 Claude Code CLI... | Installing Claude Code CLI... |
| `success` | ✓ 安装成功！ | ✓ Installation successful! |
| `failed` | ✗ 安装失败 | ✗ Installation failed |
| `config_api_key_prompt` | 是否现在配置 API Key？ | Configure API Key now? |
| `enter_api_key` | 请输入您的 Anthropic API Key | Enter your Anthropic API Key |
| `api_key_saved` | ✓ API Key 已保存到环境变量 | ✓ API Key saved to environment |
| `done` | 安装完成！运行 'claude' 开始使用 | Installation complete! Run 'claude' to start |
| `download_node` | 正在打开 Node.js 下载页面... | Opening Node.js download page... |
| `manual_install` | 请手动安装 Node.js 后重新运行此脚本 | Please install Node.js manually and re-run this script |
| `permission_denied` | ✗ 权限不足，请使用管理员权限运行 | ✗ Permission denied, run as administrator |
| `network_error` | ✗ 网络错误，请检查网络连接 | ✗ Network error, check your connection |
| `already_installed` | ✓ Claude CLI 已安装 | ✓ Claude CLI already installed |
| `upgrade_prompt` | 发现新版本，是否升级？ | New version available, upgrade? |
| `usage` | 用法：./install_claude_cli.sh [--lang=zh\|en] | Usage: ./install_claude_cli.sh [--lang=zh\|en] |

---

## 5. 脚本流程图

```
开始
  │
  ├─ 检测语言（--lang 参数 / $LANG 环境变量）
  │
  ├─ 显示欢迎信息
  │
  ├─ 检查 Node.js
  │   ├─ 已安装 → 检查版本
  │   │   ├─ 版本符合 → 继续
  │   │   └─ 版本过低 → 提示升级
  │   └─ 未安装 → 提示下载安装
  │
  ├─ 检查 npm
  │   ├─ 已安装 → 继续
  │   └─ 未安装 → 错误退出
  │
  ├─ 安装 Claude CLI
  │   ├─ npm install -g @anthropic-ai/claude-code
  │   ├─ 成功 → 显示版本信息
  │   └─ 失败 → 错误处理（权限/网络）
  │
  ├─ 配置 API Key（可选）
  │   ├─ 用户选择 Yes → 输入 API Key → 写入环境变量
  │   └─ 用户选择 No → 跳过
  │
  └─ 显示完成信息
```

---

## 6. 测试计划

### 6.1 测试场景

#### 场景 1：语言切换测试

```bash
# 测试中文
./install_claude_cli.sh --lang=zh

# 测试英文
./install_claude_cli.sh --lang=en

# 测试环境变量
export LANG=zh_CN.UTF-8
./install_claude_cli.sh

# 测试默认（无参数）
unset LANG
./install_claude_cli.sh
```

**预期结果**：
- 所有提示信息以正确语言显示
- 无乱码（UTF-8 编码正确）

#### 场景 2：依赖检测测试

```bash
# 模拟 Node.js 未安装
sudo mv /usr/bin/node /usr/bin/node.bak
./install_claude_cli.sh
# 预期：显示 "✗ 未找到 Node.js" 并提示下载

# 模拟 Node.js 版本过低
# 预期：显示 "✗ Node.js 版本过低（需要 >= 18.0.0）"
```

#### 场景 3：安装流程测试

```bash
# 全新安装
npm uninstall -g @anthropic-ai/claude-code
./install_claude_cli.sh
# 预期：成功安装，显示版本号

# 升级安装（已有旧版本）
npm install -g @anthropic-ai/claude-code@2.0.0
./install_claude_cli.sh
# 预期：检测到旧版本，提示升级

# 验证安装
claude --version
which claude
```

#### 场景 4：API Key 配置测试

```bash
# 测试环境变量写入
./install_claude_cli.sh
# 选择 Yes → 输入 API Key
source ~/.bashrc
echo $ANTHROPIC_API_KEY
# 预期：显示刚才输入的 API Key
```

### 6.2 验收标准

- [ ] 中英文消息显示正确，无乱码
- [ ] 语言检测逻辑正确（参数 > 环境变量 > 默认）
- [ ] Node.js 检测和版本检查正常
- [ ] Claude CLI 安装成功，`claude --version` 可执行
- [ ] API Key 配置可选，写入环境变量成功
- [ ] 错误处理友好（权限、网络、版本冲突）
- [ ] 跨平台兼容（Linux/macOS/Windows）

---

## 7. 扩展性设计

### 7.1 支持更多语言

添加新语言只需修改 `msg()` 函数：

**Bash 脚本**：
```bash
msg() {
    local key="$1"
    case "$SCRIPT_LANG" in
        zh) ... ;;
        en) ... ;;
        ja)  # 新增日语
            case "$key" in
                "welcome") echo "Claude Code CLI ワンクリックインストーラーへようこそ" ;;
                "check_node") echo "Node.js のインストール状態を確認しています..." ;;
                # ... 其他消息 ...
            esac
            ;;
        ko)  # 新增韩语
            case "$key" in
                "welcome") echo "Claude Code CLI 원클릭 설치 프로그램에 오신 것을 환영합니다" ;;
                "check_node") echo "Node.js 설치 상태 확인 중..." ;;
                # ... 其他消息 ...
            esac
            ;;
    esac
}
```

**Batch 脚本**：
```batch
:load_messages_ja
set "MSG_WELCOME=Claude Code CLI ワンクリックインストーラーへようこそ"
set "MSG_CHECK_NODE=Node.js のインストール状態を確認しています..."
exit /b

:load_messages_ko
set "MSG_WELCOME=Claude Code CLI 원클릭 설치 프로그램에 오신 것을 환영합니다"
set "MSG_CHECK_NODE=Node.js 설치 상태 확인 중..."
exit /b
```

### 7.2 配置文件外部化（可选）

如果消息数量增长到 50+ 条，可考虑外部化为配置文件：

```bash
# messages_zh.txt
welcome=欢迎使用 Claude Code CLI 一键安装脚本
check_node=检查 Node.js 安装状态...
node_found=✓ 已找到 Node.js
# ...

# 加载函数
declare -A MESSAGES
load_messages() {
    while IFS='=' read -r key value; do
        MESSAGES["$key"]="$value"
    done < "messages_${SCRIPT_LANG}.txt"
}

msg() {
    echo "${MESSAGES[$1]}"
}
```

**优点**：
- 消息与代码分离
- 易于翻译人员协作
- 支持热更新

**缺点**：
- 增加文件依赖
- 需要处理文件路径问题

---

## 8. 时间估算

| 任务 | 耗时 | 负责人 |
|------|------|--------|
| Bash 脚本开发（含 i18n） | 3 小时 | 开发者 |
| Windows 批处理开发（含 i18n） | 2.5 小时 | 开发者 |
| 消息翻译（20 条 × 2 语言） | 30 分钟 | 翻译/开发者 |
| 测试（4 场景 × 2 平台） | 2 小时 | 测试/开发者 |
| 文档编写（README_INSTALL.md） | 1 小时 | 开发者 |
| **总计** | **9 小时** | - |

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **Node.js 安装失败** | 用户无法继续安装 | 提供详细的手动安装指南链接 |
| **npm 权限问题** | 安装失败 | 检测权限错误，提示使用 sudo 或管理员权限 |
| **网络连接问题** | npm install 超时 | 提示使用国内镜像源（如 cnpm、淘宝镜像） |
| **UTF-8 编码问题** | Windows 中文乱码 | 使用 `chcp 65001` 设置 UTF-8 编码 |
| **环境变量未生效** | API Key 配置失败 | 提示用户重启终端或手动 source 配置文件 |

---

## 10. 使用示例

### 10.1 Linux/macOS

```bash
# 下载脚本
curl -O https://raw.githubusercontent.com/xxx/DevPalAgent/master/scripts/install_claude_cli.sh
chmod +x install_claude_cli.sh

# 中文安装
./install_claude_cli.sh --lang=zh

# 英文安装
./install_claude_cli.sh --lang=en

# 自动检测语言（根据 $LANG 环境变量）
./install_claude_cli.sh
```

### 10.2 Windows

```batch
REM 下载脚本
curl -O https://raw.githubusercontent.com/xxx/DevPalAgent/master/scripts/install_claude_cli.bat

REM 中文安装
install_claude_cli.bat --lang=zh

REM 英文安装
install_claude_cli.bat --lang=en
```

---

## 11. 后续优化方向

### 11.1 短期优化（1-2 周）

- [ ] 添加 `--mirror` 参数支持国内镜像源
- [ ] 添加 `--skip-api-key` 参数跳过 API Key 配置
- [ ] 添加 `--version` 参数指定安装特定版本的 Claude CLI
- [ ] 添加卸载功能（`--uninstall`）

### 11.2 中期优化（1-2 月）

- [ ] 支持日语、韩语
- [ ] 添加自动更新检测功能
- [ ] 生成安装日志文件（`install.log`）
- [ ] 支持离线安装（预下载 npm 包）

### 11.3 长期优化（3+ 月）

- [ ] 开发 GUI 安装向导（Electron 或 Web 界面）
- [ ] 集成到 DevPalAgent 主流程（`run_ai_flow.py --setup`）
- [ ] 支持 Docker 容器化安装
- [ ] 提供 Homebrew/Chocolatey 包管理器支持

---

## 12. 参考资料

- [Claude Code CLI 官方文档](https://docs.anthropic.com/claude/docs/claude-code)
- [npm 全局安装指南](https://docs.npmjs.com/downloading-and-installing-packages-globally)
- [Bash 国际化最佳实践](https://www.gnu.org/software/gettext/manual/html_node/sh.html)
- [Windows 批处理 UTF-8 编码](https://docs.microsoft.com/en-us/windows/console/console-code-pages)

---

## 13. 总结

本方案提供了一个轻量级、可扩展的 i18n 实现方案，适合小型脚本项目。核心优势：

1. **零依赖**：不需要 gettext、i18next 等外部库
2. **简单直接**：函数式消息查找，易于理解和维护
3. **易扩展**：添加新语言只需增加 case 分支
4. **跨平台**：Bash 和 Batch 使用相同的设计模式

实现后，用户可以通过以下方式使用：

```bash
# Linux/macOS
./scripts/install_claude_cli.sh --lang=zh

# Windows
scripts\install_claude_cli.bat --lang=zh
```

**下一步行动**：
1. 审核本方案文档
2. 开始实现 Bash 脚本（`install_claude_cli.sh`）
3. 开始实现 Windows 批处理脚本（`install_claude_cli.bat`）
4. 编写使用文档（`README_INSTALL.md`）
5. 执行测试计划
