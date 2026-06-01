# 技术设计文档

## 1. 系统架构概览

本系统为基于 C++17 STL 的简化用户登录系统，采用三层结构：

- **实体层**：`User` 表示用户账户状态与认证相关数据。
- **数据访问层**：`UserRepository` 负责用户数据的查询、保存和失败次数更新。
- **业务服务层**：`LoginService` 负责登录校验、账户锁定判断、失败次数记录与重置。

数据流：

1. `main.cpp` 或测试用例调用 `LoginService::login(username, password)`。
2. `LoginService` 校验用户名和密码格式。
3. `LoginService` 通过 `UserRepository::findByUsername()` 查询用户。
4. 若用户不存在或密码错误，记录失败次数。
5. 连续失败达到 3 次时，设置锁定结束时间为当前时间后 10 分钟。
6. 登录成功后重置失败次数与锁定状态。
7. `UserRepository::save()` 持久化用户状态。

系统采用内存仓储实现，满足演示与测试需求；后续可替换为文件或数据库持久化实现。

## 2. 核心模块清单

- **User**
  - 职责：保存用户认证信息与账户锁定状态。
  - 关键类：`User`
  - 关键成员：`username`、`password_hash`、`salt`、`failed_login_count`、`lockout_end_time`
  - 关键方法：默认构造函数、参数化构造函数、`isLockedAt()`

- **UserRepository**
  - 职责：管理用户数据的存取，提供基于用户名的查询与更新。
  - 关键类：`UserRepository`
  - 关键成员：`std::unordered_map<std::string, User> users_`
  - 关键方法：`findByUsername()`、`save()`、`updateFailedAttempts()`

- **LoginService**
  - 职责：实现登录业务逻辑、输入校验、密码哈希校验、失败次数记录与锁定策略。
  - 关键类：`LoginService`
  - 关键枚举：`LoginResult`
  - 关键方法：`login()`、`isAccountLocked()`、`recordFailedAttempt()`、`resetFailedAttempts()`

- **main**
  - 职责：演示创建用户、登录成功、登录失败和账户锁定流程。
  - 关键函数：`main()`

## 3. 关键 API 定义

```cpp
// include/user.h
#ifndef USER_H
#define USER_H

#include <chrono>
#include <string>

class User {
public:
    std::string username;
    std::string password_hash;
    std::string salt;
    int failed_login_count;
    std::chrono::system_clock::time_point lockout_end_time;

    User();
    User(const std::string& username,
         const std::string& password_hash,
         const std::string& salt);

    bool isLockedAt(const std::chrono::system_clock::time_point& now) const;
};

#endif
```

```cpp
// include/user_repository.h
#ifndef USER_REPOSITORY_H
#define USER_REPOSITORY_H

#include "user.h"
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>

class UserRepository {
public:
    UserRepository();

    User* findByUsername(const std::string& username);
    void save(const User& user);
    void updateFailedAttempts(const std::string& username, int count);

private:
    std::unordered_map<std::string, User> users_;
    mutable std::mutex mutex_;
};

#endif
```

```cpp
// include/login_service.h
#ifndef LOGIN_SERVICE_H
#define LOGIN_SERVICE_H

#include "user_repository.h"
#include <string>

enum class LoginResult {
    SUCCESS,
    INVALID_USERNAME,
    INVALID_PASSWORD,
    USER_NOT_FOUND,
    ACCOUNT_LOCKED,
    WRONG_PASSWORD
};

class LoginService {
public:
    explicit LoginService(UserRepository& user_repository);

    LoginResult login(const std::string& username, const std::string& password);
    bool isAccountLocked(const std::string& username) const;
    void recordFailedAttempt(const std::string& username);
    void resetFailedAttempts(const std::string& username);

private:
    UserRepository& user_repository_;

    bool isValidUsername(const std::string& username) const;
    bool isValidPassword(const std::string& password) const;
    std::string createSalt() const;
    std::string hashPassword(const std::string& password,
                             const std::string& salt) const;
};

#endif
```

补充约定：

```cpp
constexpr int MAX_FAILED_LOGIN_COUNT = 3;
constexpr int LOCKOUT_MINUTES = 10;
constexpr int MIN_USERNAME_LENGTH = 3;
constexpr int MAX_USERNAME_LENGTH = 20;
constexpr int MIN_PASSWORD_LENGTH = 8;
constexpr int MAX_PASSWORD_LENGTH = 32;
```

`hashPassword()` 使用 C++17 STL 实现简单哈希：

```cpp
std::hash<std::string> hasher;
auto value = hasher(password + ":" + salt);
return std::to_string(value);
```

## 4. 数据结构与持久化

### User 数据结构

`User` 保存以下字段：

- `std::string username`
- `std::string password_hash`
- `std::string salt`
- `int failed_login_count`
- `std::chrono::system_clock::time_point lockout_end_time`

默认状态：

- `failed_login_count = 0`
- `lockout_end_time = std::chrono::system_clock::time_point{}`

### UserRepository 数据结构

```cpp
std::unordered_map<std::string, User> users_;
```

- key：用户名
- value：用户实体

### 持久化策略

当前迭代使用内存持久化：

- `save(user)` 将 `User` 写入 `users_`
- `findByUsername(username)` 返回用户指针，未找到返回 `nullptr`
- `updateFailedAttempts(username, count)` 更新失败次数

为避免悬空引用，`findByUsername()` 返回的 `User*` 仅在仓储生命周期内有效，调用方不持久保存该指针。

## 5. 安全与并发设计

### 输入校验

用户名规则：

- 长度 3-20
- 仅允许字母、数字、下划线
- 使用 `std::isalnum()` 与字符比较实现

密码规则：

- 长度 8-32
- 必须包含至少一个字母
- 必须包含至少一个数字

### 密码存储

- 不保存明文密码。
- 保存 `password_hash` 与 `salt`。
- `salt` 使用 `std::random_device`、`std::mt19937` 和字符表生成。
- 哈希使用 `std::hash<std::string>`，仅满足无第三方库约束下的演示级安全，不用于生产环境。

### 账户锁定

- 登录失败次数达到 3 次后锁定账户。
- `lockout_end_time = now + std::chrono::minutes(10)`。
- 当前时间早于 `lockout_end_time` 时返回 `ACCOUNT_LOCKED`。
- 锁定过期后允许继续登录；若登录成功则重置失败次数。

### 并发控制

- `UserRepository` 内部使用 `std::mutex` 保护 `users_`。
- `save()`、`findByUsername()`、`updateFailedAttempts()` 对共享容器加锁。
- 为减少竞态，`LoginService` 对用户状态修改后统一调用 `save()` 写回。
- 不跨模块暴露锁对象，遵循 RAII 使用 `std::lock_guard<std::mutex>`。

## 6. 文件组织

```text
include/
  user.h
  user_repository.h
  login_service.h

src/
  user.cpp
  user_repository.cpp
  login_service.cpp
  main.cpp

tests/
  test_login_service.cpp
  test_base.h

docs/
  technical_design.md

CMakeLists.txt
```

文件映射：

- `include/user.h`：声明 `User`
- `src/user.cpp`：实现 `User` 构造函数与 `isLockedAt()`
- `include/user_repository.h`：声明 `UserRepository`
- `src/user_repository.cpp`：实现用户内存仓储
- `include/login_service.h`：声明 `LoginService` 与 `LoginResult`
- `src/login_service.cpp`：实现登录、校验、哈希、锁定逻辑
- `src/main.cpp`：演示登录流程
- `tests/test_login_service.cpp`：覆盖登录成功、密码错误、账户锁定、输入非法等场景
- `tests/test_base.h`：提供简单断言宏或适配 gtest
- `docs/technical_design.md`：保存本文档

CMake 目标：

- `simple_login_lib`：编译核心类
- `simple_login_demo`：链接 `simple_login_lib`，运行演示
- `simple_login_tests`：链接 `simple_login_lib`，运行测试

## 7. 测试策略

使用 gtest 或 `tests/test_base.h` 自定义测试框架。

### 单元测试

`tests/test_login_service.cpp` 覆盖：

- `login_success_when_username_and_password_are_valid`
  - 创建用户并保存正确哈希，使用正确密码登录，期望 `LoginResult::SUCCESS`
- `login_fails_when_username_invalid`
  - 用户名过短、过长、含非法字符，期望 `INVALID_USERNAME`
- `login_fails_when_password_invalid`
  - 密码过短、无数字、无字母，期望 `INVALID_PASSWORD`
- `login_fails_when_user_not_found`
  - 仓储无对应用户，期望 `USER_NOT_FOUND`
- `wrong_password_increments_failed_count`
  - 错误密码登录后，`failed_login_count` 增加
- `account_locked_after_three_failed_attempts`
  - 连续三次密码错误后，期望账户锁定
- `successful_login_resets_failed_attempts`
  - 失败后使用正确密码登录，失败次数归零

### 仓储测试

- `save_and_find_user`
- `update_failed_attempts`
- `find_unknown_user_returns_nullptr`

### 演示验证

`src/main.cpp` 中演示：

1. 初始化 `UserRepository`
2. 创建测试用户
3. 使用错误密码连续登录 3 次
4. 验证账户锁定
5. 输出每次登录结果字符串