# Interview Q&A: Quality Gate System

## 面试专题：四层质量门禁验证体系

---

## Q1: Quality Gate 的四层验证是什么？

**核心回答**:
Quality Gate (Phase 9) 采用**四层验证模型**，从语法到语义到业务规则，层层把关代码质量。

**四层模型**:
```
L1: FORMAT    (格式层) - 语法和基础格式
L2: SEMANTIC  (语义层) - 语义一致性和逻辑
L3: PARSER    (解析层) - 可解析性和接口
L4: BUSINESS  (业务层) - 业务规则和需求对齐
```

**设计理念**:
- **自底向上**: 先验证基础（格式），再验证高层（业务）
- **早失败**: L1 失败直接终止，不浪费时间检查 L2-L4
- **语言感知**: 不同语言有不同的验证器

---

## Q2: 四层验证的具体内容是什么？

### L1: FORMAT Layer (格式验证)
```python
# devpal/core/schema/validation_engine.py
class FormatValidator:
    """L1: 格式验证"""
    
    def validate(self, files: List[Path], language: str) -> List[Issue]:
        issues = []
      
        if language == "cpp":
            # C++ 语法检查
            for file in files:
          # 1. AST 解析
                try:
             ast = parse_cpp_ast(file)
                except SyntaxError as e:
            issues.append(Issue("SYNTAX_ERROR", file, str(e)))
                
         # 2. 基础格式
                if not has_header_guards(file):
                issues.append(Issue("MISSING_HEADER_GUARD", file))
                
      if not has_namespace(file):
                  issues.append(Issue("MISSING_NAMESPACE", file))
        
        elif language == "python":
        # Python 语法检查
            for file in files:
                try:
                    compile(file.read_text(), file.name, 'exec')
                except SyntaxError as e:
                issues.append(Issue("SYNTAX_ERROR", file, str(e)))
        
        return issues
```

**检查项**:
- ✅ 语法正确性（可编译/可解析）
- ✅ 文件结构（头文件保护、命名空间）
- ✅ 基础规范（缩进、换行）

### L2: SEMANTIC Layer (语义验证)
```python
class SemanticValidator:
    """L2: 语义验证""
    def validate(self, files, language) -> List[Issue]:
        issues = []
      
        # 1. 依赖完整性
        missing_deps = check_missing_dependencies(files)
        issues.extend(missing_deps)
        
        # 2. 未使用代码
      dead_code = detect_dead_code(files)
     issues.extend(dead_code)
     
        # 3. 逻辑矛盾
        contradictions = detect_contradictions(files)
      issues.extend(contradictions)
        
        return issues
```

**检查项**:
- ✅ 依赖完整性（import/include 是否存在）
- ✅ 死代码检测（未使用的函数、变量）
- ✅ 逻辑矛盾（if (true) else 永远不执行）

### L3: PARSER Layer (解析验证)
```python
class ParserValidator:
    """L3: 解析验证"""
    
    def validate(self, files) -> List[Issue]:
        issues = []
        
        # 1. 接口一致性
        # 检查函数声明与定义是否匹配
        for header, source in match_header_source(files):
            decls = parse_declarations(header)
            defs = parse_definitions(source)
            
            for decl in decls:
                if decl not in defs:
                    issues.append(Issue("MISSING_DEFINITION", source, decl))
        
        # 2. 调用关系
     # 检查函数调用是否有对应的定义
        call_graph = build_call_graph(files)
        for caller, callee in call_graph.edges():
           if not has_definition(callee):
                issues.append(Issue("UNDEFINED_FUNCTION", caller, callee))
        
        return issues
```

**检查项**:
- ✅ 函数签名匹配（声明与定义一致）
- ✅ 调用关系（被调用的函数存在）
- ✅ 类型兼容性（参数类型匹配）

### L4: BUSINESS Layer (业务验证)
```python
class BusinessValidator:
    """L4: 业务验证"""
    
    def validate(self, files, requirements) -> List[Issue]:
     issues = []
      
        # 1. 命名规范
        naming_issues = check_naming_convention(files)
        issues.extend(naming_issues)
        
        # 2. 敏感信息
        sensitive_data = detect_sensitive_data(files)
        if sensitive_data:
            issues.append(Issue("SENSITIVE_DATA_EXPOSED", sensitive_data))
        
        # 3. 需求覆盖
        coverage = check_requirement_coverage(files, requirements)
        for req in requirements:
          if req.id not in coverage:
              issues.append(Issue("REQUIREMENT_NOT_IMPLEMENTED", req.id))
        
        # 4. 项目特定规则
      custom_issues = apply_custom_rules(files)
        issues.extend(custom_issues)
     
      return issues
```

**检查项**:
- ✅ 命名约定（驼峰、下划线、前缀等）
- ✅ 安全检查（敏感信息、注入风险）
- ✅ 需求覆盖度（每个需求都有对应实现）
- ✅ 项目特定规则（自定义业务规则）

---

## Q3: Quality Gate 如何与其他阶段协作？

**工作流**:
```
Phase 4/5: 生成代码
    ↓
Phase 9: Quality Gate
  ├─ L1: FORMAT → 失败 → 终止
  ├─ L2: SEMANTIC → 失败 → 终止
  ├─ L3: PARSER → 失败 → 终止
  └─ L4: BUSINESS → 失败 → 终止
    ↓ 全部通过
Phase 9.5: Critique (LLM 深度审查)
  ↓
Phase 10: Run Tests
```

**决策逻辑**:
```python
def execute_quality_gate(context):
    # 1. L1: FORMAT 验证
    format_issues = L1_validator.validate(context.generated_files)
    if format_issues:
        return PhaseResult.fail("L1 FORMAT failed", issues=format_issues)
    
    # 2. L2: SEMANTIC 验证
    semantic_issues = L2_validator.validate(context.generated_files)
    if semantic_issues:
        return PhaseResult.fail("L2 SEMANTIC failed", issues=semantic_issues)
    
    # 3. L3: PARSER 验证
  parser_issues = L3_validator.validate(context.generated_files)
    if parser_issues:
        return PhaseResult.fail("L3 PARSER failed", issues=parser_issues)
    
    # 4. L4: BUSINESS 验证
    business_issues = L4_validator.validate(context.generated_files, context.requirements)
    if business_issues:
       return PhaseResult.fail("L4 BUSINESS failed", issues=business_issues)
    
    # 全部通过
    return PhaseResult.ok("Quality Gate passed")
```

---

## Q4: Quality Gate 的输出格式是什么？

**Quality Gate Report**:
```markdown
# Quality Gate Report

Generated: 2026-06-04 16:00:00
Project: cpp_simple_login
Files Validated: 4

## Summary
- ✅ L1 FORMAT: 0 issues
- ✅ L2 SEMANTIC: 0 issues
- ✅ L3 PARSER: 0 issues
- ✅ L4 BUSINESS: 0 issues

**Result**: PASSED ✅

---

## L1: FORMAT Validation
### Checked:
- ✅ CMakeLists.txt exists
- ✅ src/main.cpp exists with main()
- ✅ All .h files have header guards
- ✅ All files use consistent namespace

### Issues: 0

---

## L2: SEMANTIC Validation
### Checked:
- ✅ All includes resolve
- ✅ No dead code detected
- ✅ No obvious logic contradictions

### Issues: 0

---

## L3: PARSER Validation
### Checked:
- ✅ Function declarations match definitions
- ✅ All called functions are defined
- ✅ Type compatibility verified

### Issues: 0

---

## L4: BUSINESS Validation
### Checked:
- ✅ Naming convention followed
- ✅ No sensitive data exposed
- ✅ All requirements implemented (4/4)
  - REQ-001: User authentication ✅
  - REQ-002: Password validation ✅
  - REQ-003: Session management ✅
  - REQ-004: Error handling ✅
- ✅ Test files present

### Issues: 0

---

## Recommendation
✅ Code quality is excellent. Safe to proceed to testing.
```

---

## Q5: Quality Gate 的扩展性如何？

**自定义验证器**:
```python
# devpal/core/schema/custom_validators.py
class CustomSecurityValidator(BusinessValidator):
  """自定义安全验证器"""
    
    def validate(self, files, requirements):
        issues = []
        
        # 1. SQL 注入检测
        for file in files:
        if "execute(" in file.read_text() and "?" not in file.read_text():
              issues.append(Issue(
                  "SQL_INJECTION_RISK",
                 file,
                  "Use parameterized queries"
                ))
        
        # 2. XSS 检测
        for file in files:
        if "innerHTML" in file.read_text():
             issues.append(Issue(
            "XSS_RISK",
            file,
                 "Sanitize user input"
              ))
        
        return issues

# 注册到 Quality Gate
quality_gate.register_validator("L4", CustomSecurityValidator())
```

**项目特定规则**:
```python
# .devpal/quality_rules.py
def check_custom_rules(files):
    """项目特定验证规则"""
    issues = []
    
    # 规则1：所有 API 函数必须有日志
    for file in files:
        if "api_" in file.name:
            if "LOG(" not in file.read_text():
            issues.append("Missing logging in API function")
    
    # 规则2：所有数据库操作必须有事务
    for file in files:
        if "db.execute" in file.read_text():
            if "begin_transaction" not in file.read_text():
                issues.append("Missing transaction wrapper")
    
    return issues
```

---

## Q6: Quality Gate vs Critique Phase 对比？

| 维度 | Quality Gate (Phase 9) | Critique Phase (9.5) |
|------|-----------|-------------------|
| **类型** | 静态分析 | LLM 审查 |
| **速度** | 快（~1秒） | 慢（~30秒） |
| **覆盖** | 格式、语法、规则 | 逻辑、设计、可维护性 |
| **成本** | 免费 | $0.375 per project |
| **准确性** | 高（规则驱动） | 中（LLM 判断） |
| **深度** | 浅（表面检查） | 深（理解意图） |

**互补关系**:
```
Quality Gate (快速、全覆盖)
    ↓ 通过
Critique Phase (深度、理解业务)
    ↓ 通过
Phase 10: Run Tests (动态验证)
```

**最佳实践**:
- ✅ Quality Gate 作为第一道防线（必须）
- ✅ Critique Phase 作为第二道防线（AI 生成代码推荐）
- ✅ 两者结合：静态 + 动态 + LLM 三重验证

---

## 面试展示脚本

**开场**:
"Quality Gate 是 DevPalAgent 的四层质量门禁，从语法到业务规则层层把关。"

**技术深度展示**:
1. "四层验证：FORMAT → SEMANTIC → PARSER → BUSINESS，自底向上"
2. "语言感知：C++ 检查头文件保护，Python 检查 import"
3. "需求覆盖：L4 验证每个需求都有对应实现"
4. "可扩展：支持自定义验证器和项目特定规则"

**代码展示**:
- `devpal/core/schema/validation_engine.py` - 验证引擎
- `devpal/core/openspec_phases/phase9_quality_gate.py` - Phase 9 实现
- Quality Gate Report 示例

**亮点总结**:
- 🛡️ **四层防御**: FORMAT → SEMANTIC → PARSER → BUSINESS
- 🌍 **语言感知**: C++/Python/Shell 不同验证策略
- 🎯 **需求驱动**: L4 验证需求覆盖度
- 🔌 **可扩展**: 自定义验证器和规则
