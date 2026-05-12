# -*- coding: utf-8 -*-
"""
Python 模板集合
"""

from typing import List
from .base import (
    BaseTemplate, TemplateContext, GeneratedFile,
    TemplateCategory
)
from .registry import registry


@registry.register
class PythonAuthTemplate(BaseTemplate):
    """Python 认证系统模板"""
    name = "python_auth"
    description = "Python 认证系统 (User/Session/Authenticator)"
    category = TemplateCategory.AUTH
    language = "python"
    priority = 100

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        content = '''"""
认证系统核心模块
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List


class User:
    """用户实体"""

    def __init__(self, username: str, password_hash: str, salt: str):
        self.username = username
        self.password_hash = password_hash
        self.salt = salt
        self.is_locked = False
        self.failed_attempts = 0
        self.lock_time: Optional[datetime] = None

    def lock(self):
        self.is_locked = True
        self.lock_time = datetime.now()

    def unlock(self):
        self.is_locked = False
        self.failed_attempts = 0

    def increment_failed_attempts(self):
        self.failed_attempts += 1
        if self.failed_attempts >= 3:
            self.lock()

    def should_unlock(self) -> bool:
        if not self.is_locked:
            return True
        if self.lock_time and (datetime.now() - self.lock_time) >= timedelta(minutes=10):
            return True
        return False


class Session:
    """会话管理"""

    def __init__(self, session_id: str, username: str, remember_me: bool = False):
        self.session_id = session_id
        self.username = username
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.remember_me = remember_me

    def is_expired(self) -> bool:
        now = datetime.now()
        if self.remember_me:
            return (now - self.last_active) >= timedelta(days=7)
        return (now - self.last_active) >= timedelta(minutes=30)

    def refresh(self):
        self.last_active = datetime.now()


class Authenticator:
    """认证核心"""

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}

    def _generate_salt(self) -> str:
        return secrets.token_hex(16)

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def register_user(self, username: str, password: str) -> bool:
        if not self._validate_username(username):
            return False
        if not self._validate_password_strength(password):
            return False
        if username in self.users:
            return False

        salt = self._generate_salt()
        hashed = self._hash_password(password, salt)
        self.users[username] = User(username, hashed, salt)
        return True

    def login(self, username: str, password: str, remember_me: bool = False) -> str:
        user = self.users.get(username)
        if not user:
            return ""

        if user.is_locked and not user.should_unlock():
            return ""

        hash_input = self._hash_password(password, user.salt)
        if hash_input != user.password_hash:
            user.increment_failed_attempts()
            return ""

        user.unlock() if user.is_locked else None
        session_id = secrets.token_hex(16)
        self.sessions[session_id] = Session(session_id, username, remember_me)
        return session_id

    def logout(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def is_authenticated(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if not session:
            return False
        if session.is_expired():
            del self.sessions[session_id]
            return False
        session.refresh()
        return True

    def _validate_username(self, username: str) -> bool:
        if not (4 <= len(username) <= 20):
            return False
        return all(c.isalnum() or c in '_.' for c in username)

    def _validate_password_strength(self, password: str) -> bool:
        if len(password) < 8:
            return False
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        return has_letter and has_digit

    def save_to_file(self, filename: str) -> bool:
        try:
            data = {
                'users': {
                    u.username: {
                        'password_hash': u.password_hash,
                        'salt': u.salt
                    } for u in self.users.values()
                }
            }
            Path(filename).write_text(json.dumps(data, indent=2))
            return True
        except Exception:
            return False

    def load_from_file(self, filename: str) -> bool:
        try:
            data = json.loads(Path(filename).read_text())
            for username, user_data in data.get('users', {}).items():
                self.users[username] = User(
                    username,
                    user_data['password_hash'],
                    user_data['salt']
                )
            return True
        except Exception:
            return False

'''
        return [GeneratedFile(
            path="src/auth.py",
            content=content,
            description="Python 认证系统核心模块"
        )]


@registry.register
class PythonMainTemplate(BaseTemplate):
    """Python 主程序模板"""
    name = "python_main"
    description = "Python 主程序入口"
    category = TemplateCategory.CORE
    language = "python"
    priority = 90

    def generate(self, context: TemplateContext) -> List[GeneratedFile]:
        content = '''#!/usr/bin/env python3
"""
主程序入口
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from auth import Authenticator


def print_menu():
    """打印主菜单"""
    print("\\n" + "=" * 50)
    print("  用户认证系统")
    print("=" * 50)
    print("  1. 注册用户")
    print("  2. 用户登录")
    print("  3. 退出登录")
    print("  4. 检查认证状态")
    print("  5. 保存数据")
    print("  6. 加载数据")
    print("  0. 退出程序")
    print("=" * 50)


def main():
    auth = Authenticator()
    current_session = None

    while True:
        print_menu()
        choice = input("\\n请选择操作: ").strip()

        if choice == "0":
            print("再见!")
            break

        elif choice == "1":
            username = input("用户名: ").strip()
            password = input("密码: ").strip()
            if auth.register_user(username, password):
                print("✅ 注册成功!")
            else:
                print("❌ 注册失败!")

        elif choice == "2":
            username = input("用户名: ").strip()
            password = input("密码: ").strip()
            remember = input("记住我? (y/n): ").strip().lower() == 'y'
            session = auth.login(username, password, remember)
            if session:
                current_session = session
                print(f"✅ 登录成功! Session: {session}")
            else:
                print("❌ 登录失败!")

        elif choice == "3":
            if current_session:
                auth.logout(current_session)
                current_session = None
                print("✅ 已退出登录")
            else:
                print("⚠️ 当前未登录")

        elif choice == "4":
            if current_session and auth.is_authenticated(current_session):
                print("✅ 已认证")
            else:
                print("❌ 未认证")

        elif choice == "5":
            if auth.save_to_file("users.json"):
                print("✅ 保存成功!")
            else:
                print("❌ 保存失败!")

        elif choice == "6":
            if auth.load_from_file("users.json"):
                print("✅ 加载成功!")
            else:
                print("❌ 加载失败!")

        else:
            print("⚠️ 无效选择")


if __name__ == "__main__":
    main()
'''
        return [GeneratedFile(
            path="src/main.py",
            content=content,
            description="Python 主程序"
        )]
