# OpenSpec 11 阶段工作流实施指南 - Phase 3 插入

## 当前状态

✅ 已完成：
- 文档头部更新为 11 阶段
- 所有 Phase 编号已更新
- 设计文档已创建

⏳ 待完成：
- 在 Phase 2 和 Phase 4 之间插入 Phase 3
- 添加 `_generate_technical_design_doc` 方法

---

## 实施步骤

### Step 1: 在 Phase 2 之后插入 Phase 3 调用

在 `openspec_workflow.py` 的第 151 行（Phase 2 的 `print()` 之后）插入：

```python
        # 根据需求类型判断语言
     is_cpp = 'c++' in req_content.lower() or 'cpp' in req_content.lower()
        language = 'C++' if is_cpp else 'Python'

        # =============================================
        # Phase 3: 生成技术实现文档 ⭐ 新增阶段 - 设计先行
      # ====================================
        print("[Phase 3/11] 生成技术实现文档...")
        self._generate_technical_design_doc(req_content, language, is_cpp)
        print(f"  [OK] 技术实现文档已生成")
        print()
```

### Step 2: 删除原 Phase 3 中重复的代码

删除原 Phase 3（现在是 Phase 4）中的这两行：

```python
        # 根据需求类型生成代码
        is_cpp = 'c++' in req_content.lower() or 'cpp' in req_content.lower()
        language = 'C++' if is_cpp else 'Python'
```

因为这些代码已经在新的 Phase 3 中定义了。

### Step 3: 更新 Phase 3 的注释

将第 154 行的注释从：
```python
        # Phase 3: 生成核心实现代码
```

改为：
```python
        # Phase 4: 生成核心实现代码
```

### Step 4: 在文件末尾添加 `_generate_technical_design_doc` 方法

在 `_generate_final_report` 方法之后添加：

```python
    def _generate_technical_design_doc(self, req_content: str, language: str, is_cpp: bool):
        """生成技术实现文档 - Phase 3"""
        tech_doc_path = self.project_dir / 'docs' / 'technical_implementation.md'
        
        if is_cpp:
            tech_doc_content = f"""# C++ 用户认证系统 - 技术实现文档

> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **技术栈**: C++17 STL
> **架构模式**: 面向对象 + 分层设计

---

## 1. 系统架构设计

### 1.1 整体架构

系统采用三层架构设计：

```
┌────────────────────────────────┐
│     应用层 (Application Layer)         │
│  ┌─────────────┐  ┌───────────────┐  │
│  │  main.cpp   │  │  命令行交互界面  │  │
│  └─────────────┘  └─────────────────┘  │
├────────────────────────────┤
│   业务层 (Business Layer)            │
│  ┌──────────┐  ┌─────────────────┐  │
│  │ Authenticator│  │   Session 类    │  │
│  └─────────┘  └─────────────────┘  │
│  ┌─────────────┐                      │
│  │   User 类   │               │
│  └─────────────┘                     │
├─────────────────────────┤
│   持久层 (Persistence Layer)         │
│  ┌──────────────────────────┐ │
│        JSON 文件存储            │ │
│  └──────────────────────────┘ │
└───────────────────────────┘
```

### 1.2 核心组件职责

| 组件 | 职责 | 文件位置 |
|------|------|---------|
| User | 用户实体类，封装用户数据和状态 | include/auth.h |
| Session | 会话实体类，管理会话生命周期 | include/auth.h |
| Authenticator | 认证核心类，提供所有认证功能 | include/auth.h |

---

## 2. 数据结构设计

### 2.1 User 类数据结构

```cpp
class User {{
private:
    std::string username_;           // 用户名
    std::string password_hash_;      // 密码哈希值
    std::string salt_;               // 密码盐值
    bool is_locked_;                 // 账户是否锁定
    int failed_attempts_;            // 登录失败次数
    std::chrono::system_clock::time_point lock_time_;  // 锁定时间
}};
```

**设计要点**:
- 使用 `std::string` 存储所有字符串数据，确保内存安全
- 使用 `std::chrono::system_clock::time_point` 存储时间戳
- 所有成员变量为私有，通过公共方法访问

### 2.2 Session 类数据结构

```cpp
class Session {{
private:
    std::string session_id_;         // 会话ID (32字符十六进制)
    std::string username_;           // 关联的用户名
    std::chrono::system_clock::time_point create_time_;   // 创建时间
    std::chrono::system_clock::time_point last_active_;   // 最后活动时间
    bool remember_me_;               // 是否记住我
}};
```

---

## 3. 核心算法实现

### 3.1 SHA-256 密码哈希算法

**算法原理**: SHA-256 是 NIST 发布的密码学哈希函数

**实现步骤**:
1. 消息填充（Padding）
2. 附加长度
3. 初始化哈希值
4. 分块处理（64 轮压缩运算）
5. 输出最终 256 位哈希值

### 3.2 常量时间字符串比较

**算法目的**: 防止时序攻击（Timing Attack）

```cpp
bool constant_time_compare(const string& a, const string& b) {{
    if (a.length() != b.length()) return false;
    unsigned char result = 0;
    for (size_t i = 0; i < a.length(); i++) {{
        result |= a[i] ^ b[i];
    }}
    return result == 0;
}}
```

### 3.3 随机盐值生成算法

```cpp
std::string generate_salt() {{
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 255);
    
    std::stringstream ss;
    for (int i = 0; i < 16; i++) {{
        ss << std::hex << std::setw(2) << std::setfill('0') << dis(gen);
    }}
    return ss.str();
}}
```

---

## 4. 安全机制

### 4.1 密码安全
- SHA-256 哈希算法
- 随机盐值 (16 bytes)
- 密码强度验证

### 4.2 账户保护
- 3 次失败锁定
- 10 分钟自动解锁

### 4.3 会话安全
- 随机 session_id
- 自动过期机制

### 4.4 线程安全
- 使用 `std::mutex` 保护共享数据
- RAII 风格的锁管理

---

## 5. 性能分析

### 5.1 时间复杂度
- 注册: O(1)
- 登录: O(1)
- 会话验证: O(1)

### 5.2 空间复杂度
- 用户存储: O(n)
- 会话存储: O(m)

---

## 6. 扩展建议

### 6.1 短期改进
- 添加验证码功能
- 实现邮件通知
- 添加日志记录

### 6.2 长期优化
- 使用数据库存储
- 添加缓存层
- 实现双因素认证
- 支持 OAuth 登录

---

**文档生成**: OpenSpec 11 阶段工作流引擎 (Phase 3)
"""
        else:  # Python
            tech_doc_content = f"""# Python 用户认证系统 - 技术实现文档

> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **技术栈**: Python 3.8+
> **架构模式**: 面向对象设计

---

## 1. 系统架构设计

### 1.1 整体架构

系统采用三层架构设计：

```
┌──────────────────────────────┐
│     应用层 (Application Layer)         │
│  ┌─────────────┐  ┌─────────────┐  │
│  │  main.py    │  │  命令行交互界面  │  │
│  └─────────┘  └─────────────────┘  │
├─────────────────────────────────┤
│     业务层 (Business Layer)            │
│  ┌─────────┐  ┌─────────────────┐  │
│  │ Authenticator│  │   Session 类    │  │
│  └─────────────┘  └─────────────────┘  │
│  ┌─────────────┐             │
│  │   User 类   │                     │
│  └────────┘                        │
├──────────────────────────────────────┤
│     持久层 (Persistence Layer)         │
│  ┌──────────────┐ │
│  │        JSON 文件存储           │ │
│  └───────────────────────────────┘ │
└───────────────────────────┘
```

### 1.2 核心组件职责

| 组件 | 职责 | 文件位置 |
|------|------|---------|
| User | 用户实体类 | src/auth.py |
| Session | 会话实体类 | src/auth.py |
| Authenticator | 认证核心类 | src/auth.py |

---

## 2. 数据结构设计

### 2.1 User 类

```python
class User:
    def __init__(self, username: str, password_hash: str, salt: str):
        self.username = username
        self.password_hash = password_hash
        self.salt = salt
        self.is_locked = False
        self.failed_attempts = 0
        self.lock_time = None
```

### 2.2 Session 类

```python
class Session:
    def __init__(self, session_id: str, username: str, rember_me: bool = False):
        self.session_id = session_id
        self.username = username
        self.create_time = datetime.now()
        self.last_active = datetime.now()
        self.remember_me = remember_me
```

---

## 3. 核心算法实现

### 3.1 密码哈希算法

```python
def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode()).hexdigest()
```

### 3.2 随机盐值生成

```python
def generate_salt() -> str:
    return secrets.token_hex(16)
```

---

## 4. 安全机制

### 4.1 密码安全
- SHA-256 哈希算法
- 随机盐值 (16 bytes)

### 4.2 账户保护
- 3 次失败锁定
- 10 分钟自动解锁

### 4.3 会话安全
- 随机 session_id
- 自动过期机制

---

## 5. 性能分析

### 5.1 时间复杂度
- 注册: O(1)
- 登录: O(1)
- 会话验证: O(1)

---

## 6. 扩展建议

### 6.1 短期改进
- 添加验证码功能
- 实现邮件通知

### 6.2 长期优化
- 使用数据库存储
- 实现双因素认证

---

**文档生成**: OpenSpec 11 阶段工作流引擎 (Phase 3)
"""
     
        tech_doc_path.write_text(tech_doc_content, encoding='utf-8')
        self.phase_results['technical_design'] = {
            'success': True,
            'file': str(tech_doc_path),
            'size': len(tech_doc_content)
        }
```

---

## 验证步骤

完成修改后，运行以下命令验证：

```bash
# 1. 语法检查
python -m py_compile devpal/core/openspec_workflow.py

# 2. 运行测试
python test_new_11_phase_workflow.py

# 3. 检查生成的文件
ls -lh login_doc_first/docs/technical_implementation.md
```

---

## 预期结果

执行成功后，应该看到：

```
[Phase 1/11] 解析需求文档...
  [OK] 需求文档已读取: XXXX 字符

[Phase 2/11] 创建项目目录结构...
  [OK] 已创建 6 个目录

[Phase 3/11] 生成技术实现文档...  ⭐ 新增
  [OK] 技术实现文档已生成

[Phase 4/11] 生成核心实现代码...
  [OK] Python 核心代码已生成

[Phase 5/11] 代码质量审查...
  [OK] 代码审查完成: X 个问题

[Phase 6/11] 自动修复...
  [OK] 自动修复完成: X 个问题已修复

[Phase 7-11/11] 启动完整测试流程...
  ...
```
生成的文件应包括：
- ✅ `docs/technical_implementation.md` (Phase 3 新增，约 5-13K)
- ✅ `src/auth.py` 或 `src/auth.cpp` (Phase 4)
- ✅ `test_auth_doc.md` (Phase 7)
- ✅ `docs/OPENPEC_EXECUTION_REPORT.md` (最终报告)

---

## 关键改进

### 之前（9 阶段）
```
Phase 1 → Phase 2 → Phase 3 (生成代码) → ...
```
**问题**: 直接生成代码，缺少设计阶段

### 现在（11 阶段 - 文档先行）
```
Phase 1 → Phase 2 → Phase 3 (生成技术文档) → Phase 4 (生成代码) → ...
```
**优势**: 
- ✅ 设计先行，代码质量更高
- ✅ 技术文档指导实现
- ✅ 提前发现设计问题
- ✅ 文档和代码同步

---

**创建时间**: 2026-05-10  
**版本**: v2.0 - 文档先行架构
