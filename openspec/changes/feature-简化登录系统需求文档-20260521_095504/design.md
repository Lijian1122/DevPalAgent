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
- **职责**: 表示用户实体，存储用户凭证和状态
- **核心类**: `User`
- **关键属性**: username, password_hash, salt, failed_login_count, lockout_end_time

### LoginService (登录服务模块)
- **职责**: 处理登录逻辑、密码验证、账户锁定管理
- **核心类**: `LoginService`
- **关键方法**: login(), isAccountLocked(), recordFailedAttempt(), resetFailedAttempts(), hashPassword(), verifyPassword()

### UserRepository (用户仓储模块)
- **职责**: 用户数据的存储和检索
- **核心类**: `UserRepository`
- **关键方法**: findByUsername(), save(), updateFailedAttempts(), updateLockoutTime()

### LoginResult (登录结果模块)
- **职责**: 封装登录操作的结果
- **核心类**: `LoginResult`
- **关键属性**: success, message, locked_until

### Validation (验证工具模块)
- **职责**: 验证用户名和密码格式
- **核心类**: `ValidationUtils`
- **关键方法**: validateUsername(), validatePassword()

## 3. 关键 API 定义

### User 类
```cpp
class User {
public:
    User();
    User(const std::string& username, const std::string& password_hash, 
         const std::string& salt);
    
    std::string getUsername() const;
    std::string getPasswordHash() const;
    std::string getSalt() const;
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
class LoginResult {
public:
    LoginResult(bool success, const std::string& message);
    LoginResult(bool success, const std::string& message, 
                const std::chrono::system_clock::time_point& locked_until);
    
    bool isSuccess() const;
    std::string getMessage() const;
    bool isLocked() const;
    std::chrono::system_clock::time_point getLockedUntil() const;
    
private:
    bool success_;
    std::string message_;
    bool locked_;
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
    std::string generateSalt();
    bool verifyPassword(const std::string& password, const std::string& hash, 
                       const std::string& salt);
    
    UserRepository* repository_;
    static constexpr int MAX_FAILED_ATTEMPTS = 3;
    static constexpr int LOCKOUT_MINUTES = 10;
};
```

### UserRepository 类
```cpp
class UserRepository {
public:
    UserRepository();
    ~UserRepository();
    
    User* findByUsername(const std::string& username);
    bool save(const User& user);
    bool updateFailedAttempts(const std::string& username, int count);
    bool updateLockoutTime(const std::string& username, 
                          const std::chrono::system_clock::time_point& time);
    void initializeTestData();
    
private:
    std::unordered_map<std::string, std::unique_ptr<User>> users_;
};
```

### ValidationUtils 类
```cpp
class ValidationUtils {
public:
    static bool validateUsername(const std::string& username, std::string& error);
    static bool validatePassword(const std::string& password, std::string& error);
    
private:
    static bool isAlphanumericOrUnderscore(char c);
    static bool containsLetter(const std::string& str);
    static bool containsDigit(const std::string& str);
};
```

## 4. 数据结构与持久化

### 核心数据结构

#### User 实体
```cpp
struct UserData {
    std::string username;           // 用户名 (3-20字符)
    std::string password_hash;      // 密码哈希值 (SHA-256模拟)
    std::string salt;               // 盐值 (16字节随机)
    int failed_login_count;         // 失败登录次数 (0-3)
    std::chrono::system_clock::time_point lockout_end_time;  // 锁定结束时间
};
```

### 持久化策略
- **内存存储**: 使用 `std::unordered_map<std::string, std::unique_ptr<User>>` 存储用户数据
- **键**: 用户名 (username)
- **值**: User 对象的智能指针

### 初始化数据
```cpp
// 预置测试用户
username: "testuser"
password: "Test1234"
salt: 随机生成
password_hash: hashPassword("Test1234", salt)
failed_login_count: 0
lockout_end_time: epoch (未锁定)
```

### 哈希算法实现
使用 C++17 STL 实现简单哈希:
```cpp
std::string hashPassword(const std::string& password, const std::string& salt) {
    std::string combined = password + salt;
    std::hash<std::string> hasher;
    size_t hash_value = hasher(combined);
    
    // 多轮哈希增强安全性
    for (int i = 0; i < 1000; ++i) {
        std::string temp = std::to_string(hash_value) + salt;
        hash_value = hasher(temp);
    }
    
    return std::to_string(hash_value);
}
```

### 盐值生成
```cpp
std::string generateSalt() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 255);
    
    std::string salt;
    for (int i = 0; i < 16; ++i) {
        salt += static_cast<char>(dis(gen));
    }
    return salt;
}
```

## 5. 安全与并发设计

### 安全措施

#### 密码存储安全
- **不存储明文密码**: 仅存储哈希值
- **加盐哈希**: 每个用户使用唯一的随机盐值
- **多轮哈希**: 执行1000次迭代增加破解难度

#### 账户锁定机制
- **失败次数限制**: 3次失败后锁定
- **锁定时长**: 10分钟
- **时间检查**: 使用 `std::chrono::system_clock` 精确计时
- **自动解锁**: 锁定时间到期后自动重置

#### 输入验证
- **用户名规则**: 3-20字符，仅字母数字下划线
- **密码规则**: 8-32字符，必须包含字母和数字
- **防注入**: 所有输入经过严格验证

### 并发设计

#### 单线程模型
- 当前版本采用单线程设计
- 适用于命令行演示程序
- 无需复杂的同步机制

#### 未来扩展考虑
如需支持多线程:
```cpp
class UserRepository {
private:
    std::unordered_map<std::string, std::unique_ptr<User>> users_;
    mutable std::mutex mutex_;  // 保护 users_ 的互斥锁
    
public:
    User* findByUsername(const std::string& username) {
        std::lock_guard<std::mutex> lock(mutex_);
        // ... 查找逻辑
    }
};
```

### 错误处理
- **空指针检查**: 所有指针操作前检查有效性
- **异常安全**: 使用 RAII 管理资源
- **返回值检查**: 关键操作返回 bool 表示成功/失败
- **错误消息**: LoginResult 携带详细错误信息

## 6. 文件组织

### 目录结构
```
simple_login/
├── include/
│   ├── user.h                    # User 类定义
│   ├── login_result.h            # LoginResult 类定义
│   ├── login_service.h           # LoginService 类定义
│   ├── user_repository.h         # UserRepository 类定义
│   └── validation_utils.h        # ValidationUtils 类定义
├── src/
│   ├── user.cpp                  # User 类实现
│   ├── login_result.cpp          # LoginResult 类实现
│   ├── login_service.cpp         # LoginService 类实现
│   ├── user_repository.cpp       # UserRepository 类实现
│   ├── validation_utils.cpp      # ValidationUtils 类实现
│   └── main.cpp                  # 主程序入口
├── tests/
│   ├── test_user.cpp             # User 类单元测试
│   ├── test_login_service.cpp    # LoginService 类单元测试
│   ├── test_user_repository.cpp  # UserRepository 类单元测试
│   ├── test_validation.cpp       # ValidationUtils 类单元测试
│   └── test_base.h               # 测试基础设施
├── docs/
│   └── technical_design.md       # 本技术设计文档
└── CMakeLists.txt                # CMake 构建配置
```

### 模块与文件映射

| 模块 | 头文件 | 源文件 | 测试文件 |
|------|--------|--------|----------|
| User | include/user.h | src/user.cpp | tests/test_user.cpp |
| LoginResult | include/login_result.h | src/login_result.cpp | - |
| LoginService | include/login_service.h | src/login_service.cpp | tests/test_login_service.cpp |
| UserRepository | include/user_repository.h | src/user_repository.cpp | tests/test_user_repository.cpp |
| ValidationUtils | include/validation_utils.h | src/validation_utils.cpp | tests/test_validation.cpp |
| Main | - | src/main.cpp | - |

### 依赖关系
```
main.cpp
  ├─> login_service.h
  │     ├─> user_repository.h
  │     │     └─> user.h
  │     ├─> login_result.h
  │     └─> validation_utils.h
  └─> user.h
```

## 7. 测试策略

### 测试框架
- **基础框架**: 自定义 test_base.h
- **断言宏**: ASSERT_TRUE, ASSERT_FALSE, ASSERT_EQ, ASSERT_STREQ
- **测试运行**: 每个测试文件独立编译和执行

### 测试覆盖范围

#### test_user.cpp (User 类测试)
```cpp
void testUserConstruction();           // 测试构造函数
void testUserGetters();                // 测试 getter 方法
void testUserSetters();                // 测试 setter 方法
void testDefaultConstructor();         // 测试默认构造
```

#### test_validation.cpp (验证工具测试)
```cpp
void testValidUsername();              // 有效用户名
void testInvalidUsernameTooShort();    // 用户名过短
void testInvalidUsernameTooLong();     // 用户名过长
void testInvalidUsernameSpecialChars(); // 特殊字符
void testValidPassword();              // 有效密码
void testInvalidPasswordTooShort();    // 密码过短
void testInvalidPasswordNoLetter();    // 缺少字母
void testInvalidPasswordNoDigit();     // 缺少数字
```

#### test_user_repository.cpp (仓储测试)
```cpp
void testSaveAndFind();                // 保存和查找用户
void testFindNonexistentUser();        // 查找不存在的用户
void testUpdateFailedAttempts();       // 更新失败次数
void testUpdateLockoutTime();          // 更新锁定时间
void testInitializeTestData();         // 初始化测试数据
```

#### test_login_service.cpp (登录服务测试)
```cpp
void testSuccessfulLogin();            // 成功登录
void testFailedLoginWrongPassword();   // 密码错误
void testFailedLoginNonexistentUser(); // 用户不存在
void testAccountLockAfterThreeFailures(); // 三次失败后锁定
void testLockedAccountCannotLogin();   // 锁定账户无法登录
void testAccountUnlockAfterTimeout();  // 超时后自动解锁
void testResetFailedAttempts();        // 重置失败次数
void testPasswordHashing();            // 密码哈希功能
```

### 测试数据
```cpp
// 有效测试用户
username: "testuser"
password: "Test1234"

// 边界测试
username: "abc" (最短)
username: "a1234567890123456789" (最长20字符)
password: "Pass1234" (最短8字符)
password: "Pass12345678901234567890123456" (最长32字符)

// 无效测试
username: "ab" (过短)
username: "user@name" (特殊字符)
password: "Pass123" (过短)
password: "Password" (无数字)
password: "12345678" (无字母)
```

### 测试执行流程
1. 编译所有测试文件
2. 运行每个测试可执行文件
3. 收集测试结果
4. 生成测试报告

### CMake 测试配置
```cmake
enable_testing()

add_executable(test_user tests/test_user.cpp src/user.cpp)
add_test(NAME UserTest COMMAND test_user)

add_executable(test_validation tests/test_validation.cpp src/validation_utils.cpp)
add_test(NAME ValidationTest COMMAND test_validation)

add_executable(test_repository tests/test_user_repository.cpp 
               src/user_repository.cpp src/user.cpp)
add_test(NAME RepositoryTest COMMAND test_repository)

add_executable(test_login tests/test_login_service.cpp 
               src/login_service.cpp src/user_repository.cpp 
               src/user.cpp src/login_result.cpp src/validation_utils.cpp)
add_test(NAME LoginServiceTest COMMAND test_login)
```

### 集成测试
main.cpp 作为集成测试:
1. 初始化系统
2. 测试成功登录场景
3. 测试失败登录场景
4. 测试账户锁定场景
5. 显示所有测试结果

### 测试覆盖目标
- **单元测试覆盖率**: > 90%
- **关键路径覆盖**: 100%
- **边界条件测试**: 完整覆盖
- **错误处理测试**: 所有异常路径