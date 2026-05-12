#include "auth.h"
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

bool Authenticator::register_user(const std::string& username, const std::string& password) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (username.size() < 4 || username.size() > 20) return false;
    if (password.size() < 8) return false;

    bool has_letter = false, has_digit = false;
    for (char c : password) {
        if (std::isalpha(c)) has_letter = true;
        if (std::isdigit(c)) has_digit = true;
    }
    if (!has_letter || !has_digit) return false;

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

    file << "# username,password_hash,salt\n";
    for (auto& pair : users_) {
        file << pair.second->get_username() << ","
             << pair.second->get_password_hash() << ","
             << pair.second->get_salt() << "\n";
    }
    return true;
}

}
