# DevPalAgent 后续开发优先级规划

**日期**：2026-05-16  
**基于**：`plan_doc/gap_analysis_vs_openspec_2026-05-16.md`  
**当前测试**：42 个，100% 通过

---

## 战略方向

DevPalAgent 的定位是**全自动 Spec-First 开发系统**，不是复制开源 OpenSpec 的规范协作框架。核心差异化优势（端到端自动化、AI 自愈、编译测试闭环、ArtifactGraph）要继续强化，同时补齐规范管理能力（Given/When/Then、delta 归档、CLAUDE.md）。

---

## P0 — 立即修复（当天，阻塞质量）

### P0.1 修复自愈模型切换 Bug
**问题**：`test_self_healer.py` 中 `use_fallback=True` 时实际上没有切换到 Opus 模型，第二次自愈尝试和第一次用的是同一个模型。

**修复位置**：`devpal/core/openspec_phases/test_self_healer.py`

```python
# 当前（错误）：
response = self.llm_client.generate(...)  # 无论 use_fallback 是否 True

# 修复后：
client = get_llm_client(model=self.fallback_model) if use_fallback else self.llm_client
response = client.generate(...)
```

**预计时间**：30 分钟  
**价值**：自愈成功率提升，第二次尝试真正使用更强的 Opus 模型

---

## P1 — 本周完成（补齐核心 Spec 能力）

### P1.1 Phase 1 输出 Given/When/Then 验收场景
**目标**：需求解析时提取结构化验收场景，对标开源 OpenSpec 的 spec delta 格式。

**修改**：`devpal/core/openspec_phases/phase1_parse_requirements.py`
- `_parse_structured_requirements()` 增加 `scenarios` 字段解析
- 识别 `Given/When/Then` 格式（中英文均支持）
- 输出到 `requirements.json` 的 `scenarios` 列表

**输出格式**：
```json
{
  "id": "REQ-001",
  "title": "用户登录",
  "scenarios": [
    {
      "given": "用户在登录页面",
      "when": "输入正确的用户名和密码",
      "then": "跳转到首页，显示欢迎信息"
    }
  ]
}
```

**预计时间**：2 小时

---

### P1.2 需求对象增加 priority 和 status 字段
**目标**：需求模型对象化，支持优先级和状态追踪。

**修改**：`devpal/core/openspec_phases/phase1_parse_requirements.py`
- 从需求文档提取优先级标记（`P0/P1/P2`、`高/中/低`、`Critical/High/Medium/Low`）
- 初始 `status` 设为 `PROPOSED`
- Phase 10 测试全部通过后，更新相关需求 `status` 为 `VERIFIED`

**修改**：`devpal/core/openspec_phases/base.py`
- `OpenSpecContext` 增加 `requirements_status` 字典（req_id → status）

**预计时间**：1 小时

---

### P1.3 生成 `.spec/delta.json`
**目标**：Phase 1 完成后将变更写入标准格式的 delta 文件，供后续阶段和外部工具读取。

**修改**：`devpal/core/openspec_phases/phase1_parse_requirements.py`
- `_compute_requirements_delta()` 完成后写入 `.spec/delta.json`

**输出格式**（对标开源 OpenSpec）：
```json
{
  "timestamp": "2026-05-16T10:30:00",
  "added": ["REQ-002", "REQ-003"],
  "modified": ["REQ-001"],
  "removed": [],
  "changed": true,
  "summary": "2 added, 1 modified, 0 removed"
}
```

**预计时间**：1 小时

---

## P2 — 下周完成（提升系统深度）

### P2.1 ValidationEngine 接入 Phase 9
**目标**：把已有的 `validation_engine.py`（719 LOC，四层验证）真正接入 Phase 9 质量门禁。

**当前状态**：Phase 9 只做文件存在性检查，`validation_engine.py` 是死代码。

**修改**：`devpal/core/openspec_phases/phase9_quality_gate.py`
- 调用 `ValidationEngine` 执行四层验证：
  - **SYNTAX**：文件存在性、编码正确性（当前已有，迁移）
  - **SEMANTIC**：API 契约一致性（test_base.h 宏与测试文件一致）
  - **STRUCTURAL**：类三元组完整性（每个非平凡类有 include/src/test）
  - **BUSINESS**：需求覆盖率（每个 REQ 有对应测试文件）
- 验证结果写入 ArtifactGraph 节点元数据
- 报告中展示四层验证结果

**关键文件**：
- `devpal/core/openspec_phases/phase9_quality_gate.py`
- `devpal/core/schema/validation_engine.py`

**预计时间**：1 天

---

### P2.2 生成 CLAUDE.md
**目标**：Phase 11 生成 `CLAUDE.md`，让 Claude Code、Cursor 等 AI 工具能直接读取项目规范上下文。

**修改**：`devpal/core/openspec_phases/phase11_final_report.py`
- 新增 `_generate_claude_md()` 方法
- 生成内容包含：
  - 项目概述和技术栈
  - 需求列表（带 ID、优先级、验收场景）
  - 文件结构说明
  - 编码规范（命名约定、测试规范）
  - 已知限制和注意事项

**输出**：`CLAUDE.md`（项目根目录）

**预计时间**：1 天

---

### P2.3 需求状态生命周期管理
**目标**：需求从 PROPOSED 到 VERIFIED 的完整状态追踪，写入 `.spec/requirements_status.json`。

**流程**：
```
Phase 1 解析 → PROPOSED
Phase 4 生成代码 → IN_PROGRESS
Phase 10 测试通过 → VERIFIED
Phase 10 测试失败 → FAILED
```

**修改**：
- `devpal/core/openspec_phases/phase4_generate_code.py`：更新状态为 IN_PROGRESS
- `devpal/core/openspec_phases/phase10_run_tests.py`：更新状态为 VERIFIED/FAILED
- `devpal/core/openspec_phases/phase11_final_report.py`：在报告中展示状态分布

**预计时间**：半天

---

## P3 — 下下周（架构升级）

### P3.1 EventBus 接入主流程
**目标**：把已有的 `event_bus.py`（696 LOC）接入主流程，实现 Phase 间解耦通信，事件日志可追溯。

**关键事件**：
- Phase 1：`RequirementChangedEvent`（需求变更时）
- Phase 4：`FileChangedEvent`（每个文件生成后）
- Phase 9：`ValidationCompletedEvent`（质量门禁结果）
- Phase 10：`ValidationCompletedEvent`（测试结果）

**输出**：`.spec/events.json`（事件日志）

**关键文件**：
- `devpal/core/schema/event_bus.py`
- `devpal/core/openspec_phases/base.py`（context 增加 `event_bus` 字段）
- Phase 1/4/9/10 各自发布事件

**预计时间**：1 天

---

### P3.2 多语言支持框架
**目标**：从 C++ 专用扩展到支持 Python，对标开源 OpenSpec 的语言无关性。

**架构**：
```
devpal/core/language_plugins/
├── base.py          # LanguagePlugin 抽象接口
├── cpp_plugin.py    # 现有 C++ 逻辑迁移
└── python_plugin.py # Python 新实现（pytest + pyproject.toml）
```

**接口定义**：
```python
class LanguagePlugin(ABC):
    def get_build_command(self) -> List[str]: ...
    def get_test_command(self) -> List[str]: ...
    def get_file_structure(self) -> Dict: ...
    def get_cmake_template(self) -> str: ...  # C++ only
    def get_test_framework(self) -> str: ...
```

**Phase 2** 根据需求文档关键词自动检测语言（`Python`/`C++`/`Go`）。

**预计时间**：1 周

---

### P3.3 变更归档机制
**目标**：对标开源 OpenSpec 的 `archive` 命令，完成的需求变更归档到历史记录。

**实现**：
- `run_ai_flow.py` 新增 `--archive` 标志
- 执行成功后将 `.spec/delta.json` 归档到 `.spec/history/YYYYMMDD_HHMMSS_delta.json`
- 更新 `.spec/requirements.json` 为最新全量版本
- 生成变更摘要写入 `.spec/changelog.md`

**预计时间**：半天

---

## 执行顺序总览

```
Week 1（本周）
├── P0.1  修复自愈模型切换 Bug          [30分钟]
├── P1.1  Phase 1 输出 Given/When/Then  [2小时]
├── P1.2  需求增加 priority/status      [1小时]
└── P1.3  生成 .spec/delta.json         [1小时]

Week 2（下周）
├── P2.1  ValidationEngine 接入 Phase 9 [1天]
├── P2.2  生成 CLAUDE.md                [1天]
└── P2.3  需求状态生命周期管理           [半天]

Week 3（下下周）
├── P3.1  EventBus 接入主流程           [1天]
├── P3.2  多语言支持框架                [1周]
└── P3.3  变更归档机制                  [半天]
```

---

## 关键文件清单

| 文件 | 涉及任务 |
|------|----------|
| `devpal/core/openspec_phases/test_self_healer.py` | P0.1 |
| `devpal/core/openspec_phases/phase1_parse_requirements.py` | P1.1, P1.2, P1.3 |
| `devpal/core/openspec_phases/base.py` | P1.2, P3.1 |
| `devpal/core/openspec_phases/phase9_quality_gate.py` | P2.1 |
| `devpal/core/schema/validation_engine.py` | P2.1（复用） |
| `devpal/core/openspec_phases/phase11_final_report.py` | P2.2 |
| `devpal/core/openspec_phases/phase4_generate_code.py` | P2.3, P3.1 |
| `devpal/core/openspec_phases/phase10_run_tests.py` | P2.3, P3.1 |
| `devpal/core/schema/event_bus.py` | P3.1（复用） |
| `devpal/core/language_plugins/` | P3.2（新增） |
| `run_ai_flow.py` | P3.3 |

---

## 验收标准

每个任务完成后必须通过：
```bash
python -m pytest tests/openspec/ -v   # 全部通过
python -m py_compile devpal/core/openspec_phases/*.py  # 无语法错误
```

P1 全部完成后额外验证：
```bash
# requirements.json 包含 scenarios 字段
python -c "
import json
r = json.load(open('cpp_simple_login/.spec/requirements.json'))
assert r[0].get('scenarios') is not None, 'scenarios missing'
assert r[0].get('priority') is not None, 'priority missing'
print('P1 验收通过')
"

# delta.json 存在
python -c "
from pathlib import Path
assert Path('cpp_simple_login/.spec/delta.json').exists()
print('delta.json OK')
"
```

P2 全部完成后额外验证：
```bash
# CLAUDE.md 生成
python -c "
from pathlib import Path
assert Path('cpp_simple_login/CLAUDE.md').exists()
content = Path('cpp_simple_login/CLAUDE.md').read_text()
assert 'REQ-' in content
print('CLAUDE.md OK')
"
```
战略方向：不复制开源 OpenSpec，而是在 DevPalAgent 的自动化优势上补齐规范管理能力。

P0（今天，30分钟）

修复自愈模型切换 Bug — use_fallback=True 时实际没有切换到 Opus
P1（本周，4小时）

Phase 1 输出 Given/When/Then 验收场景
需求增加 priority/status 字段
生成 .spec/delta.json
P2（下周，2.5天）

ValidationEngine 接入 Phase 9（四层验证：SYNTAX/SEMANTIC/STRUCTURAL/BUSINESS）
生成 CLAUDE.md（让 Claude Code/Cursor 能读取项目规范）
需求状态生命周期（PROPOSED → IN_PROGRESS → VERIFIED）
P3（下下周，按需）

EventBus 接入主流程（事件日志 .spec/events.json）
多语言支持框架（Python 插件）
变更归档机制（--archive 命令）