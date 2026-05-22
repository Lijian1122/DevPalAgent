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
│   Domain Layer (User)           │
└─────────────────────────────────┘
```

### 数据流
1. 用户通过 main.cpp 输入用户名和密码
2. LoginService 接收登录请求，验证输入格式
3. LoginService 通过 UserRepository 查询用户
4. LoginService 检查账户锁定状态
5. LoginService 验证密码哈希
6. 根据验证结果更新失败次数或重置计数
7. 返回 LoginResult 给调用方

### 模块依赖关系
- main.cpp → LoginService
- LoginService → UserRepository, User
- UserRepository → User
- User: 独立实体，无依赖

## 2. 核心模块清单

### User (用户实体模块)
- **职责**: 封装用户数据和状态
- **核心类**: `User`
- **关键方法**: 
  - 构造函数（默认和参数化）
  - getter 方法获取用户属性
  - setter 方法更新失败次数和锁定时间

### LoginService (登录服务模块)
- **职责**: 处理登录业务逻辑、密码验证、账户锁定管理
- **核心类**: `LoginService`
- **关键方法**:
  - `login()`: 执行登录验证流程
  - `isAccountLocked()`: 检查账户是否被锁定
  - `recordFailedAttempt()`: 记录失败尝试
  - `resetFailedAttempts()`: 重置失败计数
  - `validateUsername()`: 验证用户名格式
  - `validatePassword()`: 验证密码格式
  - `hashPassword()`: 密码哈希计算
  - `verifyPassword()`: 密码验证

### UserRepository (数据访问模块)
- **职责**: 用户数据的持久化和查询
- **核心类**: `UserRepository`
- **关键方法**:
  - `findByUsername()`: 根据用户名查找用户
  - `save()`: 保存用户数据
  - `updateFailedAttempts()`: 更新失败尝试次数
  - `updateLockoutTime()`: 更新锁定时间

### LoginResult (结果封装模块)
- **职责**: 封装登录操作的结果
- **核心类**: `LoginResult`
- **关键属性**: success, message, errorCode

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
    void incrementFailedLoginCount();
    void resetFailedLoginCount();
};
```

### LoginResult 类
```cpp
enum class LoginErrorCode {
    SUCCESS = 0,
    INVALID_USERNAME_FORMAT = 1,
    INVALID_PASSWORD_FORMAT = 2,
    USER_NOT_FOUND = 3,
    ACCOUNT_LOCKED = 4,
    INVALID_CREDENTIALS = 5
};

class LoginResult {
public:
    LoginResult(bool success, const std::string& message, 
                LoginErrorCode error_code);
    
    bool isSuccess() const;
    std::string getMessage() const;
    LoginErrorCode getErrorCode() const;
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
    bool validateUsername(const std::string& username) const;
    bool validatePassword(const std::string& password) const;
    std::string hashPassword(const std::string& password, 
                            const std::string& salt) const;
    bool verifyPassword(const std::string& password, 
                       const std::string& hash, 
                       const std::string& salt) const;
    std::string generateSalt() const;
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
};
```

## 4. 数据结构与持久化

### User 数据结构
```cpp
struct UserData {
    std::string username;           // 3-20字符
    std::string password_hash;      // SHA-256 哈希结果（64字符十六进制）
    std::string salt;               // 16字节随机盐（32字符十六进制）
    int failed_login_count;         // 失败登录次数 (0-3)
    std::chrono::system_clock::time_point lockout_end_time;  // 锁定结束时间
};
```

### 持久化策略
- **内存存储**: 使用 `std::unordered_map<std::string, User>` 存储用户数据
- **键**: username (唯一标识)
- **值**: User 对象
- **初始化**: 在 UserRepository 构造时预加载测试用户

### 测试数据
```cpp
// 预置用户
username: "test_user"
password: "Test1234"
salt: 随机生成
password_hash: hashPassword("Test1234", salt)
failed_login_count: 0
lockout_end_time: epoch (未锁定)
```

## 5. 安全与并发设计

### 密码安全
- **哈希算法**: 使用 STL 实现的简单哈希（std::hash + 盐值 + 多轮迭代）
- **盐值生成**: 使用 `std::random_device` 和 `std::mt19937` 生成随机盐
- **哈希流程**:
  1. 生成 16 字节随机盐
  2. 将密码与盐拼接
  3. 使用 std::hash<std::string> 进行多轮哈希（1000轮）
  4. 转换为十六进制字符串存储

### 账户锁定机制
- **失败阈值**: 3次失败尝试
- **锁定时长**: 10分钟
- **锁定检查**: 每次登录前检查 `lockout_end_time` 是否大于当前时间
- **自动解锁**: 时间到期后自动解锁，无需手动干预

### 输入验证
- **用户名规则**: 
  - 长度: 3-20字符
  - 字符集: `[a-zA-Z0-9_]`
  - 正则表达式: `^[a-zA-Z0-9_]{3,20}$`
- **密码规则**:
  - 长度: 8-32字符
  - 必须包含至少一个字母
  - 必须包含至少一个数字
  - 验证逻辑: 遍历字符检查

### 并发设计
- **单线程模型**: 当前设计为单线程，不涉及并发
- **扩展性**: 如需支持并发，可在 UserRepository 中添加 `std::mutex` 保护共享数据

## 6. 文件组织

### 头文件 (include/)
```
include/
├── user.h                  # User 类定义
├── login_result.h          # LoginResult 和 LoginErrorCode 定义
├── login_service.h         # LoginService 类定义
└── user_repository.h       # UserRepository 类定义
```

### 源文件 (src/)
```
src/
├── user.cpp                # User 类实现
├── login_result.cpp        # LoginResult 类实现
├── login_service.cpp       # LoginService 类实现
├── user_repository.cpp     # UserRepository 类实现
└── main.cpp                # 主程序入口，演示登录流程
```

### 测试文件 (tests/)
```
tests/
├── test_user.cpp           # User 类单元测试
├── test_login_service.cpp  # LoginService 类单元测试
└── test_user_repository.cpp # UserRepository 类单元测试
```

### 构建文件
```
CMakeLists.txt              # 根目录 CMake 配置
```

### 模块映射
| 模块 | 头文件 | 源文件 | 测试文件 |
|------|--------|--------|----------|
| User | user.h | user.cpp | test_user.cpp |
| LoginResult | login_result.h | login_result.cpp | test_login_service.cpp |
| LoginService | login_service.h | login_service.cpp | test_login_service.cpp |
| UserRepository | user_repository.h | user_repository.cpp | test_user_repository.cpp |

## 7. 测试策略

### 单元测试覆盖

#### User 类测试 (test_user.cpp)
- **测试用例**:
  - `testDefaultConstructor`: 验证默认构造函数
  - `testParameterizedConstructor`: 验证参数化构造函数
  - `testGetters`: 验证所有 getter 方法
  - `testSetters`: 验证所有 setter 方法
  - `testIncrementFailedLoginCount`: 验证失败次数递增
  - `testResetFailedLoginCount`: 验证失败次数重置

#### LoginService 类测试 (test_login_service.cpp)
- **测试用例**:
  - `testValidateUsernameValid`: 验证合法用户名
  - `testValidateUsernameInvalid`: 验证非法用户名（长度、字符）
  - `testValidatePasswordValid`: 验证合法密码
  - `testValidatePasswordInvalid`: 验证非法密码（长度、缺少字母/数字）
  - `testLoginSuccess`: 验证成功登录
  - `testLoginInvalidCredentials`: 验证密码错误
  - `testLoginUserNotFound`: 验证用户不存在
  - `testLoginAccountLocked`: 验证账户锁定
  - `testRecordFailedAttempt`: 验证失败尝试记录
  - `testAccountLockAfterThreeFailures`: 验证3次失败后锁定
  - `testResetFailedAttempts`: 验证失败次数重置
  - `testHashPasswordConsistency`: 验证哈希一致性
  - `testVerifyPassword`: 验证密码验证逻辑

#### UserRepository 类测试 (test_user_repository.cpp)
- **测试用例**:
  - `testFindByUsernameExists`: 验证查找存在的用户
  - `testFindByUsernameNotExists`: 验证查找不存在的用户
  - `testSaveNewUser`: 验证保存新用户
  - `testSaveExistingUser`: 验证更新现有用户
  - `testUpdateFailedAttempts`: 验证更新失败次数
  - `testUpdateLockoutTime`: 验证更新锁定时间

### 集成测试
- **测试文件**: main.cpp 作为集成测试演示
- **测试场景**:
  1. 成功登录流程
  2. 密码错误流程
  3. 连续3次失败导致锁定
  4. 锁定期间尝试登录
  5. 锁定时间过期后成功登录

### 测试框架
- **基础框架**: 自定义 test_base.h（简单断言宏）
- **断言宏**:
  - `ASSERT_TRUE(condition)`: 断言条件为真
  - `ASSERT_FALSE(condition)`: 断言条件为假
  - `ASSERT_EQ(expected, actual)`: 断言相等
  - `ASSERT_NE(expected, actual)`: 断言不相等

### 测试执行
```bash
# 编译测试
mkdir build && cd build
cmake ..
make

# 运行所有测试
./test_user
./test_login_service
./test_user_repository

# 运行演示程序
./simple_login
```

### 测试覆盖目标
- **代码覆盖率**: 目标 >80%
- **分支覆盖**: 所有 if/else 分支
- **边界测试**: 用户名/密码长度边界、失败次数边界
- **异常场景**: 空指针、空字符串、无效输入