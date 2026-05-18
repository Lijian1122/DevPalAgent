# 自愈机制职责边界文档

**文档版本**: 1.0  
**创建日期**: 2026-05-18  
**作者**: Claude (Sonnet 4.6)  
**目的**: 明确 Phase 9 代码审查自愈和 Phase 10 测试自愈的职责边界

---

## 执行摘要

DevPalAgent 包含两个独立的自愈机制：
1. **Phase 9 代码审查自愈** - 修复静态代码分析发现的问题
2. **Phase 10 测试自愈** - 修复编译错误和测试失败

本文档明确定义两者的职责边界、触发条件、工作流程和协作方式，避免职责重叠和冲突。

---

## 1. Phase 9 代码审查自愈

### 1.1 职责范围

**主要职责**: 修复代码质量问题和安全隐患

**具体包括**:
- 移除调试代码（`std::cout`, `printf` 等）
- 替换不安全函数（`strcpy` → `strncpy`）
- 修复 SQL 注入风险（使用参数化查询）
- 实现 TODO/FIXME 标记的功能
- 添加输入验证和边界检查
- 修复性能问题（如循环中的字符串拼接）

**不包括**:
- 修复编译错误
- 修复测试失败
- 修改业务逻辑
- 添加新功能

### 1.2 触发条件

```python
def _should_trigger_self_heal(self, review_issues: List[Dict]) -> bool:
    if not self.config['code_review']['self_heal']['enabled']:
        return False
    
    if self.config['code_review']['self_heal']['only_critical']:
    critical_issues = [i for i in review_issues if i['severity'] == 'error']
        return len(critical_issues) > 0
    
    return len(review_issues) > 0
```

**触发时机**: 代码审查完成后，发现 Critical 问题（`severity == 'error'`）

**问题类型**:
- `todo`: TODO/FIXME 标记（`severity: info`）
- `debug`: 调试代码（`severity: warning`）
- `security`: 安全问题（`severity: error`）
- `performance`: 性能问题（`severity: warning`）

### 1.3 输入输出

**输入格式**: 结构化问题列表（JSON）

```json
{
  "file": "src/user.cpp",
  "line": 42,
  "severity": "error",
  "category": "security",
  "message": "Unsafe function detected: strcpy",
  "suggestion": "Use safe alternatives: strncpy"
}
```

**输出格式**: JSON 修复计划

```json
{
  "analysis": {
    "root_cause": "...",
    "issue_validity": "...",
    "fix_strategy": "...",
    "risk_assessment": "..."
  },
  "fixes": [
    {
      "file": "src/user.cpp",
      "line": 42,
      "issue_category": "security",
      "old_code": "strcpy(buffer, input);",
      "new_code": "strncpy(buffer, input, sizeof(buffer) - 1);\nbuffer[sizeof(buffer) - 1] = '\\0';",
      "reason": "Replace unsafe strcpy with safe strncpy"
    }
  ]
}
```

### 1.4 工作流程

```
1. 代码审查发现问题
   ↓
2. 判断是否触发自愈 (_should_trigger_self_heal)
   ↓
3. 分析问题 (_analyze_issues)
   ├─ 按文件分组
   ├─ 按类别分组
   └─ 生成统计摘要
   ↓
4. 生成修复计划 (_generate_fix_plan)
   ├─ 构建结构化提示词
   ├─ 调用 LLM 生成 JSON 计划
   ├─ 验证计划格式
   └─ 检测可疑关键词
   ↓
5. 执行修复 (_execute_fix_plan)
   ├─ 安全检查 (_is_fix_safe)
   ├─ 路径验证（防止路径遍历）
   ├─ 精确匹配替换
   └─ 创建备份文件
   ↓
6. 验证修复 (_verify_fix)
   ├─ 重新运行代码审查
   ├─ 比较问题数量
   └─ 检查问题签名
   ↓
7. 返回结果 (success, new_issues)
```

### 1.5 安全防护
| 防护层 | 实现 | 目的 |
|--------|------|------|
| 路径安全 | `file_path.relative_to(project_root)` | 防止路径遍历攻击 |
| 必需字段检查 | `required = ['file', 'line', 'old_code', 'new_code']` | 防止不完整修复 |
| 可疑原因检查 | `blocked_reason` 列表 | 防止危险操作 |
| 未完成标记检查 | `blocked_markers` 列表 | 防止临时修复 |
| 安全函数检查 | `unsafe_functions` 正则 | 防止引入不安全代码 |
| 精确匹配替换 | `old_code not in content` 检查 | 防止错误替换 |
| 备份机制 | `.phase9.bak` 文件 | 支持回滚 |
| 修复数量限制 | `max_fixes_per_attempt` | 防止过度修改 |

---

## 2. Phase 10 测试自愈

### 2.1 职责范围

**主要职责**: 修复编译错误和测试失败

**具体包括**:
- 修复编译错误（语法错误、类型错误、链接错误）
- 修复测试失败（断言失败、逻辑错误）
- 修复测试数据（使其符合业务规则）
- 修复实现代码（使其符合需求）
- 修复基础设施问题（创建缺失的目录）

**不包括**:
- 修复代码质量问题（应由 Phase 9 处理）
- 放松验证规则（如将密码最小长度从 8 改为 7）
- 弱化安全约束

### 2.2 触发条件

**触发时机**: 
1. 测试编译失败
2. 测试运行失败（`passed < total`）

**触发方式**: Phase 10 主动调用 `TestSelfHealer`

```python
# 编译失败
if not compile_success:
    healer.heal_compile_error(test_file, error_output, use_fallback)

# 测试失败
if passed < total:
    healer.heal_test_failure(test_file, test_output, passed, total, use_fallback)
```

### 2.3 输入输出

**输入格式**: 编译/测试错误文本

```
编译错误示例:
test_user.cpp:15:5: error: 'User' was not declared in this scope
     User user("alice", "pass1234");
     ^~~~

测试失败示例:
[FAIL] testValidUsernameFormats
  Expected: true
  Actual: false
  At: test_login_service.cpp:42
```

**输出格式**: 纯 C++ 代码

```cpp
// HEADER
#ifndef USER_H
#define USER_H
class User {
public:
    explicit User(std::string username, std::string password);
    // ...
};
#endif

// IMPLEMENTATION
#include "user.h"
User::User(std::string username, std::string password) {
    // ...
}
```

### 2.4 工作流程

```
1. 测试编译/运行失败
   ↓
2. 调用 TestSelfHealer
   ├─ heal_compile_error (编译失败)
   └─ heal_test_failure (测试失败)
   ↓
3. 查找相关源文件 (_find_related_source_files)
   ├─ src/{base_name}.cpp
   └─ include/{base_name}.h
   ↓
4. 构建修复提示词
   ├─ 强制结构化分析（4 步）
   ├─ 修改边界约束（ALLOWED/FORBIDDEN）
   ├─ 可疑关键词检测
   └─ 基础设施修复指南
   ↓
5. 调用 LLM 生成修复代码
   ├─ 提取代码块（// HEADER / // IMPLEMENTATION）
   ├─ 验证代码有效性 (_is_valid_cpp_code)
   └─ 检测可疑关键词
   ↓
6. 写入修复代码
   ├─ 验证代码长度（>= 50 字符）
   ├─ 检查 Markdown 语法
   └─ 写入文件
   ↓
7. 返回结果 (success: bool)
```

### 2.5 安全防护

| 防护层 | 实现 | 目的 |
|--------|------|------|
| 强制分析步骤 | 4 步分析（Root Cause, Test Data Validity, Implementation Correctness, Fix Decision） | 防止盲目修改 |
| 修改边界约束 | ALLOWED/FORBIDDEN 列表 | 明确允许和禁止的操作 |
| 可疑关键词检测 | `['relax', 'reduce', 'weaken', ...]` | 检测潜在的危险修改 |
| 代码有效性验证 | `_is_valid_cpp_code` | 防止返回非代码内容 |
| Markdown 检测 | 检查 `\`\`\``, `**` 等标记 | 防止返回 Markdown 格式 |
| 代码长度检查 | `len(code) >= 50` | 防止返回过短的无效代码 |

---

## 3. 职责边界对比

| 维度 | Phase 9 代码审查自愈 | Phase 10 测试自愈 |
|------|-----------------|---------------|
| **触发时机** | 代码审查发现 Critical 问题 | 测试编译失败或运行失败 |
| **输入格式** | 结构化问题列表 (JSON) | 编译/测试错误文本 |
| **输出格式** | JSON 修复计划 | 纯 C++ 代码 |
| **修复粒度** | 多文件、多行 | 单文件（测试文件或实现文件） |
| **修复类型** | 代码质量、安全问题 | 编译错误、测试失败 |
| **安全检查** | 多层检查 (_is_fix_safe) | 基础检查 (_is_valid_cpp_code) |
| **验证方式** | 重新运行代码审查 | 重新编译/运行测试 |
| **备份机制** | `.phase9.bak` | 无 |
| **提示词风格** | 结构化 JSON 输出 | 纯代码输出 |

---

## 4. 协作与冲突处理

### 4.1 正常协作流程

```
Phase 4: 生成代码
   ↓
Phase 9: 质量门禁
   ├─ 硬性结构检查
   ├─ 代码质量审查
   └─ 代码审查自愈 ✓ (修复代码质量问题)
   ↓
Phase 10: 运行测试
   ├─ 编译测试
   ├─ 运行测试
   └─ 测试自愈 ✓ (修复编译/测试失败)
   ↓
Phase 11: 生成文档
```

### 4.2 潜在冲突场景

#### 场景 1: 代码质量问题导致测试失败

**问题**: 代码中使用了不安全函数（如 `strcpy`），导致测试失败

**处理方式**:
1. Phase 9 代码审查自愈检测到 `strcpy`，生成修复计划
2. Phase 9 执行修复，替换为 `strncpy`
3. Phase 10 运行测试，如果仍然失败，测试自愈介入
4. 测试自愈修复测试失败的根本原因（可能是逻辑错误）

**关键**: Phase 9 先修复代码质量问题，Phase 10 再修复测试失败

#### 场景 2: 测试自愈引入代码质量问题

**问题**: 测试自愈为了让测试通过，引入了不安全代码

**处理方式**:
1. Phase 10 测试自愈修复测试失败
2. 如果引入了代码质量问题，Phase 9 在下一次运行时会检测到
3. **建议**: 在 Phase 10 后自动重新运行 Phase 9 代码审查

**改进方向**: 
- 在 Phase 10 中集成 Phase 9 的安全检查逻辑
- 测试自愈完成后，自动触发代码审查
#### 场景 3: 两个自愈机制都失败

**问题**: Phase 9 和 Phase 10 都无法修复问题

**处理方式**:
1. Phase 9 尝试 `max_attempts` 次（默认 3 次）
2. Phase 10 尝试 `max_attempts` 次（默认 3 次）
3. 如果都失败，生成详细的失败报告
4. 人工介入修复

---

## 5. 配置建议

### 5.1 Phase 9 配置

```json
{
  "code_review": {
    "enabled": true,
    "check_types": ["todo", "debug", "security", "performance"],
    "fail_on_critical": false,
    "max_files": 50,
    "self_heal": {
      "enabled": true,
      "max_attempts": 3,
      "only_critical": true,
      "switch_model_after": 2,
      "fallback_model": "claude-opus-4-7",
      "create_backup": true,
      "max_fixes_per_attempt": 10
    }
  }
}
```

**建议**:
- `only_critical: true` - 只修复 Critical 问题，避免过度修改
- `fail_on_critical: false` - 不因代码审查失败而终止，允许继续测试
- `create_backup: true` - 创建备份文件，支持回滚

### 5.2 Phase 10 配置

```python
# TestSelfHealer 配置
fallback_model = "claude-opus-4-7"
max_attempts = 3  # 在 Phase 10 中配置
switch_model_after = 2  # 在 Phase 10 中配置
```

**建议**:
- 与 Phase 9 使用相同的 `fallback_model`
- 与 Phase 9 使用相同的 `max_attempts` 和 `switch_model_after`

---

## 6. 最佳实践

### 6.1 何时使用代码审查自愈

✅ **适用场景**:
- 代码中有明显的代码质量问题（调试代码、不安全函数）
- 需要批量修复多个文件的相似问题
- 问题类型明确，修复方案标准化

❌ **不适用场景**:
- 编译错误（应由测试自愈处理）
- 测试失败（应由测试自愈处理）
- 需要修改业务逻辑的问题

### 6.2 何时使用测试自愈
✅ **适用场景**:
- 测试编译失败
- 测试运行失败
- 测试数据不符合业务规则
- 基础设施问题（缺失目录）

❌ **不适用场景**:
- 代码质量问题（应由代码审查自愈处理）
- 需要放松验证规则的问题
- 需要弱化安全约束的问题

### 6.3 统一安全策略

**建议**: 将 Phase 9 的安全检查逻辑提取为共享模块

```python
# devpal/core/security/fix_validator.py
class FixValidator:
    """统一的修复安全验证器"""
    
    @staticmethod
    def is_fix_safe(fix: Dict[str, Any]) -> bool:
        """验证修复是否安全"""
        # 1. 必需字段检查
        # 2. 可疑原因检查
        # 3. 未完成标记检查
        # 4. 安全函数检查
        # 5. 路径安全检查
        pass
```

**使用方式**:
- Phase 9: `FixValidator.is_fix_safe(fix)`
- Phase 10: `FixValidator.is_fix_safe(fix)` (需要适配)

---

## 7. 监控与度量

### 7.1 关键指标

| 指标 | Phase 9 | Phase 10 | 说明 |
|------|---------|-------|------|
| 触发次数 | `heal_attempts` | `heal_attempts` | 自愈尝试次数 |
| 成功次数 | `heal_success` | `heal_success` | 自愈成功次数 |
| 成功率 | `heal_success / heal_attempts` | `heal_success / heal_attempts` | 自愈成功率 |
| 模型切换次数 | `model_switches` | `model_switches` | 切换到备用模型的次数 |
| 修复问题数 | `len(old_issues) - len(new_issues)` | `total - passed` → `total - passed` | 修复的问题数量 |

### 7.2 报告生成

**Phase 9 报告**: `docs/quality_gate_report.md`

```markdown
## 3. Self-Heal Statistics

- Heal attempts: 3
- Successful fixes: 2
- Model switches: 1
```

**Phase 10 报告**: 日志输出

```
[HEAL] Attempting to fix test failures in test_user.cpp (1/3 passed, attempt #1)
[HEAL] AI Analysis:
        1. Root Cause: Password too short
        2. Test Data Validity: Invalid
        3. Implementation Correctness: Correct
        4. Fix Decision: Fix test data
[HEAL] Fixed implementation written to user.cpp
```

---

## 8. 故障排查

### 8.1 Phase 9 自愈失败

**症状**: 代码审查发现问题，但自愈失败

**排查步骤**:
1. 检查日志中的 `[HEAL]` 输出
2. 查看 AI 分析是否正确识别问题
3. 检查修复计划是否被安全检查拒绝
4. 查看 `docs/quality_gate_report.md` 中的详细信息

**常见原因**:
- LLM 返回的 JSON 格式不正确
- 修复计划包含可疑关键词
- 修复计划尝试修改项目外的文件
- 修复计划包含未完成标记（TODO/FIXME）

### 8.2 Phase 10 自愈失败

**症状**: 测试失败，但自愈失败

**排查步骤**:
1. 检查日志中的 `[HEAL]` 输出
2. 查看 AI 分析是否正确识别问题
3. 检查返回的代码是否有效
4. 查看是否检测到可疑关键词

**常见原因**:
- LLM 返回的代码包含 Markdown 语法
- LLM 返回的代码过短（< 50 字符）
- LLM 尝试放松验证规则
- LLM 返回的代码不是有效的 C++ 代码

---

## 9. 未来改进方向

### 9.1 短期改进（1-2 周）

1. **统一模型切换逻辑** ✅ (已完成)
   - 在 TestSelfHealer 中添加 `model_switched` 标志
   - 确保模型切换只计数一次

2. **添加配置验证** ✅ (已完成)
   - 验证 `max_attempts`, `switch_model_after`, `max_fixes_per_attempt` 等配置项
   - 防止无效配置导致运行时错误

3. **添加安全测试** ✅ (已完成)
   - 测试路径遍历攻击防护
   - 测试可疑修复原因检测
   - 测试不安全函数检测

### 9.2 中期改进（1-2 个月）

1. **提取共享安全模块**
   - 创建 `devpal/core/security/fix_validator.py`
   - 统一 Phase 9 和 Phase 10 的安全检查逻辑

2. **自动重新运行代码审查**
   - Phase 10 测试自愈完成后，自动触发 Phase 9 代码审查
   - 检测测试自愈是否引入代码质量问题

3. **添加更多修复模板**
   - 编译错误修复模板
   - 链接错误修复模板
   - 常见测试失败模式修复模板

### 9.3 长期改进（3-6 个月）

1. **多轮对话机制**
   - 允许 AI 在不确定时询问
   - 提供更多上下文信息

2. **学习机制**
   - 收集成功和失败的修复案例
   - 持续优化提示词

3. **更强大的模型**
   - 考虑使用 GPT-4 或更新的模型
   - 提升自愈成功率

---

## 10. 总结

### 10.1 关键要点

1. **职责分离**: Phase 9 修复代码质量问题，Phase 10 修复编译/测试失败
2. **顺序执行**: Phase 9 先执行，Phase 10 后执行，避免冲突
3. **安全优先**: 两个自愈机制都有严格的安全检查，防止危险修改
4. **可配置**: 通过配置项灵活控制自愈行为
5. **可监控**: 通过日志和报告监控自愈效果

### 10.2 决策树

```
代码生成完成
   ↓
是否有代码质量问题？
   ├─ 是 → Phase 9 代码审查自愈
   └─ 否 → 跳过
   ↓
是否有编译错误？
   ├─ 是 → Phase 10 测试自愈 (heal_compile_error)
   └─ 否 → 继续
   ↓
是否有测试失败？
   ├─ 是 → Phase 10 测试自愈 (heal_test_failure)
   └─ 否 → 完成
```

### 10.3 联系方式

如有问题或建议，请联系：
- **项目**: DevPalAgent
- **文档**: [code_review_self_healing_flow_analysis.md](code_review_self_healing_flow_analysis.md)
- **测试**: [test_phase9_security.py](../tests/test_phase9_security.py)

---

**文档结束**
