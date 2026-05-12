# -*- coding: utf-8 -*-
"""
Phase 7: 生成测试文档
"""

from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext


class Phase7TestDocs(PhaseInterface):
    """Phase 7: 生成测试文档"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 7
        self.phase_name = "生成测试文档"
        self.tool_registry = tool_registry

    def execute(self) -> PhaseResult:
        """执行 Phase 7"""
        self.log("开始生成测试文档...")

        test_doc_content = self._generate_test_doc()
        test_doc_path = self.context.project_dir / 'docs' / '测试文档.md'

        result = self.tool_registry.execute_tool('file_writer', {
            'path': str(test_doc_path),
            'content': test_doc_content
        })

        if result.success:
            self.log("  [OK] 测试文档已生成")
            self.context.generated_files.append(test_doc_path)
            return PhaseResult.ok(
                "测试文档生成成功",
                file_path=str(test_doc_path),
                content_length=len(test_doc_content)
            )
        else:
            self.log(f"  [FAIL] {result.error_message}")
            return PhaseResult.fail(
                f"测试文档生成失败: {result.error_message}",
                errors=[result.error_message]
            )

    def _generate_test_doc(self) -> str:
        """生成测试文档内容"""
        return """# C++ 用户认证系统 - 测试文档

> **生成时间**: 2026-05-08
> **版本**: 1.0
> **测试框架**: 原生 C++ assert 框架

## 1. 测试概述

本文档描述了 C++ 用户认证系统的完整测试套件，覆盖所有 4 个核心需求。

## 2. 测试覆盖矩阵

| 需求 ID | 需求名称 | 测试用例数 | 覆盖范围 |
|---------|---------|-----------|---------|
| REQ-001 | 基础登录功能 | 10 | 用户名验证、密码验证、登录/登出、账户锁定 |
| REQ-002 | 密码安全 | 5 | 哈希存储、盐值生成、常量时间比较 |
| REQ-003 | 会话管理 | 6 | 会话生成、会话销毁、会话超时、记住我功能 |
| REQ-004 | 数据持久化 | 7 | JSON 存储、数据加载、用户名唯一约束 |

## 3. REQ-001: 基础登录功能测试

### 3.1 测试目标
验证用户登录功能的正确性，包括用户名和密码验证、账户锁定机制。

### 3.2 测试用例

| 测试 ID | 测试描述 | 预期结果 |
|---------|---------|---------|
| T001-01 | 用户名长度小于4字符 | 注册失败 |
| T001-02 | 用户名长度大于20字符 | 注册失败 |
| T001-03 | 正常用户名(4-20字符) | 注册成功 |
| T001-04 | 密码长度小于8字符 | 注册失败 |
| T001-05 | 密码不包含数字 | 注册失败 |
| T001-06 | 密码不包含字母 | 注册失败 |
| T001-07 | 有效密码 | 注册成功 |
| T001-08 | 正确密码登录 | 返回非空会话ID |
| T001-09 | 错误密码登录 | 返回空会话ID |
| T001-10 | 连续3次失败后锁定 | 账户被锁定，登录失败 |

## 4. REQ-002: 密码安全测试

### 4.1 测试目标
验证密码存储的安全性，包括哈希存储、盐值生成和常量时间比较。

### 4.2 测试用例

| 测试 ID | 测试描述 | 预期结果 |
|---------|---------|---------|
| T002-01 | 密码非明文存储 | 哈希值不等于明文密码 |
| T002-02 | 哈希长度验证 | 64字符(SHA256格式) |
| T002-03 | 盐值存在且非空 | 盐值长度 >= 16字节 |
| T002-04 | 相同密码不同哈希 | 两个用户相同密码哈希不同 |
| T002-05 | 相同密码不同盐值 | 两个用户使用不同盐值 |

## 5. REQ-003: 会话管理测试

### 5.1 测试目标
验证会话生命周期管理，包括会话生成、验证、销毁和超时机制。

### 5.2 测试用例

| 测试 ID | 测试描述 | 预期结果 |
|---------|---------|---------|
| T003-01 | 登录成功返回会话ID | 会话ID非空，长度32字符 |
| T003-02 | 会话ID格式验证 | 十六进制格式 |
| T003-03 | 会话ID唯一性 | 两次登录会话ID不同 |
| T003-04 | 有效会话验证通过 | is_authenticated() 返回 true |
| T003-05 | 无效会话验证失败 | is_authenticated() 返回 false |
| T003-06 | 登出后会话失效 | is_authenticated() 返回 false |

## 6. REQ-004: 数据持久化测试

### 6.1 测试目标
验证用户数据的持久化存储功能，包括保存、加载和数据一致性。

### 6.2 测试用例

| 测试 ID | 测试描述 | 预期结果 |
|---------|---------|---------|
| T004-01 | 保存用户数据到文件 | 文件成功创建 |
| T004-02 | 加载用户数据从文件 | 数据完整加载 |
| T004-03 | 用户名唯一约束 | 相同用户名注册失败 |
| T004-04 | 删除用户功能 | 用户成功删除 |
| T004-05 | 获取所有用户名 | 返回所有已注册用户名列表 |
| T004-06 | 文件格式验证 | 合法 JSON 格式 |
| T004-07 | 密码哈希完整性 | 加载后密码哈希与保存前一致 |
"""
