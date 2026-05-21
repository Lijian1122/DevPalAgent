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
- **关键方法**: 
  - 构造函数：初始化用户属性
  - getUsername(), getPasswordHash(), getSalt()
  - getFailedLoginCount(), getLockoutEndTime()
  - setFailedLoginCount(), setLockoutEndTime()

### LoginResult (登录结果模块)
- **职责**: 封装登录操作的结果状态
- **核心类**: `LoginResult`
- **关键属性**: success (bool), message (string)

### UserRepository (数据访问模块)
- **职责**: 管理用户数据的存储和检索
- **核心类**: `UserRepository`
- **关键方法**:
  - findByUsername(): 根据用户名查找用户
  - save(): 保存新用户
  - update(): 更新用户信息
  - updateFailedAttempts(): 更新失败登录次数

### LoginService (登录服务模块)
- **职责**: 实现登录业务逻辑、密码验证、账户锁定
- **核心类**: `LoginService`
- **关键方法**:
  - login(): 执行登录验证
  - isAccountLocked(): 检查账户是否被锁定
  - recordFailedAttempt(): 记录失败尝试
  - resetFailedAttempts(): 重置失败计数
  - validateUsername(): 验证用户名格式
  - validatePassword(): 验证密码格式
  - hashPassword(): 密码哈希计算
  - verifyPassword(): 密码验证

### ValidationUtils (验证工具模块)
- **职责**: 提供输入验证辅助函数
- **核心函数**:
  - isValidUsername(): 验证用户名格式
  - isValidPassword(): 验证密码格式

## 3. 关键 API 定义

### User 类
```cpp
class User {
public:
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
};
```

### LoginResult 类
```cpp
class LoginResult {
public:
    LoginResult(bool success, const std::string& message);
    
    bool isSuccess() const;
    std::string getMessage() const;
};
```

### UserRepository 类
```cpp
class UserRepository {
public:
    UserRepository();
    
    User* findByUsername(const std::string& username);
    bool save(const User& user);
    bool update(const User& user);
    bool updateFailedAttempts(const std::string& username, 
                             int count,
                             const std::chrono::system_clock::time_point& lockout_time);
};
```

### LoginService 类
```cpp
class LoginService {
public:
    LoginService(UserRepository* repository);
    
    LoginResult login(const std::string& username, const std::string& password);
    bool isAccountLocked(const std::string& username);
    void recordFailedAttempt(const std::string& username);
    void resetFailedAttempts(const std::string& username);
    
private:
    bool validateUsername(const std::string& username);
    bool validatePassword(const std::string& password);
    std::string hashPassword(const std::string& password, const std::string& salt);
    std::string generateSalt();
    bool verifyPassword(const std::string& password, 
                       const std::string& hash,
                       const std::string& salt);
};
```

### ValidationUtils 命名空间
```cpp
namespace validation_utils {
    bool isValidUsername(const std::string& username);
    bool isValidPassword(const std::string& password);
}
```

## 4. 数据结构与持久化

### User 数据结构
```cpp
class User {
private:
    std::string username_;
    std::string password_hash_;
    std::string salt_;
    int failed_login_count_;
    std::chrono::system_clock::time_point lockout_end_time_;
};
```

### 持久化策略
- **存储方式**: 内存存储（使用 std::unordered_map）
- **数据结构**: `std::unordered_map<std::string, User>` (username → User)
- **线程安全**: 使用 std::mutex 保护共享数据

### UserRepository 内部存储
```cpp
class UserRepository {
private:
    std::unordered_map<std::string, User> users_;
    mutable std::mutex mutex_;
};
```

### 密码哈希算法
- 使用简单的哈希函数（基于 std::hash 和 salt）
- Salt: 16字节随机字符串（使用 std::random_device 和 std::mt19937）
- 哈希过程: hash(password + salt) 多次迭代

## 5. 安全与并发设计

### 安全措施

#### 密码存储
- 不存储明文密码
- 使用 salt + hash 存储
- Salt 为每个用户随机生成

#### 账户锁定机制
- 失败次数阈值: 3次
- 锁定时长: 10分钟
- 锁定时间使用 std::chrono::system_clock::time_point 存储

#### 输入验证
- 用户名: 3-20字符，仅字母数字下划线
- 密码: 8-32字符，必须包含字母和数字
- 使用正则表达式或字符遍历验证

### 并发控制

#### 线程安全策略
- UserRepository 使用 std::mutex 保护内部数据
- 所有公共方法使用 std::lock_guard 加锁
- 避免死锁：单一锁策略，不嵌套锁

#### 锁定粒度
```cpp
std::lock_guard<std::mutex> lock(mutex_);
// 临界区操作
```

### 时间处理
- 使用 std::chrono::system_clock 处理时间
- 锁定检查: `current_time < lockout_end_time`
- 锁定时间计算: `current_time + std::chrono::minutes(10)`

## 6. 文件组织

### 目录结构
```
simple_login/
├── include/
│   ├── user.h
│   ├── login_result.h
│   ├── user_repository.h
│   ├── login_service.h
│   └── validation_utils.h
├── src/
│   ├── user.cpp
│   ├── login_result.cpp
│   ├── user_repository.cpp
│   ├── login_service.cpp
│   ├── validation_utils.cpp
│   └── main.cpp
├── tests/
│   ├── test_user.cpp
│   ├── test_login_service.cpp
│   └── test_validation_utils.cpp
├── CMakeLists.txt
└── README.md
```

### 文件与模块映射

#### Domain Layer
- `include/user.h` + `src/user.cpp`: User 实体类
- `include/login_result.h` + `src/login_result.cpp`: LoginResult 值对象

#### Repository Layer
- `include/user_repository.h` + `src/user_repository.cpp`: UserRepository 数据访问类

#### Service Layer
- `include/login_service.h` + `src/login_service.cpp`: LoginService 业务逻辑类

#### Utility Layer
- `include/validation_utils.h` + `src/validation_utils.cpp`: 验证工具函数

#### Application Layer
- `src/main.cpp`: 主程序入口，演示登录流程

#### Test Layer
- `tests/test_user.cpp`: User 类单元测试
- `tests/test_login_service.cpp`: LoginService 集成测试
- `tests/test_validation_utils.cpp`: 验证工具测试

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
    src/user_repository.cpp
    src/login_service.cpp
    src/validation_utils.cpp
)

# 测试程序
enable_testing()
add_executable(test_login
    tests/test_user.cpp
    tests/test_login_service.cpp
    tests/test_validation_utils.cpp
    src/user.cpp
    src/login_result.cpp
    src/user_repository.cpp
    src/login_service.cpp
    src/validation_utils.cpp
)
```

## 7. 测试策略

### 测试层次

#### 单元测试
- **User 类测试** (test_user.cpp)
  - 构造函数正确初始化
  - Getter/Setter 方法正确工作
  - 失败计数和锁定时间更新

- **ValidationUtils 测试** (test_validation_utils.cpp)
  - 有效用户名验证（3-20字符，字母数字下划线）
  - 无效用户名拒绝（过短、过长、特殊字符）
  - 有效密码验证（8-32字符，包含字母和数字）
  - 无效密码拒绝（过短、过长、缺少字母或数字）

#### 集成测试
- **LoginService 测试** (test_login_service.cpp)
  - 成功登录场景
  - 错误密码登录失败
  - 用户名不存在登录失败
  - 3次失败后账户锁定
  - 锁定期间拒绝登录
  - 锁定期过后允许登录
  - 成功登录后重置失败计数

### 测试用例设计

#### TC-001: 成功登录
- 前置条件: 用户存在，密码正确
- 操作: login("testuser", "Password123")
- 期望: LoginResult.isSuccess() == true

#### TC-002: 密码错误
- 前置条件: 用户存在
- 操作: login("testuser", "WrongPass123")
- 期望: LoginResult.isSuccess() == false

#### TC-003: 账户锁定
- 前置条件: 用户存在
- 操作: 连续3次错误密码登录
- 期望: 第4次登录返回 "账户已锁定"

#### TC-004: 锁定解除
- 前置条件: 账户已锁定
- 操作: 等待10分钟后登录
- 期望: 允许登录尝试

#### TC-005: 用户名验证
- 操作: 测试各种用户名格式
- 期望: 
  - "abc" (有效)
  - "user_123" (有效)
  - "ab" (无效，太短)
  - "user@123" (无效，特殊字符)

#### TC-006: 密码验证
- 操作: 测试各种密码格式
- 期望:
  - "Pass1234" (有效)
  - "12345678" (无效，无字母)
  - "Password" (无效，无数字)
  - "Pass12" (无效，太短)

### 测试框架
- 使用简单的自定义测试框架（test_base.h）
- 提供 ASSERT_TRUE, ASSERT_FALSE, ASSERT_EQUAL 宏
- 每个测试函数独立运行
- 输出测试结果统计

### 测试数据准备
```cpp
// 在测试开始前创建测试用户
UserRepository repo;
User test_user("testuser", 
               "hashed_password", 
               "random_salt");
repo.save(test_user);
```

### 覆盖率目标
- 代码行覆盖率: > 80%
- 分支覆盖率: > 70%
- 核心业务逻辑: 100%

### 测试执行
```bash
mkdir build && cd build
cmake ..
make
./test_login
```