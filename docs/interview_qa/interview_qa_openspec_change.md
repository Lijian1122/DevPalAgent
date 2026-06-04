# Interview Q&A: OpenSpec Change System

## 面试专题：OpenSpec Change 架构与 AI-agnostic 协作

---

## Q1: 什么是 OpenSpec Change？它解决什么问题？

**核心回答**:
OpenSpec Change 是 DevPalAgent 的变更管理系统，它将每次需求变更封装成结构化的 Change artifacts，实现**需求到代码的完整追踪**。

**解决的核心问题**:
1. **Traceability**: 从需求到代码、测试、报告的完整追溯链
2. **Versioning**: 每个 Change 独立版本，支持回滚和对比
3. **Collaboration**: 支持与外部 AI 工具（Claude Code, Cursor）协作
4. **Auditability**: 变更历史可审计，符合企业规范

**对标**:
- OpenSpec官方: proposal + spec + tasks 结构
- Git: 类似 commit，但更高层（需求级别）
- RFC: 类似技术 RFC，但可执行

---

## Q2: OpenSpec Change 的目录结构是什么？

**标准结构**:
```
openspec/
├── project.md              # 项目元信息
├── specs/
│   └── main.md        # 主规格文档（已归档的 changes）
└── changes/
    └── <change-id>/
        ├── metadata.json        # Change 元数据
        ├── proposal.md          # 变更提案
        ├── tasks.md           # 任务清单
        ├── design.md            # 技术设计
        └── specs/
          └── spec.md          # 详细规格
```

**Change ID 格式**:
```
<change-type>-<feature-slug>-<timestamp>

示例:
feature-简化登录系统需求文档-20260604_162648
bugfix-修复用户认证失败-20260605_103020
refactor-重构数据库层-20260606_141030
```

**metadata.json**:
```json
{
  "change_id": "feature-简化登录系统需求文档-20260604_162648",
  "change_type": "feature",
  "title": "简化登录系统",
  "description": "实现基于用户名密码的登录认证",
  "status": "PROPOSED",
  "created_at": "2026-06-04T16:26:48",
  "language": "cpp",
  "project_type": "library",
  "requirements_file": "requirements/simple_login.md",
  "author": "DevPalAgent",
  "phase_range": "1-3"
}
```

---

## Q3: Phase 1 如何生成 OpenSpec Change？

**Phase 1 核心逻辑**:
```python
# devpal/core/openspec_phases/phase1_parse_requirements.py
class Phase1ParseRequirements:
    """Phase 1: 需求解析 + Change 生成"""
  
    def execute(self, context: OpenSpecContext) -> PhaseResult:
        # 1. 解析需求文档
        structured_reqs = self._parse_requirements(context.requirements_content)
        
        # 2. 生成 Delta (变更差异)
        delta = self._generate_delta(structured_reqs, context.baseline)
        
        # 3. 生成 Change Directory
      change_id = self._generate_change_directory(delta, structured_reqs)
        
        # 4. 存储 Change ID 到 context
     context.current_change_id = change_id
      context.current_change_dir = context.project_dir / "openspec/changes" / change_id
        
        return PhaseResult.ok(
            "需求文档解析成功",
            change_id=change_id,
            structured_requirements=structured_reqs,
            requirements_delta=delta
        )
    
    def _generate_change_directory(self, delta, reqs) -> str:
        """生成 Change 目录结构"""
        
        # 1. 确定 change_id
        change_type = self._infer_change_type(delta)
        feature_slug = self._extract_feature_slug(reqs)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        change_id = f"{change_type}-{feature_slug}-{timestamp}"
        
        # 2. 创建目录
        change_dir = self.context.project_dir / "openspec/changes" / change_id
        change_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. 生成 artifacts
        self._generate_proposal_md(change_dir, delta, change_id)
     self._generate_tasks_md(change_dir, reqs)
        self._generate_spec_md(change_dir, reqs)
        self._generate_metadata_json(change_dir, change_id, reqs)
        
        return change_id
```

**proposal.md 生成**:
```python
def _generate_proposal_md(self, change_dir, delta, change_id):
    """生成 proposal.md"""
    
    content = f"""# Change Proposal: {change_id}

## Overview
{self._extract_description(self.context.requirements_content)}

## Change Summary
- **Added Requirements**: {len(delta.added)}
- **Modified Requirements**: {len(delta.modified)}
- **Removed Requirements**: {len(delta.removed)}

## Added Requirements
{self._format_requirements(delta.added)}

## Rationale
{self._extract_rationale(self.context.requirements_content)}

## Risks
- Implementation complexity: MEDIUM
- Testing coverage: Full unit + integration tests required
- Deployment impact: New feature, no migration needed
"""
    
    (change_dir / "proposal.md").write_text(content, encoding="utf-8")
```

---

## Q4: AI-agnostic 协作模式如何使用 OpenSpec Change？

**三种协作模式**:

### 1. PROPOSE_ONLY 模式
```bash
# DevPalAgent 生成 Change artifacts
python run_ai_flow.py -r requirements/login.md --propose-only
```

**输出**:
```
openspec/changes/feature-login-20260604_162648/
├── metadata.json    # 元数据
├── proposal.md         # 变更提案
├── tasks.md            # 任务清单 ← Claude Code 读取
├── design.md           # 技术设计 ← Claude Code 读取
└── specs/spec.md       # 详细规格 ← Claude Code 读取

+ Rule Pack 文件（供外部 AI 工具）:
  - CLAUDE.md           # Claude Code 协作规则
  - .cursorrules        # Cursor 集成规则
  - cline-rules.md      # Cline 集成规则
```

**Claude Code 工作流**:
```
1. 读取 openspec/changes/<change-id>/tasks.md
2. 根据 tasks.md 逐个实现功能
3. 参考 design.md 了解架构设计
4. 参考 spec.md 了解详细规格
5. 实现时保持 traceability（在代码注释中添加 REQ-XXX）
```

### 2. APPLY_ONLY 模式
```bash
# DevPalAgent 从 Change artifacts 恢复并执行 Phase 4-11
python run_ai_flow.py --apply-change feature-login-20260604_162648
```

**内部流程**:
```python
# devpal/collaboration/change_loader.py
class ChangeLoader:
    """从 Change artifacts 恢复执行上下文"""
    
    def load(self, change_id: str) -> dict:
        change_dir = self._locate_change(change_id)
        
        # 1. 读取 metadata
     metadata = self._load_metadata(change_dir / "metadata.json")
     
        # 2. 恢复 requirements
        requirements_file = metadata["requirements_file"]
        requirements_content = Path(requirements_file).read_text()
        
        # 3. 恢复 design
        design_content = (change_dir / "design.md").read_text()
        
        # 4. 恢复 tasks
        tasks = self._parse_tasks(change_dir / "tasks.md")
        
        return {
            "change_id": change_id,
            "requirements_content": requirements_content,
          "tech_design_content": design_content,
            "tasks": tasks,
            "metadata": metadata
        }

# devpal/collaboration/context_restorer.py
class ContextRestorer:
    """恢复 OpenSpecContext"""
    
    def restore(self, change_data: dict) -> OpenSpecContext:
        context = OpenSpecContext(change_data["requirements_file"])
      
        # 恢复 Phase 1-3 的结果
        context.requirements_content = change_data["requirements_content"]
     context.tech_design_content = change_data["tech_design_content"]
        context.current_change_id = change_data["change_id"]
        
        return context
```

### 3. VALIDATE_ONLY 模式
```bash
# DevPalAgent 只运行 Phase 9-11 验证
python run_ai_flow.py --validate-change feature-login-20260604_162648
```

**验证流程**:
```
Phase 9: Quality Gate
  → 对比 spec.md，检查实现是否符合规格
  → 四层验证：FORMAT, SEMANTIC, PARSER, BUSINESS

Phase 10: Run Tests
  → 执行测试，验证功能正确性
  
Phase 11: Final Report
  → 生成验证报告
  → 对比 tasks.md，检查完成度
```

---

## Q5: OpenSpec Change 的 Archive 机制是什么？

**Archive 目标**:
将完成的 Change 归档到 main spec，实现长期追溯。

**Archive 流程**:
```python
# devpal/openspec/archive.py
class ChangeArchiver:
    """Change 归档器"""
    
    def archive(self, change_id: str) -> ArchiveResult:
        # 1. 加载 Change
        change_dir = self._locate_change(change_id)
        spec_content = (change_dir / "specs/spec.md").read_text()
      
        # 2. 合并到 main spec
        main_spec_path = Path("openspec/specs/main.md")
        self._merge_to_main_spec(main_spec_path, spec_content, change_id)
        
        # 3. 更新 metadata
        self._update_metadata(change_dir, status="ARCHIVED")
        
        # 4. 生成 coverage matrix
        coverage = self._generate_coverage_matrix(change_id)
        
        # 5. 更新 ArtifactGraph
     self._update_artifact_graph(change_id, coverage)
        
        # 6. 创建 archive manifest
        self._create_archive_manifest(change_id, coverage)
        
        return ArchiveResult(
            success=True,
            archived_change=change_id,
         coverage_matrix=coverage
        )
```

**Coverage Matrix**:
```markdown
# Coverage Matrix: feature-login-20260604_162648

| Requirement | Code | Test | Report |
|--------|------|------|------|
| REQ-001 用户登录 | ✅ src/auth.cpp:42 | ✅ tests/test_auth.cpp:15 | ✅ docs/final_report.md |
| REQ-002 密码验证 | ✅ src/auth.cpp:58 | ✅ tests/test_auth.cpp:30 | ✅ docs/final_report.md |
| REQ-003 会话管理 | ✅ src/session.cpp:20 | ✅ tests/test_session.cpp:10 | ✅ docs/final_report.md |

**Coverage**: 100% (3/3)
**Traceability**: Complete
**Status**: ARCHIVED
```

---

## Q6: OpenSpec Change 与 Git 的对比？

**对比表**:

| 维度 | Git Commit | OpenSpec Change |
|------|--------|----------------|
| **粒度** | 代码行级别 | 需求级别 |
| **内容** | Code diff | Requirements + Design + Code + Tests |
| **追踪** | 文件变更 | Requirement → Code → Test |
| **协作** | Branch + PR | Propose → Apply → Validate |
| **审查** | Code Review | Spec Review + Code Review |
| **归档** | Git log | Archive + Coverage Matrix |

**互补关系**:
```
OpenSpec Change (需求层)
  ↓ implements
Git Commits (代码层)
  ↓ deployed
Production Release (部署层)
```

**最佳实践**:
```bash
# 1. 生成 Change
python run_ai_flow.py -r requirements/feature.md --propose-only

# 2. 实现代码（多个 git commits）
git commit -m "feat: implement user login (REQ-001)"
git commit -m "feat: add password validation (REQ-002)"
git commit -m "test: add auth tests (REQ-001, REQ-002)"

# 3. 验证 Change
python run_ai_flow.py --validate-change feature-xxx

# 4. 归档 Change
python -m devpal.openspec archive feature-xxx

# 5. 创建 PR (关联 Change ID)
gh pr create --title "Feature: User Authentication" \
  --body "Implements OpenSpec Change: feature-xxx\nCoverage: 100%"
```

---

## 面试展示脚本

**开场**:
"OpenSpec Change 是 DevPalAgent 实现 Spec-first Development 的核心机制，它将需求变更结构化，实现完整的追溯链。"

**技术深度展示**:
1. "Change artifacts: proposal + tasks + design + spec，完整的需求表达"
2. "AI-agnostic 协作：PROPOSE → (External AI) → VALIDATE，三方协作"
3. "Archive 机制：Change → Main Spec + Coverage Matrix，长期追踪"
4. "与 Git 互补：需求层（OpenSpec）+ 代码层（Git）双层版本控制"

**代码展示**:
- `devpal/core/openspec_phases/phase1_parse_requirements.py` - Change 生成
- `devpal/collaboration/change_loader.py` - Change 加载
- `devpal/openspec/archive.py` - Archive 机制

**亮点总结**:
- 📋 **结构化变更**: proposal + tasks + design + spec
- 🔗 **完整追溯**: Requirement → Code → Test → Report
- 🤝 **AI-agnostic**: 与外部 AI 工具无缝协作
- 📊 **Coverage Matrix**: 100% 需求覆盖度追踪
