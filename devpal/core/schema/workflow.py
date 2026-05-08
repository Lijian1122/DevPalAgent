from typing import Any, Dict, List, Optional, Callable, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
import yaml
import json
from pydantic import BaseModel, Field

from devpal.tools.registry import ToolRegistry, registry as default_registry


class ExecutionMode(Enum):
    CORE = "core"          # 快速路径: 3步
    EXTENDED = "extended"  # 细粒度: 7步


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStepSchema(BaseModel):
    """工作流步骤 Schema"""
    id: str
    name: str
    description: str = ""
    tool: Optional[str] = None  # 要调用的工具名
    tool_params: Dict[str, Any] = Field(default_factory=dict)
    condition: Optional[str] = None  # 执行条件表达式
    depends_on: List[str] = Field(default_factory=list)  # 依赖的步骤
    retry_count: int = 0
    continue_on_failure: bool = False


class WorkflowExecutionConfig(BaseModel):
    """工作流执行配置"""
    on_failure: str = "stop"  # stop, continue
    retry: Dict[str, Any] = Field(default_factory=dict)
    timeout: Dict[str, Any] = Field(default_factory=dict)
    parallel: bool = False
    max_parallel_steps: int = 3


class WorkflowValidationConfig(BaseModel):
    """工作流验证配置"""
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)


class WorkflowReportingConfig(BaseModel):
    """工作流报告配置"""
    format: List[str] = Field(default_factory=lambda: ["markdown"])
    output_dir: str = ".spec/reports"
    include_timings: bool = True
    include_metrics: bool = True
    include_artifacts: bool = True


class WorkflowSchema(BaseModel):
    """工作流完整 Schema"""
    name: str
    version: str = "1.0"
    description: str = ""
    mode: ExecutionMode = ExecutionMode.EXTENDED
    workspace: str = "."
    steps: List[WorkflowStepSchema]
    variables: Dict[str, Any] = Field(default_factory=dict)
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    execution: WorkflowExecutionConfig = Field(default_factory=WorkflowExecutionConfig)
    validation: WorkflowValidationConfig = Field(default_factory=WorkflowValidationConfig)
    notifications: Dict[str, Any] = Field(default_factory=dict)
    reporting: WorkflowReportingConfig = Field(default_factory=WorkflowReportingConfig)

    model_config = {
        "coerce_numbers_to_str": True,
        "extra": "allow"  # 允许额外字段
    }


@dataclass
class WorkflowStepResult:
    step_id: str
    status: StepStatus
    output: Any = None
    error: Optional[str] = None
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_id': self.step_id,
            'status': self.status.value,
            'output': str(self.output) if self.output else None,
            'error': self.error,
            'duration': self.duration
        }


@dataclass
class WorkflowResult:
    workflow_name: str
    success: bool
    step_results: List[WorkflowStepResult]
    outputs: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'workflow_name': self.workflow_name,
            'success': self.success,
            'step_results': [r.to_dict() for r in self.step_results],
            'outputs': self.outputs,
            'duration': self.duration
        }


@dataclass
class WorkflowExecutionSnapshot:
    """工作流执行快照 - 用于断点续跑"""
    workflow_name: str
    workflow_version: str
    snapshot_id: str
    created_at: datetime
    variables: Dict[str, Any]
    step_results: Dict[str, Dict[str, Any]]
    completed_steps: List[str]
    pending_steps: List[str]
    failed_steps: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'workflow_name': self.workflow_name,
            'workflow_version': self.workflow_version,
            'snapshot_id': self.snapshot_id,
            'created_at': self.created_at.isoformat(),
            'variables': self.variables,
            'step_results': self.step_results,
            'completed_steps': self.completed_steps,
            'pending_steps': self.pending_steps,
            'failed_steps': self.failed_steps,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowExecutionSnapshot':
        return cls(
            workflow_name=data['workflow_name'],
            workflow_version=data['workflow_version'],
            snapshot_id=data['snapshot_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            variables=data['variables'],
            step_results=data['step_results'],
            completed_steps=data['completed_steps'],
            pending_steps=data['pending_steps'],
            failed_steps=data['failed_steps'],
        )


class WorkflowEngine:
    """声明式工作流引擎 - 执行 YAML 定义的工作流

    支持两种执行模式:
    - CORE (快速路径): propose → apply → archive (3步)
    - EXTENDED (细粒度): explore → new → continue → ff → apply → verify → archive (7步)

    Phase 3 增强功能:
    - 执行状态管理与持久化
    - 断点续跑支持
    - 步骤重试机制
    - 并行执行支持
    - 事件钩子系统
    - 与 SpecEngine 集成
    """

    def __init__(self, tool_registry: Optional[ToolRegistry] = None,
                 spec_engine: Optional[Any] = None,
                 snapshot_dir: Optional[Union[str, Path]] = None):
        self._registry = tool_registry or default_registry
        self._spec_engine = spec_engine
        self._snapshot_dir = Path(snapshot_dir) if snapshot_dir else None
        self._variables: Dict[str, Any] = {}
        self._step_results: Dict[str, WorkflowStepResult] = {}
        self._current_workflow: Optional[WorkflowSchema] = None
        self._execution_context: Dict[str, Any] = {}

        # 钩子系统: hook_type -> list of callable
        self._hooks: Dict[str, List[Callable]] = {
            'pre_workflow': [],      # 工作流开始前
            'post_workflow': [],     # 工作流结束后
            'pre_step': [],          # 步骤开始前
            'post_step': [],         # 步骤结束后
            'step_success': [],      # 步骤成功
            'step_failure': [],      # 步骤失败
            'step_retry': [],        # 步骤重试
            'success': [],           # 工作流成功
            'failure': [],           # 工作流失败
            'snapshot_created': [],  # 快照创建
        }

    def register_hook(self, hook_type: str, hook: Callable):
        """注册钩子函数

        Args:
            hook_type: 钩子类型 (pre_workflow, post_step, etc.)
            hook: 钩子函数，签名取决于钩子类型
        """
        if hook_type in self._hooks:
            self._hooks[hook_type].append(hook)
        else:
            raise ValueError(f"未知钩子类型: {hook_type}，可用类型: {list(self._hooks.keys())}")

    def _trigger_hook(self, hook_type: str, *args, **kwargs):
        """触发钩子"""
        for hook in self._hooks[hook_type]:
            try:
                hook(*args, **kwargs)
            except Exception:
                pass  # 钩子错误不中断执行

    def load_workflow(self, yaml_path: Union[str, Path]) -> WorkflowSchema:
        """从 YAML 文件加载工作流"""
        yaml_path = Path(yaml_path)
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return WorkflowSchema(**data)

    def parse_workflow(self, yaml_content: str) -> WorkflowSchema:
        """从 YAML 字符串解析工作流"""
        data = yaml.safe_load(yaml_content)
        return WorkflowSchema(**data)

    def execute_workflow(self, workflow: WorkflowSchema,
                        context: Dict[str, Any] = None,
                        resume_from_snapshot: Optional[WorkflowExecutionSnapshot] = None,
                        enable_parallel: Optional[bool] = None) -> WorkflowResult:
        """执行完整工作流

        Args:
            workflow: 工作流定义
            context: 执行上下文变量
            resume_from_snapshot: 从快照断点续跑
            enable_parallel: 是否启用并行执行（覆盖 workflow.execution.parallel）
        """
        import time
        start_time = time.time()
        self._current_workflow = workflow

        # 触发 pre_workflow 钩子
        self._trigger_hook('pre_workflow', workflow, context)

        # 初始化变量
        if resume_from_snapshot:
            # 断点续跑模式
            self._variables = dict(resume_from_snapshot.variables)
            self._variables.update(context or {})
            self._step_results = self._restore_step_results(resume_from_snapshot.step_results)
            skip_steps = set(resume_from_snapshot.completed_steps + resume_from_snapshot.failed_steps)
        else:
            # 全新执行模式
            self._variables = dict(workflow.variables)
            self._variables.update(context or {})
            self._step_results = {}
            skip_steps = set()

        # 确定是否启用并行
        parallel = enable_parallel if enable_parallel is not None else workflow.execution.parallel

        # 构建执行顺序（拓扑排序）
        execution_order = self._topological_sort(workflow.steps)

        # 执行
        if parallel:
            all_results = self._execute_parallel(workflow.steps, execution_order, skip_steps)
        else:
            all_results = self._execute_sequential(workflow.steps, execution_order, skip_steps)

        # 检查最终成功状态
        success = all(r.status == StepStatus.SUCCESS or r.status == StepStatus.SKIPPED
                     for r in all_results)

        total_duration = time.time() - start_time

        # 触发钩子
        if success:
            self._trigger_hook('success', self._variables, all_results)
        else:
            self._trigger_hook('failure', self._variables, all_results)

        self._trigger_hook('post_workflow', workflow, success, all_results, total_duration)

        # 生成报告
        if workflow.reporting.include_timings:
            self._generate_execution_report(workflow, all_results)

        return WorkflowResult(
            workflow_name=workflow.name,
            success=success,
            step_results=all_results,
            outputs=dict(self._variables),
            duration=total_duration
        )

    def _execute_sequential(self, steps: List[WorkflowStepSchema],
                           execution_order: List[str],
                           skip_steps: Set[str]) -> List[WorkflowStepResult]:
        """顺序执行工作流步骤"""
        all_results = []

        for step_id in execution_order:
            if step_id in skip_steps:
                continue

            step = next(s for s in steps if s.id == step_id)
            result = self._execute_step_with_retry(step)
            all_results.append(result)
            self._step_results[step_id] = result

            # 创建快照
            if self._snapshot_dir:
                self._create_snapshot(step_id, steps, execution_order)

            # 如果失败且不允许继续，中断执行
            if result.status == StepStatus.FAILED and not step.continue_on_failure:
                # 将剩余步骤标记为跳过
                remaining = [s for s in steps if s.id not in self._step_results]
                for s in remaining:
                    skip_result = WorkflowStepResult(
                        step_id=s.id,
                        status=StepStatus.SKIPPED,
                        error="前置步骤失败，工作流中断",
                        duration=0.0
                    )
                    all_results.append(skip_result)
                    self._step_results[s.id] = skip_result
                break

        return all_results

    def _execute_parallel(self, steps: List[WorkflowStepSchema],
                         execution_order: List[str],
                         skip_steps: Set[str]) -> List[WorkflowStepResult]:
        """并行执行工作流步骤"""
        from collections import deque
        import threading

        all_results = []
        step_map = {s.id: s for s in steps}
        in_degree = {s.id: len(s.depends_on) for s in steps}
        completed = set(skip_steps)
        results_lock = threading.Lock()

        def worker(step_id: str):
            step = step_map[step_id]
            result = self._execute_step_with_retry(step)

            with results_lock:
                all_results.append(result)
                self._step_results[step_id] = result
                completed.add(step_id)

                # 更新依赖计数，唤醒后续步骤
                for neighbor_id in [n for n in execution_order if step_id in step_map[n].depends_on]:
                    in_degree[neighbor_id] -= 1

        max_parallel = self._current_workflow.execution.max_parallel_steps if self._current_workflow else 3
        active_threads = {}

        while len(completed) < len(steps):
            # 找出可以执行的步骤
            ready = [s_id for s_id in execution_order
                    if s_id not in completed
                    and s_id not in active_threads
                    and in_degree[s_id] == 0]

            for step_id in ready:
                if len(active_threads) >= max_parallel:
                    break

                t = threading.Thread(target=worker, args=(step_id,), daemon=True)
                active_threads[step_id] = t
                t.start()

            # 等待至少一个线程完成
            for step_id, t in list(active_threads.items()):
                t.join(timeout=0.1)
                if not t.is_alive():
                    del active_threads[step_id]

            # 创建快照
            if self._snapshot_dir and len(all_results) % 2 == 0:
                self._create_snapshot("parallel_batch", steps, execution_order)

        # 等待所有线程完成
        for t in active_threads.values():
            t.join()

        return all_results

    def _execute_step_with_retry(self, step: WorkflowStepSchema) -> WorkflowStepResult:
        """执行单个步骤，包含重试逻辑"""
        import time
        max_attempts = step.retry_count + 1
        retry_config = self._current_workflow.execution.retry if self._current_workflow else {}
        delay = retry_config.get('delay_seconds', 1.0)
        exponential_backoff = retry_config.get('exponential_backoff', False)

        last_error = None
        for attempt in range(max_attempts):
            if attempt > 0:
                self._trigger_hook('step_retry', step, attempt, last_error)
                sleep_time = delay * (2 ** (attempt - 1)) if exponential_backoff else delay
                time.sleep(sleep_time)

            result = self._execute_single_step(step)

            if result.status == StepStatus.SUCCESS or result.status == StepStatus.SKIPPED:
                self._trigger_hook('step_success', step, result)
                return result

            last_error = result.error

        # 所有重试都失败
        self._trigger_hook('step_failure', step, result)
        return result

    def _execute_single_step(self, step: WorkflowStepSchema) -> WorkflowStepResult:
        """执行单个工作流步骤（单次尝试）"""
        import time
        start = time.time()

        # 运行 pre_step 钩子
        self._trigger_hook('pre_step', step, self._variables)

        # 检查条件
        if step.condition and not self._evaluate_condition(step.condition):
            result = WorkflowStepResult(
                step_id=step.id,
                status=StepStatus.SKIPPED,
                duration=time.time() - start
            )
            self._trigger_hook('post_step', step, result, self._variables)
            return result

        # 检查依赖是否都成功
        for dep_id in step.depends_on:
            dep_result = self._step_results.get(dep_id)
            if dep_result and dep_result.status != StepStatus.SUCCESS:
                result = WorkflowStepResult(
                    step_id=step.id,
                    status=StepStatus.SKIPPED,
                    duration=time.time() - start
                )
                self._trigger_hook('post_step', step, result, self._variables)
                return result

        # 调用工具
        if step.tool:
            try:
                params = self._resolve_params(step.tool_params)
                result = self._registry.execute_tool(step.tool, params)

                # 保存输出到变量
                self._variables[f"{step.id}_result"] = result

                step_result = WorkflowStepResult(
                    step_id=step.id,
                    status=StepStatus.SUCCESS if result.success else StepStatus.FAILED,
                    output=result,
                    duration=time.time() - start
                )
            except Exception as e:
                step_result = WorkflowStepResult(
                    step_id=step.id,
                    status=StepStatus.FAILED,
                    error=str(e),
                    duration=time.time() - start
                )
        else:
            # 无工具的步骤 - 通知 SpecEngine（如果有）
            if self._spec_engine:
                try:
                    self._spec_engine.handle_workflow_step(step, self._variables)
                except Exception:
                    pass

            step_result = WorkflowStepResult(
                step_id=step.id,
                status=StepStatus.SUCCESS,
                duration=time.time() - start
            )

        # 运行 post_step 钩子
        self._trigger_hook('post_step', step, step_result, self._variables)

        return step_result

    def _topological_sort(self, steps: List[WorkflowStepSchema]) -> List[str]:
        """拓扑排序确定执行顺序"""
        from collections import deque

        in_degree = {s.id: len(s.depends_on) for s in steps}
        adj = {s.id: [] for s in steps}

        for s in steps:
            for dep in s.depends_on:
                adj[dep].append(s.id)

        queue = deque([s.id for s in steps if in_degree[s.id] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 检测循环依赖
        if len(result) != len(steps):
            unprocessed = set(in_degree.keys()) - set(result)
            raise ValueError(f"工作流存在循环依赖: {unprocessed}")

        return result

    def _evaluate_condition(self, condition: str) -> bool:
        """评估条件表达式"""
        try:
            return bool(eval(condition, {}, self._variables))
        except Exception:
            return False

    def _resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """解析参数中的变量引用

        支持 ${var_name} 语法引用变量
        """
        def resolve_value(value: Any) -> Any:
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                var_name = value[2:-1]
                return self._variables.get(var_name, value)
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(v) for v in value]
            return value

        result = {}
        for k, v in params.items():
            result[k] = resolve_value(v)
        return result

    def _create_snapshot(self, current_step_id: str,
                        steps: List[WorkflowStepSchema],
                        execution_order: List[str]) -> WorkflowExecutionSnapshot:
        """创建执行快照"""
        if not self._snapshot_dir:
            raise ValueError("未配置快照目录")

        import uuid
        snapshot_id = str(uuid.uuid4())[:8]

        completed = [s_id for s_id, r in self._step_results.items()
                    if r.status == StepStatus.SUCCESS]
        failed = [s_id for s_id, r in self._step_results.items()
                 if r.status == StepStatus.FAILED]
        pending = [s_id for s_id in execution_order if s_id not in self._step_results]

        snapshot = WorkflowExecutionSnapshot(
            workflow_name=self._current_workflow.name if self._current_workflow else "unknown",
            workflow_version=self._current_workflow.version if self._current_workflow else "1.0",
            snapshot_id=snapshot_id,
            created_at=datetime.now(),
            variables=dict(self._variables),
            step_results={s_id: r.to_dict() for s_id, r in self._step_results.items()},
            completed_steps=completed,
            pending_steps=pending,
            failed_steps=failed,
        )

        # 保存到文件
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = self._snapshot_dir / f"snapshot_{snapshot_id}.json"
        snapshot_file.write_text(json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False),
                                encoding='utf-8')

        self._trigger_hook('snapshot_created', snapshot)
        return snapshot

    def _restore_step_results(self, results_data: Dict[str, Dict[str, Any]]) -> Dict[str, WorkflowStepResult]:
        """从快照恢复步骤结果"""
        results = {}
        for step_id, data in results_data.items():
            status = StepStatus(data['status'])
            results[step_id] = WorkflowStepResult(
                step_id=step_id,
                status=status,
                output=data.get('output'),
                error=data.get('error'),
                duration=data.get('duration', 0.0)
            )
        return results

    def load_snapshot(self, snapshot_id: str) -> Optional[WorkflowExecutionSnapshot]:
        """加载指定的执行快照"""
        if not self._snapshot_dir:
            return None

        snapshot_file = self._snapshot_dir / f"snapshot_{snapshot_id}.json"
        if not snapshot_file.exists():
            return None

        data = json.loads(snapshot_file.read_text(encoding='utf-8'))
        return WorkflowExecutionSnapshot.from_dict(data)

    def list_snapshots(self, workflow_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有可用的快照"""
        if not self._snapshot_dir or not self._snapshot_dir.exists():
            return []

        snapshots = []
        for f in self._snapshot_dir.glob("snapshot_*.json"):
            data = json.loads(f.read_text(encoding='utf-8'))
            if workflow_name and data.get('workflow_name') != workflow_name:
                continue
            snapshots.append({
                'snapshot_id': data['snapshot_id'],
                'workflow_name': data['workflow_name'],
                'created_at': data['created_at'],
                'completed_count': len(data['completed_steps']),
                'total_steps': len(data['completed_steps']) + len(data['pending_steps'])
            })
        return sorted(snapshots, key=lambda x: x['created_at'], reverse=True)

    def get_step_result(self, step_id: str) -> Optional[WorkflowStepResult]:
        """获取步骤执行结果"""
        return self._step_results.get(step_id)

    def _generate_execution_report(self, workflow: WorkflowSchema,
                                   results: List[WorkflowStepResult]) -> Dict[str, Any]:
        """生成执行报告"""
        report = {
            'workflow_name': workflow.name,
            'version': workflow.version,
            'generated_at': datetime.now().isoformat(),
            'steps': [],
            'summary': {
                'total': len(results),
                'success': sum(1 for r in results if r.status == StepStatus.SUCCESS),
                'failed': sum(1 for r in results if r.status == StepStatus.FAILED),
                'skipped': sum(1 for r in results if r.status == StepStatus.SKIPPED),
            }
        }

        for result in results:
            report['steps'].append({
                'step_id': result.step_id,
                'status': result.status.value,
                'duration': result.duration,
                'error': result.error
            })

        if workflow.reporting.output_dir:
            output_dir = Path(workflow.reporting.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            report_file = output_dir / f"workflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

        return report

    @classmethod
    def run_from_yaml(cls, yaml_path: str, context: Dict[str, Any] = None,
                     tool_registry: Optional[ToolRegistry] = None, **kwargs) -> WorkflowResult:
        """从 YAML 文件运行工作流"""
        engine = cls(tool_registry=tool_registry, **kwargs)
        workflow = engine.load_workflow(yaml_path)
        return engine.execute_workflow(workflow, context)

    @classmethod
    def run_from_yaml(cls, yaml_path: str, context: Dict[str, Any] = None) -> WorkflowResult:
        """从 YAML 文件运行工作流"""
        engine = cls()
        workflow = engine.load_workflow(yaml_path)
        return engine.execute_workflow(workflow, context)


def create_test_workflow() -> str:
    """创建示例测试工作流 YAML"""
    return '''name: "code_review_fix_test"
version: "1.0"
description: "代码审查 → 自动修复 → 生成测试文档 → 生成测试代码 → 运行测试"
variables:
  source_file: "example.cpp"
  project_name: "my_project"

steps:
  - id: code_review
    name: "代码审查"
    tool: code_review
    tool_params:
      file_path: "${source_file}"

  - id: auto_fix
    name: "自动修复"
    tool: auto_fixer
    depends_on: ["code_review"]
    tool_params:
      file_path: "${source_file}"
      create_backup: true

  - id: test_doc
    name: "生成测试文档"
    tool: test_doc_generator
    depends_on: ["auto_fix"]
    tool_params:
      source_file: "${source_file}"
      output_file: "${project_name}/test_documentation.md"

  - id: test_code
    name: "生成测试代码"
    tool: test_generator
    depends_on: ["test_doc"]
    tool_params:
      source_file: "${source_file}"
      output_file: "${project_name}/test_${source_file}"

  - id: run_tests
    name: "运行测试"
    tool: test_runner
    depends_on: ["test_code"]
    continue_on_failure: true
    tool_params:
      test_file: "${project_name}/test_${source_file}"
      source_file: "${source_file}"
'''
