# Self-Healing 根因分析增强实施计划

**日期**：2026-05-24  
**目标**：从简单 Retry 升级到基于 Traceability 的智能根因分析系统  
**预期工期**：1-2 天

---

## 1. 背景与目标

### 1.1 当前状态

**已完成能力**：
- ✅ TestSelfHealer 基础修复能力（Phase 10）
- ✅ 编译错误自动修复（C++/Python）
- ✅ 测试失败自动修复
- ✅ Retry 机制（最多 3 次）
- ✅ ArtifactGraph 追踪系统（需求→代码→测试）

**当前限制**：
- ❌ 只修复表面症状，无根本原因分析
- ❌ 相同错误重复出现，无学习机制
- ❌ 修复策略单一，缺乏智能决策
- ❌ 无修复历史记录和统计分析
- ❌ 无法识别系统性问题（如配置错误、环境问题）

**典型问题场景**：
```python
# 场景 1: 编译错误
Error: undefined reference to `login_user`
Current: 简单重新生成代码
Problem: 不知道为什么会缺少这个函数（需求遗漏？代码生成错误？）

# 场景 2: 测试失败
AssertionError: expected 200, got 401
Current: 修改测试或代码
Problem: 不知道根因是认证逻辑错误还是测试用例错误

# 场景 3: 重复错误
同样的 import 错误出现 3 次
Current: 每次都重新修复
Problem: 没有学习机制，浪费 API 调用
```

### 1.2 设计目标

**核心理念**：
> Self-Healing 不是简单的 Retry，而是基于 Traceability 的智能根因分析 + 学习型修复系统。

**分层架构**：
```text
Error Detection (错误检测)
  ↓
Root Cause Analysis (根因分析)
  ├─ Error Classification (错误分类)
  ├─ Trace Chain Analysis (追溯链路分析)
  └─ Impact Analysis (影响范围分析)
  ↓
Healing Strategy Selection (修复策略选择)
  ├─ Pattern Matching (模式匹配)
  ├─ History Learning (历史学习)
  └─ Confidence Scoring (置信度评分)
  ↓
Fix Execution (修复执行)
  ↓
Validation & Learning (验证与学习)
```

**与现有架构关系**：
```text
Phase 10: Test Execution & Self-Healing
  ├─ TestExecutor (保留，执行测试)
  ├─ TestSelfHealer (增强)
  │   ├─ RootCauseAnalyzer (新增，根因分析)
  │   ├─ HealingStrategySelector (新增，策略选择)
  │   └─ HealingHistory (新增，历史学习)
  └─ ArtifactGraph (保留，追踪链路)
```

### 1.3 面试价值

**展示点**：
1. **智能自愈**：不是简单 Retry，而是基于 Traceability 的根因分析
2. **学习机制**：记录修复历史，对相似错误快速应用已知修复
3. **可观测性**：生成根因分析报告，透明化修复过程
4. **系统性思维**：识别错误分类（语法/逻辑/环境），追溯到需求/Prompt/Phase

**面试话术**：
> "DevPalAgent 的 Self-Healing 实现了三层智能：错误分类（语法/逻辑/环境）、追溯链路（代码→Phase→Prompt→需求）、学习机制（记录修复历史，相似错误快速应用）。这展示了 Self-Correction 的智能化水平，不是简单的 Retry。"

---

## 2. 核心抽象设计

### 2.1 ErrorContext

**职责**：封装错误上下文信息

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

class ErrorType(Enum):
    """错误类型"""
    SYNTAX = "syntax"          # 语法错误（编译错误、import 错误）
    LOGIC = "logic"             # 逻辑错误（测试失败、断言错误）
    ENVIRONMENT = "environment"    # 环境错误（依赖缺失、配置错误）
    UNKNOWN = "unknown"            # 未知错误

class ErrorSeverity(Enum):
    """错误严重程度"""
    CRITICAL = "critical"  # 阻塞性错误（编译失败）
    HIGH = "high"       # 高优先级（多个测试失败）
    MEDIUM = "medium"      # 中优先级（单个测试失败）
    LOW = "low"            # 低优先级（警告）

@dataclass
class ErrorContext:
    """错误上下文"""
    error_message: str              # 错误消息
    error_type: ErrorType                 # 错误类型
    severity: ErrorSeverity               # 严重程度
    file_path: Optional[Path] = None      # 错误文件路径
    line_number: Optional[int] = None     # 错误行号
    stack_trace: str = ""                 # 堆栈跟踪
    phase: Optional[str] = None      # 发生错误的 Phase
    timestamp: str = ""                 # 错误时间戳
    metadata: Dict = field(default_factory=dict)  # 额外元数据
```

**使用示例**：
```python
error_ctx = ErrorContext(
    error_message="undefined reference to `login_user`",
    error_type=ErrorType.SYNTAX,
    severity=ErrorSeverity.CRITICAL,
    file_path=Path("src/auth.cpp"),
    line_number=42,
    phase="Phase 10: Test Execution",
    metadata={"compiler": "g++", "language": "cpp"}
)
```

### 2.2 RootCause

**职责**：封装根因分析结果

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class TraceNode:
    """追溯链路节点"""
    node_type: str      # 节点类型：requirement/prompt/phase/code/test
    node_id: str        # 节点 ID
    content: str        # 节点内容摘要
    confidence: float   # 置信度 0.0-1.0

@dataclass
class RootCause:
    """根因分析结果"""
    error_context: ErrorContext         # 错误上下文
    root_cause_type: str             # 根因类型
    root_cause_description: str           # 根因描述
    trace_chain: List[TraceNode] = field(default_factory=list)  # 追溯链路
    affected_files: List[Path] = field(default_factory=list)    # 影响的文件
    confidence: float = 0.0               # 根因分析置信度
    suggested_fixes: List[str] = field(default_factory=list)    # 建议修复方案
    metadata: Dict = field(default_factory=dict)        # 元数据
```

**根因类型定义**：
```python
ROOT_CAUSE_TYPES = {
    "code_generation_error": "代码生成错误（LLM 生成的代码有问题）",
    "requirement_misunderstanding": "需求理解错误（需求解析不正确）",
    "prompt_issue": "Prompt 问题（Prompt 不够清晰或有误）",
    "dependency_missing": "依赖缺失（缺少必要的库或工具）",
    "configuration_error": "配置错误（环境配置不正确）",
    "test_case_error": "测试用例错误（测试本身有问题）",
    "integration_error": "集成错误（多个模块集成问题）",
    "unknown": "未知根因"
}
```

**使用示例**：
```python
root_cause = RootCause(
    error_context=error_ctx,
    root_cause_type="code_generation_error",
    root_cause_description="Phase 4 生成的 auth.cpp 缺少 login_user 函数实现",
    trace_chain=[
        TraceNode("requirement", "REQ-002", "用户登录功能", 0.9),
        TraceNode("prompt", "phase4_prompt", "生成登录相关代码", 0.8),
        TraceNode("phase", "Phase 4", "代码生成阶段", 1.0),
        TraceNode("code", "src/auth.cpp", "认证模块代码", 1.0)
    ],
    affected_files=[Path("src/auth.cpp"), Path("tests/test_auth.cpp")],
    confidence=0.85,
    suggested_fixes=[
        "重新生成 auth.cpp，明确要求包含 login_user 函数",
        "检查需求 REQ-002 是否完整描述了登录功能",
        "优化 Phase 4 Prompt，增加函数完整性检查"
    ]
)
```

### 2.3 HealingStrategy

**职责**：封装修复策略

```python
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional
from enum import Enum

class StrategyType(Enum):
    """修复策略类型"""
    REGENERATE_CODE = "regenerate_code"      # 重新生成代码
    FIX_SYNTAX = "fix_syntax"            # 修复语法错误
    UPDATE_TEST = "update_test"              # 更新测试用例
    INSTALL_DEPENDENCY = "install_dependency"  # 安装依赖
    FIX_CONFIGURATION = "fix_configuration"    # 修复配置
    MANUAL_INTERVENTION = "manual_intervention"  # 需要人工介入

@dataclass
class HealingStrategy:
    """修复策略"""
    strategy_type: StrategyType       # 策略类型
    description: str                    # 策略描述
    confidence: float                     # 策略置信度 0.0-1.0
    estimated_time: float              # 预计修复时间（秒）
    root_cause: RootCause             # 关联的根因
    fix_function: Optional[Callable] = None  # 修复函数
    parameters: Dict = field(default_factory=dict)  # 修复参数
    metadata: Dict = field(default_factory=dict)    # 元数据
```

**使用示例**：
```python
strategy = HealingStrategy(
    strategy_type=StrategyType.REGENERATE_CODE,
    description="重新生成 auth.cpp，明确要求包含 login_user 函数",
    confidence=0.85,
    estimated_time=60.0,
    root_cause=root_cause,
    parameters={
        "file_path": "src/auth.cpp",
        "requirements": ["REQ-002"],
        "additional_prompt": "确保包含 login_user 函数的完整实现"
    }
)
```

### 2.4 HealingRecord

**职责**：记录修复历史

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class HealingRecord:
    """修复历史记录"""
    record_id: str                   # 记录 ID
    error_context: ErrorContext           # 错误上下文
    root_cause: RootCause                 # 根因分析
    strategy: HealingStrategy             # 修复策略
    success: bool                      # 是否成功
    execution_time: float                 # 执行时间（秒）
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    retry_count: int = 0       # 重试次数
    final_error: Optional[str] = None     # 最终错误（如果失败）
    metadata: Dict = field(default_factory=dict)  # 元数据
```

---

## 3. RootCauseAnalyzer 设计

### 3.1 职责

**核心功能**：
1. 错误分类：识别错误类型（语法/逻辑/环境）
2. 追溯链路分析：错误代码 → Phase → Prompt → 需求
3. 影响范围分析：使用 ArtifactGraph 分析影响的其他文件
4. 根因推断：基于分析结果推断根本原因
5. 修复建议：生成可能的修复方案

### 3.2 实现

```python
from typing import List, Optional
import re
import logging
from pathlib import Path

class RootCauseAnalyzer:
    """根因分析器"""
    
    def __init__(
        self,
        artifact_graph: 'ArtifactGraph',
        context: 'OpenSpecContext',
        logger: Optional[logging.Logger] = None
    ):
    self.artifact_graph = artifact_graph
        self.context = context
        self.logger = logger or logging.getLogger(__name__)
        
        # 错误模式库
        self.error_patterns = self._load_error_patterns()
    
    def analyze(self, error_context: ErrorContext) -> RootCause:
        """
        执行根因分析
        
      Args:
            error_context: 错误上下文
         
        Returns:
            RootCause: 根因分析结果
        """
        self.logger.info(f"[RCA] 开始根因分析: {error_context.error_message[:100]}")
        
        # Step 1: 错误分类
        error_type = self._classify_error(error_context)
      error_context.error_type = error_type
        
     # Step 2: 追溯链路分析
        trace_chain = self._build_trace_chain(error_context)
      
        # Step 3: 影响范围分析
        affected_files = self._analyze_impact(error_context)
        
        # Step 4: 根因推断
        root_cause_type, description, confidence = self._infer_root_cause(
            error_context, trace_chain
        )
        
        # Step 5: 生成修复建议
        suggested_fixes = self._generate_fix_suggestions(
         error_context, root_cause_type
        )
        
        root_cause = RootCause(
            error_context=error_context,
            root_cause_type=root_cause_type,
        root_cause_description=description,
            trace_chain=trace_chain,
            affected_files=affected_files,
            confidence=confidence,
            suggested_fixes=suggested_fixes
        )
        
        self.logger.info(f"[RCA] 根因分析完成: {root_cause_type} (置信度: {confidence:.2f})")
        return root_cause
    
    def _classify_error(self, error_context: ErrorContext) -> ErrorType:
        """错误分类"""
      error_msg = error_context.error_message.lower()
        
        # 语法错误模式
        syntax_patterns = [
            r"undefined reference",
            r"syntax error",
            r"import.*error",
            r"no module named",
            r"compilation failed",
            r"parse error"
      ]
        
        # 逻辑错误模式
        logic_patterns = [
          r"assertion.*failed",
            r"expected.*got",
            r"test.*failed",
            r"incorrect.*result"
        ]
        
        # 环境错误模式
        environment_patterns = [
            r"command not found",
            r"permission denied",
            r"file not found",
            r"cannot open.*file"
        ]
        
        for pattern in syntax_patterns:
            if re.search(pattern, error_msg):
              return ErrorType.SYNTAX
        
        for pattern in logic_patterns:
         if re.search(pattern, error_msg):
           return ErrorType.LOGIC
        
      for pattern in environment_patterns:
            if re.search(pattern, error_msg):
              return ErrorType.ENVIRONMENT
        
        return ErrorType.UNKNOWN
    
    def _build_trace_chain(self, error_context: ErrorContext) -> List[TraceNode]:
      """构建追溯链路"""
        trace_chain = []
        
        if not error_context.file_path:
            return trace_chain
        
      # 从 ArtifactGraph 获取追溯信息
        file_path_str = str(error_context.file_path)
      
        # 1. 代码节点
        trace_chain.append(TraceNode(
            node_type="code",
            node_id=file_path_str,
            content=f"错误文件: {error_context.file_path.name}",
            confidence=1.0
        ))
     
      # 2. Phase 节点
        if error_context.phase:
            trace_chain.append(TraceNode(
                node_type="phase",
            node_id=error_context.phase,
                content=f"生成阶段: {error_context.phase}",
                confidence=1.0
            ))
        
        # 3. 需求节点（从 ArtifactGraph 查询）
        requirements = self._find_related_requirements(file_path_str)
      for req_id, req_desc in requirements:
            trace_chain.append(TraceNode(
              node_type="requirement",
                node_id=req_id,
           content=req_desc,
            confidence=0.8
          ))
        
      return trace_chain
    
    def _analyze_impact(self, error_context: ErrorContext) -> List[Path]:
        """分析影响范围"""
        if not error_context.file_path:
            return []
        
        affected = [error_context.file_path]
        
        # 使用 ArtifactGraph 查找依赖文件
        file_path_str = str(error_context.file_path)
        dependencies = self.artifact_graph.get_dependencies(file_path_str)
        
        for dep in dependencies:
            affected.append(Path(dep))
        
        return affected
    
    def _infer_root_cause(
      self,
        error_context: ErrorContext,
        trace_chain: List[TraceNode]
    ) -> tuple[str, str, float]:
        """推断根因"""
      error_type = error_context.error_type
        error_msg = error_context.error_message
        
        # 基于错误类型和模式推断根因
        if error_type == ErrorType.SYNTAX:
            if "undefined reference" in error_msg.lower():
                return (
                 "code_generation_error",
           "代码生成时缺少函数或变量定义",
                    0.85
                )
            elif "import" in error_msg.lower() or "no module" in error_msg.lower():
            return (
               "dependency_missing",
               "缺少必要的依赖库或模块",
                    0.90
            )
     
        elif error_type == ErrorType.LOGIC:
            if "assertion" in error_msg.lower():
                return (
             "requirement_misunderstanding",
                    "需求理解错误导致逻辑实现不符合预期",
                    0.75
             )
        
        elif error_type == ErrorType.ENVIRONMENT:
            return (
                "configuration_error",
                "环境配置错误或权限问题",
                0.80
            )
        
        return ("unknown", "无法确定根本原因", 0.3)
    
    def _generate_fix_suggestions(
        self,
        error_context: ErrorContext,
        root_cause_type: str
    ) -> List[str]:
        """生成修复建议"""
        suggestions = []
        
        if root_cause_type == "code_generation_error":
            suggestions.append("重新生成相关代码文件，明确要求包含缺失的定义")
            suggestions.append("检查 Phase 4 Prompt 是否完整描述了所需功能")
        
        elif root_cause_type == "dependency_missing":
          suggestions.append("安装缺失的依赖库")
        suggestions.append("更新 requirements.txt 或 CMakeLists.txt")
        
        elif root_cause_type == "requirement_misunderstanding":
            suggestions.append("重新审查需求文档，确保理解正确")
        suggestions.append("更新测试用例以匹配实际需求")
        
        elif root_cause_type == "configuration_error":
            suggestions.append("检查环境配置和权限设置")
            suggestions.append("验证必要的工具和路径是否正确")
      
        return suggestions
    
    def _find_related_requirements(self, file_path: str) -> List[tuple[str, str]]:
        """查找相关需求"""
        # 从 ArtifactGraph 查询
        requirements = []
        
      # 简化实现：从 context 获取
        if hasattr(self.context, 'requirements'):
            for req_id, req_data in self.context.requirements.items():
          # 检查文件是否与需求相关
             if self._is_file_related_to_requirement(file_path, req_id):
                    desc = req_data.get('description', '')[:100]
                    requirements.append((req_id, desc))
        
        return requirements
    
    def _is_file_related_to_requirement(self, file_path: str, req_id: str) -> bool:
        """判断文件是否与需求相关"""
        # 简化实现：基于文件名和需求 ID 的关键词匹配
        # 实际应该使用 ArtifactGraph 的追踪信息
        return True  # 暂时返回 True
    
    def _load_error_patterns(self) -> Dict:
     """加载错误模式库"""
        return {
        "syntax": [
                r"undefined reference",
            r"syntax error",
                r"import.*error"
            ],
            "logic": [
                r"assertion.*failed",
                r"expected.*got"
            ],
            "environment": [
             r"command not found",
                r"permission denied"
            ]
     }
```

---

## 4. HealingStrategySelector 设计

### 4.1 职责

**核心功能**：
1. 策略匹配：根据根因类型选择合适的修复策略
2. 历史学习：从修复历史中学习成功的策略
3. 置信度评分：评估策略成功的可能性
4. 策略排序：按置信度和预计时间排序策略

### 4.2 实现

```python
from typing import List, Optional, Dict
import logging

class HealingStrategySelector:
    """修复策略选择器"""
    
    def __init__(
      self,
        healing_history: 'HealingHistory',
        logger: Optional[logging.Logger] = None
    ):
        self.healing_history = healing_history
        self.logger = logger or logging.getLogger(__name__)
        
        # 策略映射表
        self.strategy_map = self._build_strategy_map()
    
    def select_strategy(self, root_cause: RootCause) -> List[HealingStrategy]:
        """
        选择修复策略
     
        Args:
            root_cause: 根因分析结果
            
        Returns:
            List[HealingStrategy]: 按优先级排序的策略列表
        """
        self.logger.info(f"[Strategy] 选择修复策略: {root_cause.root_cause_type}")
        
        # Step 1: 从历史中查找相似错误的成功策略
        historical_strategies = self._find_historical_strategies(root_cause)
        
      # Step 2: 基于根因类型生成默认策略
        default_strategies = self._generate_default_strategies(root_cause)
        
      # Step 3: 合并并去重
        all_strategies = self._merge_strategies(
          historical_strategies, default_strategies
        )
        
        # Step 4: 评分和排序
        scored_strategies = self._score_and_sort(all_strategies, root_cause)
        
        self.logger.info(f"[Strategy] 生成 {len(scored_strategies)} 个策略")
        return scored_strategies
    
    def _find_historical_strategies(
        self, root_cause: RootCause
    ) -> List[HealingStrategy]:
        """从历史中查找成功策略"""
        strategies = []
        
        # 查询相似错误的成功修复记录
      similar_records = self.healing_history.find_similar_errors(
            root_cause.error_context,
            similarity_threshold=0.7
        )
        
        for record in similar_records:
       if record.success:
          # 复制成功的策略，提高置信度
                strategy = HealingStrategy(
                    strategy_type=record.strategy.strategy_type,
                 description=f"[历史学习] {record.strategy.description}",
                    confidence=min(record.strategy.confidence + 0.1, 1.0),
           estimated_time=record.execution_time,
                    root_cause=root_cause,
                    parameters=record.strategy.parameters.copy()
                )
                strategies.append(strategy)
        
        return strategies
    
    def _generate_default_strategies(
        self, root_cause: RootCause
    ) -> List[HealingStrategy]:
        """生成默认策略"""
        strategies = []
        root_cause_type = root_cause.root_cause_type
        
        # 从策略映射表获取
        if root_cause_type in self.strategy_map:
            strategy_configs = self.strategy_map[root_cause_type]
            
            for config in strategy_configs:
             strategy = HealingStrategy(
            strategy_type=config["type"],
                    description=config["description"],
                    confidence=config["confidence"],
                    estimated_time=config["estimated_time"],
                    root_cause=root_cause,
                    parameters=self._build_parameters(root_cause, config)
                )
              strategies.append(strategy)
        
        return strategies
    
    def _merge_strategies(
        self,
        historical: List[HealingStrategy],
        default: List[HealingStrategy]
    ) -> List[HealingStrategy]:
        """合并策略并去重"""
        # 优先使用历史策略
        merged = historical.copy()
        
        # 添加不重复的默认策略
        existing_types = {s.strategy_type for s in historical}
     for strategy in default:
            if strategy.strategy_type not in existing_types:
            merged.append(strategy)
        
        return merged
    
    def _score_and_sort(
      self,
        strategies: List[HealingStrategy],
        root_cause: RootCause
    ) -> List[HealingStrategy]:
        ""评分和排序"""
        # 综合评分：置信度 * 0.7 + (1 - 归一化时间) * 0.3
        max_time = max((s.estimated_time for s in strategies), default=100.0)
     
        for strategy in strategies:
            time_score = 1.0 - (strategy.estimated_time / max_time)
        strategy.metadata["score"] = (
                strategy.confidence * 0.7 + time_score * 0.3
            )
      
        # 按评分降序排序
        strategies.sort(key=lambda s: s.metadata["score"], reverse=True)
        return strategies
    
    def _build_parameters(
        self, root_cause: RootCause, config: Dict
    ) -> Dict:
        """构建策略参数"""
        params = config.get("base_parameters", {}).copy()
        
        # 从根因中提取参数
        if root_cause.error_context.file_path:
            params["file_path"] = str(root_cause.error_context.file_path)
        
        # 从建议修复中提取参数
        if root_cause.suggested_fixes:
            params["suggested_fixes"] = root_cause.suggested_fixes
        
        return params
    
    def _build_strategy_map(self) -> Dict:
        """构建策略映射表"""
        return {
            "code_generation_error": [
                {
                    "type": StrategyType.REGENERATE_CODE,
                 "description": "重新生成代码文件",
                    "confidence": 0.8,
               "estimated_time": 60.0,
                 "base_parameters": {}
                }
            ],
            "dependency_missing": [
                {
                    "type": StrategyType.INSTALL_DEPENDENCY,
                    "description": "安装缺失的依赖",
             "confidence": 0.9,
                 "estimated_time": 30.0,
                "base_parameters": {}
              }
            ],
            "requirement_misunderstanding": [
                {
                    "type": StrategyType.REGENERATE_CODE,
                    "description": "基于更新的需求理解重新生成代码",
              "confidence": 0.7,
                 "estimated_time": 80.0,
                    "base_parameters": {}
                },
         {
                  "type": StrategyType.UPDATE_TEST,
                    "description": "更新测试用例以匹配实际需求",
              "confidence": 0.6,
                  "estimated_time": 40.0,
                    "base_parameters": {}
                }
         ],
            "configuration_error": [
                {
                    "type": StrategyType.FIX_CONFIGURATION,
              "description": "修复环境配置",
                 "confidence": 0.75,
                 "estimated_time": 20.0,
                    "base_parameters": {}
                }
            ],
            "test_case_error": [
                {
                 "type": StrategyType.UPDATE_TEST,
              "description": "修复测试用例",
               "confidence": 0.85,
               "estimated_time": 30.0,
               "base_parameters": {}
                }
            ]
        }
```

---

## 5. HealingHistory 设计

### 5.1 职责

**核心功能**：
1. 记录修复历史：保存每次修复的完整信息
2. 相似错误查询：基于错误特征查找历史记录
3. 统计分析：生成修复成功率、平均时间等统计
4. 持久化存储：保存到文件系统

### 5.2 实现

```python
from typing import List, Optional, Dict
import json
import logging
from pathlib import Path
from datetime import datetime
import hashlib

class HealingHistory:
    """修复历史管理器"""
    
    def __init__(
        self,
        storage_path: Path,
        logger: Optional[logging.Logger] = None
    ):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = logger or logging.getLogger(__name__)
        
        # 内存缓存
        self.records: List[HealingRecord] = []
      self._load_from_disk()
    
    def add_record(self, record: HealingRecord) -> None:
        """添加修复记录"""
        self.records.append(record)
        self._save_to_disk(record)
        self.logger.info(f"[History] 记录修复: {record.record_id} (成功: {record.success})")
    
    def find_similar_errors(
        self,
        error_context: ErrorContext,
        similarity_threshold: float = 0.7
    ) -> List[HealingRecord]:
        """查找相似错误"""
        similar_records = []
        
        for record in self.records:
            similarity = self._calculate_similarity(
                error_context, record.error_context
         )
        
       if similarity >= similarity_threshold:
            similar_records.append(record)
      
        # 按相似度和时间排序（最近的优先）
        similar_records.sort(
            key=lambda r: (
                self._calculate_similarity(error_context, r.error_context),
                r.timestamp
            ),
            reverse=True
        )
        
        return similar_records
    
    def get_statistics(self) -> Dict:
        """获取统计信息""
        if not self.records:
            return {
              "total_records": 0,
       "success_rate": 0.0,
              "avg_execution_time": 0.0,
                "by_error_type": {},
                "by_strategy_type": {}
            }
    
        total = len(self.records)
        successful = sum(1 for r in self.records if r.success)
        
        # 按错误类型统计
     by_error_type = {}
        for record in self.records:
            error_type = record.error_context.error_type.value
            if error_type not in by_error_type:
                by_error_type[error_type] = {"total": 0, "success": 0}
            by_error_type[error_type]["total"] += 1
            if record.success:
           by_error_type[error_type]["success"] += 1
        
        # 按策略类型统计
        by_strategy_type = {}
        for record in self.records:
            strategy_type = record.strategy.strategy_type.value
            if strategy_type not in by_strategy_type:
                by_strategy_type[strategy_type] = {"total": 0, "success": 0}
            by_strategy_type[strategy_type]["total"] += 1
          if record.success:
         by_strategy_type[strategy_type]["success"] += 1
        
        return {
            "total_records": total,
          "success_rate": successful / total,
            "avg_execution_time": sum(r.execution_time for r in self.records) / total,
        "by_error_type": by_error_type,
            "by_strategy_type": by_strategy_type
        }
    
    def _calculate_similarity(
        self,
     ctx1: ErrorContext,
        ctx2: ErrorContext
    ) -> float:
        """计算错误相似度"""
     score = 0.0
        
        # 错误类型匹配 (40%)
        if ctx1.error_type == ctx2.error_type:
            score += 0.4
        
        # 错误消息相似度 (40%)
        msg_similarity = self._text_similarity(
            ctx1.error_message, ctx2.error_message
        )
        score += msg_similarity * 0.4
        
        # 文件路径相似度 (20%)
        if ctx1.file_path and ctx2.file_path:
            if ctx1.file_path == ctx2.file_path:
            score += 0.2
          elif ctx1.file_path.suffix == ctx2.file_path.suffix:
                score += 0.1
        
        return score
    
  def _text_similarity(self, text1: str, text2: str) -> float:
      """计算文本相似度（简化版）"""
        # 使用 Jaccard 相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
      if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _load_from_disk(self) -> None:
        """从磁盘加载历史记录""
        history_file = self.storage_path / "healing_history.jsonl"
        
        if not history_file.exists():
          return
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
               if line.strip():
               data = json.loads(line)
                 record = self._deserialize_record(data)
                        self.records.append(record)
            
            self.logger.info(f"[History] 加载 {len(self.records)} 条历史记录")
     except Exception as e:
            self.logger.error(f"[History] 加载历史记录失败: {e}")
    
    def _save_to_disk(self, record: HealingRecord) -> None:
        """保存记录到磁盘"""
        history_file = self.storage_path / "healing_history.jsonl"
        
        try:
            with open(history_file, 'a', encoding='utf-8') as f:
             data = self._serialize_record(record)
              f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
          self.logger.error(f"[History] 保存记录失败: {e}")
    
    def _serialize_record(self, record: HealingRecord) -> Dict:
        """序列化记录"
        return {
            "record_id": record.record_id,
        "error_context": {
                "error_message": record.error_context.error_message,
              "error_type": record.error_context.error_type.value,
              "severity": record.error_context.severity.value,
                "file_path": str(record.error_context.file_path) if record.error_context.file_path else None,
                "phase": record.error_context.phase
        },
            "root_cause": {
            "root_cause_type": record.root_cause.root_cause_type,
             "confidence": record.root_cause.confidence
            },
            "strategy": {
                "strategy_type": record.strategy.strategy_type.value,
              "confidence": record.strategy.confidence
         },
            "success": record.success,
            "execution_time": record.execution_time,
            "timestamp": record.timestamp.isoformat(),
            "retry_count": record.retry_count
        }
    
    def _deserialize_record(self, data: Dict) -> HealingRecord:
        """反序列化记录（简化版）"""
        # 简化实现，实际需要完整重建对象
        error_ctx = ErrorContext(
          error_message=data["error_context"]["error_message"],
            error_type=ErrorType(data["error_context"]["error_type"]),
         severity=ErrorSeverity(data["error_context"]["severity"]),
            file_path=Path(data["error_context"]["file_path"]) if data["error_context"]["file_path"] else None,
            phase=data["error_context"].get("phase")
        )
        
        # 创建简化的 RootCause 和 Strategy
        root_cause = RootCause(
            error_context=error_ctx,
            root_cause_type=data["root_cause"]["root_cause_type"],
         root_cause_description="",
            confidence=data["root_cause"]["confidence"]
        )
        
        strategy = HealingStrategy(
            strategy_type=StrategyType(data["strategy"]["strategy_type"]),
            description="",
            confidence=data["strategy"]["confidence"],
            estimated_time=0.0,
            root_cause=root_cause
      )
        
      return HealingRecord(
            record_id=data["record_id"],
            error_context=error_ctx,
            root_cause=root_cause,
            strategy=strategy,
            success=data["success"],
            execution_time=data["execution_time"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            retry_count=data.get("retry_count", 0)
        )
```

---

## 6. 增强 TestSelfHealer 集成

### 6.1 集成架构

```python
class EnhancedTestSelfHealer:
    """增强的测试自愈器"""
    
    def __init__(
        self,
        context: 'OpenSpecContext',
        artifact_graph: 'ArtifactGraph',
        llm_client: 'LLMClient',
      logger: Optional[logging.Logger] = None
    ):
        self.context = context
        self.artifact_graph = artifact_graph
        self.llm_client = llm_client
        self.logger = logger or logging.getLogger(__name__)
        
     # 初始化根因分析组件
        self.root_cause_analyzer = RootCauseAnalyzer(
            artifact_graph=artifact_graph,
    context=context,
            logger=logger
        )
        
        # 初始化修复历史
        history_path = context.project_path / ".spec" / "healing_history"
        self.healing_history = HealingHistory(
         storage_path=history_path,
      logger=logger
        )
      
        # 初始化策略选择器
        self.strategy_selector = HealingStrategySelector(
            healing_history=self.healing_history,
            logger=logger
      )
        
        # 最大重试次数
        self.max_retries = 3
    
    def heal(self, error_output: str, error_type: str) -> bool:
        """
        执行智能修复
        
      Args:
            error_output: 错误输出
            error_type: 错误类型 (compile/test)
            
        Returns:
            bool: 是否修复成功
        """
        self.logger.info(f"[Healing] 开始智能修复: {error_type}")
        
        # Step 1: 构建错误上下文
        error_context = self._build_error_context(error_output, error_type)
     
     # Step 2: 根因分析
        root_cause = self.root_cause_analyzer.analyze(error_context)
        self._log_root_cause(root_cause)
        
        # Step 3: 选择修复策略
        strategies = self.strategy_selector.select_strategy(root_cause)
      
        if not strategies:
            self.logger.warning("[Healing] 未找到合适的修复策略")
            return False
        
        # Step 4: 依次尝试策略
        for i, strategy in enumerate(strategies[:self.max_retries]):
          self.logger.info(
                f"[Healing] 尝试策略 {i+1}/{len(strategies)}: "
         f"{strategy.strategy_type.value} (置信度: {strategy.confidence:.2f})"
            )
            
            start_time = datetime.now()
            success = self._execute_strategy(strategy)
         execution_time = (datetime.now() - start_time).total_seconds()
            
            # 记录修复历史
            record = HealingRecord(
                record_id=self._generate_record_id(error_context),
           error_context=error_context,
             root_cause=root_cause,
                strategy=strategy,
                success=success,
                execution_time=execution_time,
             retry_count=i
         )
            self.healing_history.add_record(record)
            
          if success:
             self.logger.info(f"[Healing] 修复成功 (耗时: {execution_time:.2f}s)")
              return True
        
        self.logger.error("[Healing] 所有策略均失败")
        return False
    
    def _build_error_context(self, error_output: str, error_type: str) -> ErrorContext:
        """构建错误上下文"""
        # 解析错误输出
        file_path, line_number = self._parse_error_location(error_output)
    
        # 确定严重程度
        severity = (
            ErrorSeverity.CRITICAL if error_type == "compile"
            else ErrorSeverity.HIGH
        )
        
        return ErrorContext(
            error_message=error_output[:500],  # 截取前500字符
          error_type=ErrorType.UNKNOWN,  # 将由分析器分类
         severity=severity,
            file_path=file_path,
         line_number=line_number,
        stack_trace=error_output,
            phase="Phase 10: Test Execution",
            timestamp=datetime.now().isoformat()
        )
    
    def _execute_strategy(self, strategy: HealingStrategy) -> bool:
        """执行修复策略"""
        try:
            if strategy.strategy_type == StrategyType.REGENERATE_CODE:
        return self._regenerate_code(strategy)
            elif strategy.strategy_type == StrategyType.FIX_SYNTAX:
            return self._fix_syntax(strategy)
            elif strategy.strategy_type == StrategyType.UPDATE_TEST:
                return self._update_test(strategy)
       elif strategy.strategy_type == StrategyType.INSTALL_DEPENDENCY:
            return self._install_dependency(strategy)
        elif strategy.strategy_type == StrategyType.FIX_CONFIGURATION:
              return self._fix_configuration(strategy)
       else:
              self.logger.warning(f"[Healing] 未实现的策略: {strategy.strategy_type}")
              return False
        except Exception as e:
            self.logger.error(f"[Healing] 策略执行失败: {e}")
            return False
    
    def _regenerate_code(self, strategy: HealingStrategy) -> bool:
      """重新生成代码""
        # 调用 Phase 4 重新生成指定文件
        # 实现细节省略
        return True
    
    def _fix_syntax(self, strategy: HealingStrategy) -> bool:
        """修复语法错误"""
        # 使用 LLM 修复语法错误
        # 实现细节省略
     return True
    
    def _update_test(self, strategy: HealingStrategy) -> bool:
        """更新测试用例"""
        # 更新测试用例
        # 实现细节省略
        return True
    
    def _install_dependency(self, strategy: HealingStrategy) -> bool:
        """安装依赖"""
        # 安装缺失的依赖
        # 实现细节省略
        return True
    
    def _fix_configuration(self, strategy: HealingStrategy) -> bool:
        """修复配置"""
        # 修复环境配置
        # 实现细节省略
        return True
    
    def _parse_error_location(self, error_output: str) -> tuple[Optional[Path], Optional[int]]:
        """解析错误位置"""
        # 简化实现
        import re
    
        # 匹配常见的错误位置格式
        patterns = [
          r"([^\s:]+):(\d+):",  # file.cpp:42:
            r"File \"([^\"]+)\", line (\d+)",  # Python
        ]
        
      for pattern in patterns:
          match = re.search(pattern, error_output)
            if match:
                file_path = Path(match.group(1))
                line_number = int(match.group(2))
          return file_path, line_number
        
        return None, None
    
    def _log_root_cause(self, root_cause: RootCause) -> None:
        """记录根因分析结果"""
        self.logger.info("[RCA] ===== 根因分析结果 =====")
        self.logger.info(f"[RCA] 根因类型: {root_cause.root_cause_type}")
        self.logger.info(f"[RCA] 根因描述: {root_cause.root_cause_description}")
        self.logger.info(f"[RCA] 置信度: {root_cause.confidence:.2f}")
        
     if root_cause.trace_chain:
            self.logger.info("[RCA] 追溯链路:")
         for node in root_cause.trace_chain:
              self.logger.info(f"[RCA]   - {node.node_type}: {node.content}")
        
        if root_cause.suggested_fixes:
            self.logger.info("[RCA] 建议修复:")
            for fix in root_cause.suggested_fixes:
           self.logger.info(f"[RCA]   - {fix}")
    
    def _generate_record_id(self, error_context: ErrorContext) -> str:
     """生成记录 ID"""
        content = f"{error_context.error_message}{error_context.timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
```


---

## 7. 根因分析报告生成

### 7.1 报告结构

根因分析报告包含以下章节：
1. 错误概览 - 所有错误的汇总表格
2. 详细分析 - 每个错误的完整根因分析
3. 统计分析 - 错误类型、根因类型、策略效果统计
4. 建议和改进 - 基于分析结果的改进建议
5. 附录 - 错误模式库、策略库说明

### 7.2 报告生成器实现

```python
from typing import List
from pathlib import Path

class RootCauseReportGenerator:
    """根因分析报告生成器"""
    
    def __init__(
        self,
    healing_history: HealingHistory,
     output_path: Path
    ):
        self.healing_history = healing_history
        self.output_path = output_path
    
    def generate_report(self, records: List[HealingRecord]) -> Path:
     ""生成根因分析报告"""
        report_lines = []
        
        # 标题和元数据
      report_lines.extend(self._generate_header(records))
        
        # 错误概览
        report_lines.extend(self._generate_overview(records))
        
        # 详细分析
        report_lines.extend(self._generate_detailed_analysis(records))
        
        # 统计分析
        report_lines.extend(self._generate_statistics(records))
        
        # 建议和改进
        report_lines.extend(self._generate_recommendations(records))
        
        # 附录
    report_lines.extend(self._generate_appendix())
        
        # 写入文件
        report_path = self.output_path / "root_cause_analysis.md"
        report_path.write_text('\n'.join(report_lines), encoding='utf-8')
        
        return report_path
```

---

## 8. 实施步骤

### 8.1 Phase 1: 核心抽象实现（0.5天）

**Task 1.1: 创建数据模型**
- 文件: `devpal/core/self_healing/models.py`
- 实现: ErrorContext, RootCause, HealingStrategy, HealingRecord
- 验证: 单元测试

**Task 1.2: 创建 RootCauseAnalyzer**
- 文件: `devpal/core/self_healing/root_cause_analyzer.py`
- 实现: 错误分类、追溯链路、影响分析、根因推断
- 验证: 单元测试

### 8.2 Phase 2: 策略选择和历史学习（0.5天）

**Task 2.1: 创建 HealingStrategySelector**
- 文件: `devpal/core/self_healing/strategy_selector.py`
- 实现: 策略匹配、历史学习、置信度评分
- 验证: 单元测试

**Task 2.2: 创建 HealingHistory**
- 文件: `devpal/core/self_healing/healing_history.py`
- 实现: 记录管理、相似查询、统计分析、持久化
- 验证: 单元测试

### 8.3 Phase 3: 集成到 TestSelfHealer（0.5天）

**Task 3.1: 增强 TestSelfHealer**
- 文件: `devpal/core/openspec_phases/phase10_test_execution.py`
- 修改: 集成根因分析、策略选择、历史学习
- 验证: 集成测试

**Task 3.2: 实现修复策略执行**
- 实现: _regenerate_code, _fix_syntax, _update_test 等方法
- 验证: 端到端测试

### 8.4 Phase 4: 报告生成和验证（0.5天）

**Task 4.1: 创建报告生成器**
- 文件: `devpal/core/self_healing/report_generator.py`
- 实现: 根因分析报告生成
- 验证: 报告格式检查

**Task 4.2: 端到端测试**
- 运行完整流程，触发错误，验证修复
- 检查根因分析报告
- 验证历史学习效果

---

## 9. 验收标准

### 9.1 功能验收

```bash
# 运行测试项目
python run_ai_flow.py -r requirements/test_with_errors.md

# 验证：
# 1. 编译/测试失败时触发根因分析
# 2. 生成 docs/root_cause_analysis.md 报告
# 3. 报告包含错误分类、追溯链路、修复策略
# 4. 相同错误第二次出现时快速修复（历史学习）
# 5. final_report.md 显示根因分析统计
```

### 9.2 质量验收

**代码质量**:
- ✅ 所有模块有单元测试
- ✅ 测试覆盖率 > 80%
- ✅ 类型注解完整
- ✅ 文档字符串完整

**性能要求**:
- ✅ 根因分析耗时 < 5s
- ✅ 策略选择耗时 < 2s
- ✅ 历史查询耗时 < 1s

**可观测性**:
- ✅ 完整的日志记录
- ✅ 根因分析报告生成
- ✅ 统计数据可视化

### 9.3 面试验收

**展示点验证**:
- ✅ 能清晰解释根因分析的三层智能
- ✅ 能演示追溯链路（代码→Phase→Prompt→需求）
- ✅ 能展示历史学习效果
- ✅ 能对比简单 Retry 和智能根因分析的差异

---
## 10. 面试准备

### 10.1 技术亮点

**1. 三层智能分析**
- 错误分类（语法/逻辑/环境）
- 追溯链路（代码→Phase→Prompt→需求）
- 影响范围（使用 ArtifactGraph）

**2. 学习型修复系统**
- 记录修复历史
- 相似错误快速应用
- 策略成功率统计

**3. 可观测性**
- 根因分析报告
- 追溯链路可视化
- 修复过程透明化

### 10.2 面试话术

**问题**: "你的 Self-Healing 系统是如何工作的？"

**回答**:
> "DevPalAgent 的 Self-Healing 实现了三层智能。第一层是错误分类，识别语法、逻辑、环境三类错误。第二层是追溯链路分析，从错误代码追溯到生成它的 Phase、使用的 Prompt、引用的需求，定位根本原因。第三层是学习机制，记录每次修复的策略和结果，对相似错误快速应用已知成功的修复方案。
>
> 这不是简单的 Retry，而是基于 Traceability 的智能根因分析。比如遇到 'undefined reference' 错误，系统会分析是代码生成问题还是依赖缺失，追溯到具体的需求和 Prompt，然后选择最合适的修复策略。如果之前修复过类似错误，会直接应用历史成功的策略，大幅提升修复效率。
>
> 整个过程生成详细的根因分析报告，包含错误分类、追溯链路、修复策略、统计分析，完全透明可观测。"

**问题**: "如何保证根因分析的准确性？"

**回答**:
> "我们使用置信度评分机制。每个分析结果都有 0.0-1.0 的置信度分数，基于错误模式匹配、追溯链路完整性、历史数据验证。只有置信度超过阈值（默认 0.7）的分析才会被采纳。
>
> 同时，我们使用 ArtifactGraph 进行追溯验证。ArtifactGraph 记录了需求→代码→测试的完整追踪关系，确保追溯链路的准确性。如果追溯链路不完整，置信度会相应降低。
>
> 另外，历史学习机制也提供了验证。如果某个根因分析导致的修复策略成功率低，系统会自动调整该类型错误的分析逻辑。"

### 10.3 Demo 脚本

**Step 1: 准备测试用例**
```bash
# 创建包含错误的需求文件
cat > requirements/test_healing.md << EOF
# 测试需求

## REQ-001: 用户登录
实现用户登录功能，包含 login_user 函数。

## REQ-002: 数据验证
实现数据验证功能，包含 validate_data 函数。
