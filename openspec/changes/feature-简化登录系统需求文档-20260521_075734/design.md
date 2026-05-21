# 技术设计文档

## 1. 系统架构概览

### 架构分层
```
┌─────────────────────────────────┐
│   Presentation Layer (main.cpp) │
├─────────────────────────────────┤
│   Service Layer (LoginService)  │
├─────────────────────────────────┤
│   Domain Layer (User)           │
├─────────────────────────────────┤
│   Data Layer (UserRepository)   │
└─────────────────────────────────┘
```

### 数据流
1. 用户通过main.cpp输入用户名和密码
2. LoginService接收登录请求，验证输入格式
3. LoginService通过UserRepository查询用户数据
4. LoginService验证账户锁定状态和密码
5. 根据验证结果更新失败次数或重置计数
6. 返回登录结果给调用方

### 模块依赖关系
- main.cpp → LoginService
- LoginService → User, UserRepository
- UserRepository → User
- 所有模块 → PasswordHasher (工具类)

## 2. 核心模块清单

### User (用户实体模块)
- **职责**: 封装用户数据和状态
- **关键类**: `User`
- **关键成员**:
  - `std::string username`: 用户名
  - `std::string password_hash`: 密码哈希值
  - `std::string salt`: 密码盐值
  - `int failed_login_count`: 失败登录次数
  - `std::chrono::system_clock::time_point lockout_end_time`: 锁定结束时间

### LoginService (登录服务模块)
- **职责**: 处理登录业务逻辑，包括验证、锁定管理
- **关键类**: `LoginService`
- **关键函数**:
  - `LoginResult login(const std::string& username, const std::string& password)`
  - `bool isAccountLocked(const std::string& username)`
  - `void recordFailedAttempt(const std::string& username)`
  - `void resetFailedAttempts(const std::string& username)`

### UserRepository (数据访问模块)
- **职责**: 管理用户数据的存储和检索
- **关键类**: `UserRepository`
- **关键函数**:
  - `User* findByUsername(const std::string& username)`
  - `void save(const User& user)`
  - `void updateFailedAttempts(const std::string& username, int count)`
  - `void updateLockoutTime(const std::string& username, const std::chrono::system_clock::time_point& time)`

### PasswordHasher (密码哈希工具模块)
- **职责**: 提供密码哈希和验证功能
- **关键类**: `PasswordHasher`
- **关键函数**:
  - `std::string generateSalt()`
  - `std::string hashPassword(const std::string& password, const std::string& salt)`
  - `bool verifyPassword(const std::string& password, const std::string& hash, const std::string& salt)`

### LoginResult (登录结果模块)
- **职责**: 封装登录操作的结果
- **关键类**: `LoginResult`
- **关键成员**:
  - `bool success`: 登录是否成功
  - `std::string message`: 结果消息
  - `enum class Status`: 状态枚举(SUCCESS, INVALID_CREDENTIALS, ACCOUNT_LOCKED, INVALID_INPUT)

### InputValidator (输入验证模块)
- **职责**: 验证用户名和密码格式
- **关键类**: `InputValidator`
- **关键函数**:
  - `bool validateUsername(const std::string& username)`
  - `bool validatePassword(const std::string& password)`

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
    static constexpr int MAX_FAILED_ATTEMPTS = 3;
    static constexpr int LOCKOUT_DURATION_MINUTES = 10;
    
    bool validateInput(const std::string& username, const std::string& password);
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
    void initializeTestData();
    
private:
    std::unordered_map<std::string, User> users_;
};
```

### PasswordHasher 类
```cpp
class PasswordHasher {
public:
    static std::string generateSalt();
    static std::string hashPassword(const std::string& password, 
                                    const std::string& salt);
    static bool verifyPassword(const std::string& password, 
                              const std::string& hash, 
                              const std::string& salt);
};
```

### LoginResult 类
```cpp
class LoginResult {
public:
    enum class Status {
        SUCCESS,
        INVALID_CREDENTIALS,
        ACCOUNT_LOCKED,
        INVALID_INPUT
    };
    
    LoginResult(Status status, const std::string& message);
    
    bool isSuccess() const;
    Status getStatus() const;
    const std::string& getMessage() const;
    
private:
    Status status_;
    std::string message_;
};
```

### InputValidator 类
```cpp
class InputValidator {
public:
    static bool validateUsername(const std::string& username);
    static bool validatePassword(const std::string& password);
    
private:
    static constexpr int MIN_USERNAME_LENGTH = 3;
    static constexpr int MAX_USERNAME_LENGTH = 20;
    static constexpr int MIN_PASSWORD_LENGTH = 8;
    static constexpr int MAX_PASSWORD_LENGTH = 32;
};
```

## 4. 数据结构与持久化

### 核心数据结构

#### User 实体
```cpp
struct UserData {
    std::string username;           // 用户名
    std::string password_hash;      // SHA-256哈希值
    std::string salt;               // 16字节随机盐值
    int failed_login_count;         // 失败次数 (0-3)
    std::chrono::system_clock::time_point lockout_end_time;  // 锁定结束时间
};
```

### 内存存储
- 使用 `std::unordered_map<std::string, User>` 存储用户数据
- 键: 用户名 (username)
- 值: User对象

### 数据初始化
```cpp
// 在UserRepository中初始化测试数据
void UserRepository::initializeTestData() {
    // 创建测试用户: username="testuser", password="Test1234"
    std::string salt = PasswordHasher::generateSalt();
    std::string hash = PasswordHasher::hashPassword("Test1234", salt);
    User test_user("testuser", hash, salt);
    save(test_user);
}
```

### 持久化策略
- **第一阶段**: 仅内存存储，程序重启后数据丢失
- **扩展方向**: 可添加文件持久化或数据库支持

## 5. 安全与并发设计

### 安全措施

#### 密码安全
- **哈希算法**: 使用SHA-256进行密码哈希
- **盐值**: 每个用户生成唯一的16字节随机盐值
- **存储**: 仅存储哈希值，不存储明文密码
- **验证**: 使用常量时间比较防止时序攻击

#### 账户锁定机制
- **失败阈值**: 连续失败3次触发锁定
- **锁定时长**: 10分钟
- **锁定检查**: 每次登录前检查锁定状态
- **自动解锁**: 时间到期后自动解除锁定

#### 输入验证
- **用户名规则**: 
  - 长度: 3-20字符
  - 字符集: 字母、数字、下划线 [a-zA-Z0-9_]
  - 正则表达式: `^[a-zA-Z0-9_]{3,20}$`
  
- **密码规则**:
  - 长度: 8-32字符
  - 复杂度: 必须包含至少一个字母和一个数字
  - 验证逻辑: 遍历检查字符类型

### 并发设计

#### 当前版本 (单线程)
- 不考虑并发访问
- 适用于单用户演示场景

#### 扩展方向 (多线程)
- 使用 `std::mutex` 保护 UserRepository 的 users_ 映射
- 使用 `std::lock_guard` 进行自动锁管理
- 细粒度锁: 每个用户一个锁，减少竞争

```cpp
// 扩展示例
class UserRepository {
private:
    std::unordered_map<std::string, User> users_;
    mutable std::mutex mutex_;  // 保护users_的互斥锁
};
```

## 6. 文件组织

### 目录结构
```
simple_login/
├── CMakeLists.txt
├── include/
│   ├── user.h
│   ├── login_service.h
│   ├── user_repository.h
│   ├── password_hasher.h
│   ├── login_result.h
│   └── input_validator.h
├── src/
│   ├── user.cpp
│   ├── login_service.cpp
│   ├── user_repository.cpp
│   ├── password_hasher.cpp
│   ├── login_result.cpp
│   ├── input_validator.cpp
│   └── main.cpp
├── tests/
│   ├── test_login_service.cpp
│   ├── test_user_repository.cpp
│   ├── test_password_hasher.cpp
│   └── test_input_validator.cpp
└── docs/
    └── design.md
```

### 模块到文件映射

| 模块 | 头文件 | 源文件 | 测试文件 |
|------|--------|--------|----------|
| User | include/user.h | src/user.cpp | - |
| LoginService | include/login_service.h | src/login_service.cpp | tests/test_login_service.cpp |
| UserRepository | include/user_repository.h | src/user_repository.cpp | tests/test_user_repository.cpp |
| PasswordHasher | include/password_hasher.h | src/password_hasher.cpp | tests/test_password_hasher.cpp |
| LoginResult | include/login_result.h | src/login_result.cpp | - |
| InputValidator | include/input_validator.h | src/input_validator.cpp | tests/test_input_validator.cpp |
| Main | - | src/main.cpp | - |

### 头文件包含关系
```
main.cpp
  └─> login_service.h
        ├─> user.h
        ├─> user_repository.h
        │     └─> user.h
        ├─> login_result.h
        ├─> password_hasher.h
        └─> input_validator.h
```

## 7. 测试策略

### 测试框架
- 使用 Google Test (gtest) 或自定义 test_base.h
- 每个核心模块至少一个测试文件

### 测试覆盖范围

#### test_input_validator.cpp
- **测试用例**:
  - `ValidUsername_ReturnsTrue`: 有效用户名验证
  - `InvalidUsername_TooShort`: 用户名过短
  - `InvalidUsername_TooLong`: 用户名过长
  - `InvalidUsername_InvalidChars`: 包含非法字符
  - `ValidPassword_ReturnsTrue`: 有效密码验证
  - `InvalidPassword_TooShort`: 密码过短
  - `InvalidPassword_NoDigit`: 缺少数字
  - `InvalidPassword_NoLetter`: 缺少字母

#### test_password_hasher.cpp
- **测试用例**:
  - `GenerateSalt_ReturnsNonEmptyString`: 生成盐值
  - `HashPassword_ReturnsDifferentHashForDifferentSalts`: 不同盐值产生不同哈希
  - `VerifyPassword_CorrectPassword_ReturnsTrue`: 正确密码验证成功
  - `VerifyPassword_WrongPassword_ReturnsFalse`: 错误密码验证失败
  - `HashPassword_SameInputs_ReturnsSameHash`: 相同输入产生相同哈希

#### test_user_repository.cpp
- **测试用例**:
  - `FindByUsername_ExistingUser_ReturnsUser`: 查找存在的用户
  - `FindByUsername_NonExistingUser_ReturnsNull`: 查找不存在的用户
  - `Save_NewUser_UserIsSaved`: 保存新用户
  - `UpdateFailedAttempts_UpdatesCount`: 更新失败次数
  - `UpdateLockoutTime_UpdatesTime`: 更新锁定时间

#### test_login_service.cpp
- **测试用例**:
  - `Login_ValidCredentials_ReturnsSuccess`: 有效凭证登录成功
  - `Login_InvalidPassword_ReturnsFailure`: 无效密码登录失败
  - `Login_NonExistingUser_ReturnsFailure`: 不存在的用户登录失败
  - `Login_ThreeFailedAttempts_LocksAccount`: 三次失败后锁定账户
  - `Login_LockedAccount_ReturnsAccountLocked`: 锁定账户无法登录
  - `Login_AfterLockoutExpires_AllowsLogin`: 锁定过期后允许登录
  - `Login_InvalidUsername_ReturnsInvalidInput`: 无效用户名格式
  - `Login_InvalidPassword_ReturnsInvalidInput`: 无效密码格式
  - `Login_SuccessfulLogin_ResetsFailedCount`: 成功登录重置失败计数

### 测试数据准备
```cpp
// 在每个测试fixture的SetUp中准备测试数据
class LoginServiceTest : public ::testing::Test {
protected:
    void SetUp() override {
        repository = new UserRepository();
        std::string salt = PasswordHasher::generateSalt();
        std::string hash = PasswordHasher::hashPassword("Test1234", salt);
        User test_user("testuser", hash, salt);
        repository->save(test_user);
        service = new LoginService(repository);
    }
    
    void TearDown() override {
        delete service;
        delete repository;
    }
    
    UserRepository* repository;
    LoginService* service;
};
```

### 集成测试
- **main.cpp**: 作为手动集成测试
- **测试场景**:
  1. 成功登录流程
  2. 失败登录流程
  3. 账户锁定和解锁流程
  4. 输入验证流程

### 测试执行
```bash
# 编译测试
mkdir build && cd build
cmake ..
make

# 运行所有测试
./tests/test_login_service
./tests/test_user_repository
./tests/test_password_hasher
./tests/test_input_validator

# 或使用ctest
ctest --verbose
```

### CMakeLists.txt 配置
```cmake
cmake_minimum_required(VERSION 3.10)
project(SimpleLogin)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# 源文件
set(SOURCES
    src/user.cpp
    src/login_service.cpp
    src/user_repository.cpp
    src/password_hasher.cpp
    src/login_result.cpp
    src/input_validator.cpp
)

# 主程序
add_executable(simple_login src/main.cpp ${SOURCES})

# 测试
enable_testing()
find_package(GTest REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

add_executable(test_login_service tests/test_login_service.cpp ${SOURCES})
target_link_libraries(test_login_service ${GTEST_LIBRARIES} pthread)

add_executable(test_user_repository tests/test_user_repository.cpp ${SOURCES})
target_link_libraries(test_user_repository ${GTEST_LIBRARIES} pthread)

add_executable(test_password_hasher tests/test_password_hasher.cpp ${SOURCES})
target_link_libraries(test_password_hasher ${GTEST_LIBRARIES} pthread)

add_executable(test_input_validator tests/test_input_validator.cpp ${SOURCES})
target_link_libraries(test_input_validator ${GTEST_LIBRARIES} pthread)

add_test(NAME LoginServiceTest COMMAND test_login_service)
add_test(NAME UserRepositoryTest COMMAND test_user_repository)
add_test(NAME PasswordHasherTest COMMAND test_password_hasher)
add_test(NAME InputValidatorTest COMMAND test_input_validator)
```