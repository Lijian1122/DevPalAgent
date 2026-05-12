# -*- coding: utf-8 -*-
"""
Phase 3: 生成技术设计文档
"""

from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase3TechnicalDesign(PhaseInterface):
    """Phase 3: 生成技术设计文档"""

    def __init__(self, context: OpenSpecContext):
        super().__init__(context)
        self.phase_number = 3
        self.phase_name = "生成技术设计文档"

    def execute(self) -> PhaseResult:
        """执行 Phase 3"""
        self.log("开始生成技术设计文档...")

        tech_doc_content = self._generate_tech_design_doc()

        # 写入设计文档
        tech_doc_path = self.context.project_dir / 'docs' / '技术实现文档.md'
        tech_doc_path.write_text(tech_doc_content, encoding='utf-8')

        self.context.generated_files.append(tech_doc_path)
        self.log(f"[OK] 技术设计文档已生成: {tech_doc_path}")

        return PhaseResult.ok(
            "技术设计文档生成成功",
            file_path=str(tech_doc_path),
            content_length=len(tech_doc_content)
        )

    def _generate_tech_design_doc(self) -> str:
        """生成 C++ 认证系统技术设计文档"""
        return """# C++ 用户认证系统 - 技术实现文档

> **生成时间**: 2026-05-08
> **技术栈**: C++17 STL
> **架构模式**: 面向对象 + 分层设计

---

## 0. 设计反思与决策

### 为什么选择 C++17 STL?
- **性能**: 零成本抽象，接近 C 的性能
- **可移植**: 跨平台标准，无第三方依赖
- **现代特性**: 智能指针、lambda、结构化绑定等

### 为什么选择三层架构?
- **关注点分离**: UI 逻辑、业务逻辑、数据存储分离
- **可测试性**: 业务层无外部依赖，易于单元测试
- **可扩展性**: 各层可独立替换和升级

### 为什么用 std::map 而不是 std::unordered_map?
- **有序性**: 用户名按字典序排列，便于遍历
- **稳定性**: 最坏情况 O(log n)，无哈希冲突风险
- **易用性**: 标准库支持好，代码更简洁

### 为什么用文件存储而不是数据库?
- **轻量级**: 无需数据库服务器
- **易调试**: JSON 格式可读可查
- **易部署**: 零配置，开箱即用

## 1. 系统架构设计

### 1.1 整体架构

系统采用三层架构设计：

```
┌─────────────────────────────────────────┐
│     应用层 (Application Layer)         │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │  main.cpp   │  │  命令行交互界面  │  │
│  └─────────────┘  └─────────────────┘  │
├─────────────────────────────────────────┤
│     业务层 (Business Layer)            │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Authenticator│  │   Session 类    │  │
│  └─────────────┘  └─────────────────┘  │
│  ┌─────────────┐                        │
│  │   User 类   │                        │
│  └─────────────┘                        │
├─────────────────────────────────────────┤
│     存储层 (Storage Layer)             │
│  ┌───────────────────────────────────┐  │
│  │        JSON 文件持久化             │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 1.2 核心类设计

| 类名 | 职责 | 头文件 |
|------|------|--------|
| User | 用户实体类，封装用户名、密码哈希、盐值 | auth.h |
| Session | 会话类，管理用户登录状态 | auth.h |
| Authenticator | 认证核心类，注册/登录/登出 | auth.h |

## 2. 核心 API 定义

### 2.1 Authenticator 类关键方法

```cpp
// 用户注册
bool register_user(const std::string& username, const std::string& password);

// 用户登录
std::string login(const std::string& username, const std::string& password,
                  bool remember_me = false);

// 检查认证状态
bool is_authenticated(const std::string& session_id);

// 持久化
bool save_to_file(const std::string& filename);
bool load_from_file(const std::string& filename);
```

## 3. 安全设计

### 3.1 密码安全
- 密码哈希：SHA-256 + 随机盐值
- 恒定时间比较：防止时序攻击
- 密码强度校验：至少 8 位，包含字母和数字

### 3.2 会话安全
- 32 字符随机 session_id (密码学安全)
- 会话超时：默认 30 分钟
- "记住我"功能：会话有效期延长至 7 天

## 4. 线程安全设计
- 使用 std::mutex 保护共享数据
- 所有公共方法加锁
- RAII 风格锁管理 (std::lock_guard)

## 5. 测试策略
- 单元测试覆盖率 100%
- 边界值测试
- 并发测试
- 安全攻击场景测试
"""
