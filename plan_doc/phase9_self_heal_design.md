# Phase 9 Code Review 自愈机制设计方案

## 背景

当前 Phase 9 Code Review 可以检测到 Critical 问题（如不安全函数、SQL 注入等），但只是记录问题，不会自动修复。

**用户建议**：当遇到 Critical 问题时，使用类似 Phase 10 的自愈机制，基于 Plan 模式进行自动修复。

## 方案分析

### 可行性评估

#### ✅ 优点

1. **提前修复**: 在编译前就修复代码质量问题，避免进入 Phase 10
2. **减少迭代**: 不需要等到编译失败才发现问题
3. **提升质量**: 强制修复安全和性能问题
4. **复用机制**: 可以复用 Phase 10 的自愈提示词和逻辑

#### ⚠️ 挑战

1. **复杂度增加**: Phase 9 从"检查"变成"检查+修复"
2. **耗时增加**: 自愈需要调用 LLM，可能增加 30-60s
3. **风险增加**: 自动修改代码可能引入新问题
4. **边界模糊**: Phase 9 和 Phase 10 的职责重叠

### 对比分析

| 维度 | 当前方案 | 自愈方案 |
|------|---------|---------|
| **职责** | 检查 + 报告 | 检查 + 修复 + 报告 |
| **耗时** | < 1s | 30-60s（含 LLM 调用） |
| **风险** | 低（只读） | 中（修改代码） |
| **复杂度** | 低 | 中 |
| **效果** | 发现问题 | 发现 + 修复问题 |

## 设计方案

### 方案 1: Phase 9 内置自愈（推荐 ⭐⭐⭐⭐）

**架构**:
```
Phase 9: Quality Gate + Code Review + Self-Heal
├─ Layer 1: 硬性检查 (必须通过)
│  └─ 失败 → 立即终止
│
├─ Layer 2: 代码审查
│  ├─ 无 Critical 问题 → 通过
│  └─ 有 Critical 问题 → Layer 3
│
└─ Layer 3: 自愈修复 (可选)
   ├─ 分析问题
   ├─ 生成修复计划
   ├─ 执行修复
   ├─ 重新审查
   └─ 验证修复效果
```

**配置**:
```json
{
  "code_review": {
    "enabled": true,
    "check_types": ["todo", "debug", "security", "performance"],
    "fail_on_critical": false,
    "self_heal": {
      "enabled": true,
      "max_attempts": 3,
      "only_critical": true,  // 只修复 Critical 问题
      "require_approval": false  // 是否需要用户确认
    }
  }
}
```

**优点**:
- ✅ 职责集中在 Phase 9
- ✅ 配置灵活（可开关）
- ✅ 不影响 Phase 10

**缺点**:
- ⚠️ Phase 9 变得复杂
- ⚠️ 耗时增加

### 方案 2: 新增 Phase 9.5 自愈阶段

**架构**:
```
Phase 9: Quality Gate + Code Review
  ↓ (发现 Critical 问题)
Phase 9.5: Code Review Self-Heal
  ↓ (修复完成)
Phase 10: Compile + Test + Self-Heal
```

**优点**:
- ✅ 职责分离清晰
- ✅ Phase 9 保持简单
- ✅ 可以独立开关

**缺点**:
- ⚠️ 需要修改 11 阶段编号
- ⚠️ 增加流程复杂度

### 方案 3: Phase 10 前置检查

**架构**:
```
Phase 9: Quality Gate + Code Review (只检查)
  ↓ (记录 Critical 问题)
Phase 10: Pre-check + Compile + Test + Self-Heal
  ├─ Pre-check: 读取 Phase 9 的 Critical 问题
  ├─ 如果有 Critical 问题 → 先修复
  └─ 然后编译测试
```

**优点**:
- ✅ 不修改 Phase 9
- ✅ 复用 Phase 10 的自愈机制
- ✅ 不增加新阶段

**缺点**:
- ⚠️ Phase 10 变得更复杂
- ⚠️ 问题发现和修复分离

## 推荐方案：方案 1（Phase 9 内置自愈）

### 理由

1. **语义正确**: Quality Gate 应该确保代码质量，包括修复问题
2. **用户体验好**: 问题发现和修复在同一阶段，反馈及时
3. **配置灵活**: 可以通过配置开关自愈功能
4. **不影响现有流程**: Phase 10 保持不变

### 实施细节

#### 1. 自愈触发条件

```python
def _should_trigger_self_heal(self, review_issues: List[Dict]) -> bool:
    """判断是否应该触发自愈"""
    if not self.config['code_review']['self_heal']['enabled']:
        return False
    
    # 只修复 Critical 问题
    if self.config['code_review']['self_heal']['only_critical']:
        critical_issues = [i for i in review_issues if i['severity'] == 'error']
        return len(critical_issues) > 0
    
    return len(review_issues) > 0
```

#### 2. 自愈流程

```python
def _run_self_heal(self, review_issues: List[Dict]) -> Tuple[bool, List[Dict]]:
    """运行自愈修复"""
    max_attempts = self.config['code_review']['self_heal']['max_attempts']
    
    for attempt in range(1, max_attempts + 1):
        self.log(f"  [HEAL] Attempt {attempt}/{max_attempts}")
        
        # 1. 分析问题
        analysis = self._analyze_issues(review_issues)
        
        # 2. 生成修复计划
        plan = self._generate_fix_plan(analysis)
        
        # 3. 用户确认（可选）
        if self.config['code_review']['self_heal']['require_approval']:
            if not self._request_user_approval(plan):
                return False, review_issues
        
        # 4. 执行修复
        success = self._execute_fix_plan(plan)
        if not success:
            continue
        
        # 5. 重新审查
        new_issues = self._run_code_review()
        
        # 6. 验证修复效果
        if self._is_fixed(review_issues, new_issues):
            self.log(f"  [HEAL] Fixed successfully in attempt {attempt}")
            return True, new_issues
    
    self.log(f"  [HEAL] Failed after {max_attempts} attempts")
    return False, review_issues
```

#### 3. 问题分析

```python
def _analyze_issues(self, issues: List[Dict]) -> Dict[str, Any]:
    """分析问题，生成修复上下文"""
    # 按文件分组
    issues_by_file = {}
    for issue in issues:
        file = issue['file']
        if file not in issues_by_file:
            issues_by_file[file] = []
        issues_by_file[file].append(issue)
    
    # 按类别分组
    issues_by_category = {}
    for issue in issues:
        cat = issue['category']
        if cat not in issues_by_category:
            issues_by_category[cat] = []
        issues_by_category[cat].append(issue)
    
    return {
        'total_issues': len(issues),
        'critical_issues': [i for i in issues if i['severity'] == 'error'],
        'issues_by_file': issues_by_file,
        'issues_by_category': issues_by_category
    }
```

#### 4. 生成修复计划

```python
def _generate_fix_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """使用 LLM 生成修复计划"""
    prompt = self._build_fix_plan_prompt(analysis)
    
    # 调用 LLM
    response = self._call_llm(prompt)
    
    # 解析修复计划
    plan = self._parse_fix_plan(response)
    
    return plan

def _build_fix_plan_prompt(self, analysis: Dict[str, Any]) -> str:
    """构建修复计划提示词"""
    parts = []
    
    parts.append("**TASK: Generate a fix plan for code review issues**")
    parts.append("")
    
    parts.append("**CRITICAL: STRUCTURED ANALYSIS REQUIRED**")
    parts.append("You MUST provide a structured fix plan with the following sections:")
    parts.append("")
    
    parts.append("ANALYSIS:")
    parts.append("1. Issue Summary: [What issues were found?]")
    parts.append("2. Root Cause: [Why do these issues exist?]")
    parts.append("3. Impact: [What are the security/performance implications?]")
    parts.append("4. Fix Strategy: [How should we fix them?]")
    parts.append("")
    
    parts.append("FIX PLAN:")
    parts.append("For each file that needs changes:")
    parts.append("- File: [file path]")
    parts.append("- Issues: [list of issues in this file]")
    parts.append("- Changes:")
    parts.append("  - Line X: [old code] → [new code]")
    parts.append("  - Reason: [why this change fixes the issue]")
    parts.append("")
    
    parts.append("**MODIFICATION BOUNDARIES**:")
    parts.append("ALLOWED:")
    parts.append("- Replace unsafe functions with safe alternatives")
    parts.append("- Add input validation")
    parts.append("- Fix SQL injection by using parameterized queries")
    parts.append("- Remove debug output")
    parts.append("- Optimize performance bottlenecks")
    parts.append("")
    parts.append("FORBIDDEN:")
    parts.append("- Changing business logic")
    parts.append("- Removing functionality")
    parts.append("- Weakening security constraints")
    parts.append("- Breaking existing tests")
    parts.append("")
    
    # 添加问题详情
    parts.append("**ISSUES TO FIX**:")
    parts.append("")
    for file, issues in analysis['issues_by_file'].items():
        parts.append(f"File: {file}")
        for issue in issues:
            parts.append(f"  - Line {issue['line']}: [{issue['severity']}] {issue['message']}")
            parts.append(f"    Suggestion: {issue['suggestion']}")
        parts.append("")
    
    # 添加文件内容
    parts.append("**FILE CONTENTS**:")
    parts.append("")
    for file in analysis['issues_by_file'].keys():
        content = Path(file).read_text(encoding='utf-8')
        parts.append(f"=== {file} ===")
        parts.append("```cpp")
        parts.append(content)
        parts.append("```")
        parts.append("")
    
    return "\n".join(parts)
```

#### 5. 执行修复计划

```python
def _execute_fix_plan(self, plan: Dict[str, Any]) -> bool:
    """执行修复计划"""
    try:
        for file_fix in plan['file_fixes']:
            file_path = Path(file_fix['file'])
            
            # 读取原文件
            original_content = file_path.read_text(encoding='utf-8')
            
            # 应用修改
            new_content = self._apply_fixes(original_content, file_fix['changes'])
            
            # 写回文件
            file_path.write_text(new_content, encoding='utf-8')
            
            self.log(f"    [FIXED] {file_path.name}")
        
        return True
    except Exception as e:
        self.log(f"    [ERROR] Failed to execute fix plan: {e}")
        return False
```

#### 6. 验证修复效果

```python
def _is_fixed(self, old_issues: List[Dict], new_issues: List[Dict]) -> bool:
    """验证修复效果"""
    # 统计 Critical 问题数量
    old_critical = [i for i in old_issues if i['severity'] == 'error']
    new_critical = [i for i in new_issues if i['severity'] == 'error']
    
    # 如果 Critical 问题减少或消失，认为修复成功
    if len(new_critical) < len(old_critical):
        return True
    
    # 如果 Critical 问题数量相同，检查是否是相同的问题
    if len(new_critical) == len(old_critical):
        # 简单比较：如果问题描述不同，说明修复了旧问题但引入了新问题
        old_messages = set(i['message'] for i in old_critical)
        new_messages = set(i['message'] for i in new_critical)
        return old_messages != new_messages
    
    return False
```

### 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 9: Quality Gate + Code Review + Self-Heal            │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────┐
        │ Layer 1: 硬性检查                  │
        │ - CMakeLists.txt                  │
        │ - src/main.cpp                    │
        │ - test_base.h                     │
        │ - 测试文件                         │
        └───────────────────────────────────┘
                            ↓
                    ┌───────────┐
                    │ 通过？     │
                    └───────────┘
                    ↙         ↘
                失败           通过
                  ↓             ↓
            立即终止    ┌───────────────────────────────────┐
                        │ Layer 2: 代码审查                  │
                        │ - TODO/FIXME                      │
                        │ - 调试代码                         │
                        │ - 安全问题                         │
                        │ - 性能问题                         │
                        └───────────────────────────────────┘
                                    ↓
                        ┌───────────────────┐
                        │ 有 Critical 问题？ │
                        └───────────────────┘
                        ↙                 ↘
                    无                    有
                      ↓                     ↓
                  通过              ┌─────────────────┐
                                    │ 自愈启用？       │
                                    └─────────────────┘
                                    ↙               ↘
                                否                  是
                                  ↓                   ↓
                            记录问题通过    ┌───────────────────────────────────┐
                                            │ Layer 3: 自愈修复                  │
                                            │ 1. 分析问题                        │
                                            │ 2. 生成修复计划                    │
                                            │ 3. 用户确认（可选）                │
                                            │ 4. 执行修复                        │
                                            │ 5. 重新审查                        │
                                            │ 6. 验证效果                        │
                                            └───────────────────────────────────┘
                                                        ↓
                                            ┌───────────────────┐
                                            │ 修复成功？         │
                                            └───────────────────┘
                                            ↙               ↘
                                        成功                失败
                                          ↓                   ↓
                                      通过            ┌─────────────────┐
                                                      │ fail_on_critical?│
                                                      └─────────────────┘
                                                      ↙               ↘
                                                  true              false
                                                    ↓                   ↓
                                                失败              记录问题通过
```

## 实施步骤

### 第一阶段：基础自愈（P0）
1. 添加自愈配置
2. 实现问题分析
3. 实现修复计划生成
4. 实现修复执行
5. 实现修复验证

### 第二阶段：优化增强（P1）
1. 添加用户确认机制
2. 优化提示词
3. 添加修复历史记录
4. 支持回滚

### 第三阶段：高级功能（P2）
1. 支持批量修复
2. 支持增量修复
3. 学习用户偏好
4. 集成外部工具

## 风险和缓解

### 风险 1: 自动修改引入新问题
**缓解**:
- 修复后重新审查
- 限制修改范围（ALLOWED vs FORBIDDEN）
- 提供回滚机制
- 可选的用户确认

### 风险 2: 耗时增加
**缓解**:
- 只修复 Critical 问题
- 限制最大尝试次数
- 并行处理多个文件
- 可配置开关

### 风险 3: LLM 修复失败
**缓解**:
- 多次尝试（max_attempts）
- 详细的错误日志
- 降级策略（记录问题但不阻塞）
- 人工介入机制

### 风险 4: 与 Phase 10 冲突
**缓解**:
- Phase 9 只修复代码质量问题
- Phase 10 修复编译和测试问题
- 两者互补，不重叠

## 配置示例

### 开发阶段（宽松）
```json
{
  "code_review": {
    "enabled": true,
    "check_types": ["debug", "todo"],
    "fail_on_critical": false,
    "self_heal": {
      "enabled": false  // 开发时不自动修复
    }
  }
}
```

### 测试阶段（中等）
```json
{
  "code_review": {
    "enabled": true,
    "check_types": ["debug", "security"],
    "fail_on_critical": false,
    "self_heal": {
      "enabled": true,
      "max_attempts": 2,
      "only_critical": true,
      "require_approval": true  // 需要确认
    }
  }
}
```

### 发布前（严格）
```json
{
  "code_review": {
    "enabled": true,
    "check_types": ["todo", "debug", "security", "performance"],
    "fail_on_critical": true,
    "self_heal": {
      "enabled": true,
      "max_attempts": 3,
      "only_critical": true,
      "require_approval": false  // 自动修复
    }
  }
}
```

## 预期效果

### 量化指标
- **自愈成功率**: 目标 70-80%（Critical 问题）
- **耗时增加**: 30-60s（含 LLM 调用）
- **问题减少**: Phase 10 自愈次数减少 30-50%
- **代码质量**: 安全问题减少 80%+

### 用户体验
- ✅ 自动修复常见问题
- ✅ 减少手动修改
- ✅ 更早发现和修复问题
- ✅ 更完整的质量保障

## 总结

### 推荐采用方案 1（Phase 9 内置自愈）

**理由**:
1. ✅ 语义正确：Quality Gate 应该确保质量
2. ✅ 用户体验好：问题发现和修复在同一阶段
3. ✅ 配置灵活：可以开关和调整
4. ✅ 不影响现有流程：Phase 10 保持不变

**实施优先级**:
- P0: 基础自愈（分析、计划、执行、验证）
- P1: 优化增强（用户确认、历史记录、回滚）
- P2: 高级功能（批量修复、学习偏好）

**预期收益**:
- 代码质量提升 30-40%
- Phase 10 自愈次数减少 30-50%
- 安全问题减少 80%+
- 开发效率提升 20%+

---

**下一步**: 如果用户确认方案，可以开始实施 P0 阶段。
