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

### 模块职责
- **Domain Layer**: 定义核心实体和值对象
- **Repository Layer**: 负责用户数据的持久化和检索
- **Service Layer**: 实现登录业务逻辑、验证、锁定机制
- **Presentation Layer**: 提供命令行交互界面

### 数据流
1. 用户输入 → main.cpp 接收用户名和密码
2. main.cpp → LoginService.login()
3. LoginService → UserRepository.findByUsername()
4. LoginService 验证密码、检查锁定状态
5. LoginService → UserRepository.updateFailedAttempts()
6. LoginService 返回 LoginResult → main.cpp 显示结果

## 2. 核心模块清单

### User (用户实体模块)
- **职责**: 表示用户实体，存储用户凭证和锁定状态
- **核心类**: `User`
- **关键成员**: username, password_hash, salt, failed_login_count, lockout_end_time
- **关键方法**: 构造函数、getter方法

### LoginResult (登录结果模块)
- **职责**: 封装登录操作的结果状态
- **核心类**: `LoginResult`
- **关键成员**: success (bool), message (string), locked_until (time_point)
- **关键方法**: 构造函数、isSuccess()、getMessage()

### LoginService (登录服务模块)
- **职责**: 实现登录业务逻辑、密码验证、失败计数、账户锁定
- **核心类**: `LoginService`
- **关键方法**: login(), isAccountLocked(), recordFailedAttempt(), resetFailedAttempts(), hashPassword(), verifyPassword()

### UserRepository (用户仓储模块)
- **职责**: 管理用户数据的存储和检索
- **核心类**: `UserRepository`
- **关键方法**: findByUsername(), save(), updateFailedAttempts(), updateLockoutTime()
- **存储**: 使用 std::unordered_map 内存存储

### ValidationUtils (验证工具模块)
- **职责**: 提供用户名和密码格式验证
- **核心函数**: validateUsername(), validatePassword()

## 3. 关键 API 定义

### User 类
```cpp
class User {
public:
    User(const std::string& username, 
         const std::string& password_hash,
         const std::string& salt);
    
    const std::string& getUsername() const;
    const std::string& getPasswordHash() const;
    const std::string& getSalt() const;
    int getFailedLoginCount() const;
    std::chrono::system_clock::time_point getLockoutEndTime() const;
    
    void setFailedLoginCount(int count);
    void setLockoutEndTime(std::chrono::system_clock::time_point time);
    
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
class LoginResult {
public:
    LoginResult(bool success, const std::string& message);
    LoginResult(bool success, const std::string& message,
                std::chrono::system_clock::time_point locked_until);
    
    bool isSuccess() const;
    const std::string& getMessage() const;
    bool isLocked() const;
    std::chrono::system_clock::time_point getLockedUntil() const;
    
private:
    bool success_;
    std::string message_;
    bool is_locked_;
    std::chrono::system_clock::time_point locked_until_;
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
    std::string hashPassword(const std::string& password, const std::string& salt);
    bool verifyPassword(const std::string& password, 
                       const std::string& hash, 
                       const std::string& salt);
    std::string generateSalt();
    
    UserRepository* repository_;
    static constexpr int MAX_FAILED_ATTEMPTS = 3;
    static constexpr int LOCKOUT_DURATION_MINUTES = 10;
};
```

### UserRepository 类
```cpp
class UserRepository {
public:
    UserRepository();
    
    User* findByUsername(const std::string& username);
    bool save(const User& user);
    bool updateFailedAttempts(const std::string& username, int count);
    bool updateLockoutTime(const std::string& username, 
                          std::chrono::system_clock::time_point time);
    
private:
    std::unordered_map<std::string, User> users_;
    std::mutex mutex_;
};
```

### ValidationUtils 命名空间
```cpp
namespace ValidationUtils {
    bool validateUsername(const std::string& username);
    bool validatePassword(const std::string& password);
}
```

## 4. 数据结构与持久化

### 核心数据结构

#### User 实体
```cpp
struct UserData {
    std::string username;           // 3-20字符，字母数字下划线
    std::string password_hash;      // SHA-256哈希值（64字符十六进制）
    std::string salt;               // 16字节随机盐（32字符十六进制）
    int failed_login_count;         // 失败登录次数 (0-3)
    std::chrono::system_clock::time_point lockout_end_time;  // 锁定结束时间
};
```

### 持久化策略
- **存储方式**: 内存存储（std::unordered_map）
- **键**: username (std::string)
- **值**: User 对象
- **线程安全**: 使用 std::mutex 保护并发访问

### 密码安全
- **哈希算法**: SHA-256（使用 C++17 标准库实现简化版本）
- **盐值**: 每个用户16字节随机盐
- **存储格式**: password_hash = SHA256(password + salt)

### 时间处理
- **时间类型**: std::chrono::system_clock::time_point
- **锁定时长**: 10分钟（std::chrono::minutes(10)）
- **时间比较**: 使用 std::chrono 进行时间点比较

## 5. 安全与并发设计

### 安全措施

#### 密码安全
- 密码不以明文存储，仅存储哈希值
- 每个用户使用独立的随机盐值
- 密码验证通过哈希比较而非明文比较

#### 输入验证
- 用户名验证：长度3-20，正则 `^[a-zA-Z0-9_]+$`
- 密码验证：长度8-32，必须包含至少一个字母和一个数字
- 所有输入在处理前进行验证

#### 账户保护
- 失败登录计数：最多3次
- 自动锁定：失败3次后锁定10分钟
- 锁定期间拒绝所有登录尝试
- 成功登录后重置失败计数

### 并发控制

#### UserRepository 线程安全
```cpp
class UserRepository {
private:
    std::unordered_map<std::string, User> users_;
    mutable std::mutex mutex_;  // 保护 users_ 的并发访问
    
public:
    User* findByUsername(const std::string& username) {
        std::lock_guard<std::mutex> lock(mutex_);
        // 查找操作
    }
    
    bool updateFailedAttempts(const std::string& username, int count) {
        std::lock_guard<std::mutex> lock(mutex_);
        // 更新操作
    }
};
```

#### 并发策略
- 使用 std::lock_guard 自动管理锁的生命周期
- 所有读写操作都在锁保护下进行
- 避免死锁：单一锁策略，不嵌套锁

### 错误处理
- 用户不存在：返回 LoginResult(false, "用户名或密码错误")
- 密码错误：返回 LoginResult(false, "用户名或密码错误")
- 账户锁定：返回 LoginResult(false, "账户已锁定", lockout_end_time)
- 输入验证失败：返回 LoginResult(false, "输入格式不正确")

## 6. 文件组织

### 目录结构
```
simple_login/
├── include/
│   ├── user.h
│   ├── login_result.h
│   ├── login_service.h
│   ├── user_repository.h
│   └── validation_utils.h
├── src/
│   ├── user.cpp
│   ├── login_result.cpp
│   ├── login_service.cpp
│   ├── user_repository.cpp
│   ├── validation_utils.cpp
│   └── main.cpp
├── tests/
│   ├── test_login_service.cpp
│   ├── test_user_repository.cpp
│   └── test_validation_utils.cpp
├── CMakeLists.txt
└── README.md
```

### 文件映射

#### Domain Layer
- `include/user.h` + `src/user.cpp`: User 类实现
- `include/login_result.h` + `src/login_result.cpp`: LoginResult 类实现

#### Repository Layer
- `include/user_repository.h` + `src/user_repository.cpp`: UserRepository 类实现

#### Service Layer
- `include/login_service.h` + `src/login_service.cpp`: LoginService 类实现

#### Utility Layer
- `include/validation_utils.h` + `src/validation_utils.cpp`: 验证工具函数

#### Presentation Layer
- `src/main.cpp`: 命令行交互界面，演示登录流程

#### Test Layer
- `tests/test_login_service.cpp`: LoginService 单元测试
- `tests/test_user_repository.cpp`: UserRepository 单元测试
- `tests/test_validation_utils.cpp`: ValidationUtils 单元测试

### CMakeLists.txt 配置
```cmake
cmake_minimum_required(VERSION 3.10)
project(SimpleLogin)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# 主程序
add_executable(simple_login
    src/main.cpp
    src/user.cpp
    src/login_result.cpp
    src/login_service.cpp
    src/user_repository.cpp
    src/validation_utils.cpp
)

# 测试程序
enable_testing()
add_executable(test_login
    tests/test_login_service.cpp
    tests/test_user_repository.cpp
    tests/test_validation_utils.cpp
    src/user.cpp
    src/login_result.cpp
    src/login_service.cpp
    src/user_repository.cpp
    src/validation_utils.cpp
)
target_link_libraries(test_login gtest gtest_main pthread)
add_test(NAME LoginTests COMMAND test_login)
```

## 7. 测试策略

### 测试框架
- **单元测试**: Google Test (gtest)
- **测试组织**: 每个模块对应一个测试文件
- **测试运行**: CMake + CTest

### 测试覆盖范围

#### test_validation_utils.cpp
- **测试用例**:
  - `ValidUsername_ValidFormats`: 测试有效用户名（3-20字符，字母数字下划线）
  - `InvalidUsername_TooShort`: 测试用户名过短（<3字符）
  - `InvalidUsername_TooLong`: 测试用户名过长（>20字符）
  - `InvalidUsername_InvalidChars`: 测试非法字符（特殊符号）
  - `ValidPassword_ValidFormats`: 测试有效密码（8-32字符，含字母和数字）
  - `InvalidPassword_TooShort`: 测试密码过短（<8字符）
  - `InvalidPassword_TooLong`: 测试密码过长（>32字符）
  - `InvalidPassword_NoDigit`: 测试密码缺少数字
  - `InvalidPassword_NoLetter`: 测试密码缺少字母

#### test_user_repository.cpp
- **测试用例**:
  - `SaveAndFind_Success`: 测试保存和查找用户
  - `FindNonExistent_ReturnsNull`: 测试查找不存在的用户
  - `UpdateFailedAttempts_Success`: 测试更新失败次数
  - `UpdateLockoutTime_Success`: 测试更新锁定时间
  - `ConcurrentAccess_ThreadSafe`: 测试多线程并发访问安全性

#### test_login_service.cpp
- **测试用例**:
  - `Login_ValidCredentials_Success`: 测试正确用户名和密码登录成功
  - `Login_InvalidPassword_Failure`: 测试错误密码登录失败
  - `Login_NonExistentUser_Failure`: 测试不存在的用户登录失败
  - `Login_ThreeFailedAttempts_AccountLocked`: 测试3次失败后账户锁定
  - `Login_LockedAccount_Rejected`: 测试锁定期间登录被拒绝
  - `Login_AfterLockoutExpires_Success`: 测试锁定过期后可以登录
  - `Login_SuccessResetsFailedCount`: 测试成功登录重置失败计数
  - `IsAccountLocked_ChecksLockoutTime`: 测试账户锁定状态检查
  - `PasswordHashing_DifferentSalts_DifferentHashes`: 测试相同密码不同盐值产生不同哈希

### 测试数据准备
```cpp
// 测试夹具
class LoginServiceTest : public ::testing::Test {
protected:
    void SetUp() override {
        repository = new UserRepository();
        service = new LoginService(repository);
        
        // 创建测试用户
        User test_user("testuser", 
                      service->hashPassword("Password123", "testsalt"),
                      "testsalt");
        repository->save(test_user);
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
- **main.cpp 演示流程**:
  1. 初始化 UserRepository 和 LoginService
  2. 创建测试用户（用户名: admin, 密码: Admin123）
  3. 演示成功登录场景
  4. 演示失败登录场景（错误密码）
  5. 演示账户锁定场景（连续3次失败）
  6. 演示锁定期间登录被拒绝
  7. 显示所有操作结果

### 测试执行
```bash
# 构建项目
mkdir build && cd build
cmake ..
make

# 运行主程序
./simple_login

# 运行测试
ctest --verbose
# 或直接运行
./test_login
```

### 测试指标
- **代码覆盖率目标**: >80%
- **关键路径覆盖**: 100%（登录成功、失败、锁定）
- **边界条件测试**: 用户名/密码长度边界、失败次数边界
- **并发测试**: 多线程场景下的数据一致性