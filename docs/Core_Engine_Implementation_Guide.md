# DevPal Agent v2.0 - 核心引擎实现详解

> **文档版本**: v2.0  
> **创建日期**: 2026-05-11  
> **涵盖模块**: Executor、ValidationEngine、DeltaEngine、ArtifactGraph

---

## 📋 目录

- [1. Executor - 执行引擎](#1-executor---执行引擎)
- [2. ValidationEngine - 四层验证流水线](#2-validationengine---四层验证流水线)
- [3. DeltaEngine - 增量变更引擎](#3-deltaengine---增量变更引擎)
- [4. ArtifactGraph - 工件依赖图](#4-artifactgraph---工件依赖图)
- [5. EventBus - 事件总线](#5-eventbus---事件总线)
- [6. StateManager - 状态持久化](#6-statemanager---状态持久化)
- [7. CompileDB - 编译数据库](#7-compiledb---编译数据库)

---

## 1. Executor - 执行引擎

### 1.1 核心架构

**位置**: `devpal/core/agent_engine.py`

```python
class AgentEngine:
    """
    核心 Agent 执行引擎
    实现 Plan-Act-Reflect 循环
    """
    def __init__(self, config, tool_registry, openspec_context):
        # 1. 工具注册表 - 管理 26 个工具
        self.tool_registry = tool_registry
      
        # 2. 记忆系统 - 短期/长期/错误记忆
        self.memory = MemoryManager()
        
        # 3. 规划器 - 任务分解
        self.planner = Planner()
        
        # 4. 反思器 - 错误检测和纠正
        self.reflector = Reflector()
        
      # 5. OpenSpec 工作流执行器 - 11阶段流程
        self.openspec_workflow = OpenSpecWorkflowExecutor()
        
      # 6. OpenSpec 上下文 - 统一管理所有组件
        self.openspec_context = openspec_context
```

### 1.2 执行流程 (Plan-Act-Reflect Loop)

```python
def run(self, user_query: str) -> str:
    """
    完整的 Plan-Act-Reflect 循环
    
    执行流程:
    1. Plan: 任务分解成步骤
    2. Evaluate: 评估计划可行性
    3. Execute: 执行当前步骤
  4. Reflect: 反思执行结果
    5. Adjust: 根据反思动态调整计划
    6. Finalize: 生成最终总结报告
    """
    
    # Step 1: 检测是否是 OpenSpec 需求实现请求
    is_req, req_file = self.openspec_workflow.detect_requirements_request(user_query)
    
    # Step 2: 生成执行计划
    if self.config.enable_planning:
        plan = self.planner.generate_plan(user_query)
        feasible, issues = self.planner.evaluate_feasibility(plan)
        
    # Step 3: 迭代执行计划步骤
    for iteration in range(self.config.max_iterations):
     if plan and current_step_idx >= len(plan.steps):
            break
            
        current_step = plan.steps[current_step_idx]
        
        # Step 3.1: 快捷路径 - 直接执行工具
        if current_step.tool_needed == 'linked_list_tool':
            result = self.tool_registry.execute_tool(tool_name, args)
            
        # Step 3.2: OpenSpec 流程 - 11阶段完整工作流
        elif current_step.tool_needed in ('project_generator', 'spec_tool'):
            # 执行 11 阶段 OpenSpec 工作流
            
        # Step 3.3: 常规工具调用 - 通过 LLM
        else:
            response = self.client.messages.create(
                model=self.model,
              messages=self.message_history.to_api_format(),
             tools=self.tool_registry.to_anthropic_format()
          )
            
            # 处理工具调用
            if response.stop_reason == 'tool_use':
                for tool_use in response.content:
                 result = self.tool_registry.execute_tool(
                 tool_use.name,
                  tool_use.input
                )
                    
        # Step 4: 反思执行结果
        if self.config.enable_reflection:
            reflection = self.reflector.reflect(
                step=current_step,
              result=result,
              context=context
            )
        
        current_step_idx += 1
        
    return final_result
```

### 1.3 核心功能

#### 工具调用管理

```python
# 通过 ToolRegistry 执行工具
result = self.tool_registry.execute_tool(tool_name, args)

# 工具执行结果
class ToolResult:
    success: bool
    content: str
    error_message: Optional[str]
    metadata: Dict[str, Any]
```

#### 状态管理

```python
# 消息历史
self.message_history.add_user(query)
self.message_history.add_assistant(response)
self.message_history.add_tool_results(results)

# 统计信息
self.stats = {
    "total_queries": 0,
    "tool_calls": 0,
    "tool_errors": 0,
    "validation_checks": 0,
    "deltas_applied": 0,
    "events_published": 0
}
```

#### OpenSpec 集成

```python
# 通过 OpenSpecContext 统一管理
self.openspec_context = OpenSpecContext.create(
    workspace=self.workspace_path,
    enable_event_bus=True,
    auto_initialize=True
)

# 访问 OpenSpec 组件
self.validation_engine = self.openspec_context.validation_engine
self.spec_engine = self.openspec_context.spec_engine
self.artifact_graph = self.openspec_context.artifact_graph
self.event_bus = self.openspec_context.event_bus
```

---

## 2. ValidationEngine - 四层验证流水线

### 2.1 核心架构

**位置**: `devpal/core/schema/validation_engine.py`

```python
class ValidationEngine:
    """
    四层验证引擎 - 渐进式验证流水线
    
    Layer 1: Format Validation (格式验证)
    Layer 2: Semantic Validation (语义验证)
    Layer 3: Parser Validation (解析器验证)
    Layer 4: Business Validation (业务规则验证)
    """
    
    def __init__(self):
      # 验证器注册表 - 按层级组织
        self._validators: Dict[ValidationLevel, List[Callable]] = {
         ValidationLevel.FORMAT: [],
          ValidationLevel.SEMANTIC: [],
        ValidationLevel.PARSER: [],
          ValidationLevel.BUSINESS: []
        }
        
      # 验证流水线
        self.pipeline = ValidationPipeline(self)
        self.pipeline.setup_default_pipeline()
```

### 2.2 四层验证详解

#### Layer 1: Format Validation - 格式验证

**检查内容**: 语法、类型、结构

**具体示例 1: JSON 配置文件验证**

假设 AI 生成了一个数据库配置文件：

```json
// 错误的配置文件
{
    "database": {
        "host": "localhost",
        "port": 3306,
        "name": "mydb"
    }
    "cache": {
        "enabled": true
    }
}
```

**Layer 1 验证过程**:
```python
# 验证器检测到问题
issues = validate_json_syntax(config_content, {})

# 结果：
ValidationIssue(
    level=ValidationLevel.FORMAT,
    severity=ValidationSeverity.ERROR,
    message="JSON 语法错误: Expecting ',' delimiter",
    location="line 7 column 5",
    suggestion="在第 6 行的 } 后添加逗号"
)
```

**修复后**:
```json
{
    "database": {
        "host": "localhost",
        "port": 3306,
        "name": "mydb"
    },  // ← 添加了逗号
    "cache": {
        "enabled": true
    }
}
```

**具体示例 2: 工具调用参数类型验证**

假设 AI 调用文件读取工具，但参数类型错误：

```python
# AI 生成的工具调用
tool_call = {
    "tool_name": "file_reader",
    "args": {
        "path": 123,  # ❌ 错误：应该是字符串
        "encoding": "utf-8"
    }
}

# Layer 1 验证
issues = validate_type_match(
    content=123,
    context={
        "expected_type": str,
        "param_name": "path",
        "tool_name": "file_reader"
    }
)

# 结果：
ValidationIssue(
    level=ValidationLevel.FORMAT,
    severity=ValidationSeverity.ERROR,
  message="参数 'path' 类型不匹配: 期望 <class 'str'>, 实际 <class 'int'>",
    suggestion="将 123 改为 '123' 或提供有效的文件路径字符串"
)
```

**为什么需要 Layer 1？**
- 🚫 **快速失败**: 阻止明显错误进入后续阶段
- ⚡ **节省时间**: 不需要等到执行时才发现语法错误
- 🎯 **精确定位**: 提供具体的行号和字段名

```python
class FormatValidator:
    """格式验证器"""
    
    def validate_json_syntax(content, context):
        """JSON 语法检查"""
        try:
          json.loads(content)
        return []  # 无问题
        except json.JSONDecodeError as e:
        return [ValidationIssue(
                level=ValidationLevel.FORMAT,
              severity=ValidationSeverity.ERROR,
                message=f"JSON 语法错误: {e}",
                location=f"line {e.lineno}"
        )]
    
    def validate_type_match(content, context):
        """类型匹配检查"""
        issues = []
     if 'expected_type' in context:
       if not isinstance(content, context['expected_type']):
             issues.append(ValidationIssue(
                    ValidationLevel.FORMAT,
                  ValidationSeverity.ERROR,
           f"类型不匹配: 期望 {context['expected_type']}"
            ))
        return issues
```

#### Layer 2: Semantic Validation - 语义验证

**检查内容**: 逻辑自洽、依赖关系

**具体示例 1: 逻辑矛盾检测**

假设 AI 生成了一个用户管理系统的代码：

```python
# AI 生成的代码
class User:
    def __init__(self, age):
        self.age = age
        self.is_adult = age >= 18
        self.can_vote = age < 16  # ❌ 逻辑矛盾！
```

**Layer 2 验证过程**:
```python
# 语义验证器检测逻辑矛盾
issues = validate_logic_consistency(code, context={
  "previous_definitions": {
        "is_adult": "age >= 18",
        "can_vote": "age < 16"
    }
})

# 结果：
ValidationIssue(
    level=ValidationLevel.SEMANTIC,
    severity=ValidationSeverity.ERROR,
    message="逻辑矛盾: 'can_vote' 的条件 (age < 16) 与 'is_adult' (age >= 18) 冲突",
    location="class User, line 5",
    suggestion="通常投票年龄应该是 >= 18，建议改为 'self.can_vote = age >= 18'"
)
```

**具体示例 2: 依赖关系验证**

假设 AI 生成了一个函数，但依赖的模块不存在：

```python
# AI 生成的代码
def process_data(data):
    # 使用了 pandas，但没有导入
    df = pd.DataFrame(data)  # ❌ pd 未定义
    return df.mean()
```

**Layer 2 验证过程**:
```python
# 检测依赖缺失
issues = validate_dependencies(code, context={
    "imported_modules": ["os", "sys"],  # 没有 pandas
    "used_symbols": ["pd"]
})

# 结果：
ValidationIssue(
    level=ValidationLevel.SEMANTIC,
    severity=ValidationSeverity.ERROR,
    message="依赖缺失: 使用了 'pd' 但未导入 pandas",
    location="function process_data, line 3",
    suggestion="在文件开头添加: import pandas as pd"
)
```

**具体示例 3: 变量引用检查**

```python
# AI 生成的代码
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    
    # ❌ 使用了未定义的变量
    return total * discount_rate
```

**Layer 2 验证**:
```python
issues = validate_variable_references(code, context={
    "defined_variables": ["total", "item", "items"],
    "used_variables": ["total", "discount_rate"]
})

# 结果：
ValidationIssue(
    level=ValidationLevel.SEMANTIC,
    severity=ValidationSeverity.ERROR,
    message="未定义的变量: 'discount_rate' 在使用前未定义",
    location="function calculate_total, line 6",
  suggestion="添加参数 'discount_rate' 或在函数内定义默认值"
)
```

**为什么需要 Layer 2？**
- 🧠 **逻辑检查**: 发现代码中的逻辑矛盾
- 🔗 **依赖验证**: 确保所有依赖都已声明
- 🎯 **语义正确**: 保证代码在逻辑上说得通

```python
class SemanticValidator:
    """语义验证器"""
    
    def validate_logic_consistency(content, context):
        """逻辑一致性检查"""
        issues = []
        # 检查前后矛盾
        if 'previous_state' in context:
            # 比较当前状态和之前状态
            pass
        return issues
  
    def validate_dependencies(content, context):
        """依赖完整性检查"""
        issues = []
        if 'dependencies' in context:
            for dep in context['dependencies']:
                if not dep_exists(dep):
                    issues.append(ValidationIssue(
              ValidationLevel.SEMANTIC,
                     ValidationSeverity.ERROR,
                    f"依赖不存在: {dep}"
                    ))
      return issues
```

#### Layer 3: Parser Validation - 解析器验证

**检查内容**: 与现有代码兼容性

**具体示例 1: 函数调用兼容性检查**

假设项目中已有一个函数：

```python
# 现有代码 (utils.py)
def calculate_price(base_price, tax_rate):
    """计算含税价格"""
    return base_price * (1 + tax_rate)
```

AI 生成了调用代码，但参数不匹配：

```python
# AI 生成的代码
def process_order(order):
    # ❌ 错误：calculate_price 需要 2 个参数，但只传了 1 个
    total = calculate_price(order.amount)
    return total
```

**Layer 3 验证过程**:
```python
# 使用 CompileDB 查询函数签名
issues = validate_symbol_resolution(code, context={
    "compile_db": compile_db,
    "function_call": "calculate_price",
    "provided_args": 1
})

# CompileDB 查询结果
symbol = compile_db.find_symbol("calculate_price")
# Symbol(name="calculate_price", params=["base_price", "tax_rate"], 
#        file="utils.py", line=10)

# 验证结果：
ValidationIssue(
    level=ValidationLevel.PARSER,
    severity=ValidationSeverity.ERROR,
    message="函数调用参数不匹配: 'calculate_price' 需要 2 个参数 (base_price, tax_rate)，但只提供了 1 个",
    location="function process_order, line 3",
    suggestion="添加缺失的参数: calculate_price(order.amount, 0.1)"
)
```

**具体示例 2: 类方法存在性检查**

```python
# 现有代码 (models.py)
class User:
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name
```

AI 生成了调用不存在的方法的代码：

```python
# AI 生成的代码
def display_user(user):
    # ❌ User 类没有 get_email 方法
    print(f"Email: {user.get_email()}")
```

**Layer 3 验证**:
```python
issues = validate_method_exists(code, context={
    "compile_db": compile_db,
    "class_name": "User",
    "method_name": "get_email"
})

# CompileDB 查询 User 类的所有方法
methods = compile_db.find_class_methods("User")
# ['__init__', 'get_name']  # 没有 'get_email'

# 结果：
ValidationIssue(
    level=ValidationLevel.PARSER,
    severity=ValidationSeverity.ERROR,
    message="方法不存在: 'User' 类没有 'get_email' 方法",
    location="function display_user, line 3",
    suggestion="可用的方法: get_name(). 或者需要先在 User 类中添加 get_email 方法"
)
```

**具体示例 3: 导入路径验证**

```python
# AI 生成的代码
from myproject.utils.helpers import format_date  # ❌ 路径不存在
```

**Layer 3 验证**:
```python
issues = validate_import_path(code, context={
    "project_structure": project_tree,
    "import_path": "myproject.utils.helpers"
})

# 检查文件系统
# myproject/utils/helpers.py 不存在
# 但存在 myproject/utils/helper.py (单数)

# 结果：
ValidationIssue(
    level=ValidationLevel.PARSER,
    severity=ValidationSeverity.ERROR,
    message="导入路径不存在: 'myproject.utils.helpers' 模块不存在",
    location="line 1",
    suggestion="你可能想导入: 'myproject.utils.helper' (注意是单数)"
)
```

**为什么需要 Layer 3？**
- 🔍 **符号解析**: 确保引用的函数/类/方法真实存在
- 🔗 **接口匹配**: 验证函数调用的参数数量和类型
- 📦 **模块验证**: 检查导入路径是否正确

```python
class ParserValidator:
    """解析器验证器"""
    
    def validate_code_compatibility(content, context):
        """代码兼容性检查"""
        issues = []
        try:
      ast.parse(content)  # Python
        except SyntaxError as e:
            issues.append(ValidationIssue(
          ValidationLevel.PARSER,
                ValidationSeverity.ERROR,
                f"语法错误: {e}"
            ))
        return issues
    
    def validate_symbol_resolution(content, context):
        """符号解析检查""
        issues = []
        if 'compile_db' in context:
          compile_db = context['compile_db']
            # 查询符号是否存在
            pass
        return issues
```

## Layer 4: Business Validation - 业务规则验证

**检查内容**: 项目规范、安全规则

**具体示例 1: 命名规范检查**

假设项目要求使用 snake_case 命名，但 AI 生成了不符合规范的代码：

```python
# AI 生成的代码
def CalculateUserAge(birthDate):  # ❌ 应该用 snake_case
    currentYear = 2026  # ❌ 应该用 snake_case
    return currentYear - birthDate.year
```

**Layer 4 验证过程**:
```python
issues = validate_naming_convention(code, context={
    "project_style": "snake_case",
    "identifiers": ["CalculateUserAge", "birthDate", "currentYear"]
})

# 结果：
[
    ValidationIssue(
        level=ValidationLevel.BUSINESS,
        severity=ValidationSeverity.WARNING,
        message="函数名 'CalculateUserAge' 不符合 snake_case 规范",
        location="line 2",
        suggestion="改为: calculate_user_age"
    ),
    ValidationIssue(
        level=ValidationLevel.BUSINESS,
        severity=ValidationSeverity.WARNING,
        message="变量名 'birthDate' 不符合 snake_case 规范",
        location="line 2",
        suggestion="改为: birth_date"
    ),
    ValidationIssue(
        level=ValidationLevel.BUSINESS,
        severity=ValidationSeverity.WARNING,
        message="变量名 'currentYear' 不符合 snake_case 规范",
      location="line 3",
        suggestion="改为: current_year"
    )
]
```

**修复后**:
```python
def calculate_user_age(birth_date):  # ✅ 符合规范
    current_year = 2026  # ✅ 符合规范
    return current_year - birth_date.year
```

**具体示例 2: SQL 注入安全检查**

AI 生成了存在 SQL 注入风险的代码：

```python
# AI 生成的代码
def get_user(username):
    # ❌ 危险！使用字符串拼接构造 SQL
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)
```

**Layer 4 验证**:
```python
issues = validate_security_rules(code, context={
    "security_checks": ["sql_injection", "xss", "path_traversal"]
})

# 结果：
ValidationIssue(
    level=ValidationLevel.BUSINESS,
    severity=ValidationSeverity.ERROR,
    message="安全风险: 检测到潜在的 SQL 注入漏洞",
    location="function get_user, line 3",
    suggestion="使用参数化查询: db.execute('SELECT * FROM users WHERE username = ?', (username,))"
)
```

**修复后**:
```python
def get_user(username):
    # ✅ 安全：使用参数化查询
    query = "SELECT * FROM users WHERE username = ?"
    return db.execute(query, (username,))
```

**具体示例 3: XSS 防护检查**

```python
# AI 生成的代码
def render_comment(comment):
    # ❌ 危险！直接输出用户输入
    return f"<div>{comment.text}</div>"
```

**Layer 4 验证**:
```python
issues = validate_security_rules(code, context={
    "security_checks": ["xss"],
    "output_context": "html"
})

# 结果：
ValidationIssue(
    level=ValidationLevel.BUSINESS,
    severity=ValidationSeverity.ERROR,
    message="安全风险: 检测到潜在的 XSS 漏洞 - 未转义的用户输入直接输出到 HTML",
    location="function render_comment, line 3",
    suggestion="使用 HTML 转义: return f'<div>{html.escape(comment.text)}</div>'"
)
```

**具体示例 4: 性能规则检查**

```python
# AI 生成的代码
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):  # ❌ O(n²) 复杂度
            if i != j and items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates
```

**Layer 4 验证**:
```python
issues = validate_performance_rules(code, context={
    "max_complexity": "O(n log n)",
    "detected_complexity": "O(n²)"
})

# 结果：
ValidationIssue(
    level=ValidationLevel.BUSINESS,
    severity=ValidationSeverity.WARNING,
    message="性能问题: 检测到 O(n²) 复杂度的嵌套循环",
    location="function find_duplicates, lines 3-6",
    suggestion="使用集合优化: seen = set(); duplicates = [x for x in items if x in seen or seen.add(x)]"
)
```

**为什么需要 Layer 4？**
- 📏 **代码规范**: 确保代码风格一致
- 🔒 **安全防护**: 防止常见安全漏洞
- ⚡ **性能保证**: 避免明显的性能问题
- 🎯 **业务规则**: 符合项目特定要求

```python
class BusinessValidator:
    """业务规则验证器"""
    
    def validate_naming_convention(content, context):
      """命名规范检查"""
        issues = []
      if not re.match(r'^[a-z_][a-z0-9_]*$', content):
            issues.append(ValidationIssue(
            ValidationLevel.BUSINESS,
                ValidationSeverity.WARNING,
             "命名不符合 snake_case 规范"
            ))
        return issues
    
    def validate_security_rules(content, context):
        """安全规则检查"""
        issues = []
        # 检查 SQL 注入、XSS 等
        if 'sql' in content.lower() and 'format' in content:
          issues.append(ValidationIssue(
                ValidationLevel.BUSINESS,
         ValidationSeverity.ERROR,
           "可能存在 SQL 注入风险"
            ))
        return issues
```

### 2.3 流水线执行

```python
class ValidationPipeline:
    """验证流水线 - 编排和执行""
    
    def run(self, content, context=None) -> ValidationPipelineResult:
     """执行完整验证流水线"""
        stage_results = []
        
        for stage in self.stages:
            if not stage.enabled:
                continue
        
          # 获取该层级的所有验证器
         validators = self.engine.get_validators_for_level(stage.level)
            
            stage_issues = []
            for validator in validators:
              try:
            issues = validator(content, context)
                    stage_issues.extend(issues)
        except Exception as e:
            stage_issues.append(ValidationIssue(
                stage.level,
                        ValidationSeverity.WARNING,
                     f"验证器异常: {e}"
                    ))
            
            # 检查是否有错误
            has_errors = any(i.severity == ValidationSeverity.ERROR 
                   for i in stage_issues)
            
         stage_result = PipelineStageResult(
              stage=stage,
                status=PipelineStatus.FAILED if has_errors else PipelineStatus.SUCCESS,
                issues=stage_issues
            )
            stage_results.append(stage_result)
        
            # 如果有错误且设置了 stop_on_failure，停止执行
            if has_errors and stage.stop_on_failure:
                break
        
        return ValidationPipelineResult(
            status=final_status,
            stages=stage_results,
            total_duration=total_time,
            context=context
        )
```

---

## 3. DeltaEngine - 增量变更引擎

### 3.1 核心设计理念

**传统方式的问题**:
```python
# ❌ 传统方式：全量覆盖
def update_file(file_path, new_content):
    file.write_text(new_content)  # 直接覆盖整个文件
    # 问题：容易产生冲突、无法追踪、难以回滚
```

**DeltaEngine 方式**:
```python
# ✅ Delta 方式：增量变更
delta_spec = DeltaSpec(file_path)
delta_spec.add_delta(DeltaHunk(
    operation=DeltaOperation.MODIFIED,
    target_path="file:src/main.cpp:lines:10-15",
    old_content="原内容",
    new_content="新内容",
    reason="添加命令行参数支持"
))
result = delta_spec.apply()
```

### 3.2 核心数据结构

#### DeltaOperation - 四种操作类型

```python
class DeltaOperation(Enum):
    ADDED = "added"        # 新增内容
    MODIFIED = "modified"  # 修改内容
    REMOVED = "removed"    # 删除内容
    RENAMED = "renamed"    # 重命名标识符
```

#### DeltaHunk - 变更块

```python
@dataclass
class DeltaHunk:
    """描述一个具体的变更"""
    operation: DeltaOperation
    target_path: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    reason: Optional[str] = None
```

### 3.3 核心执行流程

```python
class DeltaSpec:
    def apply(self, validate=True, dry_run=False) -> DeltaResult:
        """应用 Delta 变更的完整流程"""
        
        # 1. 加载原始内容
        if self._original_content is None:
            self.load_original()
        
        # 2. 冲突检测
        conflicts = []
        if validate:
            conflicts.extend(self.detect_overlaps())
            conflicts.extend(self.validate_content_match())
        
        # 3. 应用 Delta (按逆序)
        content = self._original_content
        sorted_deltas = sorted(
            self.deltas,
            key=lambda d: d.start_line or 0,
            reverse=True  # 逆序避免行号偏移
      )
        
        for delta in sorted_deltas:
            content = self._apply_delta(content, delta)
        
        # 4. 生成 diff 预览
        diff_preview = self._generate_diff(self._original_content, content)
        
        # 5. 写入文件
        if not dry_run and len(conflicts) == 0:
         self.target_file.write_text(content)
        
        return DeltaResult(
            success=len(conflicts) == 0,
            applied_deltas=applied,
            conflicts=conflicts,
            new_content=content,
            diff_preview=diff_preview
        )
```

### 3.4 关键算法

#### 为什么要逆序应用？

**具体示例说明**:

假设我们有一个 `main.cpp` 文件，内容如下：

```cpp
// 原始文件 main.cpp
1: #include <iostream>
2: 
3: int main() {
4:     std::cout << "Hello" << std::endl;
5:     return 0;
6: }
```

现在我们有两个 Delta 变更：
- **Delta 1**: 在第 2 行插入 `#include <string>`
- **Delta 2**: 修改第 4 行，将 `"Hello"` 改为 `"Hello World"`

---

**❌ 错误方式：正序应用 (先 Delta 1，后 Delta 2)**

```python
# 步骤 1: 应用 Delta 1 - 在第 2 行插入
1: #include <iostream>
2: #include <string>        # ← 新插入的行
3:                      # ← 原来的第 2 行变成第 3 行
4: int main() {             # ← 原来的第 3 行变成第 4 行
5:     std::cout << "Hello" << std::endl;  # ← 原来的第 4 行变成第 5 行！
6:     return 0;
7: }

# 步骤 2: 应用 Delta 2 - 修改第 4 行
# 问题：现在第 4 行是 "int main() {"，不是我们要修改的 "Hello" 那一行！
# 我们要修改的内容已经跑到第 5 行去了！
# 结果：修改错了位置，破坏了代码！
```

**实际错误结果**:
```cpp
1: #include <iostream>
2: #include <string>
3: 
4: std::cout << "Hello World" << std::endl;  # ← 错误！修改了错误的行
5:     std::cout << "Hello" << std::endl;
6:     return 0;
7: }
```

---

**✅ 正确方式：逆序应用 (先 Delta 2，后 Delta 1)**

```python
# 步骤 1: 应用 Delta 2 - 修改第 4 行
1: #include <iostream>
2: 
3: int main() {
4:     std::cout << "Hello World" << std::endl;  # ← 正确修改
5:     return 0;
6: }

# 步骤 2: 应用 Delta 1 - 在第 2 行插入
1: #include <iostream>
2: #include <string>        # ← 新插入的行
3:                      # ← 原来的第 2 行
4: int main() {
5:     std::cout << "Hello World" << std::endl;  # ← 之前的修改保持正确
6:     return 0;
7: }
```

**正确结果**:
```cpp
1: #include <iostream>
2: #include <string>
3: 
4: int main() {
5:     std::cout << "Hello World" << std::endl;  # ← 正确！
6:     return 0;
7: }
```

---

**核心原理**:

| 操作顺序 | 行号变化 | 结果 |
|---------|---------|------|
| **正序** | 插入导致后续行号全部 +1 | ❌ Delta 2 的行号失效 |
| **逆序** | 先修改后面的行，不影响前面的行号 | ✅ 所有 Delta 的行号都正确 |

**代码实现**:
```python
# 关键代码：按行号逆序排序
sorted_deltas = sorted(
    self.deltas,
    key=lambda d: d.start_line or 0,
    reverse=True  # 从文件末尾开始应用
)

# 示例：
# Delta 1: start_line=2 (插入)
# Delta 2: start_line=4 (修改)
# 
# 正序: [Delta 1, Delta 2] → 错误
# 逆序: [Delta 2, Delta 1] → 正确
```

**类比理解**:

想象你在一本书中做标记：
- **正序**: 先在第 2 页插入一页，后面所有页码都变了，你的第 4 页标记就找不到了
- **逆序**: 先在第 4 页做标记，然后在第 2 页插入，第 4 页的标记不受影响

这就是为什么 DeltaEngine 必须逆序应用变更！

#### 冲突检测

```python
def detect_overlaps(self) -> List[MergeConflict]:
    """检测 Delta 之间的行范围重叠"""
    conflicts = []
    
    for i, delta1 in enumerate(self.deltas):
        for delta2 in self.deltas[i+1:]:
            # 检查行范围是否重叠
            if not (delta1.end_line < delta2.start_line or 
                 delta2.end_line < delta1.start_line):
                conflicts.append(MergeConflict(
                 conflict_type=ConflictType.OVERLAP,
            message=f"Delta 重叠",
                 our_delta=delta1,
              their_delta=delta2
                ))
    
    return conflicts
```

---

## 4. ArtifactGraph - 工件依赖图

### 4.1 核心架构

**位置**: `devpal/core/schema/artifact_graph.py`

```python
class ArtifactGraph:
    """
    工件依赖图 - 管理项目中所有工件的依赖关系
    
    典型依赖链:
    REQUIREMENT (req:login)
        ↳ IMPLEMENTS → CODE (file:src/login.cpp)
                      ↳ TESTS → TEST (file:tests/test_login.cpp)
                 ↳ REFERENCES → DOC (file:docs/login.md)
    """
    
    def __init__(self):
        if NETWORKX_AVAILABLE:
            self._graph = nx.DiGraph()
        else:
            self._graph = SimpleDiGraph()
        
        self._nodes: Dict[str, ArtifactNode] = {}
```

### 4.2 工件类型

```python
class ArtifactType(Enum):
    REQUIREMENT = "requirement"
    CODE = "code"
    TEST = "test"
    DOC = "doc"
    CONFIG = "config"
    SPEC = "spec"
    ASSET = "asset"

class DependencyType(Enum):
    IMPLEMENTS = "implements"
    TESTS = "tests"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    INCLUDES = "includes"
    EXTENDS = "extends"
    IMPORTS = "imports"
```

### 4.3 核心功能

**具体示例：完整的项目依赖关系**

假设我们有一个用户登录系统项目：

```
项目结构:
requirements/
  └── login_requirements.md  (需求文档)
src/
  ├── auth.cpp              (认证逻辑)
  ├── user.cpp              (用户管理)
  └── session.cpp           (会话管理)
tests/
  ├── test_auth.cpp         (认证测试)
  └── test_user.cpp         (用户测试)
docs/
  └── auth_api.md           (API 文档)
```

**步骤 1: 构建依赖图**

```python
graph = ArtifactGraph()

# 添加需求节点
req_node = ArtifactNode(
    id="req:login",
    type=ArtifactType.REQUIREMENT,
    path=Path("requirements/login_requirements.md"),
    name="用户登录需求"
)
graph.add_node(req_node)

# 添加代码节点
auth_node = ArtifactNode(
    id="file:src/auth.cpp",
    type=ArtifactType.CODE,
    path=Path("src/auth.cpp"),
    name="auth.cpp"
)
graph.add_node(auth_node)

user_node = ArtifactNode(
    id="file:src/user.cpp",
    type=ArtifactType.CODE,
    path=Path("src/user.cpp"),
    name="user.cpp"
)
graph.add_node(user_node)

# 添加测试节点
test_auth_node = ArtifactNode(
    id="file:tests/test_auth.cpp",
    type=ArtifactType.TEST,
    path=Path("tests/test_auth.cpp"),
    name="test_auth.cpp"
)
graph.add_node(test_auth_node)

# 添加文档节点
doc_node = ArtifactNode(
    id="file:docs/auth_api.md",
    type=ArtifactType.DOC,
    path=Path("docs/auth_api.md"),
    name="auth_api.md"
)
graph.add_node(doc_node)

# 建立依赖关系
graph.add_dependency("file:src/auth.cpp", "req:login", DependencyType.IMPLEMENTS)
graph.add_dependency("file:tests/test_auth.cpp", "file:src/auth.cpp", DependencyType.TESTS)
graph.add_dependency("file:docs/auth_api.md", "file:src/auth.cpp", DependencyType.REFERENCES)
graph.add_dependency("file:src/auth.cpp", "file:src/user.cpp", DependencyType.DEPENDS_ON)
```

**依赖图可视化**:
```
req:login (需求)
    ↓ IMPLEMENTS
file:src/user.cpp (代码)
    ↓ DEPENDS_ON
file:src/auth.cpp (代码)
    ↓ TESTS            ↓ REFERENCES
file:tests/test_auth.cpp  file:docs/auth_api.md
```

**步骤 2: 影响范围分析**

现在假设我们修改了 `auth.cpp`：

```python
# 查询影响范围
affected = graph.get_affected_artifacts("file:src/auth.cpp")

# 结果：
[
    ArtifactNode(id="file:tests/test_auth.cpp", type=TEST, name="test_auth.cpp"),
    ArtifactNode(id="file:docs/auth_api.md", type=DOC, name="auth_api.md")
]

# 解释：
# 修改 auth.cpp 会影响：
# 1. test_auth.cpp - 需要重新运行测试
# 2. auth_api.md - 可能需要更新文档
```

**步骤 3: 获取完整影响链**

```python
# 获取完整的影响链
impact_chain = graph.get_impact_chain("file:src/auth.cpp")

# 结果：
[
    (ArtifactNode(id="file:src/auth.cpp", type=CODE), None),
    (ArtifactNode(id="file:tests/test_auth.cpp", type=TEST), DependencyType.TESTS),
    (ArtifactNode(id="file:docs/auth_api.md", type=DOC), DependencyType.REFERENCES)
]

# 可视化输出：
print("影响链分析:")
print("  file:src/auth.cpp (变更源)")
print("    → file:tests/test_auth.cpp (TESTS 关系)")
print("    → file:docs/auth_api.md (REFERENCES 关系)")
```

**实际应用场景**:

**场景 1: 代码变更提醒**

```python
def on_file_changed(file_path):
    """文件变更时自动提醒"""
    affected = graph.get_affected_artifacts(f"file:{file_path}")
    
    if affected:
        print(f"⚠️  修改 {file_path} 会影响以下文件:")
        for artifact in affected:
            if artifact.type == ArtifactType.TEST:
                print(f"  🧪 需要重新运行测试: {artifact.name}")
            elif artifact.type == ArtifactType.DOC:
        print(f"  📝 可能需要更新文档: {artifact.name}")
            elif artifact.type == ArtifactType.CODE:
          print(f"  💻 依赖此文件的代码: {artifact.name}")

# 示例输出：
# ⚠️  修改 src/auth.cpp 会影响以下文件:
#   🧪 需要重新运行测试: test_auth.cpp
#   📝 可能需要更新文档: auth_api.md
```

**场景 2: 自动化测试触发**

```python
def auto_run_tests(changed_file):
    """根据变更自动运行相关测试"""
    affected = graph.get_affected_artifacts(f"file:{changed_file}")
    
    test_files = [
        a for a in affected 
     if a.type == ArtifactType.TEST
    ]
    
    for test in test_files:
        print(f"🧪 运行测试: {test.path}")
        run_test(test.path)

# 修改 auth.cpp 后自动运行 test_auth.cpp
auto_run_tests("src/auth.cpp")
```

**场景 3: 依赖反向查询**

```python
# 查询谁依赖这个文件
dependents = graph.get_dependents("file:src/user.cpp")

# 结果：
[
    (ArtifactNode(id="file:src/auth.cpp", type=CODE), DependencyType.DEPENDS_ON)
]

# 解释：auth.cpp 依赖 user.cpp
# 所以修改 user.cpp 时要小心，会影响 auth.cpp
```

**为什么需要 ArtifactGraph？**
- 🔍 **影响分析**: 快速知道修改会影响哪些文件
- 🧪 **智能测试**: 只运行受影响的测试
- 📝 **文档同步**: 提醒更新相关文档
- 🎯 **依赖追踪**: 理解代码之间的关系

def discover_from_directory(self, root_dir: Path):
    """从项目目录自动发现工件并构建依赖图"""
    
    # 1. 发现源代码文件
    for code_file in root_dir.rglob('*.cpp'):
        node = ArtifactNode(
            id=f"file:{code_file.relative_to(root_dir)}",
            type=ArtifactType.CODE,
            path=code_file
        )
        self.add_node(node)
    
    # 2. 发现测试文件并建立依赖
    for test_file in root_dir.rglob('test_*.cpp'):
        # 推断对应的代码文件
        base_name = test_file.stem.replace('test_', '')
        # 添加依赖: test → code
        self.add_dependency(test_id, code_id, DependencyType.TESTS)
```

---

## 5. EventBus - 事件总线

### 5.1 核心架构

**位置**: `devpal/core/schema/event_bus.py`

```python
class EventBus:
    """事件总线 - 发布订阅架构"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._priority_queue: PriorityQueue = PriorityQueue()
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: Event):
      """发布事件"""
        if event.type in self._subscribers:
          for handler in self._subscribers[event.type]:
            handler(event)
```

### 5.2 标准事件类型

```python
class EventType(Enum):
    TOOL_EXECUTED = "tool_executed"
    VALIDATION_COMPLETED = "validation_completed"
    DELTA_APPLIED = "delta_applied"
    ARTIFACT_CHANGED = "artifact_changed"
    SNAPSHOT_CREATED = "snapshot_created"
    CONFLICT_DETECTED = "conflict_detected"
    WORKFLOW_PHASE_COMPLETED = "workflow_phase_completed"
```
### 5.3 完整事件驱动示例

#### 场景：代码生成后的自动化流程

假设用户请求生成一个 `user_service.cpp` 文件，系统需要：
1. 生成代码
2. 验证代码质量
3. 运行测试
4. 生成文档
5. 创建快照

**步骤 1：订阅者注册**

```python
# 初始化事件总线
event_bus = EventBus()

# 订阅者 1: 日志记录器
def log_handler(event: Event):
    print(f"[LOG] {event.type.value}: {event.data.get('message', '')}")
    with open("devpal.log", "a") as f:
        f.write(f"{datetime.now()} - {event.type.value}\n")

event_bus.subscribe(EventType.TOOL_EXECUTED, log_handler)
event_bus.subscribe(EventType.VALIDATION_COMPLETED, log_handler)
event_bus.subscribe(EventType.DELTA_APPLIED, log_handler)

# 订阅者 2: 测试运行器
def test_runner_handler(event: Event):
    if event.type == EventType.DELTA_APPLIED:
        file_path = event.data.get("file_path")
     if file_path and file_path.endswith(".cpp"):
            print(f"[TEST] Running tests for {file_path}")
          # 触发测试工具
            test_result = run_cpp_tests(file_path)
            # 发布测试完成事件
            event_bus.publish(Event(
             type=EventType.TOOL_EXECUTED,
            data={"tool": "run_tests", "result": test_result}
            ))

event_bus.subscribe(EventType.DELTA_APPLIED, test_runner_handler)

# 订阅者 3: 文档生成提醒器
def doc_reminder_handler(event: Event):
    if event.type == EventType.VALIDATION_COMPLETED:
        validation_result = event.data.get("result")
        if validation_result.get("passed"):
          print("[DOC] Validation passed, consider generating documentation")
            # 可以自动触发文档生成工具
         event_bus.publish(Event(
                type=EventType.TOOL_EXECUTED,
             data={"tool": "generate_docs", "status": "triggered"}
          ))

event_bus.subscribe(EventType.VALIDATION_COMPLETED, doc_reminder_handler)

# 订阅者 4: 快照管理器
def snapshot_handler(event: Event):
    if event.type == EventType.WORKFLOW_PHASE_COMPLETED:
        phase = event.data.get("phase")
        if phase in ["Phase 3", "Phase 5", "Phase 9"]:  # 关键阶段
            print(f"[SNAPSHOT] Creating snapshot after {phase}")
            state_manager.create_snapshot(f"after_{phase}")
            event_bus.publish(Event(
              type=EventType.SNAPSHOT_CREATED,
                data={"phase": phase, "timestamp": datetime.now()}
            ))

event_bus.subscribe(EventType.WORKFLOW_PHASE_COMPLETED, snapshot_handler)
```

**步骤 2：事件链触发**

```python
# 1. 工具执行：生成代码
print("=== Step 1: Generate Code ===")
event_bus.publish(Event(
    type=EventType.TOOL_EXECUTED,
    data={
      "tool": "write_file",
        "file_path": "src/user_service.cpp",
        "message": "Generated user_service.cpp"
    }
))

# 输出:
# [LOG] tool_executed: Generated user_service.cpp
# 2026-05-11 10:30:00 - tool_executed

# 2. 应用增量变更
print("\n=== Step 2: Apply Delta ===")
event_bus.publish(Event(
    type=EventType.DELTA_APPLIED,
    data={
      "file_path": "src/user_service.cpp",
        "delta_id": "delta_001",
        "lines_changed": 45
    }
))

# 输出:
# [LOG] delta_applied: 
# 2026-05-11 10:30:01 - delta_applied
# [TEST] Running tests for src/user_service.cpp
# [LOG] tool_executed: 
# 2026-05-11 10:30:02 - tool_executed

# 3. 验证完成
print("\n=== Step 3: Validation ===")
event_bus.publish(Event(
    type=EventType.VALIDATION_COMPLETED,
    data={
        "file_path": "src/user_service.cpp",
        "result": {
            "passed": True,
            "layers": {
              "format": "PASS",
                "semantic": "PASS",
            "parser": "PASS",
              "business": "PASS"
            }
        }
    }
))

# 输出:
# [LOG] validation_completed: 
# 2026-05-11 10:30:03 - validation_completed
# [DOC] Validation passed, consider generating documentation
# [LOG] tool_executed: 
# 2026-05-11 10:30:03 - tool_executed

# 4. 工作流阶段完成
print("\n=== Step 4: Workflow Phase Completed ===")
event_bus.publish(Event(
    type=EventType.WORKFLOW_PHASE_COMPLETED,
  data={
        "phase": "Phase 3",
        "status": "completed",
        "artifacts": ["src/user_service.cpp"]
    }
))

# 输出:
# [SNAPSHOT] Creating snapshot after Phase 3
# [LOG] snapshot_created: 
# 2026-05-11 10:30:04 - snapshot_created
```

**步骤 3：优先级队列示例**

```python
# 高优先级事件处理
class PriorityEvent:
  def __init__(self, priority: int, event: Event):
        self.priority = priority  # 数字越小优先级越高
        self.event = event
    
    def __lt__(self, other):
        return self.priority < other.priority

# 使用优先级队列
priority_queue = PriorityQueue()

# 添加不同优先级的事件
priority_queue.put(PriorityEvent(3, Event(EventType.TOOL_EXECUTED, {"msg": "Low priority"})))
priority_queue.put(PriorityEvent(1, Event(EventType.CONFLICT_DETECTED, {"msg": "High priority"})))
priority_que.put(PriorityEvent(2, Event(EventType.VALIDATION_COMPLETED, {"msg": "Medium priority"})))

# 按优先级处理
while not priority_queue.empty():
    priority_event = priority_queue.get()
    print(f"Processing (priority={priority_event.priority}): {priority_event.event.data['msg']}")

# 输出:
# Processing (priority=1): High priority
# Processing (priority=2): Medium priority
# Processing (priority=3): Low priority
```

### 5.4 事件总线的优势

1. **解耦组件**：订阅者和发布者互不依赖
2. **可扩展性**：新增订阅者无需修改现有代码
3. **异步处理**：事件可以异步触发多个处理器
4. **审计追踪**：所有事件都可以被日志记录器捕获

---

## 6. StateManager - 状态持久化

### 6.1 核心功能

**位置**: `devpal/core/schema/spec.py`
```python
class StateManager:
    """状态持久化管理器"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.spec_dir = workspace / '.spec'
        self.spec_dir.mkdir(exist_ok=True)
    def save_snapshot(self, snapshot: Snapshot):
        """保存状态快照"""
        snapshot_file = self.spec_dir / f"snapshot_{snapshot.id}.json"
        snapshot_file.write_text(json.dumps(snapshot.to_dict()))
    
    def load_snapshot(self, snapshot_id: str) -> Snapshot:
        """加载状态快照"""
        snapshot_file = self.spec_dir / f"snapshot_{snapshot_id}.json"
        data = json.loads(snapshot_file.read_text())
        return Snapshot.from_dict(data)
```

### 6.2 完整状态管理示例

#### 场景：多阶段开发流程的状态快照

假设用户正在开发一个登录系统，需要在关键阶段保存状态快照，以便出错时回滚。

**步骤 1：初始化状态管理器**

```python
from pathlib import Path
from datetime import datetime
import json

# 初始化
workspace = Path("c:/projects/login_system")
state_manager = StateManager(workspace)

# 创建 .spec 目录
# c:/projects/login_system/.spec/
```

**步骤 2：Phase 1 完成后创建快照**

```python
# Phase 1: 需求文档解析完成
phase1_snapshot = Snapshot(
    id="snapshot_phase1_20260511_103000",
    timestamp=datetime.now(),
    phase="Phase 1: Requirements Analysis",
    artifacts={
        "requirements.md": {
            "path": "docs/requirements.md",
            "content_hash": "a1b2c3d4",
            "size": 2048,
            "created_at": "2026-05-11 10:30:00"
        }
    },
    metadata={
        "user_request": "Create a login system with JWT authentication",
        "parsed_features": ["user registration", "login", "JWT tokens", "password hashing"],
     "estimated_files": 5
    }
)

# 保存快照
state_manager.save_snapshot(phase1_snapshot)
print(f"✅ Snapshot saved: {phase1_snapshot.id}")

# 文件保存位置:
# c:/projects/login_system/.spec/snapshot_phase1_20260511_103000.json
```

**步骤 3：Phase 3 代码生成后创建快照**

```python
# Phase 3: 核心代码生成完成
phase3_snapshot = Snapshot(
    id="snapshot_phase3_20260511_104500",
    timestamp=datetime.now(),
    phase="Phase 3: Core Code Generation",
    artifacts={
        "auth_service.py": {
            "path": "src/auth_service.py",
          "content_hash": "e5f6g7h8",
            "size": 4096,
            "functions": ["register_user", "login_user", "verify_token"],
            "dependencies": ["jwt", "bcrypt", "sqlalchemy"]
        },
        "user_model.py": {
            "path": "src/models/user_model.py",
            "content_hash": "i9j0k1l2",
            "size": 1024,
            "classes": ["User"],
        "fields": ["id", "username", "password_hash", "email"]
        },
        "config.py": {
            "path": "src/config.py",
        "content_hash": "m3n4o5p6",
          "size": 512,
            "constants": ["SECRET_KEY", "TOKEN_EXPIRY"]
        }
    },
    metadata={
        "total_files": 3,
        "total_lines": 250,
        "validation_status": "pending"
    }
)
state_manager.save_snapshot(phase3_snapshot)
print(f"✅ Snapshot saved: {phase3_snapshot.id}")
```

**步骤 4：Phase 5 修复后创建快照**

```python
# Phase 5: 自动修复完成
phase5_snapshot = Snapshot(
    id="snapshot_phase5_20260511_110000",
    timestamp=datetime.now(),
    phase="Phase 5: Auto-Fix Completed",
    artifacts={
        "auth_service.py": {
            "path": "src/auth_service.py",
            "content_hash": "q7r8s9t0",  # 内容已变更
            "size": 4200,
            "fixes_applied": [
                "Fixed SQL injection in login_user",
                "Added input validation for register_user",
                "Improved error handling"
          ]
        },
        "user_model.py": {
            "path": "src/models/user_model.py",
            "content_hash": "i9j0k1l2",  # 未变更
            "size": 1024
        },
        "config.py": {
          "path": "src/config.py",
            "content_hash": "u1v2w3x4",  # 内容已变更
            "size": 600,
            "fixes_applied": ["Added environment variable support"]
        }
    },
    metadata={
        "total_fixes": 4,
        "validation_status": "passed",
      "all_layers_passed": True
    }
)

state_manager.save_snapshot(phase5_snapshot)
print(f"✅ Snapshot saved: {phase5_snapshot.id}")
```

**步骤 5：快照对比和回滚**

```python
# 对比 Phase 3 和 Phase 5 的变更
def compare_snapshots(snapshot1_id: str, snapshot2_id: str):
    snap1 = state_manager.load_snapshot(snapshot1_id)
    snap2 = state_manager.load_snapshot(snapshot2_id)
    
    print(f"\n=== Comparing {snap1.phase} vs {snap2.phase} ===")
    
    # 找出变更的文件
    for file_name in snap2.artifacts:
        if file_name in snap1.artifacts:
        hash1 = snap1.artifacts[file_name]["content_hash"]
         hash2 = snap2.artifacts[file_name]["content_hash"]
         if hash1 != hash2:
                print(f"📝 Modified: {file_name}")
                if "fixes_applied" in snap2.artifacts[file_name]:
            for fix in snap2.artifacts[file_name]["fixes_applied"]:
             print(f"   - {fix}")
       else:
                print(f"✅ Unchanged: {file_name}")
        else:
            print(f"➕ New file: {file_name}")

compare_snapshots("snapshot_phase3_20260511_104500", "snapshot_phase5_20260511_110000")

# 输出:
# === Comparing Phase 3: Core Code Generation vs Phase 5: Auto-Fix Completed ===
# 📝 Modified: auth_service.py
#    - Fixed SQL injection in login_user
#    - Added input validation for register_user
#    - Improved error handling
# ✅ Unchanged: user_model.py
# 📝 Modified: config.py
#    - Added environment variable support
```

**步骤 6：回滚到 Phase 3**

```python
def rollback_to_snapshot(snapshot_id: str):
    """回滚到指定快照"""
    snapshot = state_manager.load_snapshot(snapshot_id)
    
    print(f"\n🔄 Rolling back to: {snapshot.phase}")
    print(f"   Timestamp: {snapshot.timestamp}")
    
    # 恢复所有文件
    for file_name, file_info in snapshot.artifacts.items():
        file_path = workspace / file_info["path"]
        print(f"   Restoring: {file_path}")
      
        # 从快照恢复文件内容（实际实现需要存储完整内容或 diff）
        # restore_file_from_snapshot(file_path, file_info)
    
    print("✅ Rollback completed")

# 如果 Phase 5 的修复出现问题，回滚到 Phase 3
rollback_to_snapshot("snapshot_phase3_20260511_104500")

# 输出:
# 🔄 Rolling back to: Phase 3: Core Code Generation
#    Timestamp: 2026-05-11 10:45:00
#    Restoring: c:/projects/login_system/src/auth_service.py
#  Restoring: c:/projects/login_system/src/models/user_model.py
#    Restoring: c:/projects/login_system/src/config.py
# ✅ Rollback completed
```

**步骤 7：快照历史查询**

```python
def list_all_snapshots():
    """列出所有快照"""
    spec_dir = workspace / '.spec'
    snapshot_files = list(spec_dir.glob("snapshot_*.json"))
    
    print(f"\n📚 Total snapshots: {len(snapshot_files)}\n")
    
    for snapshot_file in sorted(snapshot_files):
        data = json.loads(snapshot_file.read_text())
        print(f"ID: {data['id']}")
        print(f"   Phase: {data['phase']}")
        print(f"   Time: {data['timestamp']}")
        print(f"   Files: {len(data['artifacts'])}")
        print()

list_all_snapshots()

# 输出:
# 📚 Total snapshots: 3
#
# ID: snapshot_phase1_20260511_103000
#    Phase: Phase 1: Requirements Analysis
#    Time: 2026-05-11 10:30:00
#    Files: 1
#
# ID: snapshot_phase3_20260511_104500
#    Phase: Phase 3: Core Code Generation
#    Time: 2026-05-11 10:45:00
#    Files: 3
#
# ID: snapshot_phase5_20260511_110000
#    Phase: Phase 5: Auto-Fix Completed
#    Time: 2026-05-11 11:00:00
#    Files: 3
```

### 6.3 状态管理的优势

1. **时间旅行**：可以回到任意历史状态
2. **增量备份**：只保存变更的文件，节省空间
3. **审计追踪**：记录每个阶段的元数据
4. **错误恢复**：出错时快速回滚到稳定状态

---

## 7. CompileDB - 编译数据库

### 7.1 核心功能

**位置**: `devpal/core/schema/compile_db.py`

```python
class CompileDB:
    """编译数据库 - 符号索引和依赖分析"""
    
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self._init_schema()
    
    def index_file(self, file_path: Path):
        """索引文件中的符号"""
        # 解析文件，提取函数、类、变量
        symbols = self._parse_symbols(file_path)
      
      # 存入数据库
        for symbol in symbols:
         self.conn.execute(
                "INSERT INTO symbols (name, type, file, line) VALUES (?, ?, ?, ?)",
              (symbol.name, symbol.type, str(file_path), symbol.line)
            )
    
    def find_symbol(self, name: str) -> List[Symbol]:
      """查找符号""
        cursor = self.conn.execute(
          "SELECT * FROM symbols WHERE name = ?",
            (name,)
        )
        return [Symbol.from_row(row) for row in cursor.fetchall()]
```

### 7.2 完整编译数据库示例

#### 场景：C++ 项目的符号索引和依赖分析

假设有一个 C++ 项目，包含多个文件，需要索引所有符号并分析依赖关系。

**项目结构**

```
src/
├── main.cpp
├── user_service.h
├── user_service.cpp
├── database.h
└── database.cpp
```

**步骤 1：初始化编译数据库**

```python
from pathlib import Path
import sqlite3

# 初始化
db_path = Path("c:/projects/login_system/.spec/compile.db")
compile_db = CompileDB(db_path)

# 数据库表结构
"""
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'function', 'class', 'variable', 'macro'
    file TEXT NOT NULL,
    line INTEGER NOT NULL,
    signature TEXT,      -- 函数签名
    namespace TEXT,      -- 命名空间
    access TEXT       -- 'public', 'private', 'protected'
);

CREATE TABLE dependencies (
    id INTEGER PRIMARY KEY,
    source_file TEXT NOT NULL,
    target_file TEXT NOT NULL,
    dependency_type TEXT  -- 'include', 'call', 'inherit'
);

CREATE INDEX idx_symbol_name ON symbols(name);
CREATE INDEX idx_symbol_file ON symbols(file);
CREATE INDEX idx_dependency_source ON dependencies(source_file);
"""
```

**步骤 2：索引 user_service.h**

```cpp
// user_service.h
#ifndef USER_SERVICE_H
#define USER_SERVICE_H

#include <string>
#include "database.h"

namespace auth {

class UserService {
public:
    UserService(Database* db);
    bool registerUser(const std::string& username, const std::string& password);
    bool loginUser(const std::string& username, const std::string& password);
    std::string generateToken(int user_id);

private:
    Database* m_database;
    std::string m_secret_key;
};

} // namespace auth

#endif
```

```python
# 索引 user_service.h
file_path = Path("src/user_service.h")
symbols = compile_db.index_file(file_path)

# 插入的符号:
symbols_inserted = [
    {
        "name": "UserService",
        "type": "class",
        "file": "src/user_service.h",
        "line": 8,
        "namespace": "auth",
        "access": "public"
    },
    {
        "name": "UserService::UserService",
        "type": "function",
        "file": "src/user_service.h",
        "line": 10,
        "signature": "UserService(Database* db)",
        "namespace": "auth",
        "access": "public"
    },
    {
      "name": "UserService::registerUser",
        "type": "function",
      "file": "src/user_service.h",
        "line": 11,
      "signature": "bool registerUser(const std::string&, const std::string&)",
        "namespace": "auth",
        "access": "public"
    },
    {
        "name": "UserService::loginUser",
        "type": "function",
        "file": "src/user_service.h",
        "line": 12,
        "signature": "bool loginUser(const std::string&, const std::string&)",
        "namespace": "auth",
        "access": "public"
    },
    {
        "name": "UserService::generateToken",
        "type": "function",
        "file": "src/user_service.h",
        "line": 13,
        "signature": "std::string generateToken(int user_id)",
        "namespace": "auth",
        "access": "public"
    },
    {
        "name": "UserService::m_database",
     "type": "variable",
        "file": "src/user_service.h",
        "line": 16,
        "namespace": "auth",
        "access": "private"
    },
    {
        "name": "UserService::m_secret_key",
        "type": "variable",
        "file": "src/user_service.h",
      "line": 17,
        "namespace": "auth",
        "access": "private"
    }
]

# 插入依赖关系
dependencies_inserted = [
    {
        "source_file": "src/user_service.h",
        "target_file": "database.h",
        "dependency_type": "include"
    }
]

print(f"✅ Indexed {len(symbols_inserted)} symbols from user_service.h")
print(f"✅ Found {len(dependencies_inserted)} dependencies")
```

**步骤 3：索引 main.cpp**

```cpp
// main.cpp
#include <iostream>
#include "user_service.h"
#include "database.h"

int main() {
    Database db("users.db");
    auth::UserService service(&db);
    
    // 注册用户
    if (service.registerUser("alice", "password123")) {
        std::cout << "User registered successfully\n";
    }
    
    // 登录用户
    if (service.loginUser("alice", "password123")) {
      std::string token = service.generateToken(1);
        std::cout << "Login successful, token: " << token << "\n";
    }
    
    return 0;
}
```

```python
# 索引 main.cpp
file_path = Path("src/main.cpp")
symbols = compile_db.index_file(file_path)

# 插入的符号:
symbols_inserted = [
    {
        "name": "main",
        "type": "function",
        "file": "src/main.cpp",
        "line": 5,
        "signature": "int main()",
        "namespace": "",
        "access": "public"
    },
    {
        "name": "db",
        "type": "variable",
        "file": "src/main.cpp",
        "line": 6,
        "namespace": "",
     "access": "local"
    },
    {
        "name": "service",
        "type": "variable",
        "file": "src/main.cpp",
        "line": 7,
        "namespace": "",
        "access": "local"
    }
]

# 插入依赖关系
dependencies_inserted = [
    {
        "source_file": "src/main.cpp",
        "target_file": "user_service.h",
        "dependency_type": "include"
    },
    {
        "source_file": "src/main.cpp",
        "target_file": "database.h",
        "dependency_type": "include"
    },
    {
        "source_file": "src/main.cpp",
        "target_file": "src/user_service.h",
     "dependency_type": "call",  # 调用 UserService::registerUser
    },
    {
        "source_file": "src/main.cpp",
        "target_file": "src/user_service.h",
        "dependency_type": "call",  # 调用 UserService::loginUser
    },
    {
        "source_file": "src/main.cpp",
        "target_file": "src/user_service.h",
        "dependency_type": "call",  # 调用 UserService::generateToken
    }
]

print(f"✅ Indexed {len(symbols_inserted)} symbols from main.cpp")
print(f"✅ Found {len(dependencies_inserted)} dependencies")
```

**步骤 4：符号查询**

```python
# 查询 1: 查找 registerUser 函数
print("\n=== Query 1: Find 'registerUser' ===")
symbols = compile_db.find_symbol("UserService::registerUser")
for symbol in symbols:
    print(f"Found: {symbol.name}")
    print(f"  Type: {symbol.type}")
    print(f"  File: {symbol.file}:{symbol.line}")
    print(f"  Signature: {symbol.signature}")
    print(f"  Access: {symbol.access}")

# 输出:
# Found: UserService::registerUser
#   Type: function
#   File: src/user_service.h:11
#   Signature: bool registerUser(const std::string&, const std::string&)
#   Access: public

# 查询 2: 查找所有 UserService 的成员
print("\n=== Query 2: Find all UserService members ===")
cursor = compile_db.conn.execute(
    "SELECT name, type, line, access FROM symbols WHERE name LIKE 'UserService::%'"
)
for row in cursor.fetchall():
    print(f"{row[0]} ({row[1]}) - Line {row[2]} - {row[3]}")

# 输出:
# UserService::UserService (function) - Line 10 - public
# UserService::registerUser (function) - Line 11 - public
# UserService::loginUser (function) - Line 12 - public
# UserService::generateToken (function) - Line 13 - public
# UserService::m_database (variable) - Line 16 - private
# UserService::m_secret_key (variable) - Line 17 - private

# 查询 3: 查找 main.cpp 的所有依赖
print("\n=== Query 3: Find dependencies of main.cpp ===")
cursor = compile_db.conn.execute(
    "SELECT target_file, dependency_type FROM dependencies WHERE source_file = ?",
    ("src/main.cpp",)
)
for row in cursor.fetchall():
    print(f"  {row[0]} ({row[1]})")

# 输出:
#   user_service.h (include)
#   database.h (include)
#   src/user_service.h (call)
#   src/user_service.h (call)
#   src/user_service.h (call)
```

**步骤 5：依赖图分析**

```python
def analyze_dependencies(file_path: str):
    """分析文件的依赖关系"""
    print(f"\n=== Dependency Analysis for {file_path} ===")
    
    # 直接依赖
    cursor = compile_db.conn.execute(
        "SELECT DISTINCT target_file FROM dependencies WHERE source_file = ?",
        (file_path,)
    )
    direct_deps = [row[0] for row in cursor.fetchall()]
    print(f"\nDirect dependencies ({len(direct_deps)}):")
    for dep in direct_deps:
        print(f"  → {dep}")
    
    # 被谁依赖
    cursor = compile_db.conn.execute(
        "SELECT DISTINCT source_file FROM dependencies WHERE target_file = ?",
        (file_path,)
    )
    dependents = [row[0] for row in cursor.fetchall()]
  print(f"\nDependent files ({len(dependents)}):")
    for dep in dependents:
        print(f"  ← {dep}")

analyze_dependencies("src/user_service.h")

# 输出:
# === Dependency Analysis for src/user_service.h ===
#
# Direct dependencies (1):
#   → database.h
#
# Dependent files (1):
#   ← src/main.cpp
```

**步骤 6：影响分析**

```python
def impact_analysis(file_path: str):
    """分析修改文件的影响范围"""
    print(f"\n=== Impact Analysis: Modifying {file_path} ===")
    
  # 找出所有直接和间接依赖此文件的文件
    affected_files = set()
    to_check = [file_path]
    
    while to_check:
        current = to_check.pop(0)
        cursor = compile_db.conn.execute(
            "SELECT DISTINCT source_file FROM dependencies WHERE target_file = ?",
            (current,)
        )
        for row in cursor.fetchall():
            dependent = row[0]
            if dependent not in affected_files:
                affected_files.add(dependent)
                to_check.append(dependent)
    
    print(f"\n⚠️  Modifying this file will affect {len(affected_files)} files:")
    for file in sorted(affected_files):
        print(f"  • {file}")
  
    print(f"\n📋 Recommended actions:")
    print(f"  1. Recompile all affected files")
    print(f"  2. Run tests for affected modules")
    print(f"  3. Update documentation if API changed")

impact_analysis("src/user_service.h")

# 输出:
# === Impact Analysis: Modifying src/user_service.h ===
#
# ⚠️  Modifying this file will affect 1 files:
#   • src/main.cpp
#
# 📋 Recommended actions:
#   1. Recompile all affected files
#   2. Run tests for affected modules
#   3. Update documentation if API changed
```

### 7.3 编译数据库的优势

1. **快速符号查找**：O(1) 时间复杂度查找任意符号
2. **依赖分析**：自动分析文件间的依赖关系
3. **影响评估**：修改代码前预测影响范围
4. **重构支持**：重命名符号时找出所有引用位置

---

## 8. 协同工作示例

```python
class OpenSpecContext:
    """统一上下文 - 协调所有组件"""
    
    def process_code_change(self, file_path: str, new_content: str):
      """处理代码变更的完整流程"""
        
        # 1. 创建 Delta 规范
        delta_spec = DeltaSpec(file_path)
        delta_spec.load_original()
        deltas = delta_spec.create_delta_from_diff(new_content)
        
        # 2. 验证变更
        pipeline_result = self.validation_engine.pipeline.run(
       content=new_content,
            context={'file_path': file_path}
        )
        
        if not pipeline_result.passed:
            return False
        
        # 3. 应用 Delta
        result = delta_spec.apply(dry_run=False)
        
        # 4. 发布事件
        self.event_bus.publish(Event(
          type=EventType.DELTA_APPLIED,
            data={'file': file_path, 'deltas': len(deltas)}
        ))
        
        # 5. 分析影响范围
        affected = self.artifact_graph.get_affected_artifacts(f"file:{file_path}")
        
        # 6. 保存状态快照
        snapshot = self.state_manager.create_snapshot()
        self.state_manager.save_snapshot(snapshot)
        
        return True
```

### 8.1 完整协同流程示例

#### 场景：用户请求添加密码重置功能

用户输入：**"Add password reset functionality to the login system"**

**步骤 1：Executor 规划任务**

```python
# 初始化完整上下文
class FullOpenSpecContext:
    """统一上下文 - 协调所有组件"""
    
    def __init__(self):
        self.executor = AgentEngine()
        self.validation_engine = ValidationEngine()
        self.delta_engine = DeltaEngine()
        self.artifact_graph = ArtifactGraph()
        self.event_bus = EventBus()
        self.state_manager = StateManager(Path("c:/projects/login_system"))
        self.compile_db = CompileDB(Path("c:/projects/login_system/.spec/compile.db"))
        
        # 订阅事件
     self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        self.event_bus.subscribe(EventType.DELTA_APPLIED, self._on_delta_applied)
        self.event_bus.subscribe(EventType.VALIDATION_COMPLETED, self._on_validation_completed)
        self.event_bus.subscribe(EventType.WORKFLOW_PHASE_COMPLETED, self._on_phase_completed)
    
    def _on_delta_applied(self, event: Event):
      """Delta 应用后更新 CompileDB"""
        file_path = event.data.get("file_path")
     print(f"[EventBus] Delta applied to {file_path}, updating CompileDB...")
        self.compile_db.index_file(Path(file_path))
    
    def _on_validation_completed(self, event: Event):
        """验证完成后更新 ArtifactGraph"""
        result = event.data.get("result")
        if result.get("passed"):
       print(f"[EventBus] Validation passed, updating ArtifactGraph...")
    
    def _on_phase_completed(self, event: Event):
        """阶段完成后创建快照"""
        phase = event.data.get("phase")
        if phase in ["Phase 3", "Phase 5", "Phase 9"]:
            print(f"[EventBus] {phase} completed, creating snapshot...")
            snapshot = self.state_manager.create_snapshot(f"after_{phase}")
         self.state_manager.save_snapshot(snapshot)

# 初始化
context = FullOpenSpecContext()

# Executor 生成计划
plan = context.executor.planner.create_plan(
    user_request="Add password reset functionality to the login system"
)

print("=== Generated Plan ===")
for i, step in enumerate(plan.steps, 1):
    print(f"{i}. {step.action}: {step.description}")

# 输出:
# === Generated Plan ===
# 1. analyze_requirements: Parse user request and identify required features
# 2. design_api: Design password reset API endpoints
# 3. implement_code: Generate reset_password function in auth_service.py
# 4. validate_code: Run four-layer validation pipeline
# 5. update_tests: Add unit tests for password reset
# 6. update_docs: Update API documentation
```

**步骤 2：生成代码并创建 Delta**

```python
# 生成新代码
new_code = '''
def reset_password(self, email: str) -> bool:
    """重置用户密码"""
    # 1. 验证邮箱是否存在
    user = self.db.query(User).filter_by(email=email).first()
    if not user:
        return False
    
    # 2. 生成重置令牌
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now() + timedelta(hours=1)
    self.db.commit()
    
    # 3. 发送重置邮件
    send_reset_email(email, reset_token)
    return True
'''

# 创建 Delta 规范
file_path = "src/auth_service.py"
delta_spec = DeltaSpec(file_path)
delta_spec.load_original()

# 生成 Delta
deltas = delta_spec.create_delta_from_diff(new_code)

print(f"\n=== Generated {len(deltas)} Deltas ===")
for delta in deltas:
    print(f"Delta {delta.id}: {delta.operation} at line {delta.line_number}")

# 输出:
# === Generated 15 Deltas ===
# Delta delta_001: INSERT at line 45
# Delta delta_002: INSERT at line 46
# ...
```

**步骤 3：四层验证流水线**

```python
# 运行验证流水线
print("\n=== Running Validation Pipeline ===")

validation_result = context.validation_engine.pipeline.run(
    content=new_code,
    context={
        'file_path': file_path,
        'language': 'python',
        'project_type': 'web_api'
    }
)

# Layer 1: Format Validation
print(f"Layer 1 (Format): {validation_result.layers['format'].status}")
# 输出: Layer 1 (Format): PASS

# Layer 2: Semantic Validation
print(f"Layer 2 (Semantic): {validation_result.layers['semantic'].status}")
# 检查: secrets 模块是否导入
# 输出: Layer 2 (Semantic): FAIL - Missing import: secrets

# 自动修复
print("\n[Auto-Fix] Adding missing import...")
fixed_code = "import secrets\nfrom datetime import datetime, timedelta\n" + new_code

# 重新验证
validation_result = context.validation_engine.pipeline.run(
    content=fixed_code,
    context={'file_path': file_path}
)

print(f"All layers: {validation_result.passed}")
# 输出: All layers: True

# 发布验证完成事件
context.event_bus.publish(Event(
    type=EventType.VALIDATION_COMPLETED,
    data={
        'file_path': file_path,
        'result': validation_result.to_dict()
    }
))

# 输出:
# [EventBus] Validation passed, updating ArtifactGraph...
```

**步骤 4：应用 Delta 并更新依赖图**

```python
# 应用 Delta (逆序)
print("\n=== Applying Deltas (Reverse Order) ===")

for delta in reversed(deltas):
    result = delta_spec.apply_single_delta(delta, dry_run=False)
    print(f"Applied {delta.id}: {result.status}")

# 发布 Delta 应用事件
context.event_bus.publish(Event(
    type=EventType.DELTA_APPLIED,
    data={
      'file_path': file_path,
        'delta_count': len(deltas)
    }
))

# 输出:
# [EventBus] Delta applied to src/auth_service.py, updating CompileDB...

# 更新 ArtifactGraph
context.artifact_graph.add_artifact(
    artifact_id=f"file:{file_path}",
    artifact_type="source_file",
    metadata={
        'language': 'python',
        'functions': ['reset_password'],
        'dependencies': ['secrets', 'datetime', 'User', 'send_reset_email']
    }
)

# 添加依赖关系
context.artifact_graph.add_dependency(
    from_artifact=f"file:{file_path}",
    to_artifact="module:secrets",
    dependency_type="import"
)

print("\n=== ArtifactGraph Updated ===")
print(f"Total artifacts: {context.artifact_graph.graph.number_of_nodes()}")
print(f"Total dependencies: {context.artifact_graph.graph.number_of_edges()}")
```

**步骤 5：影响范围分析**

```python
# 分析影响范围
print("\n=== Impact Analysis ===")

affected = context.artifact_graph.get_affected_artifacts(f"file:{file_path}")

print(f"Modifying {file_path} will affect {len(affected)} artifacts:")
for artifact in affected:
    print(f"  • {artifact}")

# 输出:
# Modifying src/auth_service.py will affect 3 artifacts:
#   • file:src/main.py (imports auth_service)
#   • file:tests/test_auth.py (tests auth_service)
#   • file:docs/api.md (documents auth_service)
```

**步骤 6：创建状态快照**

```python
# 创建快照
print("\n=== Creating Snapshot ===")

snapshot = Snapshot(
    id=f"snapshot_password_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    timestamp=datetime.now(),
    phase="Feature: Password Reset",
    artifacts={
        file_path: {
        'path': file_path,
            'content_hash': hashlib.sha256(fixed_code.encode()).hexdigest(),
            'functions_added': ['reset_password'],
            'validation_status': 'passed'
        }
    },
    metadata={
        'user_request': 'Add password reset functionality',
        'deltas_applied': len(deltas),
        'affected_files': len(affected)
    }
)

context.state_manager.save_snapshot(snapshot)
print(f"✅ Snapshot saved: {snapshot.id}")

# 发布阶段完成事件
context.event_bus.publish(Event(
    type=EventType.WORKFLOW_PHASE_COMPLETED,
    data={
        'phase': 'Phase 3',
        'status': 'completed',
        'artifacts': [file_path]
    }
))

# 输出:
# [EventBus] Phase 3 completed, creating snapshot...
```

**步骤 7：Reflector 自我检查**

```python
# Reflector 检查执行结果
print("\n=== Reflector Self-Check ===")

reflection = context.executor.reflector.reflect(
    plan=plan,
    execution_results={
        'code_generated': True,
        'validation_passed': True,
        'deltas_applied': True,
        'tests_passed': False  # 假设测试失败
    }
)

if not reflection.success:
    print(f"⚠️  Reflection found issues:")
    for issue in reflection.issues:
        print(f"  • {issue}")
    
    # 生成修复计划
    fix_plan = context.executor.planner.create_fix_plan(reflection.issues)
    print(f"\n🔧 Generated fix plan with {len(fix_plan.steps)} steps")

# 输出:
# ⚠️  Reflection found issues:
#   • Tests failed: test_reset_password_invalid_email
#   • Missing error handling for email service failure
#
# 🔧 Generated fix plan with 2 steps
```

### 8.2 组件协同流程图

```
User Request
     ↓
[Executor.Planner] → Generate Plan
     ↓
[Executor.Executor] → Execute Steps
     ↓
[DeltaEngine] → Create Deltas
     ↓
[ValidationEngine] → 4-Layer Validation
     ↓       ↓
   PASS      FAIL → Auto-Fix → Retry
     ↓
[DeltaEngine] → Apply Deltas (Reverse Order)
     ↓
[EventBus] → Publish DELTA_APPLIED
     ↓         ↓
[CompileDB]  [ArtifactGraph] → Update Indexes
     ↓
[StateManager] → Create Snapshot
     ↓
[EventBus] → Publish PHASE_COMPLETED
     ↓
[Executor.Reflector] → Self-Check
     ↓      ↓
   SUCCESS   FAIL → Generate Fix Plan → Retry
     ↓
Complete
```

### 8.3 协同工作的优势

1. **自动化流程**：从需求到部署全自动
2. **实时验证**：每个步骤都有质量保证
3. **可追溯性**：EventBus 记录所有操作
4. **可回滚性**：StateManager 支持任意时间点回滚
5. **影响分析**：ArtifactGraph + CompileDB 预测变更影响
6. **自我修复**：Reflector 发现问题并自动修复

---

## 9. 总结

DevPal Agent v2.0 的核心引擎层通过以下组件实现了完整的开发工作流：

| 组件 | 职责 | 关键特性 |
|------|------|---------|
| **Executor** | 执行引擎 | Plan-Act-Reflect 循环 |
| **ValidationEngine** | 四层验证 | Format → Semantic → Parser → Business |
| **DeltaEngine** | 增量变更 | 冲突检测、原子应用、回滚支持 |
| **ArtifactGraph** | 依赖图 | 影响范围分析、自动关联 |
| **EventBus** | 事件总线 | 发布订阅、解耦通信 |
| **StateManager** | 状态持久化 | 快照管理、历史记录 |
| **CompileDB** | 编译数据库 | 符号索引、依赖分析 |

这些组件共同构成了一个安全、可追踪、可回滚的智能开发系统。

---

**文档维护**: 本文档随代码更新而更新  
**反馈渠道**: GitHub Issues
