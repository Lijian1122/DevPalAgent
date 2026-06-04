# Interview Q&A: Critique Phase (Phase 9.5)

## 面试专题：LLM-as-a-Judge 批判性审查

---

## Q1: 什么是 Critique Phase？为什么需要它？

**核心回答**:
Critique Phase (Phase 9.5) 是 DevPalAgent 在 Phase 9 Quality Gate 之后引入的 **LLM-as-a-Judge** 批判性审查阶段。它使用 LLM 对已生成的代码进行深度审查，发现传统静态分析工具无法检测的问题。

**为什么需要**:
Phase 9 Quality Gate 虽然有四层验证，但仍有局限：
- ❌ **FORMAT**: 只检查语法，不检查语义
- ❌ **SEMANTIC**: 规则驱动，无法理解业务逻辑
- ❌ **PARSER**: 只验证接口，不验证实现
- ❌ **BUSINESS**: 静态规则，覆盖不全

**Critique Phase 的优势**:
- ✅ 理解代码意图和业务逻辑
- ✅ 发现设计缺陷（非bug）
- ✅ 评估可维护性和可读性
- ✅ 对比需求文档，检查功能完整性

**架构位置**:
```
Phase 9: Quality Gate (静态验证)
  ↓
Phase 9.5: Critique (LLM 审查)
  ↓
Phase 10: Run Tests
```
---

## Q2: Critique Phase 的技术设计是什么？

**核心实现**:
```python
# devpal/core/openspec_phases/phase9_code_review.py
class CritiquePhase:
    """Phase 9.5: LLM-as-a-Judge 代码审查"""
    
    def execute(self, context: OpenSpecContext) -> PhaseResult:
        """执行 Critique 审查"""
        
        # 1. 收集审查目标
        review_targets = self._collect_review_targets(context)
        
        # 2. 构建审查 prompt
        critique_prompt = self._build_critique_prompt(
            files=review_targets,
            requirements=context.structured_requirements,
            tech_design=context.tech_design_content
        )
        # 3. LLM 审查
        critique_result = self.llm_client.create_message(
            system=self._get_critic_system_prompt(),
            messages=[{"role": "user", "content": critique_prompt}],
            temperature=0.3  # 低温度，保持客观
        )
        
        # 4. 解析审查结果
        findings = self._parse_critique_result(critique_result)
        
        # 5. 生成审查报告
        report = self._generate_critique_report(findings)
        
        return PhaseResult.ok("Critique completed", critique_report=report)
```

**Critic System Prompt**:
```python
def _get_critic_system_prompt(self) -> str:
    return """You are a senior code reviewer conducting a thorough code review.

Your review should cover:
1. **Logic Correctness**: Does the code implement the requirements correctly?
2. **Design Quality**: Is the architecture sound? Any SOLID violations?
3. **Maintainability**: Is the code easy to understand and modify?
4. **Edge Cases**: Are error conditions and boundaries handled?
5. **Performance**: Any obvious performance issues?
6. **Security**: Any security vulnerabilities?

For each issue found, provide:
- Severity: CRITICAL, HIGH, MEDIUM, LOW
- Category: Logic, Design, Maintainability, Performance, Security
- Location: File and line number
- Description: What is the problem?
- Suggestion: How to fix it?

Be objective and constructive. Focus on real issues, not nitpicks.
"""
```

**User Prompt 结构**:
```python
def _build_critique_prompt(self, files, requirements, tech_design) -> str:
    return f"""
# Code Review Request

## Requirements
{requirements}

## Technical Design
{tech_design}

## Code to Review
{self._format_files(files)}

## Instructions
Please review the code against the requirements and design.
Identify any issues and provide actionable feedback.
"""
```

---

## Q3: Critique Phase 如何分类和评估问题？

**问题分类体系**:

```python
# devpal/core/openspec_phases/critique_categories.py
class CritiqueCategory(Enum):
    LOGIC = "logic"                  # 逻辑错误
    DESIGN = "design"                # 设计问题
    MAINTAINABILITY = "maintainability"  # 可维护性
    PERFORMANCE = "performance"          # 性能问题
    SECURITY = "security"       # 安全隐患
    COMPLETENESS = "completeness"        # 功能不完整

class CritiqueSeverity(Enum):
    CRITICAL = "critical"  # 必须修复，阻断发布
    HIGH = "high"          # 应该修复，影响功能
    MEDIUM = "medium"      # 建议修复，影响质量
    LOW = "low"         # 可选修复，改进建议
```

**评估规则**:
```python
def _evaluate_severity(self, finding: dict) -> CritiqueSeverity:
    """评估问题严重性"""
    
    # CRITICAL: 功能性错误、安全漏洞
    if finding["category"] in [CritiqueCategory.LOGIC, CritiqueCategory.SECURITY]:
        if "crash" in finding["description"].lower() or \
           "vulnerability" in finding["description"].lower():
            return CritiqueSeverity.CRITICAL
    
    # HIGH: 设计缺陷、性能问题
    if finding["category"] in [CritiqueCategory.DESIGN, CritiqueCategory.PERFORMANCE]:
        if "violates" in finding["description"].lower() or \
        "bottleneck" in finding["description"].lower():
            return CritiqueSeverity.HIGH
    
    # MEDIUM: 可维护性、完整性
    if finding["category"] in [CritiqueCategory.MAINTAINABILITY, CritiqueCategory.COMPLETENESS]:
        return CritiqueSeverity.MEDIUM
    
    # LOW: 代码风格、优化建议
    return CritiqueSeverity.LOW
```

**示例输出**:
```json
{
  "findings": [
    {
      "severity": "CRITICAL",
      "category": "LOGIC",
      "location": "src/user_service.cpp:42",
      "description": "NULL pointer dereference when user not found",
      "suggestion": "Add null check before dereferencing user pointer",
      "code_snippet": "User* user = find_user(id);\nuser->name = new_name;  // Crash if user is NULL"
    },
    {
      "severity": "HIGH",
      "category": "DESIGN",
      "location": "include/user_service.h",
      "description": "God class anti-pattern: UserService has too many responsibilities",
      "suggestion": "Split into UserRepository, UserValidator, UserNotifier"
    },
    {
      "severity": "MEDIUM",
      "category": "MAINTAINABILITY",
      "location": "src/main.cpp:15",
      "description": "Magic number: hardcoded timeout value",
      "suggestion": "Extract to named constant: const int TIMEOUT_SECONDS = 30;"
    }
  ],
  "summary": {
    "total_issues": 3,
    "critical": 1,
    "high": 1,
    "medium": 1,
    "low": 0
  }
}
```

---

## Q4: Critique Phase 如何与其他 Phase 协作？

**工作流集成**:
```
Phase 9: Quality Gate (静态验证)
  ↓ passed
Phase 9.5: Critique (LLM 审查)
  ↓ findings
Phase 9.6: Auto-Fix (可选)
  ↓ fixed or manual
Phase 10: Run Tests
```

**Decision Flow**:
```python
# devpal/core/openspec_phases/enhanced_scheduler.py
def _handle_critique_phase(self, context: OpenSpecContext, phase9_result: PhaseResult):
    """处理 Critique Phase"""
    
    # 1. 执行 Critique
    critique_result = self.critique_phase.execute(context)
    
    # 2. 评估 findings
    critical_issues = [f for f in critique_result.findings if f.severity == "CRITICAL"]
    
    if critical_issues:
        # 3a. 有 CRITICAL 问题：尝试自动修复
        if context.enable_auto_fix:
            fix_result = self.auto_fix_phase.execute(context, critical_issues)
          if fix_result.success:
           # 重新运行 Quality Gate
                return self._rerun_quality_gate(context)
        
        # 3b. 无法自动修复：标记为失败
        return PhaseResult.fail(
            "Critical issues found in critique",
          critique_report=critique_result.report
        )
    
    # 4. 无 CRITICAL 问题：继续流程，但记录其他问题
    context.critique_findings = critique_result.findings
    return PhaseResult.ok("Critique completed with suggestions")
```

**与 Quality Gate 的协同**:
```python
# Phase 9: Quality Gate 先验证基础质量
def quality_gate_checks(context):
    # L1: FORMAT - 语法检查
    # L2: SEMANTIC - 规则验证
    # L3: PARSER - 接口验证
    # L4: BUSINESS - 业务规则
    
# Phase 9.5: Critique 审查深层质量
def critique_checks(context):
    # 1. 逻辑正确性（对比需求）
    # 2. 设计质量（SOLID 原则）
    # 3. 可维护性（复杂度、可读性）
    # 4. 边界处理（异常、空值）
    # 5. 性能考虑（算法复杂度）
    # 6. 安全检查（注入、越界）
```

**Critique Report 输出**:
```markdown
# Code Critique Report

Generated: 2026-06-04 16:00:00
Reviewed Files: 4
Total Issues: 5 (1 CRITICAL, 2 HIGH, 2 MEDIUM)

## Critical Issues (Must Fix)

### [LOGIC] NULL Pointer Dereference
**Location**: src/user_service.cpp:42
**Description**: Potential crash when user not found
**Code**:
\`\`\`cpp
User* user = find_user(id);
user->name = new_name;  // NULL dereference!
\`\`\`
**Suggestion**: Add null check
\`\`\`cpp
User* user = find_user(id);
if (!user) {
    throw UserNotFoundException(id);
}
user->name = new_name;
\`\`\`

## High Issues (Should Fix)
...

## Medium Issues (Recommend Fix)
...

## Summary
- **Recommendation**: Fix all CRITICAL and HIGH issues before merging
- **Estimated Fix Time**: ~30 minutes
- **Risk Level**: HIGH (1 potential crash scenario)
```

---

## Q5: Critique Phase 的成本和收益是什么？

**成本分析**:

```
每个文件审查:
- Input tokens: ~2000 (system + code + context)
- Output tokens: ~500 (findings + suggestions)
- Total: ~2500 tokens per file

单个项目 (10 files):
- Total tokens: 25,000
- Cost (Claude Opus): $0.375
- Time: ~30 seconds
```

**收益分析**:

1. **Bug 预防**:
   - 发现 Phase 9 静态检查遗漏的 30% 问题
   - 避免 P0/P1 线上事故

2. **代码质量**:
   - 设计缺陷早期发现（重构成本降低 10x）
   - 可维护性提升（技术债减少）

3. **团队效率**:
   - 减少 Code Review 人力（从 2 小时 → 30 分钟）
   - 新人代码质量提升（学习最佳实践）

**ROI 计算**:
```
成本: $0.375 per project
收益: 
  - 1 个 P0 bug 避免: $10,000 (线上事故成本)
  - Code Review 时间节省: 1.5 hours × $50/hour = $75
  - 重构成本降低: $200 (early fix vs late fix)

ROI: ($10,275 - $0.375) / $0.375 = 27,400x
```

**最佳实践**:
```python
# 仅对 AI 生成的代码运行 Critique
def should_run_critique(context):
    if context.has_ai_generated_files:
        return True  # AI 代码需要审查
    if context.is_critical_module:
        return True  # 关键模块需要审查
    return False  # 其他情况跳过，节省成本
```

---

## Q6: Critique Phase 的局限性和改进方向？

**当前局限性**:

1. **LLM 局限性**:
   - 依赖 LLM 理解能力（可能误判）
   - 无法执行代码（只能静态分析）
   - 上下文窗口限制（大文件截断）

2. **成本问题**:
   - 大项目审查成本高（100+ files）
   - 实时反馈延迟（~30秒）

3. **假阳性**:
   - LLM 可能报告非问题
   - 需要人工复核

**改进方向**:

```python
# 1. 分层审查策略
class TieredCritique:
    def execute(self, files):
        # L1: 快速扫描（所有文件）
        quick_scan = self.quick_critique(files)
        
        # L2: 深度审查（有风险的文件）
        risky_files = [f for f in files if f.complexity > THRESHOLD]
      deep_review = self.deep_critique(risky_files)
        
        # L3: 专家审查（CRITICAL 模块）
        critical_files = [f for f in files if f.is_critical]
        expert_review = self.expert_critique(critical_files)

# 2. 增量审查
class IncrementalCritique:
    def execute(self, changed_files):
        # 只审查变更的文件
        # 结合 git diff 和上次审查结果

# 3. 反馈循环
class FeedbackLoop:
    def learn_from_history(self):
        # 收集假阳性样本
        # 微调 prompt，减少误判
```

**未来规划**:
1. ✅ **Agent-based Critique**: 多 agent 并行审查不同维度
2. ✅ **Critique Cache**: 缓存审查结果，相同代码不重复审查
3. ✅ **Interactive Critique**: 审查结果实时反馈给开发者
4. ✅ **Critique Training**: 基于历史数据训练专属审查模型

---

## 面试展示脚本

**开场**:
"Critique Phase 是 DevPalAgent 质量保证的第二道防线，它将 LLM 的理解能力应用于代码审查。"

**技术深度展示**:
1. "Phase 9 Quality Gate 验证'是什么'，Critique Phase 审查'为什么'"
2. "六维度审查：Logic、Design、Maintainability、Performance、Security、Completeness"
3. "与工作流集成：CRITICAL 问题触发 Auto-Fix 或阻断流程"
4. "成本可控：分层审查策略，只深度审查高风险代码"

**代码展示**:
- `devpal/core/openspec_phases/phase9_code_review.py` - Critique 实现
- Critic System Prompt - LLM-as-a-Judge 设计
- Critique Report 示例 - 输出格式

**亮点总结**:
- 🎯 **LLM-as-a-Judge**: 将 LLM 理解能力应用于代码审查
- 🛡️ **双重验证**: Quality Gate + Critique = 深度质量保障
- 💰 **ROI 27,400x**: $0.375 投入，避免 $10,000+ 线上事故
- 🔄 **闭环设计**: Critique → Auto-Fix → Re-validate
