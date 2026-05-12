# C++ 用户登录认证系统

> **版本**: 1.0
> **生成方式**: DevPal Agent OpenSpec
> **生成时间**: 2026-05-11

## 项目概述

完整的 C++ 用户认证系统，基于需求文档实现了所有 3 个核心需求：

- **REQ-001**: 基础登录功能（用户名/密码验证、账户锁定）
- **REQ-002**: 验证码功能（4位图形验证码）
- **REQ-003**: 记住登录状态（7天会话有效期）

## 功能特性

### REQ-001: 基础登录功能
- 用户名长度限制：4-20 字符
- 密码强度验证：至少 8 字符，包含字母和数字
- 登录成功返回会话 ID
- 连续 3 次登录失败后锁定账户 10 分钟

### REQ-002: 验证码功能
- 4 位字母数字组合验证码
- 不区分大小写验证
- 常量时间比较防止时序攻击

### REQ-003: 记住登录状态
- "记住我" 复选框支持
- 勾选后会话有效期 7 天
- 未勾选时会话有效期 30 分钟

## 项目结构

```
cpp_login_system/
├── include/
│   └── auth.h              # 核心头文件
├── src/
│   ├── auth.cpp           # 认证系统实现
│   └── main.cpp           # 主程序入口
├── tests/
│   └── test_auth.cpp      # 完整测试套件
├── docs/
│   ├── 技术实现文档.md
│   └── 测试文档.md
└── CMakeLists.txt
```

## 构建说明

### 环境要求
- Windows 10/11
- Visual Studio 2019+
- CMake 3.10+
- C++17 标准支持

### 编译步骤
```bash
mkdir build && cd build
cmake .. -G "Visual Studio 16 2019" -A x64
cmake --build . --config Release
```

### 运行程序
```bash
bin/Release/auth_system.exe
```
