# -*- coding: utf-8 -*-
"""
OpenSpec 完整工作流入口

使用 OpenSpecWorkflowExecutor 执行完整的 11 阶段流程。

Prerequisites:
  1. pip install anthropic pyyaml
  2. Set env ANTHROPIC_API_KEY (or ANTHROPIC_AUTH_TOKEN)
  3. A requirements file under requirements/*.md
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from devpal.core.openspec_executor import OpenSpecRunOptions, OpenSpecWorkflowExecutor
from devpal.core.schema.performance_analyzer import PerformanceAnalyzer
from devpal.core.schema.progress_monitor import ProgressMonitor
from devpal.tools.registry import registry as tool_registry


# --------------------------------------
# P2.3: Environment variable config support
# ---------------------------------------------

def _apply_env_overrides() -> None:
    """Apply environment variable overrides to config.yaml values at runtime."""
    config_path = ROOT / "config" / "config.yaml"
    if not config_path.exists():
        return
    try:
        import yaml
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        changed = False
        anthropic = config.setdefault("anthropic", {})

        for env_key, cfg_key in [
            ("ANTHROPIC_API_KEY", "api_key"),
            ("ANTHROPIC_AUTH_TOKEN", "auth_token"),
            ("OPENSPEC_MODEL", "model"),
    ]:
            val = os.environ.get(env_key)
        if val:
                anthropic[cfg_key] = val
                changed = True

                timeout_val = os.environ.get("OPENSPEC_TIMEOUT")
        if timeout_val:
            try:
              config["timeout"] = int(timeout_val)
              changed = True
            except ValueError:
                pass

        if changed:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True)
    except Exception:
        pass  # non-fatal


# ------------------------------------------------------
# P2.2: Health check
# ------------------------------------------------

def _run_health_check() -> int:
    """Check system prerequisites and print a status report."""
    print("OpenSpec Health Check")
    print("=" * 50)
    ok = True

    # API key
    has_key = bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )
    _check("API key configured", has_key)
    if not has_key:
        ok = False

    # CMake
    cmake = shutil.which("cmake")
    _check("CMake available", bool(cmake), cmake or "not found")

    # C++ compiler
    gpp = shutil.which("g++")
    cl = shutil.which("cl")
    has_compiler = bool(gpp or cl)
    _check("C++ compiler (g++ or cl)", has_compiler, gpp or cl or "not found")

    # Python deps
    for pkg in ["anthropic", "yaml"]:
        try:
            __import__(pkg)
            _check(f"Python package: {pkg}", True)
        except ImportError:
            _check(f"Python package: {pkg}", False, "not installed")
            ok = False

    # Requirements dir
    req_dir = ROOT / "requirements"
    _check("requirements/ directory", req_dir.exists(), str(req_dir))

    print("=" * 50)
    if ok:
      print("[OK] All checks passed")
    else:
        print("[WARN] Some checks failed — see above")
    return 0 if ok else 1


def _check(label: str, passed: bool, detail: str = "") -> None:
    status = "[OK]  " if passed else "[FAIL]"
    suffix = f"  ({detail})" if detail else ""
    print(f"  {status} {label}{suffix}")


# ---------------------------------------------------
# P2.1: Dry-run
# ------------------------------------------------

def _run_dry_run(requirements_file: Path) -> int:
    """Print the execution plan without running anything."""
    from devpal.core.openspec_phases.enhanced_scheduler import PHASE_TIMEOUTS, CRITICAL_PHASES

    phase_names = {
        1: "Parse requirements",
        2: "Create project structure",
        3: "Generate tech design (AI)",
        4: "Generate core code (AI)",
        5: "Verify tests + generate test docs",
        6: "CMake config",
        7: "Test docs (merged into Phase 5)",
        8: "README",
        9: "Quality gate",
        10: "Compile and run tests",
        11: "Final report",
    }

    print("OpenSpec Dry-Run — Execution Plan")
    print("=" * 60)
    print(f"  Requirements: {requirements_file}")
    print()
    print(f"  {'Phase':<6} {'Name':<38} {'Timeout':>8}  {'Critical'}")
    print(f"  {'-'*6} {'-'*38} {'-'*8}  {'-'*8}")
    for num in range(1, 12):
        name = phase_names.get(num, "")
        timeout = PHASE_TIMEOUTS.get(num, 30)
        critical = "YES" if num in CRITICAL_PHASES else ""
        print(f"  {num:<6} {name:<38} {timeout:>6}s  {critical}")
    print()
    print("[DRY-RUN] No files written.")
    return 0


# ------------------------------------------------------
# Main
# -----------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="OpenSpec 需求驱动开发工作流",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_ai_flow.py
  python run_ai_flow.py -r requirements/simple_login.md
  python run_ai_flow.py --dry-run          # 预览执行计划
  python run_ai_flow.py --health-check     # 检查系统配置
  python run_ai_flow.py --no-abort         # 关键阶段失败时不终止
  python run_ai_flow.py --resume           # 从 checkpoint 恢复
  python run_ai_flow.py --verbose          # 详细输出
  python run_ai_flow.py --debug        # DEBUG 级别日志

环境变量:
  ANTHROPIC_API_KEY    Anthropic API 密钥
  ANTHROPIC_AUTH_TOKEN 同上（备用）
  OPENSPEC_MODEL       覆盖 config.yaml 中的模型名
  OPENSPEC_TIMEOUT     覆盖全局超时（秒）""",
    )
    parser.add_argument(
        "--requirements", "-r",
        default="requirements/simple_login.md",
        help="需求文档路径 (默认: requirements/simple_login.md)",
    )
    parser.add_argument("--no-abort", action="store_true",
                  help="关键阶段失败时不终止流程")
    parser.add_argument("--force-regenerate-code", action="store_true",
                   help="强制重新生成所有业务代码")
    parser.add_argument("--vector-retrieval", action="store_true",
                        help="启用语义检索上下文注入（默认关闭）")
    parser.add_argument("--vector-persist-dir",
                        help="向量库持久化目录（默认: <project>/.spec/vector_store）")
    parser.add_argument("--vector-top-k", type=int, default=5,
                        help="语义检索返回条数 (默认: 5)")
    parser.add_argument("--no-vector-chroma", action="store_true",
                        help="禁用 ChromaDB，使用内存向量检索")
    parser.add_argument("--max-concurrency", type=int, default=3,
                        help="Phase 内部文件任务最大并发数 (默认: 3)")
    parser.add_argument("--resume", action="store_true",
             help="从 .spec/checkpoint.json 恢复执行")
    parser.add_argument("--verbose", "-v", action="store_true",
               help="启用详细输出模式")
    parser.add_argument("--debug", action="store_true",
                    help="启用 DEBUG 级别日志")
    parser.add_argument("--dry-run", action="store_true",
                  help="预览执行计划，不实际运行")
    parser.add_argument("--health-check", action="store_true",
                        help="检查系统配置（API 密钥、编译器、依赖等）")

    # AI-agnostic collaboration mode arguments
    parser.add_argument("--propose-only", action="store_true",
                help="仅生成 OpenSpec Change（Phase 1-3），输出 Rule Pack 供外部 AI 工具使用")
    parser.add_argument("--apply-change",
            help="从已有 Change 恢复并执行 Phase 4-11（需提供 change-id）")
    parser.add_argument("--validate-change",
               help="从已有 Change 恢复并仅执行验证（Phase 9-11）")
    args = parser.parse_args()

    # P2.2: health check (no requirements file needed)
    if args.health_check:
        return _run_health_check()

    # P2.3: apply env var overrides before anything else
    _apply_env_overrides()
    # Determine run mode based on CLI arguments
    from devpal.collaboration.modes import RunMode

    run_mode = RunMode.FULL
    change_id = None

    if args.propose_only:
        run_mode = RunMode.PROPOSE_ONLY
        print("[INFO] Mode: PROPOSE_ONLY - Will generate OpenSpec Change and stop at Phase 3")
        print()
    elif args.apply_change:
        run_mode = RunMode.APPLY_ONLY
        change_id = args.apply_change
        print(f"[INFO] Mode: APPLY_ONLY - Will load change '{change_id}' and run Phase 4-11")
        print()
    elif args.validate_change:
        run_mode = RunMode.VALIDATE_ONLY
        change_id = args.validate_change
        print(f"[INFO] Mode: VALIDATE_ONLY - Will load change '{change_id}' and run Phase 9-11")
        print()

    # Validate requirements file
    requirements_file = ROOT / args.requirements
    if not requirements_file.exists():
        print(f"[ERROR] 需求文件不存在: {requirements_file}")
        return 1

    # P2.1: dry-run
    if args.dry_run:
        return _run_dry_run(requirements_file)

    # Warn if no API key
    if not os.environ.get("ANTHROPIC_AUTH_TOKEN") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[WARNING] ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY 未设置")
        print("          请设置环境变量或填充 config/config.yaml 后再运行")
        print()

    # Initialize EventBus monitoring (if not in quiet mode)
    progress_monitor = None
    performance_analyzer = None
    if not args.debug:  # Only show monitors in normal mode
        try:
            progress_monitor = ProgressMonitor(total_phases=11)
            performance_analyzer = PerformanceAnalyzer()
            print("[EventBus] Monitoring enabled: ProgressMonitor + PerformanceAnalyzer")
            print()
        except Exception as e:
            print(f"[WARNING] Failed to initialize EventBus monitors: {e}")
            print()

    executor = OpenSpecWorkflowExecutor(tool_registry)
    result = executor.run(
        str(requirements_file),
        OpenSpecRunOptions(
            abort_on_critical_failure=not args.no_abort,
            enable_timeout=True,
            enable_retry=True,
            enable_checkpoint=True,
            enable_progress=True,
            resume=args.resume,
            force_regenerate_code=args.force_regenerate_code,
            vector_retrieval_enabled=args.vector_retrieval,
            vector_persist_dir=args.vector_persist_dir,
            vector_top_k=args.vector_top_k,
            vector_prefer_chroma=not args.no_vector_chroma,
            max_concurrency=args.max_concurrency,
            verbose=args.verbose,
            debug=args.debug,
       run_mode=run_mode,
            change_id=change_id,
        ),
    )

    if not result["success"]:
        print("\n" + "=" * 70)
        print(
            f"[CRITICAL] 流程失败于 Phase {result['failed_phase']}: "
            f"{result['failed_phase_name']}"
        )
        print(f"错误: {result['error_message']}")
        if result.get("errors"):
            print("详细错误:")
            for error in result["errors"]:
                print(f"  - {error}")
        if result.get("log_file"):
            print(f"\n详细日志: {result['log_file']}")
        print("=" * 70)
        return 1

    print("\n[SUCCESS] 流程成功完成")
    if result.get("log_file"):
        print(f"详细日志: {result['log_file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
