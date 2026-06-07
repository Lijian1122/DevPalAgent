# DevPalAgent E2E Demo Guide

> 用最短路径演示 DevPalAgent 的 Spec-first Agent workflow、语言感知跳过、质量门禁和最终报告。

---

## 1. Demo 目标

这个 demo 展示一个 installer 项目的完整 OpenSpec flow：

- 从 requirements markdown 开始。
- 自动识别项目类型为 installer。
- 自动跳过不适用的 C++ 阶段。
- 仍然生成 Python installer 项目。
- Phase 9 质量门禁按 Python/installer 检查。
- Phase 10 显示 skipped，而不是 `0/0 passed`。
- Phase 11 生成 final report 和 CLAUDE.md。
- 不生成 `cpp_test_phase_skip`。

---

## 2. 前置条件

```bash
python --version
pip install pytest
```

如需真实 AI 代码生成，确保 LLM/API 配置可用。

---

## 3. 输入需求文件

文件：

```text
requirements/test_phase_skip.md
```

示例内容：

```markdown
# 安装脚本生成器测试

## 项目概述

这是一个安装脚本项目，用于生成 Claude Code CLI 的安装脚本。

本项目是安装脚本类型，不需要 C++ 编译、CMake 配置和测试。

## 功能需求

### REQ-001: 生成安装脚本
- 生成简单的安装脚本
- 支持基本的环境检查
- 这是一个安装工具项目

## 验收标准

- [ ] 生成安装脚本文件
- [ ] 脚本能够运行
```

---

## 4. 手动 smoke demo

运行：

```bash
python test_simple.py
```

预期控制台关键信息：

```text
[INFO] 检测到特性: install
[INFO] 项目类型: installer
[INFO] 语言: python, is_cpp: False

[SKIP] Phase 3 ... 安装脚本项目不需要 AI 技术设计
[SKIP] Phase 5 ... 安装脚本项目不需要生成测试代码
[SKIP] Phase 6 ... 安装脚本项目不需要 CMake 配置
[SKIP] Phase 7 ... 安装脚本项目不需要测试文档
[SKIP] Phase 10 ... 安装脚本项目不需要编译和运行测试

Phase 9:
[OK] FORMAT layer: 0 issue(s)
[OK] SEMANTIC layer: 0 issue(s)
[OK] PARSER layer: 0 issue(s)
[OK] BUSINESS layer: 0 issue(s)

Phase 11:
tests: skipped (...)
```

---

## 5. 生成目录检查

运行后会生成：

```text
test_phase_skip/
├── src/
├── tests/
├── docs/
├── .spec/
├── README.md
└── CLAUDE.md
```

Installer 项目不应生成：

```text
cpp_test_phase_skip/
test_phase_skip/include/
```

检查命令：

```bash
# Linux/macOS/Git Bash
[ ! -d cpp_test_phase_skip ] && echo "OK: no cpp_test_phase_skip"
[ ! -d test_phase_skip/include ] && echo "OK: no include dir for installer"
```

---

## 6. Final Report 检查

文件：

```text
test_phase_skip/docs/final_report.md
```

应包含：

```text
- Status: skipped
- Summary: skipped (...)
| 10 | Compile and run tests | skipped |
```

不应包含：

```text
0/0 passed
```

检查命令：

```bash
grep -n "Summary: skipped\|Compile and run tests\|0/0 passed" test_phase_skip/docs/final_report.md
```

---

## 7. Quality Gate 检查

文件：

```text
test_phase_skip/docs/quality_gate_report.md
```

应包含：

```text
- FORMAT layer: 0 error(s), 0 warning(s)
- SEMANTIC layer: 0 error(s), 0 warning(s)
- PARSER layer: 0 error(s), 0 warning(s)
- BUSINESS layer: 0 error(s), 0 warning(s)
```

不应包含：

```text
CMakeLists.txt not found
src/main.cpp not found
tests/test_base.h not found
No test files found in tests/ directory
```

---

## 8. CLAUDE.md 检查

文件：

```text
test_phase_skip/CLAUDE.md
```

应包含：

```text
- Language: Python
- Test framework: pytest
- Project type: installer/tooling; native build phases are not applicable
- Summary: skipped (...)
```

Coding Conventions 段不应出现：

```text
.cpp
test_base.h
CMake
```

注意：需求原文可能包含“不需要 CMake 配置和测试”，这是需求内容，不是编码规范残留。

---

## 9. 自动化 e2e 测试

运行：

```bash
python -m pytest tests/e2e/test_installer_flow.py
```

预期：

```text
1 passed
```

该测试会断言：

- flow 成功。
- project name 是 `test_phase_skip`。
- 不存在 `cpp_test_phase_skip`。
- Phase 3/5/6/7/10 都是 skipped。
- `test_skipped is True`。
- final report 不含 `0/0 passed`。
- quality gate 没有 C++ 缺失文件误报。
- CLAUDE.md Coding Conventions 没有 C++ 残留。

---

## 10. M1 全量目标测试

推荐命令：

```bash
python -m pytest tests/openspec/test_spec_first_artifacts.py tests/openspec/test_phase10_run_tests.py tests/openspec/test_phase9_quality_gate.py tests/e2e/test_installer_flow.py
```

最近结果：

```text
22 passed, 2 warnings
```

---

## 11. OpenSpec 主线能力 smoke demo

除 installer skip demo 外，当前项目还可以用同一个需求文件展示语义检索、AI-agnostic 协作、Archive 和 multi-agent sandbox summary。

### 11.1 Semantic Retrieval

```bash
python run_ai_flow.py -r requirements/simple_login.md --vector-retrieval --vector-top-k 5
```

检查 final report：

```bash
grep -n "Semantic Retrieval\|Search count\|Indexed documents" simple_login/docs/final_report.md
```

应看到 Semantic Retrieval 章节和检索统计。默认 provider 是 deterministic mock embedding，适合离线演示；ChromaDB 是可选持久化后端。

### 11.2 AI-agnostic collaboration lifecycle

```bash
python run_ai_flow.py -r requirements/simple_login.md --propose-only
python run_ai_flow.py -r requirements/simple_login.md --apply-change <change-id>
python run_ai_flow.py -r requirements/simple_login.md --validate-change <change-id>
```

讲解重点：

- `--propose-only` 只生成 `openspec/changes/<change-id>/` 和 Rule Pack，不直接写业务代码。
- `--apply-change` 从已有 change artifacts 恢复 context，执行 Phase 4-11。
- `--validate-change` 从已有 change artifacts 恢复 context，只执行 Phase 9-11。

### 11.3 Archive + Coverage Matrix

```bash
python -m devpal.openspec archive <change-id> --project-dir <project-dir>
```

检查：

```bash
ls <project-dir>/.spec/archive/
grep -n "REQ-" <project-dir>/.spec/coverage_matrix.md
```

Archive 会合并 spec、更新 metadata 状态、生成 `.spec/archive/<change-id>.json`，并输出 requirement → code/test/report coverage matrix。

### 11.4 Multi-Agent Sandbox Summary

```bash
python run_ai_flow.py -r requirements/simple_login.md --enable-multi-agent --max-concurrency 3
```

检查：

```bash
grep -n "Multi-Agent Sandbox Summary\|manifest.json\|Policy violations" simple_login/docs/final_report.md
ls simple_login/.spec/sandboxes/*/manifest.json
```

讲解重点：当前 sandbox 是本地 MVP，主要提供路径/命令策略、workspace artifact 和 manifest 审计；不是容器或 OS 级隔离。

---

## 12. Demo 结束后的清理

运行产物不应提交到 git。

清理：

```bash
rm -rf .spec test_phase_skip cpp_test_phase_skip
```

如果有 Python 缓存：

```bash
find . -type d -name __pycache__ -prune -exec rm -rf {} +
```

Windows PowerShell 可用：

```powershell
Remove-Item -Recurse -Force .spec,test_phase_skip,cpp_test_phase_skip -ErrorAction SilentlyContinue
```

---

## 13. Demo 讲解词

可以这样讲：

> 这个 demo 的输入只是一个 installer requirements markdown。系统在 Phase 1 自动识别为 installer，因此把语言切换为 Python，并记录 project_type=installer。由于 installer 不需要 C++ 技术设计、CMake 和编译测试，Phase 3/5/6/7/10 被显式 skipped。Phase 9 仍然执行质量门禁，但使用 Python/installer 检查器，所以不会误报 CMakeLists.txt 或 main.cpp 缺失。Phase 11 生成 final_report 和 CLAUDE.md，其中测试结果显示 skipped，而不是 0/0 passed。这体现了 Agent workflow 的可靠性：它不只是生成代码，还能理解什么阶段适用、什么阶段不适用，并把状态准确报告出来。
