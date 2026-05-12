#include <iostream>
#include <string>
#include "auth.h"

using namespace auth;

void print_menu() {
    std::cout << "\n";
    std::cout << "================================\n";
    std::cout << "   C++ Authentication System\n";
    std::cout << "================================\n";
    std::cout << "1. Register User\n";
    std::cout << "2. Login\n";
    std::cout << "3. Logout\n";
    std::cout << "4. Query User Info\n";
    std::cout << "5. List Users\n";
    std::cout << "6. Delete User\n";
    std::cout << "7. Save Data\n";
    std::cout << "8. Load Data\n";
    std::cout << "0. Exit\n";
    std::cout << "================================\n";
    std::cout << "Please select an option: ";
    std::cout.flush();
}

int main() {
    Authenticator auth;
    auth.load_from_file("users.json");
    std::string current_session;
    std::string current_captcha;

    std::cout << "C++ Authentication System initialized successfully\n";

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
                    std::cout << "[OK] Registration successful!\n";
                } else {
                    std::cout << "[FAIL] Registration failed!\n";
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
                std::cout << "CAPTCHA: " << current_captcha << "\n";
                std::cout << "Enter captcha (case-insensitive): ";
                std::string captcha_input;
                std::getline(std::cin, captcha_input);
                if (!auth.validate_captcha(captcha_input, current_captcha)) {
                    std::cout << "[FAIL] Invalid captcha!\n";
                    break;
                }
                std::cout << "Remember me (y/n): ";
                std::string remember_str;
                std::getline(std::cin, remember_str);
                bool remember_me = (remember_str == "y" || remember_str == "Y");
                std::string session = auth.login(username, password, remember_me);
                if (!session.empty()) {
                    current_session = session;
                    std::cout << "[OK] Login successful!\n";
                } else {
                    std::cout << "[FAIL] Login failed!\n";
                }
                break;
            }
            case 3: {
                if (!current_session.empty()) {
                    auth.logout(current_session);
                    current_session.clear();
                    std::cout << "[OK] Logged out successfully!\n";
                } else {
                    std::cout << "[WARN] Not logged in!\n";
                }
                break;
            }
            case 4: {
                if (auth.is_authenticated(current_session)) {
                    std::string username = auth.get_username_from_session(current_session);
                    std::cout << "[OK] Logged in as: " << username << "\n";
                } else {
                    std::cout << "[FAIL] Session invalid or expired!\n";
                    current_session.clear();
                }
                break;
            }
            case 5: {
                auto users = auth.get_all_usernames();
                std::cout << "Total users: " << users.size() << "\n";
                for (const auto& u : users) {
                    std::cout << "  - " << u << "\n";
                }
                break;
            }
            case 6: {
                std::string username;
                std::cout << "Enter username to delete: ";
                std::getline(std::cin, username);
                if (auth.delete_user(username)) {
                    std::cout << "[OK] User deleted!\n";
                } else {
                    std::cout << "[FAIL] User not found!\n";
                }
                break;
            }
            case 7: {
                if (auth.save_to_file("users.json")) {
                    std::cout << "[OK] Data saved!\n";
                } else {
                    std::cout << "[FAIL] Save failed!\n";
                }
                break;
            }
            case 8: {
                if (auth.load_from_file("users.json")) {
                    std::cout << "[OK] Data loaded!\n";
                } else {
                    std::cout << "[FAIL] Load failed!\n";
                }
                break;
            }
            case 0: {
                std::cout << "Goodbye!\n";
                return 0;
            }
            default: {
                std::cout << "[FAIL] Invalid option!\n";
                break;
            }
        }
    }
    return 0;
}
