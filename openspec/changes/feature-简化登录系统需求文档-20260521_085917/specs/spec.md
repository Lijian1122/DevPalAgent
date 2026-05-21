# Specification Delta

Generated: 2026-05-21T08:59:17.307317

## ADDED Requirements

### REQ-001: 项目概述

实现一个简单的用户登录系统，仅包含核心功能。

---

### REQ-002: 功能需求

### REQ-001: 用户登录
- 用户可以使用用户名和密码登录
- 用户名：3-20个字符，仅允许字母、数字、下划线
- 密码：8-32个字符，必须包含字母和数字
- 登录失败3次后，账户锁定10分钟

---

### REQ-003: 核心类设计（仅3个类）

### 1. User（用户实体）
- 属性：username, passwordHash, salt, failedLoginCount, lockoutEndTime
- 方法：构造函数
### 2. LoginService（登录服务）
- 方法：login(username, password) -> LoginResult
- 方法：isAccountLocked(username) -> bool
- 方法：recordFailedAttempt(username)
- 方法：resetFailedAttempts(username)
### 3. UserRepository（用户数据访问）
- 方法：findByUsername(username) -> User*
- 方法：save(user)
- 方法：updateFailedAttempts(username, count)

---

### REQ-004: 技术约束

- C++17 标准库
- 不使用第三方库
- 每个类一个 .h 和 .cpp 文件
- 提供 main.cpp 演示登录流程
- 提供至少一个测试文件

---
