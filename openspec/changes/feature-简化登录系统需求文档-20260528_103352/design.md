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
  - updateFailedAttempts(): 更新失败登录次数
  - updateLockoutTime(): 更新锁定时间

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

### PasswordUtils (密码工具模块)
- **职责**: 提供密码哈希和验证功能
- **核心函数**:
  - generateSalt(): 生成随机盐值
  - hashPassword(): 使用盐值哈希密码
  - verifyPassword(): 验证密码是否匹配

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
    bool updateFailedAttempts(const std::string& username, int count);
    bool updateLockoutTime(const std::string& username, 
                          const std::chrono::system_clock::time_point& time);
    
    void initializeSampleUsers();
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
    
    static bool validateUsername(const std::string& username);
    static bool validatePassword(const std::string& password);
};
```

### PasswordUtils 命名空间
```cpp
namespace PasswordUtils {
    std::string generateSalt(size_t length = 16);
    std::string hashPassword(const std::string& password, const std::string& salt);
    bool verifyPassword(const std::string& password, 
                       const std::string& hash, 
                       const std::string& salt);
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
- **键**: username (std::string)
- **值**: User 对象
- **数据结构**: `std::unordered_map<std::string, User> users_`

### UserRepository 内部存储
```cpp
class UserRepository {
private:
    std::unordered_map<std::string, User> users_;
    std::mutex mutex_;  // 线程安全保护
};
```

### 初始化数据
系统启动时通过 `initializeSampleUsers()` 创建测试用户：
- 用户名: "testuser"
- 密码: "Test1234"
- 其他用户可通过 save() 方法添加

## 5. 安全与并发设计

### 密码安全
- **盐值生成**: 使用 std::random_device 和 std::mt19937 生成16字节随机盐值
- **哈希算法**: 实现简单的哈希函数（基于 std::hash 和盐值混合）
- **存储**: 仅存储密码哈希值和盐值，不存储明文密码
- **验证**: 使用相同盐值重新哈希输入密码并比较

### 账户锁定机制
- **失败阈值**: 3次失败登录
- **锁定时长**: 10分钟
- **时间管理**: 使用 std::chrono::system_clock 记录锁定结束时间
- **检查逻辑**: 每次登录前检查当前时间是否超过 lockout_end_time_

### 并发控制
- **互斥锁**: UserRepository 使用 std::mutex 保护共享数据
- **锁定范围**: 所有读写操作（findByUsername, save, update）
- **线程安全**: 使用 std::lock_guard<std::mutex> 自动管理锁

### 输入验证
- **用户名规则**: 
  - 长度: 3-20字符
  - 字符集: [a-zA-Z0-9_]
  - 实现: 正则表达式或字符遍历
  
- **密码规则**:
  - 长度: 8-32字符
  - 必须包含至少一个字母和一个数字
  - 实现: 字符遍历检查

## 6. 文件组织

### include/ 目录
```
include/
├── user.h                 # User 类定义
├── login_result.h         # LoginResult 类定义
├── user_repository.h      # UserRepository 类定义
├── login_service.h        # LoginService 类定义
└── password_utils.h       # PasswordUtils 工具函数
```

### src/ 目录
```
src/
├── user.cpp               # User 类实现
├── login_result.cpp       # LoginResult 类实现
├── user_repository.cpp    # UserRepository 类实现
├── login_service.cpp      # LoginService 类实现
├── password_utils.cpp     # PasswordUtils 工具函数实现
└── main.cpp               # 主程序入口，演示登录流程
```

### tests/ 目录
```
tests/
├── test_user.cpp          # User 类单元测试
├── test_login_service.cpp # LoginService 类单元测试
├── test_password_utils.cpp# PasswordUtils 工具测试
└── test_user_repository.cpp# UserRepository 类测试
```

### 根目录文件
```
CMakeLists.txt             # CMake 构建配置
README.md                  # 项目说明文档
```

## 7. 测试策略

### 单元测试覆盖

#### test_user.cpp
- 测试 User 对象创建和属性访问
- 测试 failed_login_count 的设置和获取
- 测试 lockout_end_time 的设置和获取

#### test_password_utils.cpp
- 测试盐值生成的随机性和长度
- 测试密码哈希的一致性（相同输入产生相同输出）
- 测试密码验证的正确性（正确密码返回true，错误密码返回false）
- 测试不同盐值产生不同哈希

#### test_user_repository.cpp
- 测试用户保存和查找
- 测试不存在用户的查找返回nullptr
- 测试更新失败尝试次数
- 测试更新锁定时间
- 测试并发访问安全性（多线程测试）

#### test_login_service.cpp
- 测试成功登录场景
- 测试错误密码登录失败
- 测试用户名格式验证（有效和无效用户名）
- 测试密码格式验证（有效和无效密码）
- 测试失败3次后账户锁定
- 测试锁定期间登录被拒绝
- 测试锁定时间过后可以重新登录
- 测试成功登录后重置失败计数

### 集成测试

#### main.cpp 演示流程
1. 初始化系统（创建 UserRepository 和 LoginService）
2. 创建测试用户
3. 演示成功登录
4. 演示失败登录（错误密码）
5. 演示连续3次失败导致锁定
6. 演示锁定期间登录被拒绝
7. 模拟等待锁定时间结束
8. 演示锁定解除后成功登录

### 测试工具
- **框架**: Google Test (gtest) 或自定义 test_base.h
- **断言**: ASSERT_EQ, ASSERT_TRUE, ASSERT_FALSE, ASSERT_NE
- **测试运行**: 通过 CMake 配置的测试目标

### CMake 测试配置
```cmake
enable_testing()
add_executable(run_tests 
    tests/test_user.cpp
    tests/test_login_service.cpp
    tests/test_password_utils.cpp
    tests/test_user_repository.cpp
)
target_link_libraries(run_tests gtest gtest_main pthread)
add_test(NAME AllTests COMMAND run_tests)
```

### 测试覆盖目标
- 代码覆盖率: > 80%
- 所有公共 API 必须有测试
- 所有边界条件必须测试
- 所有错误路径必须测试