#include <iostream>
#include <cassert>
#include "auth.h"

using namespace auth;

int tests_passed = 0;
int tests_failed = 0;

void test_assert(const char* test_name, bool condition) {
    if (condition) {
        std::cout << "  [OK] " << test_name << "\n";
        tests_passed++;
    } else {
        std::cout << "  [FAIL] " << test_name << "\n";
        tests_failed++;
    }
}

void test_requirement_001() {
    std::cout << "\n[REQ-001] Basic Login Tests\n";
    std::cout << "================================\n";
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
    std::cout << "\n[REQ-002] Captcha Tests\n";
    std::cout << "================================\n";
    Authenticator auth;
    std::string captcha = auth.get_new_captcha();
    test_assert("Captcha is 4 characters", captcha.size() == 4);
    test_assert("Correct captcha validates", auth.validate_captcha(captcha, captcha));
    test_assert("Wrong captcha rejected", !auth.validate_captcha("WRONG", captcha));
    test_assert("Case insensitive validation", auth.validate_captcha("abcd", "ABCD"));
}

void test_requirement_003() {
    std::cout << "\n[REQ-003] Remember Me Tests\n";
    std::cout << "================================\n";
    Authenticator auth;
    auth.register_user("rememberuser", "Password123");
    std::string session = auth.login("rememberuser", "Password123", true);
    test_assert("Remember me login works", !session.empty());
    test_assert("Session valid after remember me login", auth.is_authenticated(session));
    auth.logout(session);
    test_assert("Session invalid after logout", !auth.is_authenticated(session));
}

int main() {
    std::cout << "================================\n";
    std::cout << " C++ Authentication System Tests\n";
    std::cout << "================================\n";
    test_requirement_001();
    test_requirement_002();
    test_requirement_003();
    std::cout << "\n================================\n";
    std::cout << " Test Summary\n";
    std::cout << " Total: " << tests_passed + tests_failed << "\n";
    std::cout << " Passed: " << tests_passed << "\n";
    std::cout << " Failed: " << tests_failed << "\n";
    std::cout << "================================\n";
    return tests_failed > 0 ? 1 : 0;
}
