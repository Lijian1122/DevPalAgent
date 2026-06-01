# Archive + Traceability 生命周期闭环架构设计

**日期**：2026-05-29  
**目标**：补齐 OpenSpec Change 的归档、合并、追踪和覆盖率矩阵能力，让 DevPalAgent 从“生成 change artifacts”升级为“管理需求生命周期闭环”  
**预期工期**：3-4 天 MVP  
**优先级**：P1  
**关联路线图**：`plan_doc/plan_0528_priority_roadmap.md`

---

## 1. 背景与目标

### 1.1 当前状态

**已完成能力**：
- ✅ OpenSpec 11 阶段 workflow 可生成 proposal/spec/tasks/design
- ✅ ArtifactGraph 可记录需求、代码、测试、报告等 artifacts
- ✅ EventBus 可记录 workflow/phase/file task/vector 检索事件
- ✅ final_report 可汇总测试、并行执行、语义检索等结果
- ✅ requirements status 已支持 PROPOSED / IN_PROGRESS / VERIFIED / FAILED

### 1.2 当前缺口

**缺口 1：Change 生命周期未闭环**
- 当前 change artifacts 生成后缺少正式 archive 操作。
- proposal/spec/tasks/design 没有从 “proposed change” 合并到长期主规格。
- change metadata 状态没有稳定流转到 ARCHIVED。

**缺口 2：Traceability 不够显式**
- ArtifactGraph 已有基础结构，但 change_id / requirement_id / archived_at 没有形成闭环。
- final_report 缺少 Requirement → Code → Test → Report 覆盖矩阵。
- 面试展示时难以证明“每个需求都能追踪到实现和验证结果”。

**缺口 3：缺少归档命令入口**
- 路线图要求 `python -m devpal.openspec archive <change-id>`。
- 当前没有统一 archive CLI/API 可复用到 Claude Code / Cursor / Cline 协作流。

### 1.3 设计目标

**目标 1：Archive Change**
- 支持 `archive_change(change_id)` API 和 CLI。
- 将 `openspec/changes/<change-id>/` 标记为 ARCHIVED。
- 将 spec delta 合并到 `openspec/specs/main.md`。

**目标 2：Traceability Matrix**
- 生成 Requirement → Code → Test → Report 覆盖矩阵。
- 在 ArtifactGraph 中记录 `introduced_by` / `change_id` / `archived_at`。
- final_report 展示 archive summary 和 coverage matrix。

**目标 3：可验证、可回滚、可复盘**
- archive 前做 preflight validation。
- archive 后生成 archive manifest。
- EventBus 记录 archive 生命周期事件。

---

## 2. 当前实现分析

### 2.1 OpenSpec Change artifacts

**现状**：
```text
openspec/changes/<change-id>/
├── proposal.md
├── tasks.md
├── design.md
├── metadata.json
└── specs/spec.md
```

这些 artifacts 能表达“计划做什么”，但 archive 后缺少长期落点。

### 2.2 ArtifactGraph

**现状能力**：
- 已能写出 `.spec/artifact_graph.json`。
- 已能表示 artifact node 和 dependency edge。

**待增强**：
- node metadata 增加 `change_id`、`requirement_id`、`introduced_by`、`archived_at`。
- edge 增加 `satisfies`、`tested_by`、`reported_by`、`archived_from` 类型。

### 2.3 final_report

**现状能力**：
- 汇总测试结果、生成文件、LLM usage、并行统计、向量检索统计。

**待增强**：
- Archive Summary。
- Coverage Matrix。
- Uncovered Requirements 列表。

---

## 3. 架构设计

### 3.1 总体流程

```text
OpenSpec Change
  ↓
Archive Preflight
  ├─ verify metadata
  ├─ verify tasks completed
  ├─ verify generated files exist
  └─ verify tests/report exist
  ↓
Delta Merge
  ├─ specs/spec.md → openspec/specs/main.md
  └─ metadata status → ARCHIVED
  ↓
Traceability Build
  ├─ requirements → source
  ├─ source → tests
  └─ tests → final_report
  ↓
ArtifactGraph + final_report + EventBus
```

### 3.2 模块结构

```text
devpal/openspec/
├── __init__.py
├── archive.py          # ArchiveChangeService
├── coverage.py         # CoverageMatrixBuilder
├── spec_merge.py       # SpecMerger
└── __main__.py         # python -m devpal.openspec archive <change-id>
```

### 3.3 核心抽象

#### ArchiveChangeService

```python
class ArchiveChangeService:
    def archive_change(self, project_dir: Path, change_id: str) -> ArchiveResult:
        pass
```

职责：
- 读取 change metadata。
- 执行 preflight。
- 调用 SpecMerger。
- 更新 ArtifactGraph。
- 写 archive manifest。

#### ArchiveResult

```python
@dataclass
class ArchiveResult:
    change_id: str
    success: bool
    status: str
    archived_at: str
    merged_spec_path: Path | None
    coverage_matrix_path: Path | None
    errors: list[str]
```

#### CoverageMatrixBuilder

输出：
```text
| Requirement | Code | Tests | Report | Status |
|-------------|------|-------|--------|--------|
| REQ-001 | src/calculator.cpp | tests/test_calculator.cpp | docs/final_report.md | VERIFIED |
```

---

## 4. 数据与事件设计

### 4.1 metadata.json 增强

```json
{
  "change_id": "add-login-service",
  "status": "ARCHIVED",
  "created_at": "2026-05-29T10:00:00",
  "implemented_at": "2026-05-29T11:00:00",
  "archived_at": "2026-05-29T12:00:00",
  "merged_into": "openspec/specs/main.md"
}
```

### 4.2 ArtifactGraph metadata

每个生成文件 node 增加：
```json
{
  "change_id": "add-login-service",
  "introduced_by": "openspec/changes/add-login-service",
  "archived_at": "2026-05-29T12:00:00",
  "requirement_ids": ["REQ-001"]
}
```

### 4.3 EventBus 事件

新增事件：
- `archive.started`
- `archive.preflight_completed`
- `archive.spec_merged`
- `archive.coverage_generated`
- `archive.completed`
- `archive.failed`

---

## 5. 分阶段实施路线

### Day 1：Archive CLI + metadata 状态流转

验收：
- `python -m devpal.openspec archive <change-id>` 可执行。
- metadata 状态从 IMPLEMENTED/IN_PROGRESS 更新为 ARCHIVED。
- archive manifest 写入 `.spec/archive/<change-id>.json`。

### Day 2：Spec delta merge

验收：
- `openspec/changes/<change-id>/specs/spec.md` 合并到 `openspec/specs/main.md`。
- 重复 archive 不重复追加相同 spec block。
- merge 前后有备份或 manifest 可追溯。

### Day 3：Coverage matrix + ArtifactGraph 增强

验收：
- 生成 `.spec/coverage_matrix.md`。
- ArtifactGraph nodes/edges 保留 change_id 和 requirement_id。
- final_report 展示 coverage matrix summary。

### Day 4：测试与端到端验证

验收：
- archive 成功、重复 archive、缺失 change、缺失 spec、未通过测试等场景有测试。
- golden case 能完成 generate → validate → archive → final_report。

---

## 6. 验收标准

```bash
python run_ai_flow.py -r requirements/simple_login.md
python -m devpal.openspec archive add-simple-login
```

验证点：
1. change metadata 状态变为 ARCHIVED。
2. `openspec/specs/main.md` 包含该 change 的 spec delta。
3. `.spec/archive/<change-id>.json` 存在并记录归档结果。
4. `.spec/coverage_matrix.md` 展示 Requirement → Code → Test → Report。
5. final_report 展示 Archive Summary 和 Coverage Matrix。
6. EventBus 包含 archive 生命周期事件。

---

## 7. 风险与缓解

1. **重复归档风险**：使用 change_id marker 包裹 merged spec，重复执行时跳过。
2. **错误合并风险**：archive 前 preflight，缺失 spec 或 metadata 时失败。
3. **覆盖矩阵误判风险**：MVP 先基于 artifact metadata 和路径规则，后续结合向量检索和 static symbol mapping。
4. **破坏现有主流程风险**：archive 独立 CLI/API，不影响 run_ai_flow 默认路径。

---

## 8. 面试讲法

DevPalAgent 不只生成代码，还把需求变更当成可归档的生命周期对象。每次需求会生成 OpenSpec Change，代码和测试通过后执行 archive，把 spec delta 合并进主规格，并生成 Requirement → Code → Test → Report 覆盖矩阵。这样可以证明每个需求从提出、实现、验证到归档都有可追踪证据，而不是一次性的代码生成脚本。
