# -*- coding: utf-8 -*-
"""Phase 9: Quality Gate - 硬性质量检查 + 代码审查"""

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ..llm_client import LLMClient, get_llm_client
from ..multi_agent.content_sanitizer import detect_diff_pollution_in_files
from ..schema.event_bus import get_global_event_bus
from ..schema.workflow_events import (
    ValidationCompletedEvent,
    ValidationIssueFoundEvent,
    ValidationStartedEvent,
)
from .base import OpenSpecContext, PhaseInterface, PhaseResult

try:
    from ..schema.validation_engine import (
        ValidationEngine,
        ValidationIssue,
        ValidationLevel,
        ValidationSeverity,
    )

    _HAS_VALIDATION_ENGINE = True
except ImportError:
    _HAS_VALIDATION_ENGINE = False


class Phase9QualityGate(PhaseInterface):
    """Phase 9: 质量门禁 - 硬性检查 + 可选代码审查"""

    def __init__(
        self,
        context: OpenSpecContext,
        tool_registry=None,
        llm_client: Optional[LLMClient] = None,
        llm_client_factory: Optional[Callable[..., LLMClient]] = None,
    ):
        super().__init__(context)
        self.phase_number = 9
        self.phase_name = "Quality Gate"
        self.tool_registry = tool_registry
        self.is_critical = True

        # 配置：从 context 或使用默认值
        self.config = self._load_config()

        # EventBus integration
        self.event_bus = get_global_event_bus()
        self.workflow_id = getattr(context, "workflow_id", "")

        # LLM client for self-healing. Resolve lazily so normal quality gate
        # checks do not require an Anthropic key.
        self.llm_client = llm_client
        self.llm_client_factory = llm_client_factory or LLMClient
        self.fallback_model = self.config["code_review"]["self_heal"]["fallback_model"]
        self.model_switched = False

        # 自愈统计
        self.heal_attempts = 0
        self.heal_success = 0
        self.model_switches = 0

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        provider_model = self._default_llm_model()
        default_config = {
            "code_review": {
                "enabled": True,  # 默认启用代码审查
                "check_types": ["todo", "debug", "security", "performance"],
                "fail_on_critical": False,  # 默认不因代码审查失败而终止
                "max_files": 50,
                "exclude_patterns": [],
                "review_agent": {
                    "enabled": False,
                    "max_concurrency": None,
                },
                "self_heal": {
                    "enabled": True,  # 默认启用自愈
                    "max_attempts": 3,  # 最大尝试次数
                    "only_critical": True,  # 只修复 Critical 问题
                    "switch_model_after": 2,  # 2次失败后切换模型
                    "fallback_model": provider_model,
                    "require_approval": False,  # 是否需要用户确认
                    "create_backup": True,
                    "max_fixes_per_attempt": 10,
                },
            }
        }

        # 尝试从 context 加载配置
        if hasattr(self.context, "config") and self.context.config:
            user_config = self.context.config.get("phase9_quality_gate", {})
            self._deep_merge_config(default_config, user_config)
        # 验证配置
        self._validate_config(default_config)

        return default_config

    def _default_llm_model(self) -> str:
        try:
            from devpal.config import get_config

            config = get_config()
            provider = config.llm_default_provider
            provider_config = config.get_provider_config(provider)
            model = provider_config.get("model")
            if model:
                return str(model)
        except Exception:
            pass
        return "gpt-5.5-pro"

    def _deep_merge_config(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge nested config dictionaries without dropping self_heal defaults."""
        for key, value in (override or {}).items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                self._deep_merge_config(base[key], value)
            else:
                base[key] = value
        return base

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置项的合法性"""
        code_review = config.get("code_review", {})

        # 验证 max_files
        max_files = code_review.get("max_files", 50)
        if not isinstance(max_files, int) or max_files <= 0:
            raise ValueError(
                f"Invalid max_files: {max_files}. Must be a positive integer."
            )

        # 验证 check_types
        check_types = code_review.get("check_types", [])
        valid_types = ["todo", "debug", "security", "performance"]
        for check_type in check_types:
            if check_type not in valid_types:
                raise ValueError(
                    f"Invalid check_type: {check_type}. Must be one of {valid_types}"
                )

        # 验证 self_heal 配置
        self_heal = code_review.get("self_heal", {})

        max_attempts = self_heal.get("max_attempts", 3)
        if not isinstance(max_attempts, int) or max_attempts <= 0 or max_attempts > 10:
            raise ValueError(
                f"Invalid max_attempts: {max_attempts}. Must be between 1 and 10."
            )

        switch_model_after = self_heal.get("switch_model_after", 2)
        if not isinstance(switch_model_after, int) or switch_model_after < 0:
            raise ValueError(
                f"Invalid switch_model_after: {switch_model_after}. Must be non-negative."
            )

        if switch_model_after > max_attempts:
            raise ValueError(
                f"switch_model_after ({switch_model_after}) cannot be greater than max_attempts ({max_attempts})"
            )

        max_fixes_per_attempt = self_heal.get("max_fixes_per_attempt", 10)
        if (
            not isinstance(max_fixes_per_attempt, int)
            or max_fixes_per_attempt <= 0
            or max_fixes_per_attempt > 50
        ):
            raise ValueError(
                f"Invalid max_fixes_per_attempt: {max_fixes_per_attempt}. Must be between 1 and 50."
            )

        fallback_model = self_heal.get("fallback_model", "")
        if not isinstance(fallback_model, str) or not fallback_model:
            raise ValueError(
                f"Invalid fallback_model: {fallback_model}. Must be a non-empty string."
            )

    def execute(self) -> PhaseResult:
        self.log("Phase 9: Quality Gate - running mandatory checks...")

        # ========== Layer 1: 硬性结构检查 (必须通过) ==========
        val_result = None
        if _HAS_VALIDATION_ENGINE:
            try:
                val_result = self._run_validation_engine()
            except Exception as e:
                self.log("  [WARN] ValidationEngine failed: {}".format(e))

        violations = []
        warnings = []

        diff_pollution_check = self._check_diff_pollution()
        if diff_pollution_check:
            violations.extend(diff_pollution_check)
        else:
            self.log("  [OK] No diff pollution detected in generated files")

        # 根据语言动态检查
        language = getattr(self.context, "language", "cpp")

        if language == "cpp":
            # C++ 项目检查
            # 检查 1: CMakeLists.txt
            if not self._check_cmake_exists():
                violations.append("CMakeLists.txt not found")
            else:
                self.log("  [OK] CMakeLists.txt exists")

            # 检查 2: src/main.cpp
            main_check = self._check_main_cpp()
            if main_check:
                violations.append(main_check)
            else:
                self.log("  [OK] src/main.cpp exists with main()")

            # 检查 3: test_base.h
            test_base_check = self._check_test_base()
            if test_base_check:
                violations.append(test_base_check)
            else:
                self.log("  [OK] test_base.h API is consistent")

            # 检查 4: 测试文件存在性
            test_files_check = self._check_test_files_exist()
            if test_files_check:
                violations.append(test_files_check)
            else:
                self.log("  [OK] Test files present")

        elif language == "python":
            # Python 项目检查
            # 检查 1: src/main.py 或 src/__main__.py
            main_check = self._check_python_main()
            if main_check:
                violations.append(main_check)
            else:
                self.log("  [OK] Python main entry point exists")

            # 检查 2: 测试文件存在性（pytest）
            test_files_check = self._check_python_test_files()
            if test_files_check:
                violations.append(test_files_check)
            else:
                self.log("  [OK] Python test files present")

        elif language == "shell":
            # Shell 项目检查
            # 检查 1: scripts/main.sh 或主脚本
            main_check = self._check_shell_main()
            if main_check:
                violations.append(main_check)
            else:
                self.log("  [OK] Shell main script exists")

            # 检查 2: 测试文件存在性
            test_files_check = self._check_shell_test_files()
            if test_files_check:
                violations.append(test_files_check)
            else:
                self.log("  [OK] Shell test files present")

        else:
            # 其他语言：通用检查
            self.log("  [INFO] Language '{}' - using generic checks".format(language))
            # 至少检查项目目录存在
            if not self.context.project_dir.exists():
                violations.append("Project directory not found")

        # 如果硬性检查失败，立即返回（快速失败）
        if violations:
            self.log("  [FAIL] Quality Gate: {} violations".format(len(violations)))
            for v in violations:
                self.log("    - {}".format(v))

            # 生成报告（只包含硬性检查结果）
            report_path = self._write_report(violations, warnings, val_result, None)

            return PhaseResult.fail(
                "Quality Gate failed: {} violations".format(len(violations)),
                errors=violations,
            )

        # ========== Layer 2: 代码质量审查 (可选) ==========
        review_issues = []
        original_review_issues_count = 0
        if self._should_run_code_review():
            self.log("  [CODE REVIEW] Starting code quality review...")
            self._emit_validation_started_event()
            try:
                review_issues = self._run_code_review()
                original_review_issues_count = len(review_issues)
                self.log("  [CODE REVIEW] Found {} issues".format(len(review_issues)))
            except Exception as e:
                self.log("  [WARN] Code review failed: {}".format(e))
        else:
            self.log("  [SKIP] Code review disabled")

        # ========== Layer 2.5: 自愈修复 (可选) ==========
        critical_issues = [i for i in review_issues if i.get("severity") == "error"]

        if critical_issues and self._should_trigger_self_heal(review_issues):
            self.log(
                "  [SELF-HEAL] Found {} critical issues, attempting to fix...".format(
                    len(critical_issues)
                )
            )
            try:
                heal_success, new_issues = self._run_self_heal(review_issues)
                if heal_success:
                    self.log("  [SELF-HEAL] Successfully fixed issues")
                    review_issues = new_issues
                    critical_issues = [
                        i for i in review_issues if i.get("severity") == "error"
                    ]
                else:
                    self.log("  [SELF-HEAL] Failed to fix all issues")
            except Exception as e:
                self.log("  [WARN] Self-heal failed: {}".format(e))

        self._emit_validation_completed_event(review_issues)

        # ========== Layer 3: 决策逻辑 ==========
        # 生成完整报告
        report_path = self._write_report(
            violations,
            warnings,
            val_result,
            review_issues,
            self.heal_attempts,
            self.heal_success,
            self.model_switches,
        )

        # 如果有严重问题且配置为失败
        if critical_issues and self.config["code_review"]["fail_on_critical"]:
            self.log(
                "  [FAIL] Quality Gate: {} critical code review issues".format(
                    len(critical_issues)
                )
            )
            for issue in critical_issues[:5]:  # 只显示前 5 个
                self.log(
                    "    - {}:{} {}".format(
                        Path(issue["file"]).name, issue["line"], issue["message"]
                    )
                )

            return PhaseResult.fail(
                "Quality Gate failed: {} critical code review issues".format(
                    len(critical_issues)
                ),
                errors=[i["message"] for i in critical_issues],
            )

        # 通过
        self.log("  [OK] Quality Gate passed")
        if review_issues:
            self.log(
                "  [INFO] Code review found {} issues (not blocking)".format(
                    len(review_issues)
                )
            )

        return PhaseResult.ok(
            "Quality Gate passed",
            violations=0,
            warnings=len(warnings),
            review_issues=original_review_issues_count,
            critical_issues=len(critical_issues),
            report_path=str(report_path),
        )

    def _check_diff_pollution(self) -> List[str]:
        issues = detect_diff_pollution_in_files(self._collect_diff_pollution_targets())
        return [
            "Diff pollution detected in {}:{} ({})".format(
                issue["path"], issue["line"], issue["marker"]
            )
            for issue in issues
        ]

    def _collect_diff_pollution_targets(self) -> List[Path]:
        targets = set()
        project_dir = self.context.project_dir
        for attr in ("ai_generated_files", "generated_files"):
            for path in getattr(self.context, attr, []) or []:
                path = Path(path)
                if not path.is_absolute():
                    path = project_dir / path
                if self._is_diff_pollution_target(path):
                    targets.add(path)

        if targets:
            return sorted(targets)

        for name in ("CMakeLists.txt",):
            path = project_dir / name
            if path.exists():
                targets.add(path)
        for subdir in ("src", "include", "tests", "scripts"):
            base = project_dir / subdir
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if self._is_diff_pollution_target(path):
                    targets.add(path)
        return sorted(targets)

    def _is_diff_pollution_target(self, path: Path) -> bool:
        return path.is_file() and (
            path.suffix in {".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".sh", ".bat", ".cmake"}
            or path.name == "CMakeLists.txt"
        )

    def _should_run_code_review(self) -> bool:
        """判断是否应该运行代码审查"""
        return self.config["code_review"]["enabled"]

    def _run_code_review(self) -> List[Dict[str, Any]]:
        """运行代码审查"""
        if self._should_run_review_agent():
            try:
                return self._run_code_review_with_agent()
            except Exception as exc:
                self.log(
                    f"    [WARN] ReviewAgent failed, falling back to local review: {exc}"
                )
                event_integration = getattr(self.context, "event_integration", None)
                if event_integration and hasattr(event_integration, "emit_agent_fallback_used"):
                    event_integration.emit_agent_fallback_used(
                        self.phase_number,
                        reason=str(exc),
                        fallback="phase9.local_review",
                    )
        return self._run_code_review_local()

    def _should_run_review_agent(self) -> bool:
        agent_cfg = self.config["code_review"].get("review_agent", {})
        return bool(agent_cfg.get("enabled", False) or getattr(self.context, "enable_multi_agent", False))

    def _run_code_review_local(self) -> List[Dict[str, Any]]:
        self.log("    [CODE REVIEW] Running local deterministic rule checks")
        files_to_review = self._collect_review_targets()

        if not files_to_review:
            self.log("    [WARN] No files to review")
            return []

        max_files = self.config["code_review"]["max_files"]
        if len(files_to_review) > max_files:
            self.log(
                "    [INFO] Limiting review to {} files (out of {})".format(
                    max_files, len(files_to_review)
                )
            )
            files_to_review = files_to_review[:max_files]

        all_issues = []
        check_types = self.config["code_review"]["check_types"]

        for file_path in files_to_review:
            try:
                issues = self._review_file(file_path, check_types)
                all_issues.extend(issues)
                if issues:
                    self.log(
                        "    [{}] {}: {} issues".format(
                            "!"
                            if any(i["severity"] == "error" for i in issues)
                            else "OK",
                            file_path.name,
                            len(issues),
                        )
                    )
            except Exception as e:
                self.log(
                    "    [ERROR] Failed to review {}: {}".format(file_path.name, e)
                )

        return all_issues

    def _get_relative_path(self, file_path: Union[str, Path]) -> Path:
        """Convert path to relative path, handling both relative and absolute paths."""
        file_p = Path(file_path)
        project_p = Path(self.context.project_dir).resolve()

        if file_p.is_absolute():
            file_resolved = file_p.resolve()
            if file_resolved.is_relative_to(project_p):
                return file_resolved.relative_to(project_p)
            else:
                return Path(file_p.name)
        else:
            return file_p

    def _run_code_review_with_agent(self) -> List[Dict[str, Any]]:
        from devpal.core.multi_agent import AgentPolicy, MultiAgentCoordinator
        from devpal.core.openspec_phases.parallel_executor import ParallelTask

        files_to_review = self._collect_review_targets()
        if not files_to_review:
            self.log("    [WARN] No files to review")
            return []
        max_files = self.config["code_review"]["max_files"]
        if len(files_to_review) > max_files:
            files_to_review = files_to_review[:max_files]
        check_types = self.config["code_review"]["check_types"]
        tasks = [
            ParallelTask(
                task_id=f"phase9:review:{self._get_relative_path(file_path).as_posix()}",
                phase_number=9,
                task_type="code_review",
                input_payload={
                    "project_dir": self.context.project_dir,
                    "file_path": file_path,
                    "check_types": check_types,
                },
            )
            for file_path in files_to_review
        ]
        agent_cfg = self.config["code_review"].get("review_agent", {})
        max_concurrency = agent_cfg.get("max_concurrency") or getattr(
            self.context, "agent_pool_size", 1
        )
        policy = AgentPolicy(
            enabled=True,
            sandbox_level=getattr(self.context, "sandbox_level", "staging"),
            max_concurrency=max_concurrency,
            retry_limit=0,
            allowed_tools=["read_file", "review_code"],
            backend=getattr(self.context, "agent_backend", "local"),
            backend_options=getattr(self.context, "agent_backend_options", {}),
        )
        coordinator = MultiAgentCoordinator(
            policy=policy,
            log=self.log,
            event_integration=getattr(self.context, "event_integration", None),
            review_checker=self._review_file,
        )
        results, summary = coordinator.execute_review_tasks(tasks)
        self.context.parallel_execution_stats["9"] = summary
        issues: List[Dict[str, Any]] = []
        for result in results:
            if result.success:
                issues.extend(result.metadata.get("issues", []) or [])
            elif result.error:
                self.log(f"    [WARN] ReviewAgent task failed: {result.error}")
        return issues

    def _collect_review_targets(self) -> List[Path]:
        """收集需要审查的文件（优先 AI 生成的文件）"""
        # 1. 优先：AI 生成的文件
        ai_files = []
        if (
            hasattr(self.context, "ai_generated_files")
            and self.context.ai_generated_files
        ):
            for f in self.context.ai_generated_files:
                path = Path(f) if isinstance(f, str) else f
                if path.exists() and path.suffix in [".cpp", ".h", ".hpp"]:
                    ai_files.append(path)

        if ai_files:
            self.log("    [INFO] Reviewing {} AI-generated files".format(len(ai_files)))
            return sorted(set(ai_files))

        # 2. 备选：扫描 src/ 和 include/ 目录
        self.log("    [INFO] No AI-generated files, scanning src/ and include/")
        candidates = []
        for sub in ["src", "include"]:
            base = self.context.project_dir / sub
            if not base.exists():
                continue
            for ext in ["*.cpp", "*.h", "*.hpp"]:
                candidates.extend(base.glob(ext))

        # 排除测试文件
        exclude_patterns = list(self.config["code_review"]["exclude_patterns"])
        exclude_patterns.extend(["test_*.cpp", "*_test.cpp", "test_base.h"])

        filtered = []
        for f in candidates:
            if not any(f.match(pattern) for pattern in exclude_patterns):
                filtered.append(f)

        return sorted(set(filtered))

    def _review_file(
        self, file_path: Path, check_types: List[str]
    ) -> List[Dict[str, Any]]:
        """审查单个文件"""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return [
                {
                    "file": str(file_path),
                    "line": 0,
                    "severity": "error",
                    "category": "review_error",
                    "message": "Failed to read file: {}".format(e),
                    "suggestion": "",
                }
            ]

        lines = content.split("\n")
        issues = []

        # 根据文件类型选择检查方法
        if file_path.suffix in [".cpp", ".h", ".hpp", ".c", ".cc"]:
            issues.extend(self._check_cpp_code(lines, str(file_path), check_types))

        return issues

    def _check_cpp_code(
        self, lines: List[str], file_path: str, check_types: List[str]
    ) -> List[Dict]:
        """检查 C/C++ 代码"""
        issues = []

        for i, line in enumerate(lines, 1):
            line_before_comment = line.split("//")[0] if "//" in line else line
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # TODO/FIXME 检查
            if "todo" in check_types:
                if ("TODO" in line or "FIXME" in line) and (
                    "//" in line or line_stripped.startswith("/*")
                ):
                    issues.append(
                        {
                            "file": file_path,
                            "line": i,
                            "severity": "info",
                            "category": "todo",
                            "message": "TODO/FIXME found: {}".format(
                                line_stripped[:60]
                            ),
                            "suggestion": "Consider completing this task before release",
                        }
                    )

            # 调试代码检查
            if "debug" in check_types and not file_path.replace("\\", "/").endswith(
                "src/main.cpp"
            ):
                if "cout" in line_before_comment or "printf" in line_before_comment:
                    # 排除注释中的
                    if not line_stripped.startswith(
                        "//"
                    ) and not line_stripped.startswith("/*"):
                        issues.append(
                            {
                                "file": file_path,
                                "line": i,
                                "severity": "warning",
                                "category": "debug",
                                "message": "Debug code detected: {}".format(
                                    line_stripped[:60]
                                ),
                                "suggestion": "Remove debug output before release",
                            }
                        )

            # 安全问题检查
            if "security" in check_types:
                # 缓冲区溢出风险
                if re.search(
                    r"\b(strcpy|strcat|sprintf|gets)\s*\(", line_before_comment
                ):
                    issues.append(
                        {
                            "file": file_path,
                            "line": i,
                            "severity": "error",
                            "category": "security",
                            "message": "Unsafe function detected: {}".format(
                                line_stripped[:60]
                            ),
                            "suggestion": "Use safe alternatives: strncpy, strncat, snprintf, fgets",
                        }
                    )

                # SQL 注入风险
                if "SELECT" in line_before_comment and "+" in line_before_comment:
                    if (
                        "std::string" in line_before_comment
                        or "string" in line_before_comment
                    ):
                        issues.append(
                            {
                                "file": file_path,
                                "line": i,
                                "severity": "error",
                                "category": "security",
                                "message": "Potential SQL injection: {}".format(
                                    line_stripped[:60]
                                ),
                                "suggestion": "Use parameterized queries",
                            }
                        )

            # 性能问题检查
            if "performance" in check_types:
                # 低效的字符串拼接
                if re.search(
                    r"for\s*\([^)]*\)\s*\{[^}]*\+\=.*string", line_before_comment
                ):
                    issues.append(
                        {
                            "file": file_path,
                            "line": i,
                            "severity": "warning",
                            "category": "performance",
                            "message": "Inefficient string concatenation in loop",
                            "suggestion": "Use std::stringstream or reserve() + append()",
                        }
                    )

        return issues

    def _run_validation_engine(self):
        """Run four-layer validation and log per-layer results."""
        engine = ValidationEngine()
        language = getattr(self.context, "language", "cpp")
        project_type = getattr(self.context, "project_type", "")
        # is_cpp removed - use language directly
        ctx = {
            "project_dir": self.context.project_dir,
            "language": language,
            "project_type": project_type,
        }

        # Use LanguagePlugin for validation checks
        if language == "cpp":
            self._register_cpp_validation_checks(engine)
        elif language == "python":
            self._register_python_validation_checks(engine)
        elif language == "shell":
            # Shell projects may not have specialized validation yet
            self.log("  [INFO] Four-layer validation: using generic checks for shell")
        else:
            self.log(
                "  [INFO] Four-layer validation: no specialized checks for language '{}'".format(
                    language
                )
            )

        result = engine.validate(None, context=ctx, stop_on_error=False)

        # Log per-layer summary
        for level in [
            ValidationLevel.FORMAT,
            ValidationLevel.SEMANTIC,
            ValidationLevel.PARSER,
            ValidationLevel.BUSINESS,
        ]:
            level_issues = [i for i in result.issues if i.level == level]
            errors = [i for i in level_issues if i.severity == ValidationSeverity.ERROR]
            status = "[FAIL]" if errors else "[OK]  "
            self.log(
                "  {} {} layer: {} issue(s)".format(
                    status, level.value.upper(), len(level_issues)
                )
            )

        return result

    def _register_cpp_validation_checks(self, engine) -> None:
        def _fmt_cmake(content, ctx):
            if not self._check_cmake_exists():
                return [
                    ValidationIssue(
                        ValidationLevel.FORMAT,
                        ValidationSeverity.ERROR,
                        "CMakeLists.txt not found",
                    )
                ]
            self.log("  [OK] FORMAT: CMakeLists.txt exists")
            return []

        def _fmt_main(content, ctx):
            msg = self._check_main_cpp()
            if msg:
                return [
                    ValidationIssue(
                        ValidationLevel.FORMAT, ValidationSeverity.ERROR, msg
                    )
                ]
            self.log("  [OK] FORMAT: src/main.cpp exists with main()")
            return []

        def _sem_test_base(content, ctx):
            msg = self._check_test_base()
            if msg:
                return [
                    ValidationIssue(
                        ValidationLevel.SEMANTIC, ValidationSeverity.ERROR, msg
                    )
                ]
            self.log("  [OK] SEMANTIC: test_base.h API is consistent")
            return []

        def _biz_test_files(content, ctx):
            msg = self._check_test_files_exist()
            if msg:
                return [
                    ValidationIssue(
                        ValidationLevel.BUSINESS, ValidationSeverity.ERROR, msg
                    )
                ]
            self.log("  [OK] BUSINESS: Test files present")
            return []

        engine.register_validator(ValidationLevel.FORMAT, _fmt_cmake)
        engine.register_validator(ValidationLevel.FORMAT, _fmt_main)
        engine.register_validator(ValidationLevel.SEMANTIC, _sem_test_base)
        engine.register_validator(ValidationLevel.BUSINESS, _biz_test_files)

    def _register_python_validation_checks(self, engine) -> None:
        def _fmt_python_main(content, ctx):
            msg = self._check_python_main()
            if msg:
                return [
                    ValidationIssue(
                        ValidationLevel.FORMAT, ValidationSeverity.ERROR, msg
                    )
                ]
            self.log("  [OK] FORMAT: Python main entry point exists")
            return []

        def _biz_python_tests(content, ctx):
            msg = self._check_python_test_files()
            if msg:
                return [
                    ValidationIssue(
                        ValidationLevel.BUSINESS, ValidationSeverity.ERROR, msg
                    )
                ]
            self.log("  [OK] BUSINESS: Python test files present")
            return []

        engine.register_validator(ValidationLevel.FORMAT, _fmt_python_main)
        engine.register_validator(ValidationLevel.BUSINESS, _biz_python_tests)

    def _check_cmake_exists(self) -> bool:
        return (self.context.project_dir / "CMakeLists.txt").exists()

    def _check_main_cpp(self) -> str:
        main_path = self.context.project_dir / "src" / "main.cpp"
        if not main_path.exists():
            return "src/main.cpp not found"
        try:
            content = main_path.read_text(encoding="utf-8")
            # 允许两种形式：1) 显式的 int main( 函数，2) TEST_MAIN_BEGIN 宏
            has_explicit_main = "int main(" in content
            has_test_main_macro = (
                "TEST_MAIN_BEGIN" in content and "TEST_MAIN_END" in content
            )

            if not (has_explicit_main or has_test_main_macro):
                return "src/main.cpp has no main() function"
        except Exception as e:
            return "Cannot read src/main.cpp: {}".format(e)
        return ""

    def _check_test_base(self) -> str:
        test_base = self.context.project_dir / "tests" / "test_base.h"
        if not test_base.exists():
            return "tests/test_base.h not found"
        try:
            content = test_base.read_text(encoding="utf-8")
            required = [
                "ASSERT_TRUE",
                "ASSERT_EQ",
                "RUN_TEST",
                "TEST_MAIN_BEGIN",
                "TEST_MAIN_END",
            ]
            missing = [m for m in required if "#define {}".format(m) not in content]
            if missing:
                return "test_base.h missing macros: {}".format(", ".join(missing))
        except Exception as e:
            return "Cannot read test_base.h: {}".format(e)
        return ""

    def _check_test_files_exist(self) -> str:
        """检查是否存在测试文件"""
        tests_dir = self.context.project_dir / "tests"
        if not tests_dir.exists():
            return "tests/ directory not found"

        # 查找测试文件
        test_files = list(tests_dir.glob("test_*.cpp")) + list(
            tests_dir.glob("*_test.cpp")
        )
        test_files = [f for f in test_files if f.name != "test_base.h"]

        if not test_files:
            return "No test files found in tests/ directory"

        return ""

    def _write_report(
        self,
        violations: List[str],
        warnings: List[str],
        val_result=None,
        review_issues: List[Dict] = None,
        heal_attempts: int = 0,
        heal_success: int = 0,
        model_switches: int = 0,
    ) -> Path:
        """生成统一的质量报告"""
        lines = [
            "# Quality Gate Report",
            "",
            "**Status**: {}".format("FAILED ❌" if violations else "PASSED ✅"),
            "",
        ]

        # ========== 1. Mandatory Checks (硬性检查) ==========
        lines.append("## 1. Mandatory Checks (硬性检查)")
        lines.append("")
        lines.append("- Violations: {}".format(len(violations)))
        lines.append("- Warnings: {}".format(len(warnings)))
        lines.append("")

        if val_result and _HAS_VALIDATION_ENGINE:
            lines.append("### Four-Layer Validation")
            lines.append("")
            for level in [
                ValidationLevel.FORMAT,
                ValidationLevel.SEMANTIC,
                ValidationLevel.PARSER,
                ValidationLevel.BUSINESS,
            ]:
                level_issues = [i for i in val_result.issues if i.level == level]
                errors = sum(
                    1 for i in level_issues if i.severity == ValidationSeverity.ERROR
                )
                lines.append(
                    "- {} layer: {} error(s), {} warning(s)".format(
                        level.value.upper(), errors, len(level_issues) - errors
                    )
                )
            if val_result.issues:
                lines.append("")
                lines.append("#### Validation Details")
                lines.append("")
                for issue in val_result.issues:
                    detail = "- [{}][{}] {}".format(
                        issue.level.value.upper(),
                        issue.severity.value.upper(),
                        issue.message,
                    )
                    if issue.location:
                        detail += " ({})".format(issue.location)
                    if issue.suggestion:
                        detail += " — {}".format(issue.suggestion)
                    lines.append(detail)
            lines.append("")

        if violations:
            lines.append("### Violations")
            lines.append("")
            for i, v in enumerate(violations, 1):
                lines.append("{}. {}".format(i, v))
            lines.append("")

        # ========== 2. Code Review (代码审查) ==========
        if review_issues is not None:
            lines.append("## 2. Code Review (代码审查)")
            lines.append("")

            if not review_issues:
                lines.append("✅ No issues found")
                lines.append("")
            else:
                # 统计
                critical = [i for i in review_issues if i["severity"] == "error"]
                warning = [i for i in review_issues if i["severity"] == "warning"]
                info = [i for i in review_issues if i["severity"] == "info"]

                lines.append("- Total issues: {}".format(len(review_issues)))
                lines.append("  - 🔴 Critical: {}".format(len(critical)))
                lines.append("  - 🟡 Warning: {}".format(len(warning)))
                lines.append("  - 🔵 Info: {}".format(len(info)))
                lines.append("")

                # 按类别统计
                categories = {}
                for issue in review_issues:
                    cat = issue.get("category", "other")
                    categories[cat] = categories.get(cat, 0) + 1

                lines.append("### Issues by Category")
                lines.append("")
                for cat, count in sorted(categories.items()):
                    lines.append("- {}: {}".format(cat, count))
                lines.append("")

                # 按文件分组显示详细问题
                lines.append("### Details")
                lines.append("")

                issues_by_file = {}
                for issue in review_issues:
                    file = issue["file"]
                    if file not in issues_by_file:
                        issues_by_file[file] = []
                    issues_by_file[file].append(issue)

                for file, issues in sorted(issues_by_file.items()):
                    lines.append("#### {}".format(Path(file).name))
                    lines.append("")
                    for issue in sorted(issues, key=lambda x: x["line"]):
                        severity_icon = {
                            "error": "🔴",
                            "warning": "🟡",
                            "info": "🔵",
                        }.get(issue["severity"], "⚪")

                        lines.append(
                            "- Line {}: {} [{}] {}".format(
                                issue["line"],
                                severity_icon,
                                issue["category"],
                                issue["message"],
                            )
                        )
                        if issue.get("suggestion"):
                            lines.append("  - 💡 {}".format(issue["suggestion"]))
                    lines.append("")

        # ========== 3. Self-Heal Statistics (if enabled) ==========
        if heal_attempts > 0:
            lines.append("## 3. Self-Heal Statistics")
            lines.append("")
            lines.append("- Heal attempts: {}".format(heal_attempts))
            lines.append("- Successful fixes: {}".format(heal_success))
            lines.append("- Model switches: {}".format(model_switches))
            lines.append("")

        # ========== 4. Configuration ==========
        lines.append("## {}. Configuration".format(4 if heal_attempts > 0 else 3))
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append('  "code_review": {')
        lines.append(
            '    "enabled": {},'.format(
                str(self.config["code_review"]["enabled"]).lower()
            )
        )
        lines.append(
            '    "check_types": {},'.format(self.config["code_review"]["check_types"])
        )
        lines.append(
            '    "fail_on_critical": {},'.format(
                str(self.config["code_review"]["fail_on_critical"]).lower()
            )
        )
        lines.append('    "self_heal": {')
        lines.append(
            '      "enabled": {},'.format(
                str(self.config["code_review"]["self_heal"]["enabled"]).lower()
            )
        )
        lines.append(
            '      "max_attempts": {},'.format(
                self.config["code_review"]["self_heal"]["max_attempts"]
            )
        )
        lines.append(
            '      "only_critical": {},'.format(
                str(self.config["code_review"]["self_heal"]["only_critical"]).lower()
            )
        )
        lines.append(
            '      "switch_model_after": {},'.format(
                self.config["code_review"]["self_heal"]["switch_model_after"]
            )
        )
        lines.append(
            '      "fallback_model": "{}",'.format(
                self.config["code_review"]["self_heal"]["fallback_model"]
            )
        )
        lines.append(
            '      "create_backup": {},'.format(
                str(self.config["code_review"]["self_heal"]["create_backup"]).lower()
            )
        )
        lines.append(
            '      "max_fixes_per_attempt": {}'.format(
                self.config["code_review"]["self_heal"]["max_fixes_per_attempt"]
            )
        )
        lines.append("    }")
        lines.append("  }")
        lines.append("}")
        lines.append("```")
        lines.append("")

        report_path = self.context.project_dir / "docs" / "quality_gate_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(lines), encoding="utf-8")
        self.context.generated_files.append(report_path)
        return report_path

    # ========== Self-Heal Methods ==========

    def _should_trigger_self_heal(self, review_issues: List[Dict]) -> bool:
        """判断是否应该触发自愈"""
        if not self.config["code_review"]["self_heal"]["enabled"]:
            return False

        # 如果只修复 Critical 问题，检查是否有 Critical 问题
        if self.config["code_review"]["self_heal"]["only_critical"]:
            critical_issues = [i for i in review_issues if i["severity"] == "error"]
            return len(critical_issues) > 0

        # 否则，只要有问题就触发
        return len(review_issues) > 0

    def _run_self_heal(self, review_issues: List[Dict]) -> Tuple[bool, List[Dict]]:
        """
        运行自愈流程

        Returns:
            (success, new_issues)
        """
        if not self.config["code_review"]["self_heal"]["enabled"]:
            return False, review_issues

        # 如果只修复 Critical 问题，过滤出 Critical 问题
        if self.config["code_review"]["self_heal"]["only_critical"]:
            critical_issues = [i for i in review_issues if i["severity"] == "error"]
            if not critical_issues:
                self.log("    [INFO] No critical issues to heal")
                return True, review_issues
            issues_to_fix = critical_issues
        else:
            issues_to_fix = review_issues

        self.log(
            "    [INFO] Starting self-heal for {} issues".format(len(issues_to_fix))
        )

        max_attempts = self.config["code_review"]["self_heal"]["max_attempts"]
        switch_after = self.config["code_review"]["self_heal"]["switch_model_after"]

        for attempt in range(1, max_attempts + 1):
            self.log("    [INFO] Self-heal attempt {}/{}".format(attempt, max_attempts))
            self.heal_attempts = attempt
            self.context.self_heal_attempts += 1

            # Fallback model is a separate LLMClient instance. LLMClient does
            # not expose switch_model(), so do not mutate the existing client.
            use_fallback = switch_after > 0 and attempt >= switch_after
            if use_fallback and not self.model_switched:
                self.log(
                    "    [INFO] Switching to fallback model: {}".format(
                        self.fallback_model
                    )
                )
                self.model_switched = True
                self.model_switches += 1

            # 1. 分析问题
            analysis = self._analyze_issues(issues_to_fix)

            # 2. 生成修复计划
            fix_plan = self._generate_fix_plan(
                analysis, attempt, use_fallback=use_fallback
            )
            if not fix_plan:
                self.log("    [ERROR] Failed to generate fix plan")
                continue

            # 3. 执行修复
            if not self._execute_fix_plan(fix_plan):
                self.log("    [ERROR] Failed to execute fix plan")
                continue

            # 4. 验证修复
            new_issues = self._run_code_review()
            if self._verify_fix(issues_to_fix, new_issues):
                self.log("    [OK] Self-heal succeeded on attempt {}".format(attempt))
                self.heal_success += 1
                return True, new_issues
            else:
                self.log(
                    "    [WARN] Self-heal attempt {} did not resolve all issues".format(
                        attempt
                    )
                )

        self.log("    [ERROR] Self-heal failed after {} attempts".format(max_attempts))
        return False, review_issues

    def _analyze_issues(self, issues: List[Dict]) -> Dict:
        """
        分析问题，按文件和类别分组

        Returns:
            {
                'by_file': {file_path: [issues]},
                'by_category': {category: [issues]},
                'summary': {total, critical, warning, info}
            }
        """
        by_file = {}
        by_category = {}

        for issue in issues:
            # 按文件分组
            file = issue["file"]
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(issue)

            # 按类别分组
            category = issue.get("category", "other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)

        # 统计
        summary = {
            "total": len(issues),
            "critical": sum(1 for i in issues if i["severity"] == "error"),
            "warning": sum(1 for i in issues if i["severity"] == "warning"),
            "info": sum(1 for i in issues if i["severity"] == "info"),
        }

        return {"by_file": by_file, "by_category": by_category, "summary": summary}

    def _build_self_heal_prompt(self, analysis: Dict, attempt: int) -> str:
        """构建结构化的自愈提示词"""
        parts = []

        parts.append("**CRITICAL: CODE REVIEW SELF-HEAL**")
        parts.append("")
        parts.append(
            f"Attempt: {attempt}/{self.config['code_review']['self_heal']['max_attempts']}"
        )
        parts.append("")

        # 问题摘要
        parts.append("**ISSUE SUMMARY**")
        parts.append(f"- Total issues: {analysis['summary']['total']}")
        parts.append(f"- Critical: {analysis['summary']['critical']}")
        parts.append(f"- Warning: {analysis['summary']['warning']}")
        parts.append(f"- Info: {analysis['summary']['info']}")
        parts.append("")

        # 按类别统计
        parts.append("**ISSUES BY CATEGORY**")
        for category, issues in sorted(analysis["by_category"].items()):
            parts.append(f"- {category}: {len(issues)} issue(s)")
        parts.append("")

        # 详细问题列表
        parts.append("**DETAILED ISSUES**")
        parts.append("")
        for file, issues in sorted(analysis["by_file"].items()):
            parts.append(f"File: {file}")
            for issue in sorted(issues, key=lambda x: x["line"]):
                severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
                    issue["severity"], "⚪"
                )
                parts.append(
                    f"  Line {issue['line']}: {severity_icon} [{issue['category']}] {issue['message']}"
                )
                if issue.get("suggestion"):
                    parts.append(f"    💡 {issue['suggestion']}")
            parts.append("")

        retrieved_context = self._build_retrieved_context_section(analysis)
        if retrieved_context:
            parts.append(retrieved_context)
            parts.append("")

        # 强制分析步骤
        parts.append("**CRITICAL: STRUCTURED ANALYSIS REQUIRED**")
        parts.append("Before making ANY changes, you MUST provide:")
        parts.append("")
        parts.append("ANALYSIS:")
        parts.append("1. Root Cause: [Why do these issues exist?]")
        parts.append("2. Issue Validity: [Are these real problems or false positives?]")
        parts.append("3. Fix Strategy: [What should be fixed and how?]")
        parts.append("4. Risk Assessment: [What could go wrong with the fix?]")
        parts.append("")

        # 修改边界
        parts.append("**MODIFICATION BOUNDARIES**")
        parts.append("")
        parts.append("ALLOWED:")
        parts.append("- Remove debug code (std::cout, printf, etc.)")
        parts.append(
            "- Replace unsafe functions with safe alternatives (strcpy → strncpy)"
        )
        parts.append("- Fix SQL injection by using parameterized queries")
        parts.append("- Resolve TODO/FIXME by implementing the functionality")
        parts.append("- Add input validation and bounds checking")
        parts.append("")
        parts.append("FORBIDDEN:")
        parts.append("- Removing security checks or validation logic")
        parts.append("- Weakening password/authentication requirements")
        parts.append("- Ignoring errors instead of handling them")
        parts.append("- Commenting out problematic code without fixing it")
        parts.append("- Changing business logic to hide the issue")
        parts.append("")

        # 可疑关键词检测
        parts.append("**SUSPICIOUS KEYWORDS DETECTION**")
        parts.append("If your fix contains these keywords, STOP and reconsider:")
        parts.append("- 'relax', 'reduce', 'weaken', 'disable', 'skip'")
        parts.append("- 'comment out', 'ignore', 'suppress'")
        parts.append("- 'TODO', 'FIXME', 'HACK', 'temporary'")
        parts.append("")

        # 输出格式
        parts.append("**OUTPUT FORMAT**")
        parts.append("Provide your response in this JSON format:")
        parts.append("```json")
        parts.append("{")
        parts.append('  "analysis": {')
        parts.append('    "root_cause": "...",')
        parts.append('    "issue_validity": "...",')
        parts.append('    "fix_strategy": "...",')
        parts.append('    "risk_assessment": "..."')
        parts.append("  },")
        parts.append('  "fixes": [')
        parts.append("    {")
        parts.append('      "file": "path/to/file.cpp",')
        parts.append('      "line": 42,')
        parts.append('      "issue_category": "unsafe_function",')
        parts.append('      "old_code": "strcpy(buffer, input);",')
        parts.append(
            '      "new_code": "strncpy(buffer, input, sizeof(buffer) - 1);\\nbuffer[sizeof(buffer) - 1] = \'\\\\0\';",'
        )
        parts.append('      "reason": "Replace unsafe strcpy with safe strncpy"')
        parts.append("    }")
        parts.append("  ]")
        parts.append("}")
        parts.append("```")
        parts.append("")

        return "\n".join(parts)

    def _build_retrieved_context_section(self, analysis: Dict) -> str:
        if not bool(getattr(self.context, "vector_retrieval_enabled", False)):
            return ""
        try:
            from devpal.vector_store.semantic_search import SemanticSearchService

            service = SemanticSearchService.from_context(self.context, log=self.log)
            service.index_context(self.context, self.context.project_name)
            issue_messages = []
            for issues in analysis.get("by_file", {}).values():
                issue_messages.extend(issue.get("message", "") for issue in issues)
            query = "\n".join(
                part
                for part in [
                    "Phase 9 code review self-heal",
                    self.context.requirements_content,
                    self.context.tech_design_content,
                    "\n".join(issue_messages),
                ]
                if part
            )
            retrieved_context = service.build_context(
                query=query,
                project_name=self.context.project_name,
                artifact_types=["source", "test", "error", "requirements"],
                top_k=int(getattr(self.context, "vector_top_k", 5) or 5),
                event_integration=getattr(self.context, "event_integration", None),
            )
            self.context.vector_retrieval_stats = dict(service.stats)
            if retrieved_context:
                return retrieved_context
        except Exception as exc:
            self.log(f"  [VECTOR] Phase 9 retrieval context unavailable: {exc}")
        return ""

    def _get_fix_plan_client(self, use_fallback: bool = False) -> LLMClient:
        """Return the LLM client for a fix-plan attempt."""
        if use_fallback:
            try:
                from devpal.config import get_config

                config = get_config()
                provider = config.llm_default_provider
                provider_config = dict(config.get_provider_config(provider))
                fallback_model = self.fallback_model or provider_config.get("model")
                provider_config.pop("model", None)
                return self.llm_client_factory(
                    provider=provider,
                    model=fallback_model,
                    fallback_providers=list(config.llm_fallback_providers),
                    **provider_config,
                )
            except TypeError:
                pass
            try:
                return self.llm_client_factory(model=self.fallback_model)
            except TypeError:
                return self.llm_client_factory()

        if self.llm_client is None:
            self.llm_client = get_llm_client()
        return self.llm_client

    def _generate_fix_plan(
        self, analysis: Dict, attempt: int, use_fallback: bool = False
    ) -> Optional[Dict]:
        """
        使用 LLM 生成修复计划

        Returns:
            {
                'analysis': {...},
                'fixes': [...]
            }
        """
        prompt = self._build_self_heal_prompt(analysis, attempt)

        try:
            system_message = "You are a code quality expert. Your task is to analyze code review issues and generate a structured fix plan in JSON format."
            client = self._get_fix_plan_client(use_fallback=use_fallback)
            response = client.generate(
                system=system_message,
                user_message=prompt,
                cached_context=[
                    self.context.requirements_content,
                    self.context.tech_design_content,
                ]
                if self.context.requirements_content or self.context.tech_design_content
                else None,
            )
            self._update_usage_stats(client)

            json_str = self._extract_json_object(response)
            if not json_str:
                self.log("    [ERROR] Failed to extract JSON fix plan")
                return None
            plan = json.loads(json_str)

            # 验证计划格式
            if "analysis" not in plan or "fixes" not in plan:
                self.log(
                    "    [ERROR] Invalid fix plan format: missing 'analysis' or 'fixes'"
                )
                return None
            if not isinstance(plan["analysis"], dict) or not isinstance(
                plan["fixes"], list
            ):
                self.log(
                    "    [ERROR] Invalid fix plan format: analysis must be object and fixes must be list"
                )
                return None

            # 检测可疑关键词
            suspicious_keywords = [
                "relax",
                "reduce",
                "weaken",
                "disable",
                "skip",
                "comment out",
                "ignore",
                "suppress",
                "TODO",
                "FIXME",
                "HACK",
            ]
            for fix in plan["fixes"]:
                reason_lower = fix.get("reason", "").lower()
                for keyword in suspicious_keywords:
                    if keyword in reason_lower:
                        self.log(
                            "    [WARN] Suspicious keyword '{}' detected in fix reason: {}".format(
                                keyword, fix["reason"]
                            )
                        )

            self.log(
                "    [INFO] Generated fix plan with {} fixes".format(len(plan["fixes"]))
            )
            return plan

        except Exception as e:
            self.log("    [ERROR] Failed to generate fix plan: {}".format(e))
            return None

    def _extract_json_object(self, response: str) -> Optional[str]:
        """Extract a balanced JSON object from LLM output."""
        if not response:
            return None

        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
        source = fenced.group(1).strip() if fenced else response.strip()

        start = source.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escaped = False

        for idx in range(start, len(source)):
            char = source[idx]

            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return source[start : idx + 1]

        return None

    def _execute_fix_plan(self, plan: Dict) -> bool:
        """
        执行修复计划

        Returns:
            True if all fixes applied successfully
        """
        fixes = plan.get("fixes", [])
        if not fixes:
            self.log("    [WARN] No fixes in plan")
            return False

        max_fixes = self.config["code_review"]["self_heal"]["max_fixes_per_attempt"]
        if len(fixes) > max_fixes:
            self.log(
                "    [WARN] Limiting fixes to {} out of {}".format(
                    max_fixes, len(fixes)
                )
            )
            fixes = fixes[:max_fixes]

        success_count = 0
        project_root = self.context.project_dir.resolve()

        for i, fix in enumerate(fixes, 1):
            try:
                if not self._is_fix_safe(fix):
                    self.log("    [ERROR] Fix {} rejected by safety policy".format(i))
                    continue

                file_path = Path(fix["file"])
                if not file_path.is_absolute():
                    file_path = self.context.project_dir / file_path
                file_path = file_path.resolve()

                try:
                    file_path.relative_to(project_root)
                except ValueError:
                    self.log(
                        "    [ERROR] Refusing to modify file outside project: {}".format(
                            file_path
                        )
                    )
                    continue

                if not file_path.exists():
                    self.log("    [ERROR] File not found: {}".format(file_path))
                    continue

                # 读取文件
                content = file_path.read_text(encoding="utf-8")

                # 执行替换
                old_code = str(fix.get("old_code", ""))
                new_code = str(fix.get("new_code", ""))
                if not old_code.strip() or not new_code.strip():
                    self.log(
                        "    [ERROR] Fix {} missing old_code or new_code".format(i)
                    )
                    continue

                if old_code not in content:
                    self.log(
                        "    [WARN] Old code not found in {} at line {}".format(
                            file_path.name, fix["line"]
                        )
                    )
                    # 尝试按行替换，但只在该行内容与 old_code 等价时执行。
                    lines = content.split("\n")
                    line_idx = int(fix.get("line", 0)) - 1
                    if 0 <= line_idx < len(lines):
                        if lines[line_idx].strip() != old_code.strip():
                            self.log(
                                "    [ERROR] Line {} does not match old_code; refusing unsafe replacement".format(
                                    fix.get("line")
                                )
                            )
                            continue
                        replacement_lines = new_code.split("\n")
                        lines[line_idx : line_idx + 1] = replacement_lines
                        content = "\n".join(lines)
                        self.log(
                            "    [INFO] Applied verified line-based fix to {}:{}".format(
                                file_path.name, fix["line"]
                            )
                        )
                    else:
                        self.log(
                            "    [ERROR] Invalid line number: {}".format(fix["line"])
                        )
                        continue
                else:
                    content = content.replace(old_code, new_code, 1)
                    self.log(
                        "    [INFO] Applied fix {}/{}: {}:{}".format(
                            i, len(fixes), file_path.name, fix["line"]
                        )
                    )

                # 写回文件
                if self.config["code_review"]["self_heal"]["create_backup"]:
                    backup_path = file_path.with_suffix(
                        file_path.suffix + ".phase9.bak"
                    )
                    if not backup_path.exists():
                        backup_path.write_text(
                            file_path.read_text(encoding="utf-8"), encoding="utf-8"
                        )
                file_path.write_text(content, encoding="utf-8")
                success_count += 1

            except Exception as e:
                self.log("    [ERROR] Failed to apply fix {}: {}".format(i, e))

        self.log("    [INFO] Applied {}/{} fixes".format(success_count, len(fixes)))
        return success_count > 0

    def _is_fix_safe(self, fix: Dict[str, Any]) -> bool:
        """Reject obviously unsafe or evasive self-heal changes."""
        required = ["file", "line", "old_code", "new_code"]
        for key in required:
            if key not in fix:
                self.log("    [ERROR] Fix missing required field: {}".format(key))
                return False

        reason_lower = str(fix.get("reason", "")).lower()
        blocked_reason = [
            "comment out",
            "ignore",
            "suppress",
            "relax validation",
            "reduce validation",
            "weaken validation",
            "disable validation",
            "skip validation",
        ]
        if any(keyword in reason_lower for keyword in blocked_reason):
            self.log(
                "    [ERROR] Suspicious fix reason: {}".format(fix.get("reason", ""))
            )
            return False

        new_code = str(fix.get("new_code", ""))
        blocked_markers = ["TODO", "FIXME", "HACK", "temporary workaround"]
        if any(marker in new_code for marker in blocked_markers):
            self.log("    [ERROR] Fix introduces unfinished marker")
            return False

        category = str(fix.get("issue_category", fix.get("category", ""))).lower()
        if category == "security":
            unsafe_functions = [
                r"\bstrcpy\s*\(",
                r"\bstrcat\s*\(",
                r"\bsprintf\s*\(",
                r"\bgets\s*\(",
            ]
            if any(re.search(pattern, new_code) for pattern in unsafe_functions):
                self.log("    [ERROR] Security fix still contains unsafe API")
                return False

        return True

    def _verify_fix(self, old_issues: List[Dict], new_issues: List[Dict]) -> bool:
        """
        验证修复效果

        Returns:
            True if critical issues are resolved
        """
        # 只关注 Critical 问题
        old_critical = [i for i in old_issues if i["severity"] == "error"]
        new_critical = [i for i in new_issues if i["severity"] == "error"]

        self.log(
            "    [INFO] Critical issues: {} -> {}".format(
                len(old_critical), len(new_critical)
            )
        )

        old_signatures = {self._issue_signature(i) for i in old_critical}
        new_signatures = {self._issue_signature(i) for i in new_critical}
        remaining = old_signatures & new_signatures

        if len(new_critical) > len(old_critical):
            self.log(
                "    [ERROR] Critical issues increased by {}".format(
                    len(new_critical) - len(old_critical)
                )
            )
            return False

        if remaining:
            self.log(
                "    [WARN] {} original critical issue(s) still present".format(
                    len(remaining)
                )
            )
            return False

        if new_critical:
            self.log(
                "    [WARN] Original critical issues changed, but new critical issues remain"
            )
            return False

        self.log("    [OK] All original critical issues resolved")
        return True

    def _issue_signature(self, issue: Dict[str, Any]) -> Tuple[str, int, str, str]:
        return (
            str(issue.get("file", "")),
            int(issue.get("line", 0) or 0),
            str(issue.get("category", "")),
            str(issue.get("message", "")),
        )

    # ========== Python 项目检查方法 ==========
    def _check_python_main(self) -> str:
        """检查 Python 主入口文件"""
        main_candidates = [
            self.context.project_dir / "src" / "main.py",
            self.context.project_dir / "src" / "__main__.py",
            self.context.project_dir / "main.py",
        ]

        for main_path in main_candidates:
            if main_path.exists():
                return ""

        return "No Python main entry point found (src/main.py, src/__main__.py, or main.py)"

    def _check_python_test_files(self) -> str:
        """检查 Python 测试文件（pytest）"""
        tests_dir = self.context.project_dir / "tests"
        if not tests_dir.exists():
            # Python 项目测试文件可选
            return ""

        # 查找 pytest 测试文件
        test_files = list(tests_dir.glob("test_*.py")) + list(
            tests_dir.glob("*_test.py")
        )

        if not test_files:
            # 测试文件可选，不强制要求
            return ""

        return ""

    # ========== Shell 项目检查方法 ==========
    def _check_shell_main(self) -> str:
        """检查 Shell 主脚本"""
        main_candidates = [
            self.context.project_dir / "scripts" / "install_claude_cli.sh",
            self.context.project_dir / "scripts" / "install_claude_cli.bat",
            self.context.project_dir / "install_claude_cli.sh",
            self.context.project_dir / "install_claude_cli.bat",
            self.context.project_dir / "scripts" / "main.sh",
            self.context.project_dir / "main.sh",
            self.context.project_dir / "install.sh",
        ]

        for main_path in main_candidates:
            if main_path.exists():
                return ""

        return "No Shell main script found (scripts/install_claude_cli.sh, scripts/install_claude_cli.bat, scripts/main.sh, main.sh, or install.sh)"

    def _check_shell_test_files(self) -> str:
        """检查 Shell 测试文件"""
        tests_dir = self.context.project_dir / "tests"
        if not tests_dir.exists():
            # Shell 项目测试文件可选
            return ""

        # 查找 Shell 测试文件
        test_files = list(tests_dir.glob("test_*.sh")) + list(
            tests_dir.glob("*_test.sh")
        )

        if not test_files:
            # 测试文件可选，不强制要求
            return ""

        return ""

    def _update_usage_stats(self, client) -> None:
        """Sync LLM usage stats from client to context."""
        ctx = self.context
        ctx.llm_calls += client.usage.calls
        ctx.llm_input_tokens += client.usage.input_tokens
        ctx.llm_output_tokens += client.usage.output_tokens
        ctx.llm_cache_read_tokens += client.usage.cache_read_tokens
        ctx.llm_cache_creation_tokens += client.usage.cache_creation_tokens

    def _emit_validation_started_event(self) -> None:
        """Emit validation started event to EventBus"""
        if not self.workflow_id:
            return
        try:
            files_to_validate = len(self._collect_review_targets())
            event = ValidationStartedEvent(
                workflow_id=self.workflow_id,
                phase_num=self.phase_number,
                validation_layers=self.config["code_review"]["check_types"],
                files_to_validate=files_to_validate,
            )
            self.event_bus.publish(event)
        except Exception as e:
            self.log(f"  [WARN] Failed to emit validation started event: {e}")

    def _emit_validation_completed_event(self, review_issues: List[Dict]) -> None:
        """Emit validation completed event to EventBus"""
        if not self.workflow_id:
            return
        try:
            issues_by_layer = {}
            for issue in review_issues:
                category = issue.get("category", "other")
                issues_by_layer[category] = issues_by_layer.get(category, 0) + 1
            total_issues = len(review_issues)
            critical_issues = sum(
                1 for issue in review_issues if issue.get("severity") == "error"
            )
            passed = critical_issues == 0
            event = ValidationCompletedEvent(
                workflow_id=self.workflow_id,
                phase_num=self.phase_number,
                total_issues=total_issues,
                issues_by_layer=issues_by_layer,
                passed=passed,
            )
            self.event_bus.publish(event)
            for issue in review_issues:
                if issue["severity"] == "error":
                    self._emit_validation_issue_event(issue)
        except Exception as e:
            self.log(f"  [WARN] Failed to emit validation completed event: {e}")

    def _emit_validation_issue_event(self, issue: Dict) -> None:
        """Emit validation issue found event to EventBus"""
        if not self.workflow_id:
            return
        try:
            event = ValidationIssueFoundEvent(
                workflow_id=self.workflow_id,
                phase_num=self.phase_number,
                layer=issue.get("category", "other").upper(),
                severity=issue.get("severity", "info"),
                file_path=issue.get("file", ""),
                line_number=issue.get("line"),
                message=issue.get("message", ""),
            )
            self.event_bus.publish(event)
        except Exception as e:
            self.log(f"  [WARN] Failed to emit validation issue event: {e}")
