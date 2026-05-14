# -*- coding: utf-8 -*-
"""End-to-end smoke test for the AI-driven OpenSpec flow.

Runs: Phase 2 (structure) -> Phase 3 (AI tech design) -> Phase 4 (infra + AI code)
     -> Phase 5 (verify tests) -> Phase 9 (review) -> Phase 10 (compile+test w/ self-heal)
     -> Phase 11 (final report).

Prerequisites:
  1. pip install anthropic pyyaml
  2. Set env ANTHROPIC_AUTH_TOKEN (or edit config/config.yaml with anthropic.auth_token)
  3. A requirements file under requirements/*.md
"""

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from devpal.core.openspec_phases.base import OpenSpecContext
from devpal.core.openspec_phases.phase2_create_structure import Phase2CreateStructure
from devpal.core.openspec_phases.phase3_technical_design import Phase3TechnicalDesign
from devpal.core.openspec_phases.phase4_generate_code import Phase4GenerateCode
from devpal.core.openspec_phases.phase5_generate_tests import Phase5GenerateTests
from devpal.core.openspec_phases.phase9_code_review import Phase9CodeReview
from devpal.core.openspec_phases.phase10_run_tests import Phase10RunTests
from devpal.core.openspec_phases.phase11_final_report import Phase11FinalReport
from devpal.tools.registry import registry as tool_registry


# ---- Configurable --
REQUIREMENTS_FILE = ROOT / "requirements" / "simple_login.md"
PROJECT_NAME = "simple_auth"
PROJECT_DIR = ROOT / "simple_auth_project"
# ----------------


def reset_project_dir():
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)


def run_phase(phase, name):
    print("\n" + "=" * 70)
    print("  {}".format(name))
    print("=" * 70)
    result = phase.execute()
    status = "OK" if result.success else "FAIL"
    print("[{}] {}".format(status, result.message))
    if result.errors:
        for err in result.errors:
            print("  error: {}".format(err[:300]))
    return result


def main():
    if not REQUIREMENTS_FILE.exists():
        print("requirements file not found: {}".format(REQUIREMENTS_FILE))
        return 1

    if not os.environ.get("ANTHROPIC_AUTH_TOKEN") and not os.environ.get(
        "ANTHROPIC_API_KEY"
    ):
        print("WARNING: ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY not set.")
        print("Set one of them or populate config/config.yaml before running.")

    print("=" * 70)
    print("  OpenSpec AI Flow - Smoke Test")
    print("  requirements: {}".format(REQUIREMENTS_FILE))
    print("  project_dir : {}".format(PROJECT_DIR))
    print("=" * 70)

    reset_project_dir()
    requirements_content = REQUIREMENTS_FILE.read_text(encoding="utf-8")

    ctx = OpenSpecContext(
        project_dir=PROJECT_DIR,
        requirements_file=REQUIREMENTS_FILE,
        requirements_content=requirements_content,
        project_name=PROJECT_NAME,
        language="cpp",
        is_cpp=True,
    )

    # Phase 2: create structure
    r2 = run_phase(Phase2CreateStructure(ctx, tool_registry), "Phase 2: Create structure")
    ctx.set_phase_result(2, r2)
    if not r2.success:
        return 1

    # Phase 3: AI tech design
    r3 = run_phase(Phase3TechnicalDesign(ctx), "Phase 3: Tech design (AI)")
    ctx.set_phase_result(3, r3)
    if not r3.success:
        return 1

    # Phase 4: infra templates + AI code
    r4 = run_phase(Phase4GenerateCode(ctx, tool_registry), "Phase 4: Generate code (templates + AI)")
    ctx.set_phase_result(4, r4)
    if not r4.success:
        return 1

    # Phase 5: verify tests
    r5 = run_phase(Phase5GenerateTests(ctx, tool_registry), "Phase 5: Verify tests")
    ctx.set_phase_result(5, r5)

    # Phase 9: code review (optional, non-fatal)
    r9 = run_phase(Phase9CodeReview(ctx, tool_registry), "Phase 9: Code review")
    ctx.set_phase_result(9, r9)

    # Phase 10: compile + test + self-heal
    r10 = run_phase(Phase10RunTests(ctx, tool_registry), "Phase 10: Compile + test + self-heal")
    ctx.set_phase_result(10, r10)

    # Phase 11: final report (always run)
    r11 = run_phase(Phase11FinalReport(ctx), "Phase 11: Final report")
    ctx.set_phase_result(11, r11)

    print("\n" + "=" * 70)
    print("  DONE")
    print("  project : {}".format(PROJECT_DIR))
    print("  ai_files: {}".format(len(ctx.ai_generated_files)))
    print("  tests   : {}/{} passed".format(ctx.test_passed, ctx.test_total))
    print("  llm     : {} calls, in={} out={}".format(
        ctx.llm_calls, ctx.llm_input_tokens, ctx.llm_output_tokens
    ))
    print("  heal    : {} attempts".format(ctx.self_heal_attempts))
    print("=" * 70)
    return 0 if r10.success else 2


if __name__ == "__main__":
    sys.exit(main())
