# -*- coding: utf-8 -*-
"""
C++ 模板集合

所有模板内容内联，无外部文件依赖。
支持 auth/database/test/build/docs 等各类需求。
"""

from typing import List
from .base import (
    BaseTemplate, TemplateContext, GeneratedFile,
    TemplateCategory
)
from .registry import registry


@registry.register
class CppAuthHeaderTemplate(BaseTemplate):
    """C++ 认证系统头文件模板"""
    name = "cpp_auth_header"
    description = "C++ 认证系统头文件 (User/Session/Authenticator)"
    category = TemplateCategory.AUTH
    language = "cpp"
    priority = 100

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        content = '''#ifndef AUTH_H
#define AUTH_H

#include <string>
#include <map>
#include <memory>
#include <mutex>
#include <chrono>
#include <random>
#include <vector>

namespace auth {

class User {
private:
    std::string username_;
    std::string password_hash_;
    std::string salt_;
    bool is_locked_;
    int failed_attempts_;
    std::chrono::system_clock::time_point lock_time_;

public:
    User(const std::string& username, const std::string& password_hash, const std::string& salt);

    std::string get_username() const;
    std::string get_password_hash() const;
    std::string get_salt() const;
    bool is_locked() const;
    void lock();
    void unlock();
    void increment_failed_attempts();
    void reset_failed_attempts();
    int get_failed_attempts() const;
    bool should_unlock() const;
};

class Session {
private:
    std::string session_id_;
    std::string username_;
    std::chrono::system_clock::time_point create_time_;
    std::chrono::system_clock::time_point last_active_;
    bool remember_me_;

public:
    Session(const std::string& session_id, const std::string& username, bool remember_me = false);

    std::string get_session_id() const;
    std::string get_username() const;
    bool is_expired() const;
    void refresh();
    void set_remember_me(bool remember);
};

class Authenticator {
private:
    std::map<std::string, std::shared_ptr<User>> users_;
    std::map<std::string, std::shared_ptr<Session>> sessions_;
    mutable std::mutex mutex_;

    std::string generate_salt();
    std::string hash_password(const std::string& password, const std::string& salt);
    bool constant_time_compare(const std::string& a, const std::string& b);
    std::string generate_session_id();
    std::string generate_captcha();

public:
    Authenticator();
    ~Authenticator();

    bool load_from_file(const std::string& filename);
    bool save_to_file(const std::string& filename);

    bool register_user(const std::string& username, const std::string& password);
    std::string login(const std::string& username, const std::string& password, bool remember_me);
    void logout(const std::string& session_id);
    bool is_authenticated(const std::string& session_id);
    std::string get_username_from_session(const std::string& session_id);
    bool delete_user(const std::string& username);
    std::vector<std::string> get_all_usernames();

    std::string get_new_captcha();
    bool validate_captcha(const std::string& input, const std::string& expected);

    static bool validate_username(const std::string& username);
    static bool validate_password_strength(const std::string& password);
};

}

#endif
'''
        return [GeneratedFile(
            path="include/auth.h",
            content=content,
            description="认证系统核心头文件"
        )]


@registry.register
class CppAuthImplTemplate(BaseTemplate):
    """C++ 认证系统实现模板"""
    name = "cpp_auth_impl"
    description = "C++ 认证系统实现"
    category = TemplateCategory.AUTH
    language = "cpp"
    priority = 99

    def get_dependencies(self) -> List[str]:
        return ["cpp_auth_header"]

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        content = '''#include "auth.h"
#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <cctype>

namespace auth {

User::User(const std::string& username, const std::string& password_hash, const std::string& salt)
    : username_(username), password_hash_(password_hash), salt_(salt), is_locked_(false), failed_attempts_(0) {
}

std::string User::get_username() const { return username_; }
std::string User::get_password_hash() const { return password_hash_; }
std::string User::get_salt() const { return salt_; }
bool User::is_locked() const { return is_locked_; }
int User::get_failed_attempts() const { return failed_attempts_; }

void User::lock() {
    is_locked_ = true;
    lock_time_ = std::chrono::system_clock::now();
}

void User::unlock() {
    is_locked_ = false;
    failed_attempts_ = 0;
}

void User::increment_failed_attempts() {
    failed_attempts_++;
}

void User::reset_failed_attempts() {
    failed_attempts_ = 0;
}

bool User::should_unlock() const {
    if (!is_locked_) return true;
    auto now = std::chrono::system_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::minutes>(now - lock_time_);
    return duration.count() >= 10;
}

Session::Session(const std::string& session_id, const std::string& username, bool remember_me)
    : session_id_(session_id), username_(username), remember_me_(remember_me) {
    create_time_ = std::chrono::system_clock::now();
    last_active_ = create_time_;
}

std::string Session::get_session_id() const { return session_id_; }
std::string Session::get_username() const { return username_; }

void Session::refresh() {
    last_active_ = std::chrono::system_clock::now();
}

void Session::set_remember_me(bool remember) {
    remember_me_ = remember;
}

bool Session::is_expired() const {
    auto now = std::chrono::system_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::minutes>(now - last_active_);
    int timeout = remember_me_ ? 7 * 24 * 60 : 30;
    return duration.count() >= timeout;
}

Authenticator::Authenticator() {}

Authenticator::~Authenticator() {
    save_to_file("users.json");
}

std::string Authenticator::generate_salt() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 255);
    std::stringstream ss;
    for (int i = 0; i < 16; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << dis(gen);
    }
    return ss.str();
}

std::string Authenticator::hash_password(const std::string& password, const std::string& salt) {
    std::string combined = password + salt;
    uint32_t h[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                     0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    for (size_t i = 0; i < combined.size(); i++) {
        h[i % 8] ^= (uint32_t)((unsigned char)combined[i]) << ((i * 7) % 24);
    }
    std::stringstream ss;
    for (int i = 0; i < 8; i++) {
        ss << std::hex << std::setw(8) << std::setfill('0') << h[i];
    }
    return ss.str();
}

bool Authenticator::constant_time_compare(const std::string& a, const std::string& b) {
    if (a.length() != b.length()) return false;
    volatile int result = 0;
    for (size_t i = 0; i < a.length(); i++) {
        result |= ((unsigned char)a[i]) ^ ((unsigned char)b[i]);
    }
    return result == 0;
}

std::string Authenticator::generate_session_id() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 15);
    std::stringstream ss;
    for (int i = 0; i < 32; i++) {
        ss << std::hex << dis(gen);
    }
    return ss.str();
}

std::string Authenticator::generate_captcha() {
    const std::string chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, chars.size() - 1);
    std::string captcha;
    for (int i = 0; i < 4; i++) {
        captcha += chars[dis(gen)];
    }
    return captcha;
}

std::string Authenticator::get_new_captcha() {
    return generate_captcha();
}

bool Authenticator::validate_captcha(const std::string& input, const std::string& expected) {
    std::string input_upper = input;
    std::string expected_upper = expected;
    std::transform(input_upper.begin(), input_upper.end(), input_upper.begin(), ::toupper);
    std::transform(expected_upper.begin(), expected_upper.end(), expected_upper.begin(), ::toupper);
    return constant_time_compare(input_upper, expected_upper);
}

bool Authenticator::validate_username(const std::string& username) {
    if (username.size() < 4 || username.size() > 20) {
        return false;
    }
    for (char c : username) {
        if (!std::isalnum(c) && c != '_' && c != '.') {
            return false;
        }
    }
    return true;
}

bool Authenticator::validate_password_strength(const std::string& password) {
    if (password.size() < 8) {
        return false;
    }
    bool has_letter = false;
    bool has_digit = false;
    for (char c : password) {
        if (std::isalpha(c)) has_letter = true;
        if (std::isdigit(c)) has_digit = true;
    }
    return has_letter && has_digit;
}

bool Authenticator::register_user(const std::string& username, const std::string& password) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!validate_username(username)) return false;
    if (!validate_password_strength(password)) return false;

    if (users_.find(username) != users_.end()) return false;

    std::string salt = generate_salt();
    std::string hash = hash_password(password, salt);
    users_[username] = std::make_shared<User>(username, hash, salt);
    return true;
}

std::string Authenticator::login(const std::string& username, const std::string& password, bool remember_me) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = users_.find(username);
    if (it == users_.end()) return "";

    auto user = it->second;

    if (user->is_locked()) {
        if (user->should_unlock()) {
            user->unlock();
        } else {
            return "";
        }
    }

    std::string hash = hash_password(password, user->get_salt());
    if (!constant_time_compare(hash, user->get_password_hash())) {
        user->increment_failed_attempts();
        if (user->get_failed_attempts() >= 3) {
            user->lock();
        }
        return "";
    }

    user->reset_failed_attempts();

    std::string session_id = generate_session_id();
    sessions_[session_id] = std::make_shared<Session>(session_id, username, remember_me);
    return session_id;
}

void Authenticator::logout(const std::string& session_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    sessions_.erase(session_id);
}

bool Authenticator::is_authenticated(const std::string& session_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = sessions_.find(session_id);
    if (it == sessions_.end()) return false;
    if (it->second->is_expired()) {
        sessions_.erase(session_id);
        return false;
    }
    it->second->refresh();
    return true;
}

std::string Authenticator::get_username_from_session(const std::string& session_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = sessions_.find(session_id);
    if (it == sessions_.end()) return "";
    return it->second->get_username();
}

bool Authenticator::delete_user(const std::string& username) {
    std::lock_guard<std::mutex> lock(mutex_);
    return users_.erase(username) > 0;
}

std::vector<std::string> Authenticator::get_all_usernames() {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> result;
    for (auto& pair : users_) {
        result.push_back(pair.first);
    }
    return result;
}

bool Authenticator::load_from_file(const std::string& filename) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::ifstream file(filename);
    if (!file.is_open()) return false;

    users_.clear();
    sessions_.clear();

    std::string line;
    while (std::getline(file, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::stringstream ss(line);
        std::string username, hash, salt;
        std::getline(ss, username, ',');
        std::getline(ss, hash, ',');
        std::getline(ss, salt, ',');
        if (!username.empty()) {
            users_[username] = std::make_shared<User>(username, hash, salt);
        }
    }
    return true;
}

bool Authenticator::save_to_file(const std::string& filename) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::ofstream file(filename);
    if (!file.is_open()) return false;

    file << "# username,password_hash,salt\\n";
    for (auto& pair : users_) {
        file << pair.second->get_username() << ","
             << pair.second->get_password_hash() << ","
             << pair.second->get_salt() << "\\n";
    }
    return true;
}

}
'''
        return [GeneratedFile(
            path="src/auth.cpp",
            content=content,
            description="认证系统核心实现"
        )]


@registry.register
class CppMainTemplate(BaseTemplate):
    """C++ 主程序模板"""
    name = "cpp_main"
    description = "C++ 主程序入口"
    category = TemplateCategory.CORE
    language = "cpp"
    priority = 90

    def get_dependencies(self) -> List[str]:
        return ["cpp_auth_impl"]

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        content = '''#include <iostream>
#include <string>
#include "auth.h"

using namespace auth;

void print_menu() {
    std::cout << "\\n";
    std::cout << "================================\\n";
    std::cout << "   C++ Authentication System\\n";
    std::cout << "================================\\n";
    std::cout << "1. Register User\\n";
    std::cout << "2. Login\\n";
    std::cout << "3. Logout\\n";
    std::cout << "4. Query User Info\\n";
    std::cout << "5. List Users\\n";
    std::cout << "6. Delete User\\n";
    std::cout << "7. Save Data\\n";
    std::cout << "8. Load Data\\n";
    std::cout << "0. Exit\\n";
    std::cout << "================================\\n";
    std::cout << "Please select an option: ";
    std::cout.flush();
}

int main() {
    Authenticator auth;
    auth.load_from_file("users.json");
    std::string current_session;
    std::string current_captcha;

    std::cout << "C++ Authentication System initialized successfully\\n";

    while (true) {
        print_menu();
        std::string choice_str;
        std::getline(std::cin, choice_str);
        if (choice_str.empty()) continue;
        int choice = choice_str[0] - '0';

        switch (choice) {
            case 1: {
                std::string username, password;
                std::cout << "Enter username (4-20 chars): ";
                std::getline(std::cin, username);
                std::cout << "Enter password (min 8 chars, letter + digit): ";
                std::getline(std::cin, password);
                if (auth.register_user(username, password)) {
                    std::cout << "[OK] Registration successful!\\n";
                } else {
                    std::cout << "[FAIL] Registration failed!\\n";
                }
                break;
            }
            case 2: {
                std::string username, password;
                std::cout << "Enter username: ";
                std::getline(std::cin, username);
                std::cout << "Enter password: ";
                std::getline(std::cin, password);
                current_captcha = auth.get_new_captcha();
                std::cout << "CAPTCHA: " << current_captcha << "\\n";
                std::cout << "Enter captcha (case-insensitive): ";
                std::string captcha_input;
                std::getline(std::cin, captcha_input);
                if (!auth.validate_captcha(captcha_input, current_captcha)) {
                    std::cout << "[FAIL] Invalid captcha!\\n";
                    break;
                }
                std::cout << "Remember me (y/n): ";
                std::string remember_str;
                std::getline(std::cin, remember_str);
                bool remember_me = (remember_str == "y" || remember_str == "Y");
                std::string session = auth.login(username, password, remember_me);
                if (!session.empty()) {
                    current_session = session;
                    std::cout << "[OK] Login successful!\\n";
                } else {
                    std::cout << "[FAIL] Login failed!\\n";
                }
                break;
            }
            case 3: {
                if (!current_session.empty()) {
                    auth.logout(current_session);
                    current_session.clear();
                    std::cout << "[OK] Logged out successfully!\\n";
                } else {
                    std::cout << "[WARN] Not logged in!\\n";
                }
                break;
            }
            case 4: {
                if (auth.is_authenticated(current_session)) {
                    std::string username = auth.get_username_from_session(current_session);
                    std::cout << "[OK] Logged in as: " << username << "\\n";
                } else {
                    std::cout << "[FAIL] Session invalid or expired!\\n";
                    current_session.clear();
                }
                break;
            }
            case 5: {
                auto users = auth.get_all_usernames();
                std::cout << "Total users: " << users.size() << "\\n";
                for (const auto& u : users) {
                    std::cout << "  - " << u << "\\n";
                }
                break;
            }
            case 6: {
                std::string username;
                std::cout << "Enter username to delete: ";
                std::getline(std::cin, username);
                if (auth.delete_user(username)) {
                    std::cout << "[OK] User deleted!\\n";
                } else {
                    std::cout << "[FAIL] User not found!\\n";
                }
                break;
            }
            case 7: {
                if (auth.save_to_file("users.json")) {
                    std::cout << "[OK] Data saved!\\n";
                } else {
                    std::cout << "[FAIL] Save failed!\\n";
                }
                break;
            }
            case 8: {
                if (auth.load_from_file("users.json")) {
                    std::cout << "[OK] Data loaded!\\n";
                } else {
                    std::cout << "[FAIL] Load failed!\\n";
                }
                break;
            }
            case 0: {
                std::cout << "Goodbye!\\n";
                return 0;
            }
            default: {
                std::cout << "[FAIL] Invalid option!\\n";
                break;
            }
        }
    }
    return 0;
}
'''
        return [GeneratedFile(
            path="src/main.cpp",
            content=content,
            description="主程序入口"
        )]


@registry.register
class CppAuthTestTemplate(BaseTemplate):
    """C++ 认证系统测试模板"""
    name = "cpp_auth_test"
    description = "C++ 认证系统单元测试"
    category = TemplateCategory.TEST
    language = "cpp"
    priority = 80

    def get_dependencies(self) -> List[str]:
        return ["cpp_auth_header"]

    def should_apply(self, context: TemplateContext) -> bool:
        return 'test' in context.features or True

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        content = '''#include <iostream>
#include <cassert>
#include "auth.h"

using namespace auth;

int tests_passed = 0;
int tests_failed = 0;

void test_assert(const char* test_name, bool condition) {
    if (condition) {
        std::cout << "  [OK] " << test_name << "\\n";
        tests_passed++;
    } else {
        std::cout << "  [FAIL] " << test_name << "\\n";
        tests_failed++;
    }
}

void test_requirement_001() {
    std::cout << "\\n[REQ-001] Basic Login Tests\\n";
    std::cout << "================================\\n";
    Authenticator auth;
    test_assert("Short username rejected", !auth.register_user("abc", "Password123"));
    test_assert("Valid username accepted", auth.register_user("testuser", "Password123"));
    test_assert("Short password rejected", !auth.register_user("user2", "Pass12"));
    test_assert("No digit password rejected", !auth.register_user("user3", "Password"));
    test_assert("Valid password accepted", auth.register_user("validuser", "Password123"));
    std::string session = auth.login("testuser", "Password123", false);
    test_assert("Valid login returns session", !session.empty());
    test_assert("Wrong password rejected", auth.login("testuser", "WrongPass", false).empty());
}

void test_requirement_002() {
    std::cout << "\\n[REQ-002] Captcha Tests\\n";
    std::cout << "================================\\n";
    Authenticator auth;
    std::string captcha = auth.get_new_captcha();
    test_assert("Captcha is 4 characters", captcha.size() == 4);
    test_assert("Correct captcha validates", auth.validate_captcha(captcha, captcha));
    test_assert("Wrong captcha rejected", !auth.validate_captcha("WRONG", captcha));
    test_assert("Case insensitive validation", auth.validate_captcha("abcd", "ABCD"));
}

void test_requirement_003() {
    std::cout << "\\n[REQ-003] Remember Me Tests\\n";
    std::cout << "================================\\n";
    Authenticator auth;
    auth.register_user("rememberuser", "Password123");
    std::string session = auth.login("rememberuser", "Password123", true);
    test_assert("Remember me login works", !session.empty());
    test_assert("Session valid after remember me login", auth.is_authenticated(session));
    auth.logout(session);
    test_assert("Session invalid after logout", !auth.is_authenticated(session));
}

int main() {
    std::cout << "================================\\n";
    std::cout << " C++ Authentication System Tests\\n";
    std::cout << "================================\\n";
    test_requirement_001();
    test_requirement_002();
    test_requirement_003();
    std::cout << "\\n================================\\n";
    std::cout << " Test Summary\\n";
    std::cout << " Total: " << tests_passed + tests_failed << "\\n";
    std::cout << " Passed: " << tests_passed << "\\n";
    std::cout << " Failed: " << tests_failed << "\\n";
    std::cout << "================================\\n";
    return tests_failed > 0 ? 1 : 0;
}
'''
        return [GeneratedFile(
            path="tests/test_auth.cpp",
            content=content,
            description="认证系统单元测试"
        )]


@registry.register
class CppCMakeTemplate(BaseTemplate):
    """C++ CMakeLists 模板"""
    name = "cpp_cmake"
    description = "CMake 构建配置"
    category = TemplateCategory.BUILD
    language = "cpp"
    priority = 85

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        project_name = context.project_name or "AuthSystem"
        content = f'''cmake_minimum_required(VERSION 3.10)
project({project_name} VERSION 1.0 LANGUAGES CXX)

message(STATUS "========================================")
message(STATUS " DevPal C++ Authentication System")
message(STATUS " Version: ${{PROJECT_VERSION}}")
message(STATUS "========================================")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

message(STATUS "C++ Standard: C++${{CMAKE_CXX_STANDARD}}")

if(MSVC)
    message(STATUS "Compiler: MSVC")
    set(CMAKE_CXX_FLAGS_RELEASE "${{CMAKE_CXX_FLAGS_RELEASE}} /O2 /MD /W2")
    set(CMAKE_CXX_FLAGS_DEBUG "${{CMAKE_CXX_FLAGS_DEBUG}} /Od /MDd /W2 /Zi")
else()
    message(STATUS "Compiler: ${{CMAKE_CXX_COMPILER_ID}}")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

include_directories(${{PROJECT_SOURCE_DIR}}/include)

# Build library
file(GLOB SOURCES src/*.cpp)
list(REMOVE_ITEM SOURCES ${{PROJECT_SOURCE_DIR}}/src/main.cpp)
add_library(auth_lib STATIC ${{SOURCES}})

# Main executable
add_executable(auth_system src/main.cpp)
target_link_libraries(auth_system PRIVATE auth_lib)

# Test executable
enable_testing()
add_executable(test_auth tests/test_auth.cpp)
target_link_libraries(test_auth PRIVATE auth_lib)
add_test(NAME AuthSystemTests COMMAND test_auth)

message(STATUS "========================================")
message(STATUS " Configuration complete!")
message(STATUS " - auth_system: Main executable")
message(STATUS " - test_auth: Test executable")
message(STATUS "========================================")
'''
        return [GeneratedFile(
            path="CMakeLists.txt",
            content=content,
            description="CMake 构建配置"
        )]


@registry.register
class CppReadmeTemplate(BaseTemplate):
    """C++ 项目 README 模板"""
    name = "cpp_readme"
    description = "项目 README 文档"
    category = TemplateCategory.DOCS
    language = "cpp"
    priority = 70

    def should_apply(self, context: TemplateContext) -> bool:
        return 'docs' in context.features or True

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        project_name = context.project_name or "C++ 用户登录认证系统"
        content = f'''# {project_name}

> **版本**: 1.0
> **生成方式**: DevPal Agent OpenSpec
> **生成时间**: 2026-05-12

## 项目概述

完整的 C++ 用户认证系统，基于需求文档实现了所有 3 个核心需求：

- **REQ-001**: 基础登录功能（用户名/密码验证、账户锁定）
- **REQ-002**: 验证码功能（4位图形验证码）
- **REQ-003**: 记住登录状态（7天会话有效期）

## 功能特性

### REQ-001: 基础登录功能
- 用户名长度限制：4-20 字符
- 密码强度验证：至少 8 字符，包含字母和数字
- 登录成功返回会话 ID
- 连续 3 次登录失败后锁定账户 10 分钟

### REQ-002: 验证码功能
- 4 位字母数字组合验证码
- 不区分大小写验证
- 常量时间比较防止时序攻击

### REQ-003: 记住登录状态
- "记住我" 复选框支持
- 勾选后会话有效期 7 天
- 未勾选时会话有效期 30 分钟

## 项目结构

```
cpp_login_system/
├── include/
│   └── auth.h              # 核心头文件
├── src/
│   ├── auth.cpp           # 认证系统实现
│   └── main.cpp           # 主程序入口
├── tests/
│   └── test_auth.cpp      # 完整测试套件
├── docs/
│   ├── 技术实现文档.md
│   └── 测试文档.md
└── CMakeLists.txt
```

## 构建说明

### 环境要求
- Windows 10/11
- Visual Studio 2019+
- CMake 3.10+
- C++17 标准支持

### 编译步骤
```bash
mkdir build && cd build
cmake .. -G "Visual Studio 16 2019" -A x64
cmake --build . --config Release
```

### 运行程序
```bash
bin/Release/auth_system.exe
```
'''
        return [GeneratedFile(
            path="README.md",
            content=content,
            description="项目说明文档"
        )]


@registry.register
class CppSqliteTemplate(BaseTemplate):
    """C++ SQLite 数据库模板 - 纯 C++17 STL 实现（无第三方依赖）"""
    name = "cpp_sqlite"
    description = "SQLite 风格文件数据库（纯 STL 实现）"
    category = TemplateCategory.DATABASE
    language = "cpp"
    priority = 75

    def should_apply(self, context: TemplateContext) -> bool:
        return 'database' in context.features

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        db_header = '''#ifndef DB_CONNECTION_H
#define DB_CONNECTION_H

#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <sstream>
#include <optional>

namespace db {

class Row {
public:
    std::map<std::string, std::string> data;

    std::optional<std::string> get(const std::string& key) const {
        auto it = data.find(key);
        if (it != data.end()) return it->second;
        return std::nullopt;
    }

    void set(const std::string& key, const std::string& value) {
        data[key] = value;
    }
};

class Table {
public:
    std::string name;
    std::vector<std::string> columns;
    std::vector<Row> rows;

    Table() = default;
    Table(const std::string& n, const std::vector<std::string>& cols)
        : name(n), columns(cols) {}

    bool insert(const Row& row) {
        rows.push_back(row);
        return true;
    }

    std::vector<Row> select_all() const {
        return rows;
    }

    std::vector<Row> select_where(const std::string& col, const std::string& value) const {
        std::vector<Row> result;
        for (const auto& row : rows) {
            auto val = row.get(col);
            if (val && *val == value) {
                result.push_back(row);
            }
        }
        return result;
    }

    size_t delete_where(const std::string& col, const std::string& value) {
        size_t count = 0;
        auto it = rows.begin();
        while (it != rows.end()) {
            auto val = it->get(col);
            if (val && *val == value) {
                it = rows.erase(it);
                count++;
            } else {
                ++it;
            }
        }
        return count;
    }
};

class Connection {
private:
    std::string filepath_;
    std::map<std::string, Table> tables_;

public:
    Connection(const std::string& filepath) : filepath_(filepath) {}

    bool open() {
        std::ifstream file(filepath_);
        if (!file.is_open()) return true;

        std::string line;
        std::string current_table;
        std::vector<std::string> columns;

        while (std::getline(file, line)) {
            if (line.empty() || line[0] == '#') continue;

            if (line.starts_with("TABLE:")) {
                current_table = line.substr(6);
                tables_[current_table] = Table(current_table, {});
            } else if (line.starts_with("COLS:") && !current_table.empty()) {
                std::string cols_str = line.substr(5);
                std::stringstream ss(cols_str);
                std::string col;
                columns.clear();
                while (std::getline(ss, col, ',')) {
                    columns.push_back(col);
                }
                tables_[current_table].columns = columns;
            } else if (!current_table.empty() && !columns.empty()) {
                std::stringstream ss(line);
                std::string val;
                Row row;
                size_t idx = 0;
                while (std::getline(ss, val, ',') && idx < columns.size()) {
                    row.set(columns[idx], val);
                    idx++;
                }
                tables_[current_table].rows.push_back(row);
            }
        }
        return true;
    }

    bool close() {
        std::ofstream file(filepath_);
        if (!file.is_open()) return false;

        for (const auto& [name, table] : tables_) {
            file << "TABLE:" << name << "\\n";
            file << "COLS:";
            for (size_t i = 0; i < table.columns.size(); i++) {
                if (i > 0) file << ",";
                file << table.columns[i];
            }
            file << "\\n";
            for (const auto& row : table.rows) {
                for (size_t i = 0; i < table.columns.size(); i++) {
                    if (i > 0) file << ",";
                    auto val = row.get(table.columns[i]);
                    if (val) file << *val;
                }
                file << "\\n";
            }
        }
        return true;
    }

    Table* get_table(const std::string& name) {
        auto it = tables_.find(name);
        if (it != tables_.end()) return &it->second;
        return nullptr;
    }

    bool create_table(const std::string& name, const std::vector<std::string>& columns) {
        if (tables_.count(name)) return false;
        tables_[name] = Table(name, columns);
        return true;
    }
};

} // namespace db

#endif
'''
        return [
            GeneratedFile(
                path="include/db_connection.h",
                content=db_header,
                description="数据库连接头文件"
            )
        ]
