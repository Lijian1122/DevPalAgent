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
4. LoginService验证密码哈希值并检查账户锁定状态
5. 根据验证结果更新失败次数或重置计数器
6. 返回登录结果给调用方

### 模块依赖关系
- main.cpp → LoginService
- LoginService → User, UserRepository
- UserRepository → User
- 所有模块 → 标准库（string, chrono, memory, unordered_map）

## 2. 核心模块清单

### User（用户实体模块）
- **职责**: 封装用户数据和状态
- **关键类**: `User`
- **关键函数**: 
  - `User(username, passwordHash, salt)` - 构造函数
  - `getUsername()` - 获取用户名
  - `getPasswordHash()` - 获取密码哈希
  - `getSalt()` - 获取盐值
  - `getFailedLoginCount()` - 获取失败次数
  - `getLockoutEndTime()` - 获取锁定结束时间
  - `setFailedLoginCount(count)` - 设置失败次数
  - `setLockoutEndTime(time)` - 设置锁定时间

### LoginService（登录服务模块）
- **职责**: 处理登录业务逻辑、密码验证、账户锁定管理
- **关键类**: `LoginService`, `LoginResult`
- **关键函数**:
  - `login(username, password)` - 执行登录验证
  - `isAccountLocked(username)` - 检查账户是否锁定
  - `recordFailedAttempt(username)` - 记录失败尝试
  - `resetFailedAttempts(username)` - 重置失败计数
  - `validateUsername(username)` - 验证用户名格式
  - `validatePassword(password)` - 验证密码格式
  - `hashPassword(password, salt)` - 密码哈希计算

### UserRepository（数据访问模块）
- **职责**: 管理用户数据的存储和检索
- **关键类**: `UserRepository`
- **关键函数**:
  - `findByUsername(username)` - 查找用户
  - `save(user)` - 保存用户
  - `updateFailedAttempts(username, count)` - 更新失败次数
  - `updateLockoutTime(username, time)` - 更新锁定时间

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

### LoginResult 枚举
```cpp
enum class LoginResult {
    SUCCESS,
    INVALID_USERNAME,
    INVALID_PASSWORD,
    USER_NOT_FOUND,
    WRONG_PASSWORD,
    ACCOUNT_LOCKED
};
```

### LoginService 类
```cpp
class LoginService {
public:
    explicit LoginService(std::shared_ptr<UserRepository> repository);
    
    LoginResult login(const std::string& username, const std::string& password);
    bool isAccountLocked(const std::string& username);
    void recordFailedAttempt(const std::string& username);
    void resetFailedAttempts(const std::string& username);
    
    static bool validateUsername(const std::string& username);
    static bool validatePassword(const std::string& password);
    static std::string hashPassword(const std::string& password, 
                                    const std::string& salt);
    static std::string generateSalt();

private:
    std::shared_ptr<UserRepository> repository_;
    static constexpr int MAX_FAILED_ATTEMPTS = 3;
    static constexpr int LOCKOUT_DURATION_MINUTES = 10;
};
```

### UserRepository 类
```cpp
class UserRepository {
public:
    UserRepository();
    
    std::shared_ptr<User> findByUsername(const std::string& username);
    void save(const User& user);
    void updateFailedAttempts(const std::string& username, int count);
    void updateLockoutTime(const std::string& username, 
                          std::chrono::system_clock::time_point time);

private:
    std::unordered_map<std::string, std::shared_ptr<User>> users_;
};
```

## 4. 数据结构与持久化

### 内存数据结构
```cpp
// UserRepository 内部存储
std::unordered_map<std::string, std::shared_ptr<User>> users_;
// Key: username (string)
// Value: User对象的智能指针
```

### User 对象结构
```cpp
struct UserData {
    std::string username;           // 3-20字符
    std::string password_hash;      // SHA-256哈希值（64字符十六进制）
    std::string salt;               // 16字节随机盐值（32字符十六进制）
    int failed_login_count;         // 0-3
    std::chrono::system_clock::time_point lockout_end_time;  // 锁定结束时间
};
```

### 持久化策略
- **当前版本**: 内存存储（unordered_map）
- **初始化**: 在UserRepository构造函数中预置测试用户
- **数据生命周期**: 程序运行期间保持在内存中
- **扩展性**: 接口设计支持未来添加文件或数据库持久化

### 密码哈希算法
- 使用SHA-256算法（通过C++标准库实现）
- 每个用户使用唯一的随机盐值
- 哈希计算: `SHA256(password + salt)`
- 盐值生成: 16字节随机数据，转换为32字符十六进制字符串

## 5. 安全与并发设计

### 安全措施

#### 密码安全
- 密码永不明文存储，仅存储哈希值
- 每个用户使用唯一盐值防止彩虹表攻击
- 密码格式验证：8-32字符，必须包含字母和数字
- 使用正则表达式验证输入格式

#### 账户保护
- 失败登录计数器：最多3次失败尝试
- 自动锁定机制：失败3次后锁定10分钟
- 时间基于系统时钟（std::chrono::system_clock）
- 成功登录后自动重置失败计数器

#### 输入验证
```cpp
// 用户名验证规则
- 长度: 3-20字符
- 字符集: [a-zA-Z0-9_]
- 正则表达式: ^[a-zA-Z0-9_]{3,20}$

// 密码验证规则
- 长度: 8-32字符
- 必须包含至少一个字母
- 必须包含至少一个数字
- 正则表达式: ^(?=.*[a-zA-Z])(?=.*\d).{8,32}$
```

### 并发设计
- **当前版本**: 单线程设计，无并发访问
- **数据访问**: 直接访问unordered_map，无锁保护
- **扩展性**: 如需支持多线程，可在UserRepository中添加std::mutex保护共享数据

### 错误处理
- 使用枚举类型LoginResult表示所有可能的登录结果
- 不抛出异常，通过返回值传递错误状态
- 空指针检查：findByUsername返回nullptr时表示用户不存在

## 6. 文件组织

### 目录结构
```
simple_login/
├── CMakeLists.txt
├── include/
│   ├── user.h
│   ├── login_service.h
│   └── user_repository.h
├── src/
│   ├── user.cpp
│   ├── login_service.cpp
│   ├── user_repository.cpp
│   └── main.cpp
└── tests/
    └── test_login.cpp
```

### 文件映射

#### include/user.h
- User类声明
- 包含guards: `#ifndef USER_H`
- 依赖: `<string>`, `<chrono>`

#### src/user.cpp
- User类实现
- 构造函数、getter、setter实现

#### include/login_service.h
- LoginService类声明
- LoginResult枚举定义
- 包含guards: `#ifndef LOGIN_SERVICE_H`
- 依赖: `<string>`, `<memory>`, `"user_repository.h"`

#### src/login_service.cpp
- LoginService类实现
- 密码验证、哈希计算、账户锁定逻辑
- 依赖: `<regex>`, `<sstream>`, `<iomanip>`, `<random>`

#### include/user_repository.h
- UserRepository类声明
- 包含guards: `#ifndef USER_REPOSITORY_H`
- 依赖: `<unordered_map>`, `<memory>`, `"user.h"`

#### src/user_repository.cpp
- UserRepository类实现
- 内存数据存储管理
- 预置测试用户数据

#### src/main.cpp
- 主程序入口
- 演示登录流程
- 创建测试用户并执行登录测试场景

#### tests/test_login.cpp
- 单元测试
- 测试用例覆盖所有LoginResult场景
- 使用gtest框架或自定义test_base.h

### CMakeLists.txt 配置
```cmake
cmake_minimum_required(VERSION 3.10)
project(SimpleLogin)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# 主程序
add_executable(simple_login
    src/user.cpp
    src/login_service.cpp
    src/user_repository.cpp
    src/main.cpp
)

# 测试程序
add_executable(test_login
    src/user.cpp
    src/login_service.cpp
    src/user_repository.cpp
    tests/test_login.cpp
)
```

## 7. 测试策略

### 测试框架
- 优先使用gtest（如果可用）
- 备选方案：自定义test_base.h提供简单断言宏

### 测试文件: tests/test_login.cpp

#### 测试用例清单

**TC-001: 用户名格式验证**
- 测试有效用户名: "user123", "test_user", "ABC"
- 测试无效用户名: "ab" (太短), "a".repeat(21) (太长), "user@123" (非法字符)

**TC-002: 密码格式验证**
- 测试有效密码: "Pass1234", "abc123XYZ"
- 测试无效密码: "short1" (太短), "onlyletters" (无数字), "12345678" (无字母)

**TC-003: 成功登录**
- 前置条件: 创建用户 "testuser" / "Test1234"
- 执行: login("testuser", "Test1234")
- 预期: LoginResult::SUCCESS
- 验证: failed_login_count == 0

**TC-004: 用户不存在**
- 执行: login("nonexistent", "Pass1234")
- 预期: LoginResult::USER_NOT_FOUND

**TC-005: 密码错误**
- 前置条件: 用户 "testuser" 存在
- 执行: login("testuser", "WrongPass1")
- 预期: LoginResult::WRONG_PASSWORD
- 验证: failed_login_count == 1

**TC-006: 账户锁定机制**
- 前置条件: 用户 "testuser" 存在
- 执行: 连续3次错误密码登录
- 验证: 第3次后 LoginResult::ACCOUNT_LOCKED
- 验证: isAccountLocked("testuser") == true
- 执行: 第4次尝试登录
- 预期: LoginResult::ACCOUNT_LOCKED（即使密码正确）

**TC-007: 锁定时间过期**
- 前置条件: 账户已锁定
- 模拟: 修改lockout_end_time为过去时间
- 执行: login("testuser", "Test1234")
- 预期: LoginResult::SUCCESS
- 验证: failed_login_count == 0

**TC-008: 成功登录重置计数器**
- 前置条件: 用户有2次失败记录
- 执行: login("testuser", "Test1234")
- 预期: LoginResult::SUCCESS
- 验证: failed_login_count == 0

**TC-009: 密码哈希一致性**
- 执行: 使用相同密码和盐值多次哈希
- 验证: 所有哈希结果相同
- 执行: 使用不同盐值哈希相同密码
- 验证: 哈希结果不同

**TC-010: UserRepository数据持久性**
- 执行: 保存用户
- 执行: 通过findByUsername查找
- 验证: 返回的用户数据与保存的一致
- 执行: 更新失败次数
- 验证: 再次查找时数据已更新

### 测试数据准备
```cpp
// 预置测试用户
User testUser1("alice", hashPassword("Alice123", salt1), salt1);
User testUser2("bob", hashPassword("Bob456", salt2), salt2);
User testUser3("charlie", hashPassword("Charlie789", salt3), salt3);
```

### 测试执行
```bash
# 编译测试
mkdir build && cd build
cmake ..
make

# 运行测试
./test_login

# 运行主程序演示
./simple_login
```

### 覆盖率目标
- 代码行覆盖率: > 90%
- 分支覆盖率: > 85%
- 所有公共API必须有对应测试用例
- 所有LoginResult枚举值必须被测试覆盖