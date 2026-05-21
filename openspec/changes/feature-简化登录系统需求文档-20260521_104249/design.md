# 技术设计文档

## 1. 系统架构概览

### 架构分层
```
┌─────────────────────────────────┐
│   Presentation Layer (main.cpp) │
├─────────────────────────────────┤
│   Service Layer (LoginService)  │
├─────────────────────────────────┤
│   Repository Layer (UserRepo)   │
├─────────────────────────────────┤
│   Domain Layer (User, LoginRes) │
└─────────────────────────────────┘
```

### 数据流
1. 用户通过 main.cpp 输入用户名和密码
2. LoginService 接收凭证，验证账户锁定状态
3. UserRepository 从内存存储中查询用户数据
4. LoginService 验证密码哈希，更新失败计数
5. 返回 LoginResult 给调用者

### 核心模块
- **Domain**: User, LoginResult（领域实体和值对象）
- **Service**: LoginService（业务逻辑层）
- **Repository**: UserRepository（数据访问层）
- **Utility**: PasswordHasher（密码哈希工具）

## 2. 核心模块清单

### User（用户实体）
- **职责**: 表示系统用户及其认证信息
- **关键成员**:
  - `std::string username`: 用户名
  - `std::string password_hash`: 密码哈希值
  - `std::string salt`: 盐值
  - `int failed_login_count`: 失败登录次数
  - `std::chrono::system_clock::time_point lockout_end_time`: 锁定结束时间

### LoginResult（登录结果）
- **职责**: 封装登录操作的结果状态
- **关键成员**:
  - `bool success`: 登录是否成功
  - `std::string message`: 结果消息
  - `enum class Status`: SUCCESS, INVALID_CREDENTIALS, ACCOUNT_LOCKED

### LoginService（登录服务）
- **职责**: 处理用户登录业务逻辑
- **关键方法**:
  - `LoginResult login(const std::string& username, const std::string& password)`: 执行登录
  - `bool isAccountLocked(const std::string& username)`: 检查账户锁定状态
  - `void recordFailedAttempt(const std::string& username)`: 记录失败尝试
  - `void resetFailedAttempts(const std::string& username)`: 重置失败计数

### UserRepository（用户仓储）
- **职责**: 管理用户数据的持久化和查询
- **关键方法**:
  - `User* findByUsername(const std::string& username)`: 按用户名查找
  - `void save(const User& user)`: 保存用户
  - `void updateFailedAttempts(const std::string& username, int count)`: 更新失败次数
  - `void updateLockoutTime(const std::string& username, const std::chrono::system_clock::time_point& time)`: 更新锁定时间

### PasswordHasher（密码哈希工具）
- **职责**: 提供密码哈希和验证功能
- **关键方法**:
  - `std::string generateSalt()`: 生成随机盐值
  - `std::string hashPassword(const std::string& password, const std::string& salt)`: 哈希密码
  - `bool verifyPassword(const std::string& password, const std::string& hash, const std::string& salt)`: 验证密码

### InputValidator（输入验证器）
- **职责**: 验证用户输入的合法性
- **关键方法**:
  - `bool validateUsername(const std::string& username)`: 验证用户名格式
  - `bool validatePassword(const std::string& password)`: 验证密码强度

## 3. 关键 API 定义

### User 类
```cpp
class User {
public:
    User();
    User(const std::string& username, 
         const std::string& password_hash,
         const std::string& salt);
    
    const std::string& getUsername() const;
    const std::string& getPasswordHash() const;
    const std::string& getSalt() const;
    int getFailedLoginCount() const;
    std::chrono::system_clock::time_point getLockoutEndTime() const;
    
    void setFailedLoginCount(int count);
    void setLockoutEndTime(const std::chrono::system_clock::time_point& time);
    
private:
    std::string username_;
    std::string password_hash_;
    std::string salt_;
    int failed_login_count_;
    std::chrono::system_clock::time_point lockout_end_time_;
};
```

### LoginResult 类
```cpp
enum class LoginStatus {
    SUCCESS,
    INVALID_CREDENTIALS,
    ACCOUNT_LOCKED,
    INVALID_INPUT
};

class LoginResult {
public:
    LoginResult(LoginStatus status, const std::string& message);
    
    bool isSuccess() const;
    LoginStatus getStatus() const;
    const std::string& getMessage() const;
    
private:
    LoginStatus status_;
    std::string message_;
};
```

### LoginService 类
```cpp
class LoginService {
public:
    explicit LoginService(UserRepository* repository);
    
    LoginResult login(const std::string& username, const std::string& password);
    bool isAccountLocked(const std::string& username);
    void recordFailedAttempt(const std::string& username);
    void resetFailedAttempts(const std::string& username);
    
private:
    UserRepository* repository_;
    PasswordHasher hasher_;
    InputValidator validator_;
    
    static constexpr int MAX_FAILED_ATTEMPTS = 3;
    static constexpr int LOCKOUT_DURATION_MINUTES = 10;
};
```

### UserRepository 类
```cpp
class UserRepository {
public:
    UserRepository();
    ~UserRepository();
    
    User* findByUsername(const std::string& username);
    void save(const User& user);
    void updateFailedAttempts(const std::string& username, int count);
    void updateLockoutTime(const std::string& username, 
                          const std::chrono::system_clock::time_point& time);
    bool exists(const std::string& username);
    
private:
    std::unordered_map<std::string, User> users_;
};
```

### PasswordHasher 类
```cpp
class PasswordHasher {
public:
    std::string generateSalt(size_t length = 16);
    std::string hashPassword(const std::string& password, const std::string& salt);
    bool verifyPassword(const std::string& password, 
                       const std::string& hash, 
                       const std::string& salt);
    
private:
    std::string computeHash(const std::string& input);
};
```

### InputValidator 类
```cpp
class InputValidator {
public:
    bool validateUsername(const std::string& username);
    bool validatePassword(const std::string& password);
    
private:
    bool isAlphanumericOrUnderscore(char c);
    bool containsLetter(const std::string& str);
    bool containsDigit(const std::string& str);
};
```

## 4. 数据结构与持久化

### 内存数据结构
```cpp
// UserRepository 内部存储
std::unordered_map<std::string, User> users_;
// Key: username (string)
// Value: User object
```

### User 对象结构
```cpp
struct UserData {
    std::string username;           // 3-20字符
    std::string password_hash;      // SHA-256哈希结果（64字符十六进制）
    std::string salt;               // 16字符随机盐值
    int failed_login_count;         // 0-3
    std::chrono::system_clock::time_point lockout_end_time;  // 锁定结束时间戳
};
```

### 持久化策略
- **当前版本**: 内存存储（std::unordered_map）
- **初始化数据**: 在 UserRepository 构造函数中预置测试用户
- **数据生命周期**: 程序运行期间保持在内存中
- **扩展性**: 接口设计支持未来迁移到文件或数据库存储

### 示例初始数据
```cpp
// 在 UserRepository 构造函数中初始化
User testUser("admin", 
              hasher.hashPassword("Admin123", "randomsalt123"),
              "randomsalt123");
users_["admin"] = testUser;
```

## 5. 安全与并发设计

### 安全措施

#### 密码存储安全
- **盐值生成**: 使用 std::random_device 和 std::mt19937 生成随机盐值
- **哈希算法**: 使用 std::hash 结合自定义迭代实现密码哈希
- **存储方式**: 仅存储哈希值和盐值，不存储明文密码

#### 账户锁定机制
```cpp
// 失败尝试计数
if (failed_login_count >= MAX_FAILED_ATTEMPTS) {
    lockout_end_time = now + std::chrono::minutes(LOCKOUT_DURATION_MINUTES);
}

// 锁定检查
bool isLocked = (now < lockout_end_time);
```

#### 输入验证
- **用户名**: 正则验证 `^[a-zA-Z0-9_]{3,20}$`
- **密码**: 长度8-32，必须包含字母和数字
- **防注入**: 所有输入在处理前进行验证

### 并发设计

#### 当前版本（单线程）
- 不涉及多线程操作
- UserRepository 的 std::unordered_map 在单线程环境下安全

#### 未来扩展（多线程支持）
```cpp
// 可添加互斥锁保护共享数据
class UserRepository {
private:
    std::unordered_map<std::string, User> users_;
    mutable std::mutex mutex_;  // 保护 users_ 的访问
    
public:
    User* findByUsername(const std::string& username) {
        std::lock_guard<std::mutex> lock(mutex_);
        // ... 查询逻辑
    }
};
```

### 时间处理
```cpp
// 使用 std::chrono 进行时间计算
auto now = std::chrono::system_clock::now();
auto lockout_duration = std::chrono::minutes(10);
auto lockout_end = now + lockout_duration;

// 时间比较
bool is_locked = (now < user->getLockoutEndTime());
```

## 6. 文件组织

### 目录结构
```
simple_login/
├── include/
│   ├── user.h                    # User 类声明
│   ├── login_result.h            # LoginResult 类声明
│   ├── login_service.h           # LoginService 类声明
│   ├── user_repository.h         # UserRepository 类声明
│   ├── password_hasher.h         # PasswordHasher 类声明
│   └── input_validator.h         # InputValidator 类声明
├── src/
│   ├── user.cpp                  # User 类实现
│   ├── login_result.cpp          # LoginResult 类实现
│   ├── login_service.cpp         # LoginService 类实现
│   ├── user_repository.cpp       # UserRepository 类实现
│   ├── password_hasher.cpp       # PasswordHasher 类实现
│   ├── input_validator.cpp       # InputValidator 类实现
│   └── main.cpp                  # 主程序入口
├── tests/
│   ├── test_user.cpp             # User 类单元测试
│   ├── test_login_service.cpp    # LoginService 集成测试
│   ├── test_password_hasher.cpp  # PasswordHasher 单元测试
│   ├── test_input_validator.cpp  # InputValidator 单元测试
│   └── test_base.h               # 测试基础设施
├── docs/
│   └── technical_design.md       # 本技术设计文档
└── CMakeLists.txt                # CMake 构建配置
```

### 模块到文件映射

| 模块 | 头文件 | 实现文件 | 测试文件 |
|------|--------|----------|----------|
| User | include/user.h | src/user.cpp | tests/test_user.cpp |
| LoginResult | include/login_result.h | src/login_result.cpp | - |
| LoginService | include/login_service.h | src/login_service.cpp | tests/test_login_service.cpp |
| UserRepository | include/user_repository.h | src/user_repository.cpp | - |
| PasswordHasher | include/password_hasher.h | src/password_hasher.cpp | tests/test_password_hasher.cpp |
| InputValidator | include/input_validator.h | src/input_validator.cpp | tests/test_input_validator.cpp |

### 依赖关系
```
main.cpp
  └─> LoginService
       ├─> UserRepository
       │    └─> User
       ├─> PasswordHasher
       ├─> InputValidator
       └─> LoginResult
```

### CMakeLists.txt 结构
```cmake
cmake_minimum_required(VERSION 3.10)
project(SimpleLogin)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# 源文件列表
set(SOURCES
    src/user.cpp
    src/login_result.cpp
    src/login_service.cpp
    src/user_repository.cpp
    src/password_hasher.cpp
    src/input_validator.cpp
)

# 主程序
add_executable(simple_login src/main.cpp ${SOURCES})

# 测试程序
add_executable(test_login
    tests/test_user.cpp
    tests/test_login_service.cpp
    tests/test_password_hasher.cpp
    tests/test_input_validator.cpp
    ${SOURCES}
)
```

## 7. 测试策略

### 测试层次

#### 单元测试
- **User 类测试** (test_user.cpp)
  - 构造函数正确初始化所有字段
  - Getter/Setter 方法正确工作
  - 失败计数和锁定时间更新正确

- **PasswordHasher 测试** (test_password_hasher.cpp)
  - 盐值生成长度和随机性
  - 相同密码+盐值产生相同哈希
  - 不同盐值产生不同哈希
  - 密码验证正确性

- **InputValidator 测试** (test_input_validator.cpp)
  - 用户名长度验证（<3, 3-20, >20）
  - 用户名字符验证（字母、数字、下划线、特殊字符）
  - 密码长度验证（<8, 8-32, >32）
  - 密码强度验证（仅字母、仅数字、字母+数字）

#### 集成测试
- **LoginService 测试** (test_login_service.cpp)
  - 成功登录场景
  - 错误密码登录失败
  - 连续3次失败后账户锁定
  - 锁定期间无法登录
  - 锁定10分钟后自动解锁
  - 成功登录后重置失败计数
  - 无效用户名格式拒绝
  - 无效密码格式拒绝

### 测试框架

#### test_base.h 结构
```cpp
#ifndef TEST_BASE_H
#define TEST_BASE_H

#include <iostream>
#include <string>
#include <functional>

class TestBase {
public:
    static int total_tests;
    static int passed_tests;
    
    static void assert_true(bool condition, const std::string& message);
    static void assert_false(bool condition, const std::string& message);
    static void assert_equal(const std::string& expected, const std::string& actual);
    static void run_test(const std::string& name, std::function<void()> test_func);
    static void print_summary();
};

#define TEST(name) \
    void test_##name(); \
    struct TestRunner_##name { \
        TestRunner_##name() { \
            TestBase::run_test(#name, test_##name); \
        } \
    } runner_##name; \
    void test_##name()

#endif
```

### 测试用例示例

#### 成功登录测试
```cpp
TEST(successful_login) {
    UserRepository repo;
    PasswordHasher hasher;
    std::string salt = hasher.generateSalt();
    std::string hash = hasher.hashPassword("Test1234", salt);
    User user("testuser", hash, salt);
    repo.save(user);
    
    LoginService service(&repo);
    LoginResult result = service.login("testuser", "Test1234");
    
    TestBase::assert_true(result.isSuccess(), "Login should succeed");
    TestBase::assert_equal("SUCCESS", result.getMessage());
}
```

#### 账户锁定测试
```cpp
TEST(account_lockout_after_three_failures) {
    UserRepository repo;
    PasswordHasher hasher;
    std::string salt = hasher.generateSalt();
    std::string hash = hasher.hashPassword("Test1234", salt);
    User user("testuser", hash, salt);
    repo.save(user);
    
    LoginService service(&repo);
    
    // 三次失败尝试
    service.login("testuser", "wrong1");
    service.login("testuser", "wrong2");
    service.login("testuser", "wrong3");
    
    // 第四次应该被锁定
    LoginResult result = service.login("testuser", "Test1234");
    TestBase::assert_false(result.isSuccess(), "Account should be locked");
    TestBase::assert_true(service.isAccountLocked("testuser"), "Account should be locked");
}
```

### 测试覆盖目标
- **代码覆盖率**: 目标 >80%
- **分支覆盖率**: 目标 >75%
- **关键路径**: 100%覆盖（登录成功、失败、锁定）

### 测试执行
```bash
# 构建测试
mkdir build && cd build
cmake ..
make test_login

# 运行测试
./test_login

# 预期输出
Running test: successful_login ... PASSED
Running test: failed_login_invalid_password ... PASSED
Running test: account_lockout_after_three_failures ... PASSED
...
Total: 12 tests, 12 passed, 0 failed
```