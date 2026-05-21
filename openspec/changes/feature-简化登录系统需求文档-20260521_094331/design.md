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
2. LoginService 接收凭证，调用 UserRepository 查询用户
3. LoginService 验证密码哈希，检查账户锁定状态
4. 根据验证结果更新失败次数或重置计数器
5. 返回 LoginResult 给调用方

### 核心模块
- **Domain**: User（用户实体）、LoginResult（登录结果枚举）
- **Service**: LoginService（业务逻辑层）
- **Repository**: UserRepository（数据访问层）
- **Utility**: PasswordHasher（密码哈希工具）
- **Presentation**: main.cpp（演示程序）

## 2. 核心模块清单

### User（用户实体模块）
- **职责**: 表示用户数据模型
- **关键类**: `User`
- **关键成员**:
  - `std::string username`: 用户名
  - `std::string password_hash`: 密码哈希值
  - `std::string salt`: 盐值
  - `int failed_login_count`: 失败登录次数
  - `std::chrono::system_clock::time_point lockout_end_time`: 锁定结束时间

### LoginService（登录服务模块）
- **职责**: 处理登录业务逻辑、账户锁定、密码验证
- **关键类**: `LoginService`
- **关键方法**:
  - `LoginResult login(const std::string& username, const std::string& password)`: 执行登录
  - `bool isAccountLocked(const std::string& username)`: 检查账户是否锁定
  - `void recordFailedAttempt(const std::string& username)`: 记录失败尝试
  - `void resetFailedAttempts(const std::string& username)`: 重置失败计数

### UserRepository（用户仓储模块）
- **职责**: 用户数据的持久化和查询
- **关键类**: `UserRepository`
- **关键方法**:
  - `User* findByUsername(const std::string& username)`: 根据用户名查找用户
  - `void save(const User& user)`: 保存用户
  - `void updateFailedAttempts(const std::string& username, int count)`: 更新失败次数
  - `void updateLockoutTime(const std::string& username, const std::chrono::system_clock::time_point& time)`: 更新锁定时间

### PasswordHasher（密码哈希工具模块）
- **职责**: 密码哈希和验证
- **关键函数**:
  - `std::string generateSalt()`: 生成随机盐值
  - `std::string hashPassword(const std::string& password, const std::string& salt)`: 哈希密码
  - `bool verifyPassword(const std::string& password, const std::string& hash, const std::string& salt)`: 验证密码

### Validator（输入验证模块）
- **职责**: 验证用户名和密码格式
- **关键函数**:
  - `bool validateUsername(const std::string& username)`: 验证用户名格式
  - `bool validatePassword(const std::string& password)`: 验证密码格式

## 3. 关键 API 定义

### User 类
```cpp
class User {
public:
    User();
    User(const std::string& username, 
         const std::string& password_hash,
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

### LoginResult 枚举
```cpp
enum class LoginResult {
    SUCCESS,
    INVALID_CREDENTIALS,
    ACCOUNT_LOCKED,
    USER_NOT_FOUND,
    INVALID_INPUT
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
    static const int MAX_FAILED_ATTEMPTS = 3;
    static const int LOCKOUT_DURATION_MINUTES = 10;
    
    UserRepository* repository_;
    
    bool verifyPassword(const User& user, const std::string& password);
    void lockAccount(const std::string& username);
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
    
private:
    std::unordered_map<std::string, User> users_;
};
```

### PasswordHasher 工具函数
```cpp
namespace password_hasher {
    std::string generateSalt(size_t length = 16);
    std::string hashPassword(const std::string& password, const std::string& salt);
    bool verifyPassword(const std::string& password, 
                       const std::string& hash, 
                       const std::string& salt);
}
```

### Validator 工具函数
```cpp
namespace validator {
    bool validateUsername(const std::string& username);
    bool validatePassword(const std::string& password);
}
```

## 4. 数据结构与持久化

### 内存数据结构
- **用户存储**: `std::unordered_map<std::string, User>` - 以用户名为键的哈希表
- **时间点**: `std::chrono::system_clock::time_point` - 存储锁定结束时间

### 持久化策略
本迭代使用内存存储，数据在程序重启后丢失。UserRepository 在构造时初始化测试用户数据。

### 初始测试数据
```cpp
// 在 UserRepository 构造函数中初始化
User testUser("testuser", 
              hashPassword("Test1234", salt), 
              salt);
users_["testuser"] = testUser;
```

### 数据一致性
- 所有用户数据修改通过 UserRepository 进行
- 失败次数和锁定时间原子性更新
- 使用值语义避免悬空指针（返回指针时确保生命周期）

## 5. 安全与并发设计

### 安全设计

#### 密码存储
- **盐值生成**: 使用 `std::random_device` 和 `std::mt19937` 生成16字节随机盐
- **哈希算法**: 使用 `std::hash` 结合盐值进行多轮哈希（简化实现）
- **存储格式**: 仅存储哈希值和盐值，不存储明文密码

#### 账户锁定机制
- 失败3次后锁定10分钟
- 锁定时间使用 `std::chrono::system_clock::time_point` 精确记录
- 每次登录前检查当前时间与锁定结束时间

#### 输入验证
- 用户名: 3-20字符，正则验证 `^[a-zA-Z0-9_]{3,20}$`
- 密码: 8-32字符，必须包含字母和数字
- 所有输入在进入业务逻辑前验证

### 并发设计
本迭代为单线程设计，不涉及并发控制。未来扩展可考虑：
- 在 UserRepository 中使用 `std::mutex` 保护 `users_` 映射
- 使用 `std::lock_guard` 确保操作原子性

## 6. 文件组织

### 目录结构
```
simple_login/
├── include/
│   ├── user.h                    # User 类定义
│   ├── login_service.h           # LoginService 类定义
│   ├── user_repository.h         # UserRepository 类定义
│   ├── password_hasher.h         # 密码哈希工具
│   └── validator.h               # 输入验证工具
├── src/
│   ├── user.cpp                  # User 类实现
│   ├── login_service.cpp         # LoginService 类实现
│   ├── user_repository.cpp       # UserRepository 类实现
│   ├── password_hasher.cpp       # 密码哈希工具实现
│   ├── validator.cpp             # 输入验证工具实现
│   └── main.cpp                  # 演示程序
├── tests/
│   ├── test_login_service.cpp    # LoginService 单元测试
│   ├── test_validator.cpp        # Validator 单元测试
│   └── test_password_hasher.cpp  # PasswordHasher 单元测试
├── CMakeLists.txt                # CMake 构建配置
└── README.md                     # 项目说明
```

### 模块到文件映射

| 模块 | 头文件 | 源文件 | 测试文件 |
|------|--------|--------|----------|
| User | include/user.h | src/user.cpp | - |
| LoginService | include/login_service.h | src/login_service.cpp | tests/test_login_service.cpp |
| UserRepository | include/user_repository.h | src/user_repository.cpp | - |
| PasswordHasher | include/password_hasher.h | src/password_hasher.cpp | tests/test_password_hasher.cpp |
| Validator | include/validator.h | src/validator.cpp | tests/test_validator.cpp |

### 依赖关系
```
main.cpp
  └─> LoginService
       ├─> UserRepository
       │    └─> User
       ├─> PasswordHasher
       └─> Validator
```

## 7. 测试策略

### 单元测试

#### test_validator.cpp
- `TEST(ValidatorTest, ValidUsername)`: 测试合法用户名
- `TEST(ValidatorTest, InvalidUsernameTooShort)`: 测试过短用户名
- `TEST(ValidatorTest, InvalidUsernameTooLong)`: 测试过长用户名
- `TEST(ValidatorTest, InvalidUsernameSpecialChars)`: 测试非法字符
- `TEST(ValidatorTest, ValidPassword)`: 测试合法密码
- `TEST(ValidatorTest, InvalidPasswordTooShort)`: 测试过短密码
- `TEST(ValidatorTest, InvalidPasswordNoDigit)`: 测试缺少数字
- `TEST(ValidatorTest, InvalidPasswordNoLetter)`: 测试缺少字母

#### test_password_hasher.cpp
- `TEST(PasswordHasherTest, GenerateSalt)`: 测试盐值生成
- `TEST(PasswordHasherTest, HashPassword)`: 测试密码哈希
- `TEST(PasswordHasherTest, VerifyCorrectPassword)`: 测试正确密码验证
- `TEST(PasswordHasherTest, VerifyIncorrectPassword)`: 测试错误密码验证
- `TEST(PasswordHasherTest, DifferentSaltsDifferentHashes)`: 测试不同盐值产生不同哈希

#### test_login_service.cpp
- `TEST(LoginServiceTest, SuccessfulLogin)`: 测试成功登录
- `TEST(LoginServiceTest, InvalidCredentials)`: 测试错误密码
- `TEST(LoginServiceTest, UserNotFound)`: 测试用户不存在
- `TEST(LoginServiceTest, AccountLockAfterThreeFailures)`: 测试3次失败后锁定
- `TEST(LoginServiceTest, AccountUnlockAfterTimeout)`: 测试10分钟后解锁
- `TEST(LoginServiceTest, ResetFailedAttemptsAfterSuccess)`: 测试成功登录后重置计数
- `TEST(LoginServiceTest, InvalidInputFormat)`: 测试非法输入格式

### 集成测试
在 main.cpp 中提供交互式测试场景：
1. 正常登录流程
2. 错误密码3次触发锁定
3. 等待锁定时间后重新登录
4. 输入格式验证

### 测试覆盖目标
- 单元测试覆盖率 > 80%
- 所有公共 API 至少一个测试用例
- 边界条件和异常路径测试

### 测试执行
```bash
# 构建测试
mkdir build && cd build
cmake ..
make

# 运行所有测试
ctest --verbose

# 运行演示程序
./simple_login
```