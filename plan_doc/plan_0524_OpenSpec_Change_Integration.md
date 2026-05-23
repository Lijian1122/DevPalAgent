# OpenSpec Change 完整集成实施计划

**日期**：2026-05-24  
**目标**：实现 OpenSpec Changes 完整集成，生成 change 目录结构  
**预期收益**：团队协作能力展示，变更追踪完整性，面试核心亮点

---

## 1. 背景与目标

### 1.1 当前问题

**OpenSpec Changes 现状**：
- ✅ **Phase 1 有代码**：`_generate_change_directory()` 方法已实现
- ❌ **但未执行**：条件检查 `if not delta["changed"]` 导致提前返回
- ❌ **目录不存在**：实际文件系统中找不到 `openspec/changes/` 目录
- ❌ **集成不完整**：Phase 3/4/11 未读取或引用 change artifacts

**具体缺口**：
1. **代码存在但不工作**：Phase 1 的变更目录生成逻辑被跳过
2. **缺少完整流程**：Phase 3 不输出 design.md，Phase 4 不读取 specs
3. **缺少追踪**：Phase 11 Final Report 不显示 change-id
4. **面试故事不完整**：无法展示"团队协作平台"能力

**外部建议**（TEST20260516.md）：
> "OpenSpec Changes 代码存在但未执行。这导致项目看起来像'单人工具'而非'团队协作平台'。补齐这个能力，证明适配真实企业研发流程（Proposal→Approval→Apply→Validation）。"

### 1.2 设计目标

**核心理念**：
> OpenSpec Changes 是变更隔离和追踪的核心模型，每次运行生成独立的 change 目录，包含 proposal、specs、tasks、design，支持团队协作和变更审批流程。

**设计原则**：
1. **变更隔离**：每个 change 独立目录，互不干扰
2. **完整追踪**：从 proposal 到 design 到 code 全链路
3. **可审批**：proposal.md 可供人工审批
4. **可归档**：完成后可 merge 到 main spec

### 1.3 预期收益

| 指标 | 当前 | 目标 | 说明 |
|---|:---:|:---:|---|
| Change 目录生成 | 0% | 100% | 每次运行生成完整目录 |
| Proposal 生成 | 否 | 是 | proposal.md 包含变更提案 |
| Specs 生成 | 否 | 是 | specs/spec.md 采用 ADDED/MODIFIED/REMOVED 格式 |
| Tasks 生成 | 否 | 是 | tasks.md 包含任务清单 |
| Design 输出 | 否 | 是 | Phase 3 输出 design.md |
| Phase 4 读取 | 否 | 是 | 读取 specs 和 tasks 作为上下文 |
| Final Report 引用 | 否 | 是 | 显示 change-id 和文件列表 |

**面试价值**：
- 🏆 **团队协作能力**：不是单人工具，而是团队协作平台
- 💡 **OpenSpec 规范遵循**：完整实现 proposal/specs/tasks/design 结构
- 🔥 **企业研发流程**：Proposal→Approval→Apply→Validation 闭环
- 📊 **变更追踪**：change-id 生成 + ADDED/MODIFIED/REMOVED 格式

---

## 2. OpenSpec Change 模型详解

### 2.1 目录结构

**完整结构**：
```
openspec/
├── project.md                  # 项目元信息
├── specs/
│   └── main.md           # 主规范（归档后的累积）
└── changes/
    └── <change-id>/
        ├── proposal.md           # 变更提案
        ├── specs/
        │   └── spec.md           # 变更规范（ADDED/MODIFIED/REMOVED）
        ├── tasks.md        # 任务清单
        ├── design.md      # 技术设计
        └── metadata.json         # 变更元数据
```

### 2.2 change-id 生成规则

**格式**：`<type>-<feature>-<timestamp>-<hash>`

**示例**：
- `feat-login-20260524_143022-a3f2b1` - 新增登录功能
- `fix-auth-20260524_150315-9c4e7d` - 修复认证问题
- `refactor-api-20260524_162045-2b8f3a` - 重构 API 层

**生成逻辑**：
```python
def generate_change_id(requirements: dict) -> str:
    change_type = infer_type(requirements)  # feat/fix/refactor/docs
    feature_slug = slugify(requirements["title"])[:20]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    content_hash = hashlib.sha256(
        json.dumps(requirements, sort_keys=True).encode()
    ).hexdigest()[:6]
    return f"{change_type}-{feature_slug}-{timestamp}-{content_hash}"
```

**类型推断**：
```python
def infer_type(requirements: dict) -> str:
    title = requirements.get("title", "").lower()
    description = requirements.get("description", "").lower()
    
    if any(kw in title or kw in description for kw in ["新增", "添加", "实现", "add", "implement"]):
        return "feat"
    elif any(kw in title or kw in description for kw in ["修复", "解决", "fix", "resolve"]):
        return "fix"
    elif any(kw in title or kw in description for kw in ["重构", "优化", "refactor", "optimize"]):
        return "refactor"
    elif any(kw in title or kw in description for kw in ["文档", "说明", "docs", "documentation"]):
        return "docs"
    else:
        return "feat"  # 默认为 feat
```

### 2.3 文件内容格式

#### proposal.md

```markdown
# Change Proposal: {title}

**Change ID**: {change-id}  
**Type**: {feat/fix/refactor/docs}  
**Created**: {timestamp}  
**Status**: proposed

---

## 1. 变更概述

{简要描述变更内容}

## 2. 变更原因

{为什么需要这个变更}

## 3. 影响范围

- 新增文件：{list}
- 修改文件：{list}
- 删除文件：{list}

## 4. 风险评估

- 兼容性风险：{评估}
- 性能影响：{评估}
- 安全影响：{评估}

## 5. 审批清单

- [ ] 技术负责人审批
- [ ] 架构师审批
- [ ] 安全审查通过
```

#### specs/spec.md

```markdown
# Change Specification: {title}

**Change ID**: {change-id}

---

## ADDED

### File: src/User.h
```cpp
class User {
public:
    User(const std::string& username);
    bool login(const std::string& password);
};
```

### File: src/User.cpp
```cpp
#include "User.h"
// Implementation...
```

## MODIFIED

### File: src/main.cpp
```diff
- // Old code
+ // New code
```

## REMOVED

### File: src/OldAuth.cpp
```cpp
// This file will be removed
```
```

#### tasks.md

```markdown
# Task List: {title}

**Change ID**: {change-id}

---

## Phase 1: 需求分析
- [x] 解析需求文档
- [x] 生成结构化需求
## Phase 2: 目录结构
- [ ] 创建 src/ 目录
- [ ] 创建 include/ 目录

## Phase 3: 技术设计
- [ ] 设计 User 类
- [ ] 设计 Database 接口

## Phase 4: 代码生成
- [ ] 生成 User.h
- [ ] 生成 User.cpp
- [ ] 生成 Database.h

## Phase 5: 测试生成
- [ ] 生成 test_user.cpp
- [ ] 生成 test_database.cpp
```

#### design.md

```markdown
# Technical Design: {title}

**Change ID**: {change-id}

---

## 1. 架构设计

### 1.1 模块划分
- User 模块：用户管理
- Database 模块：数据持久化

### 1.2 类图
```
User
  ├─ username: string
  ├─ password_hash: string
  └─ login(password): bool

Database
  ├─ connect(): bool
  ├─ query(sql): Result
  └─ close(): void
```

## 2. 接口设计

### 2.1 User 类
```cpp
class User {
public:
    User(const std::string& username);
    bool login(const std::string& password);
    bool logout();
private:
    std::string username_;
    std::string password_hash_;
};
```

## 3. 数据库设计

### 3.1 users 表
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. 安全设计

- 密码使用 bcrypt 加密
- SQL 使用参数化查询
- 输入验证和长度限制
```

#### metadata.json

```json
{
  "change_id": "feat-login-20260524_143022-a3f2b1",
  "type": "feat",
  "title": "实现用户登录功能",
  "created_at": "2026-05-24T14:30:22Z",
  "status": "proposed",
  "author": "DevPalAgent",
  "files_added": ["src/User.h", "src/User.cpp"],
  "files_modified": ["src/main.cpp"],
  "files_removed": [],
  "requirements_hash": "a3f2b1c4d5e6",
  "tech_design_hash": "f7g8h9i0j1k2"
}
```

---

## 3. 系统设计

### 3.1 Phase 1 改造

**当前问题**：
```python
# devpal/core/openspec_phases/phase1_parse_requirements.py

def execute(self, context):
    # ... 解析需求 ...
    
    # 问题：这个条件检查导致提前返回
    if not delta.get("changed", False):
        self.logger.info("No changes detected, skipping change directory generation")
        return result  # ← 提前返回，_generate_change_directory() 未执行
    
    # 这段代码永远不会执行
    self._generate_change_directory(context, delta)
```

**解决方案**：
```python
def execute(self, context):
    # ... 解析需求 ...
    
    # 修复：总是生成 change 目录
    change_id = self._generate_change_id(context)
    context.current_change_id = change_id
    
    # 生成 change 目录结构
    self._generate_change_directory(context, change_id, delta)
    
    return result
```

**实现细节**：
```python
def _generate_change_directory(self, context, change_id, delta):
    """生成 OpenSpec Change 目录结构"""
    change_dir = context.workspace_path / "openspec" / "changes" / change_id
    change_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 生成 proposal.md
    self._generate_proposal(context, change_dir, delta)
    
    # 2. 生成 specs/spec.md
    self._generate_spec(context, change_dir, delta)
    
    # 3. 生成 tasks.md
    self._generate_tasks(context, change_dir, delta)
    
    # 4. 生成 metadata.json
    self._generate_metadata(context, change_dir, change_id, delta)
    
    self.logger.info(f"Generated change directory: {change_dir}")
```

### 3.2 Phase 3 改造

**目标**：输出 design.md 到 change 目录

**实现**：
```python
# devpal/core/openspec_phases/phase3_technical_design.py

def execute(self, context):
    # ... 生成技术设计 ...
    
    tech_design = self._generate_tech_design(context)
    context.tech_design_content = tech_design
    
    # 新增：输出 design.md 到 change 目录
    if hasattr(context, 'current_change_id'):
        self._save_design_to_change(context, tech_design)
    
    return result

def _save_design_to_change(self, context, tech_design):
    """保存 design.md 到 change 目录"""
    change_id = context.current_change_id
    change_dir = context.workspace_path / "openspec" / "changes" / change_id
    design_path = change_dir / "design.md"
    
    design_content = f"""# Technical Design: {context.requirements_content.get('title', 'Untitled')}

**Change ID**: {change_id}

---

{tech_design}
"""
    
    design_path.write_text(design_content, encoding='utf-8')
    self.logger.info(f"Saved design.md to {design_path}")
```

### 3.3 Phase 4 改造

**目标**：读取 change artifacts 作为上下文

**实现**：
```python
# devpal/core/openspec_phases/phase4_generate_code.py

def execute(self, context):
    # 新增：读取 change artifacts
    change_context = self._load_change_context(context)
    
    # 生成代码时使用 change context
    for file_info in files_to_generate:
        code = self._generate_file(context, file_info, change_context)
        # ...
    
    return result

def _load_change_context(self, context):
    ""加载 change artifacts 作为上下文"""
    if not hasattr(context, 'current_change_id'):
      return {}
    
    change_id = context.current_change_id
    change_dir = context.workspace_path / "openspec" / "changes" / change_id
    
    change_context = {}
    
    # 读取 specs/spec.md
    spec_path = change_dir / "specs" / "spec.md"
    if spec_path.exists():
        change_context['spec'] = spec_path.read_text(encoding='utf-8')
    
    # 读取 tasks.md
    tasks_path = change_dir / "tasks.md"
    if tasks_path.exists():
        change_context['tasks'] = tasks_path.read_text(encoding='utf-8')
    
    # 读取 design.md
    design_path = change_dir / "design.md"
    if design_path.exists():
        change_context['design'] = design_path.read_text(encoding='utf-8')
    
    return change_context

def _generate_file(self, context, file_info, change_context):
    """生成单个文件，使用 change context"""
    # 构建 prompt 时引用 change context
    prompt = f"""
生成文件：{file_info['path']}

**变更规范**：
{change_context.get('spec', 'N/A')[:500]}...

**任务清单**：
{change_context.get('tasks', 'N/A')[:300]}...

**技术设计**：
{change_context.get('design', 'N/A')[:500]}...
请生成符合规范的代码。
"""
    
    # 调用 LLM
    code = self.llm_client.generate_with_tool_loop(
        system=system_prompt,
        cached_context=[
            context.requirements_content,
         context.tech_design_content,
            change_context.get('spec', '')  # 缓存 spec
        ],
        user_message=prompt,
        tools=[write_file_tool]
    )
    
    return code
```

### 3.4 Phase 11 改造

**目标**：在 Final Report 中引用 change-id 和文件列表

**实现**：
```python
# devpal/core/openspec_phases/phase11_final_report.py

def _add_change_artifacts_section(self, context):
    """添加 Change Artifacts 章节"""
    if not hasattr(context, 'current_change_id'):
     return ""
    
    change_id = context.current_change_id
    change_dir = context.workspace_path / "openspec" / "changes" / change_id
    
    # 列出所有文件
    files = []
    if change_dir.exists():
        for file_path in change_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(context.workspace_path)
         files.append(str(rel_path))
    
    files_list = "\n".join(f"- [{f}]({f})" for f in sorted(files))
    
    return f"""
## Change Artifacts

**Change ID**: `{change_id}`

**Generated Files**:
{files_list}

**Change Directory**: `openspec/changes/{change_id}/`

**Contents**:
- `proposal.md` - 变更提案
- `specs/spec.md` - 变更规范（ADDED/MODIFIED/REMOVED）
- `tasks.md` - 任务清单
- `design.md` - 技术设计
- `metadata.json` - 变更元数据
"""
```

---

## 4. 实施计划

### 4.1 Task 1: 调试 Phase 1 变更目录生成（0.5天）

**目标**：确保 `_generate_change_directory()` 正确执行

**实施步骤**：

1. **定位问题**（1小时）
   - 阅读 `phase1_parse_requirements.py`
   - 找到 `if not delta["changed"]` 条件检查
   - 确认为什么会提前返回

2. **修复逻辑**（2小时）
   - 移除或修改条件检查
   - 确保 `_generate_change_directory()` 总是执行
   - 实现 `_generate_change_id()` 方法

3. **实现文件生成**（3小时）
   - `_generate_proposal()` - 生成 proposal.md
   - `_generate_spec()` - 生成 specs/spec.md
   - `_generate_tasks()` - 生成 tasks.md
   - `_generate_metadata()` - 生成 metadata.json

4. **测试验证**（2小时）
   ```bash
   python test_simple.py
   
   # 验证：
   # 1. openspec/changes/{change-id}/ 目录存在
   # 2. proposal.md 存在且内容正确
   # 3. specs/spec.md 存在且采用 ADDED/MODIFIED/REMOVED 格式
   # 4. tasks.md 存在且包含任务清单
   # 5. metadata.json 存在且格式正确
   ```

**验收标准**：
```bash
# 测试 1: 运行完整流程
python test_simple.py

# 验证目录结构
ls openspec/changes/
ls openspec/changes/feat-*-*/

# 验证文件存在
ls openspec/changes/feat-*-*/proposal.md
ls openspec/changes/feat-*-*/specs/spec.md
ls openspec/changes/feat-*-*/tasks.md
ls openspec/changes/feat-*-*/metadata.json

# 验证内容格式
cat openspec/changes/feat-*-*/specs/spec.md | grep "## ADDED"
cat openspec/changes/feat-*-*/specs/spec.md | grep "## MODIFIED"
cat openspec/changes/feat-*-*/specs/spec.md | grep "## REMOVED"
```

### 4.2 Task 2: Phase 3 输出 design.md（0.5天）

**目标**：在技术设计生成后，写入 design.md

**实施步骤**：

1. **修改 Phase 3**（2小时）
   - 在 `execute()` 方法末尾添加 `_save_design_to_change()`
   - 实现 `_save_design_to_change()` 方法
   - 格式化 design.md 内容

2. **测试验证**（2小时）
   ```bash
   python test_simple.py
   
   # 验证：
   # 1. openspec/changes/{change-id}/design.md 存在
   # 2. 内容包含技术设计
   # 3. 格式正确（包含 Change ID）
   ```

**验收标准**：
```bash
# 验证 design.md 存在
ls openspec/changes/feat-*-*/design.md

# 验证内容
cat openspec/changes/feat-*-*/design.md | head -20

# 验证包含 Change ID
grep "Change ID" openspec/changes/feat-*-*/design.md
```

### 4.3 Task 3: Phase 4 读取 change artifacts（0.5天）

**目标**：读取 specs 和 tasks 作为代码生成上下文

**实施步骤**：

1. **实现 _load_change_context()**（2小时）
   - 读取 specs/spec.md
   - 读取 tasks.md
   - 读取 design.md
   - 返回 dict

2. **修改 _generate_file()**（2小时）
   - 在 prompt 中引用 change context
   - 使用 Prompt Caching 缓存 spec

3. **测试验证**（1小时）
   ```bash
   python test_simple.py
   
   # 验证：
   # 1. Phase 4 日志显示读取了 change artifacts
   # 2. 生成的代码符合 spec 规范
   ```

**验收标准**：
```bash
# 验证日志
grep "Loading change context" logs/openspec.log
grep "Loaded spec.md" logs/openspec.log

# 验证生成的代码
cat src/User.cpp | head -20
```

### 4.4 Task 4: Phase 11 引用 change-id（0.5天）

**目标**：在 Final Report 中显示 change-id 和文件列表

**实施步骤**：

1. **实现 _add_change_artifacts_section()**（2小时）
   - 读取 change_id
   - 列出 change 目录下的所有文件
   - 格式化为 Markdown

2. **集成到 Final Report**（1小时）
   - 在 `_generate_report()` 中调用
   - 添加到报告的合适位置

3. **测试验证**（1小时）
   ```bash
   python test_simple.py
   
   # 验证：
   # 1. final_report.md 包含 "Change Artifacts" 章节
   # 2. 显示 change-id
   # 3. 列出所有文件
   ```

**验收标准**：
```bash
# 验证 Final Report
cat docs/final_report.md | grep "Change Artifacts"
cat docs/final_report.md | grep "Change ID"
cat docs/final_report.md | grep "proposal.md"
```

---
## 5. 数据流设计

### 5.1 完整数据流

```
Phase 1: Parse Requirements
  ↓
  生成 change-id
  ↓
  创建 openspec/changes/{change-id}/
  ├─ proposal.md
  ├─ specs/spec.md
  ├─ tasks.md
  └─ metadata.json
  ↓
  context.current_change_id = change-id
  ↓
Phase 3: Technical Design
  ↓
  生成 tech_design
  ↓
  保存到 openspec/changes/{change-id}/design.md
  ↓
Phase 4: Generate Code
  ↓
  读取 change artifacts:
  ├─ specs/spec.md
  ├─ tasks.md
  └─ design.md
  ↓
  使用 change context 生成代码
  ↓
Phase 11: Final Report
  ↓
  引用 change-id
  ↓
  列出 change 目录下的所有文件
  ↓
  生成 "Change Artifacts" 章节
```

### 5.2 Context 字段

```python
class OpenSpecContext:
    # 新增字段
    current_change_id: Optional[str] = None  # 当前 change-id
    change_metadata: Optional[dict] = None   # 变更元数据
```

---

## 6. 验收标准

### 6.1 功能验收

**必须满足**：
- ✅ Phase 1 生成 change 目录
- ✅ proposal.md 存在且格式正确
- ✅ specs/spec.md 存在且采用 ADDED/MODIFIED/REMOVED 格式
- ✅ tasks.md 存在且包含任务清单
- ✅ metadata.json 存在且格式正确
- ✅ Phase 3 输出 design.md
- ✅ Phase 4 读取 change artifacts
- ✅ Phase 11 引用 change-id

**可选满足**：
- ⏳ 支持多次运行（不覆盖已有 change）
- ⏳ 支持 change 归档（merge 到 main spec）
- ⏳ 支持 change 状态管理（proposed/approved/applied）

### 6.2 质量验收

**目录结构正确性**：
- ✅ change-id 格式正确（type-feature-timestamp-hash）
- ✅ 目录结构完整（proposal/specs/tasks/design/metadata）
- ✅ 文件格式正确（Markdown/JSON）

**内容正确性**：
- ✅ proposal.md 包含变更概述、原因、影响范围
- ✅ specs/spec.md 采用 ADDED/MODIFIED/REMOVED 格式
- ✅ tasks.md 包含 Phase 1-11 的任务清单
- ✅ design.md 包含技术设计内容
- ✅ metadata.json 包含完整元数据

### 6.3 集成验收

**Phase 集成**：
- ✅ Phase 1 生成 change 目录
- ✅ Phase 3 输出 design.md
- ✅ Phase 4 读取 change artifacts
- ✅ Phase 11 引用 change-id

**日志验证**：
```bash
grep "Generated change directory" logs/openspec.log
grep "Saved design.md" logs/openspec.log
grep "Loading change context" logs/openspec.log
grep "Change Artifacts" docs/final_report.md
```

---

## 7. 面试价值

### 7.1 技术亮点

**1. OpenSpec 规范遵循**
> "我完整实现了 OpenSpec Changes 模型，每次运行生成独立的 change 目录，包含 proposal、specs、tasks、design。这证明项目不是单人开发工具，而是适配真实企业研发流程的团队协作平台。"

**2. 变更隔离和追踪**
> "每个 change 有独立的 change-id，采用 type-feature-timestamp-hash 格式，确保唯一性和可读性。specs/spec.md 采用 ADDED/MODIFIED/REMOVED 格式，清晰展示变更内容。"

**3. 团队协作流程**
> "proposal.md 可供人工审批，支持 Proposal→Approval→Apply→Validation 闭环。这展示了对企业研发流程的理解。"

**4. 完整集成**
> "Phase 1 生成 change 目录，Phase 3 输出 design.md，Phase 4 读取 change artifacts 作为上下文，Phase 11 引用 change-id。全流程集成，不是孤立功能。"

### 7.2 面试话术

**Q: 你的项目如何支持团队协作？**
> "DevPalAgent 实现了 OpenSpec Changes 模型。每次运行生成独立的 change 目录，包含 proposal（可供审批）、specs（ADDED/MODIFIED/REMOVED 格式）、tasks（任务清单）、design（技术设计）。这支持 Proposal→Approval→Apply→Validation 的企业研发流程，不是单人工具，而是团队协作平台。"

**Q: 如何追踪变更？**
> "每个 change 有唯一的 change-id（type-feature-timestamp-hash 格式），所有 artifacts 都在 openspec/changes/{change-id}/ 目录下。Phase 4 读取 specs 作为代码生成上下文，Phase 11 在 Final Report 中引用 change-id 和文件列表。全链路追踪，从需求到代码。"

**Q: 与 OpenSpec 规范的关系？**
> "完全遵循 OpenSpec 规范。proposal/specs/tasks/design 结构、ADDED/MODIFIED/REMOVED 格式、change-id 生成规则，都符合 OpenSpec 标准。这证明项目不是自创规范，而是遵循业界标准。"

### 7.3 演示脚本

**Demo: OpenSpec Change 演示**（2分钟）

```bash
# 1. 运行完整流程
python test_simple.py

# 2. 展示 change 目录结构
tree openspec/changes/feat-*-*/

# 3. 展示 proposal.md
cat openspec/changes/feat-*-*/proposal.md | head -30

# 4. 展示 specs/spec.md（ADDED/MODIFIED/REMOVED 格式）
cat openspec/changes/feat-*-*/specs/spec.md | head -50

# 5. 展示 Final Report 中的 Change Artifacts 章节
cat docs/final_report.md | grep -A 20 "Change Artifacts"
```

**预期输出**：
```
openspec/changes/feat-login-20260524_143022-a3f2b1/
├── proposal.md
├── specs/
│   └── spec.md
├── tasks.md
├── design.md
└── metadata.json

Change ID: feat-login-20260524_143022-a3f2b1
Type: feat
Status: proposed

## ADDED
### File: src/User.h
### File: src/User.cpp

## MODIFIED
### File: src/main.cpp
```

---

## 8. 风险和缓解

### 8.1 风险识别

**风险 1：change-id 冲突**
- **描述**：多次运行可能生成相同的 change-id
- **影响**：覆盖已有 change 目录
- **概率**：低（timestamp + hash 确保唯一性）
- **缓解**：
  1. 使用 timestamp（精确到秒）
  2. 使用 content hash（6 位）
  3. 检查目录是否存在，存在则追加序号

**风险 2：文件格式不规范**
- **描述**：LLM 生成的 specs/spec.md 格式不符合 ADDED/MODIFIED/REMOVED
- **影响**：无法正确解析
- **概率**：中等
- **缓解**：
  1. 在 Prompt 中强调格式要求
  2. 实现格式验证和修复
  3. 提供默认模板
**风险 3：Phase 4 读取失败**
- **描述**：change artifacts 文件不存在或格式错误
- **影响**：Phase 4 无法使用 change context
- **概率**：低
- **缓解**：
  1. 检查文件是否存在
  2. 提供默认值
  3. 记录警告日志

**风险 4：Final Report 引用错误**
- **描述**：change-id 不存在或文件列表为空
- **影响**：Final Report 显示不完整
- **概率**：低
- **缓解**：
  1. 检查 context.current_change_id 是否存在
  2. 检查 change 目录是否存在
  3. 提供默认文本

### 8.2 回退方案

**如果 change 目录生成失败**：
1. 记录错误日志
2. 跳过 change 目录生成，继续后续流程
3. 在 Final Report 中标注 "Change directory generation failed"

**如果 Phase 4 读取失败**：
1. 记录警告日志
2. 使用默认上下文（requirements + tech_design）
3. 继续代码生成

---

## 9. 后续优化方向

### 9.1 短期优化（1-2周）

1. **change 状态管理**：proposed → approved → applied → archived
2. **change 归档**：merge 到 main spec
3. **change 冲突检测**：检测多个 change 是否修改同一文件

### 9.2 中期优化（1-2月）

1. **change 审批流程**：集成 GitHub PR / GitLab MR
2. **change 回滚**：支持回滚到之前的 change
3. **change 依赖**：支持 change 之间的依赖关系

### 9.3 长期优化（3-6月）

1. **change 可视化**：Web UI 展示 change 历史
2. **change 分析**：统计 change 类型、频率、影响范围
3. **change 推荐**：基于历史 change 推荐相似变更

---

## 10. 总结

### 10.1 核心价值

**OpenSpec Change 完整集成**：
1. **变更隔离**：每个 change 独立目录，互不干扰
2. **完整追踪**：从 proposal 到 design 到 code 全链路
3. **团队协作**：支持 Proposal→Approval→Apply→Validation 闭环
4. **规范遵循**：完全符合 OpenSpec 标准

### 10.2 面试故事完整性

**已具备的核心能力**（10/10）：
- ✅ Agent Workflow Orchestration（11 阶段 + Skills）
- ✅ Tool Use（Phase 4 tool loop）
- ✅ State Management（OpenSpecContext + checkpoint）
- ✅ Prompt Engineering（PromptEngine + Caching）
- ✅ Multi-Agent Collaboration（Skills 系统）
- ✅ Evaluation（Phase 9/10/11 + Critique Phase）
- ✅ Memory System（三层架构）
- ✅ Reliability（retry/checkpoint/self-healing）
- ✅ **Change Management**（OpenSpec Changes）← 本次补齐
- ✅ Traceability（ArtifactGraph + change-id）

**完成度**：10/10（100%）

### 10.3 关键文件清单

**新增文件**：
- `openspec/changes/{change-id}/proposal.md`
- `openspec/changes/{change-id}/specs/spec.md`
- `openspec/changes/{change-id}/tasks.md`
- `openspec/changes/{change-id}/design.md`
- `openspec/changes/{change-id}/metadata.json`

**修改文件**：
- `devpal/core/openspec_phases/phase1_parse_requirements.py` - 生成 change 目录
- `devpal/core/openspec_phases/phase3_technical_design.py` - 输出 design.md
- `devpal/core/openspec_phases/phase4_generate_code.py` - 读取 change artifacts
- `devpal/core/openspec_phases/phase11_final_report.py` - 引用 change-id
- `devpal/core/openspec_phases/base.py` - 添加 current_change_id 字段

---

**文档版本**：v1.0  
**创建日期**：2026-05-24  
**预计完成**：2026-05-26（1-2 天）  
**负责人**：DevPalAgent Team
