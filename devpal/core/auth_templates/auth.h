#ifndef AUTH_H
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
};

}

#endif
