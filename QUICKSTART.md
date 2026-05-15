# DevPal Agent - 快速开始指南

## 系统状态

✅ **OpenSpec 架构组件全部实现并通过测试**

| 组件 | 状态 | 测试通过 |
|------|------|----------|
| Validation Engine (四层验证) | ✅ 完成 | 4/4 |
| Delta Spec (增量变更机制) | ✅ 完成 | 3/3 |
| Artifact Graph (工件依赖图) | ✅ 完成 | 4/4 |
| Workflow Engine (声明式工作流) | ✅ 完成 | 3/3 |
| Requirements Management (需求管理) | ✅ 完成 | 2/2 |
| EventBus (事件总线) | ✅ 完成 | 5/5 |
| SpecEngine (规范引擎) | ✅ 完成 | - |
| Diagnostic Engine (诊断引擎) | ✅ 完成 | - |
| Config Policy (配置策略) | ✅ 完成 | - |
| Rollout Engine (发布引擎) | ✅ 完成 | - |
| Error Manager (错误管理) | ✅ 完成 | - |
| C/C++ Language Plugin | ✅ 完成 | 9/9 |

## 快速开始

### 1. 运行完整 OpenSpec 演示

```bash
python run_demo.py
```

这将执行完整的 7 阶段规范驱动开发工作流：
- **Phase 1**: 初始化 OpenSpec 上下文
- **Phase 2**: 解析需求文档 (`requirements/login_requirements.md`)
- **Phase 3**: 分析项目工件
- **Phase 4**: C++ 代码质量检查
- **Phase 5**: 构建项目依赖图
- **Phase 6**: 执行规范验证流水线
- **Phase 7**: 生成最终验证报告

### 2. 运行集成测试

```bash
# Phase 4 测试 (闭环集成)
python test_openspec_phase4_integration.py

# Phase 6 测试 (C/C++ 多语言支持)
python test_openspec_phase6_integration.py
```

### 3. 交互模式

```bash
python -m devpal.main
```

### 4. 运行 OpenSpec 11 阶段生成流程

推荐使用 `run_ai_flow.py` 作为稳定的完整链路验证入口：

```bash
python run_ai_flow.py -r requirements/simple_login.md
```

为了节省 token，`run_ai_flow.py` 默认采用“复用已有业务代码”策略：

- 如果生成项目中已经存在业务代码，Phase 4 不会再次调用 AI 重新生成代码。
- 后续仍会继续执行文档、审查、编译、测试和最终报告阶段。
- 这个默认跳过策略 **只在 `run_ai_flow.py` 入口生效**。
- 其他入口（例如交互模式 `python -m devpal.main`）仍保持默认重新生成行为，避免因为复用旧代码掩盖问题。

如果你希望强制重新生成业务代码，使用：

```bash
python run_ai_flow.py -r requirements/simple_login.md --force-regenerate-code
```

| 命令 | Phase 4 行为 |
|------|--------------|
| `python run_ai_flow.py -r requirements/simple_login.md` | 已有业务代码时跳过 AI 重新生成，节省 token |
| `python run_ai_flow.py -r requirements/simple_login.md --force-regenerate-code` | 即使业务代码已存在，也强制调用 AI 重新生成 |
| `python -m devpal.main` | 不受该节省 token 策略影响，默认走完整重新生成流程 |

## 如何使用需求文档驱动流程

### 步骤 1: 创建需求文档

在 `requirements/` 目录下创建 `.md` 文件，格式如下：

```markdown
---
title: "你的项目需求"
version: "1.0"
---

## REQ-001: 用户登录功能

**描述**: 用户可以通过用户名和密码登录系统

**验收标准**:
- [ ] 用户名长度 4-20 字符
- [ ] 密码长度至少 8 位
- [ ] 支持手机号/邮箱两种登录方式
- [ ] 登录失败 5 次后锁定账户
- [ ] 登录成功后跳转首页

## REQ-002: 密码重置功能

**描述**: 用户可以通过邮箱重置密码

**验收标准**:
- [ ] 发送重置链接到注册邮箱
- [ ] 链接 30 分钟内有效
- [ ] 新密码强度验证
```

### 步骤 2: 修改演示脚本

编辑 `run_demo.py` 中的 `req_file` 变量指向你的需求文档。

### 步骤 3: 运行演示

```bash
python run_demo.py
```

## C++ 登录系统 (c_login_system/)

项目中包含一个完整的 C++ 登录系统示例，用于演示 OpenSpec 的代码质量检查功能。

### 编译方法

```bash
cd c_login_system
mkdir build
cd build
cmake ..
make
```

或使用 g++ 直接编译：

```bash
cd c_login_system
g++ -std=c++17 -I include src/*.cpp -o login_system.exe
```

### 系统特性

- 盐化密码哈希 (1000 次迭代 SHA-256)
- 常量时间密码验证 (防止时序攻击)
- 线程安全的单例 UserManager
- 用户角色权限系统
- 文件持久化存储

## 项目架构

```
DevPalAgent/
├── devpal/
│   ├── core/
│   │   ├── schema/              # OpenSpec 架构核心
│   │   │   ├── __init__.py
│   │   │   ├── validation_engine.py    # 四层验证引擎
│   │   │   ├── delta_spec.py           # 增量变更机制
│   │   │   ├── artifact_graph.py       # 工件依赖图
│   │   │   ├── workflow.py             # 声明式工作流
│   │   │   ├── requirements.py         # 需求文档管理
│   │   │   ├── event_bus.py            # 事件总线
│   │   │   ├── spec.py                 # 规范引擎
│   │   │   ├── diagnostic_engine.py    # 诊断引擎 (Phase 5)
│   │   │   ├── config_policy.py        # 配置策略 (Phase 5)
│   │   │   ├── rollout_engine.py       # 发布引擎 (Phase 5)
│   │   │   ├── error_manager.py        # 错误管理 (Phase 5)
│   │   │   ├── compile_db.py           # 编译数据库 (Phase 6)
│   │   │   └── languages/              # 多语言插件 (Phase 6)
│   │   │       ├── base.py
│   │   │       ├── cpp_plugin.py
│   │   │       └── cpp_rules.py
│   │   ├── agent_engine.py
│   │   ├── planner.py
│   │   └── reflector.py
│   └── tools/                   # 20+ AI 工具
├── requirements/                # 需求文档目录
│   └── login_requirements.md
├── c_login_system/              # C++ 登录系统示例
├── run_demo.py                  # OpenSpec 完整演示
├── test_openspec_phase4_integration.py
└── test_openspec_phase6_integration.py
```

## 下一步

1. 修改 `requirements/login_requirements.md` 定制你的需求
2. 运行 `python run_demo.py` 查看验证结果
3. 使用交互模式 `python -m devpal.main` 进行 AI 辅助开发
