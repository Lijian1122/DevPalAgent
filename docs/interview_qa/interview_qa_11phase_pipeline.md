# Interview Q&A: OpenSpec 11-Phase Pipeline

## 面试专题：OpenSpec 确定性流水线设计

---

## Q1: OpenSpec 11-Phase Pipeline 是什么？

**核心回答**:
OpenSpec 11-Phase Pipeline 是 DevPalAgent 实现 Spec-first Development 的核心流程，将需求文档转换为可交付软件项目的确定性流水线。

**11 个阶段**:
```
Phase 1  → Parse Requirements     (需求解析)
Phase 2  → Create Structure       (项目结构)
Phase 3  → Technical Design       (技术设计)
Phase 4  → Generate Code          (代码生成，支持 Multi-Agent)
Phase 5  → Generate Tests         (测试生成，支持 Multi-Agent)
Phase 6  → Build Configuration    (构建配置)
Phase 7  → Test Documentation     (测试文档)
Phase 8  → README Documentation   (README)
Phase 9  → Quality Gate           (质量门禁)
Phase 10 → Run Tests              (测试执行)
Phase 11 → Final Report         (最终报告)
```

**为什么需要11个阶段**:
- **可追踪**: 每个阶段输入输出明确
- **可恢复**: Checkpoint 可在任意阶段恢复
- **可验证**: 每个阶段有成功/失败标准
- **可优化**: 针对性优化瓶颈阶段

---

## Q2: 各阶段的详细职责是什么？

### Phase 1: Parse Requirements
```python
# 输入: requirements.md
# 输出: structured_requirements, delta.json, change_id

def phase1_execute(context):
    # 1. 读取需求文档
  content = Path(context.requirements_file).read_text()
    
    # 2. 解析结构化需求
    structured_reqs = parse_structured_requirements(content)
    # - id, title, description
    # - acceptance_criteria
    # - priority, status
    
    # 3. 生成 Delta（变更差异）
    delta = generate_delta(structured_reqs, context.baseline)
    # - added: 新增需求
    # - modified: 修改需求
    # - removed: 删除需求
    
    # 4. 生成 OpenSpec Change
    change_id = generate_change_directory(delta)
    
    return PhaseResult(
        structured_requirements=structured_reqs,
        requirements_delta=delta,
        change_id=change_id
    )
```

### Phase 2: Create Structure
```python
# 输入: structured_requirements, language
# 输出: project_structure

def phase2_execute(context):
    # 根据语言创建目录结构
    if context.language == "cpp":
        create_directories(["include/", "src/", "tests/", "build/"])
        create_file("CMakeLists.txt")
    elif context.language == "python":
        create_directories(["src/", "tests/", "docs/"])
    create_file("setup.py")
    
    # 写入 requirements.json
    write_spec_file(".spec/requirements.json", context.structured_requirements)
    
    return PhaseResult(project_structure="created")
```

### Phase 3: Technical Design
```python
# 输入: structured_requirements
# 输出: tech_design_content

def phase3_execute(context):
    # LLM 生成技术设计文档
    design = llm_client.create_message(
        system="You are a software architect...",
        messages=[{
         "role": "user",
          "content": f"Design architecture for:\n{context.structured_requirements}"
        }]
    )
  
    # 保存设计文档
    write_file("docs/技术实现文档.md", design)
    write_file(f"openspec/changes/{context.change_id}/design.md", design)
    
   return PhaseResult(tech_design_content=design)
```

### Phase 4: Generate Code (Multi-Agent)
```python
# 输入: tech_design_content, structured_requirements
# 输出: generated_files

def phase4_execute(context):
    # 1. 基础设施代码（模板）
    infra_files = generate_infrastructure_templates(context.language)
    
    # 2. 业务代码（LLM 生成）
    if context.enable_multi_agent:
        # 多智能体并行生成
       files = multi_agent_code_generation(
            design=context.tech_design_content,
       requirements=context.structured_requirements,
          pool_size=4
        )
    else:
        # 顺序生成
        files = sequential_code_generation(context)
    
    return PhaseResult(generated_files=infra_files + files)
```

### Phase 5-8: 测试、构建、文档
```python
# Phase 5: 生成测试代码（支持 Multi-Agent）
# Phase 6: 生成 CMakeLists.txt / setup.py
# Phase 7: 生成测试文档
# Phase 8: 生成 README.md
```

### Phase 9: Quality Gate
```python
# 输入: generated_files
# 输出: quality_gate_report

def phase9_execute(context):
    issues = []
    
    # L1: FORMAT 验证
    issues += validate_format(context.generated_files)
    
    # L2: SEMANTIC 验证
    issues += validate_semantic(context.generated_files)
    
    # L3: PARSER 验证
    issues += validate_parser(context.generated_files)
    
    # L4: BUSINESS 验证
    issues += validate_business_rules(context.generated_files, context.structured_requirements)
    
    if issues:
        return PhaseResult.fail("Quality Gate failed", issues=issues)
    
  return PhaseResult.ok("Quality Gate passed")
```

### Phase 10: Run Tests
```python
# 输入: generated_files
# 输出: test_result, test_summary

def phase10_execute(context):
    if context.language == "cpp":
      result = run_cpp_tests(context.project_dir / "tests")
    elif context.language == "python":
        result = run_pytest(context.project_dir / "tests")
    
    return PhaseResult(
        test_result=result,
        test_summary={
         "total": result.total,
            "passed": result.passed,
            "failed": result.failed,
            "skipped": result.skipped
        }
    )
```

### Phase 11: Final Report
```python
# 输入: 所有 phase_results
# 输出: final_report, artifact_graph

def phase11_execute(context):
    # 1. 生成最终报告
    report = generate_final_report(context)
    
    # 2. 生成 ArtifactGraph
    graph = generate_artifact_graph(context)
    
    # 3. 生成 CLAUDE.md
    claude_md = generate_claude_md(context)
    
    return PhaseResult(
        final_report=report,
        artifact_graph=graph,
        claude_md=claude_md
    )
```

---

## Q3: Phase 间的依赖关系是什么？

**依赖图**:
```
Phase 1 (Parse Requirements)
    ↓ structured_requirements, delta
Phase 2 (Create Structure)
    ↓ project_structure
Phase 3 (Technical Design)
    ↓ tech_design_content
Phase 4 (Generate Code) ←━━┓
    ↓ generated_files      ┃ 并行
Phase 5 (Generate Tests) ←━┛
    ↓ test_files
Phase 6-8 (Build/Docs)
    ↓ build_config, docs
Phase 9 (Quality Gate)
    ↓ quality_report
Phase 10 (Run Tests)
    ↓ test_results
Phase 11 (Final Report)
    ↓ deliverables
```

**关键依赖**:
- Phase 4 依赖 Phase 3 的设计文档
- Phase 5 依赖 Phase 4 的代码（测试需要知道接口）
- Phase 9 依赖 Phase 4/5 的生成文件
- Phase 10 依赖 Phase 6 的构建配置
- Phase 11 依赖所有 phase_results

---

## Q4: Phase Skip Rules 如何工作？

**跳过规则**:
```python
# devpal/core/openspec_phases/phase_skip_rules.py
PHASE_SKIP_RULES = {
    "installer": {
     3: "installer projects don't need tech design",
        5: "installer projects don't need tests",
        7: "installer projects don't need test docs",
        9: "installer projects skip quality gate",
      10: "installer projects skip test execution"
  },
    "tooling": {
        3: "tooling scripts don't need full design",
    6: "tooling scripts don't need CMake"
    },
    "python": {
        6: "Python projects don't need CMake"
    }
}

def should_skip_phase(phase_num, context):
    """判断是否跳过阶段"""
    project_type = context.project_type
    language = context.language
    
    # 检查项目类型规则
    if project_type in PHASE_SKIP_RULES:
      if phase_num in PHASE_SKIP_RULES[project_type]:
          return True, PHASE_SKIP_RULES[project_type][phase_num]
  
    # 检查语言规则
    if language in PHASE_SKIP_RULES:
        if phase_num in PHASE_SKIP_RULES[language]:
          return True, PHASE_SKIP_RULES[language][phase_num]
    
    return False, None
```

**示例**:
```
installer 项目:
✅ Phase 1-2: 需求解析、目录结构
❌ Phase 3: 跳过（安装脚本不需要复杂设计）
✅ Phase 4: 生成安装脚本
❌ Phase 5-7: 跳过（不需要测试）
❌ Phase 9-10: 跳过（不需要质量检查和测试执行）
✅ Phase 11: 生成报告
```

---

## Q5: Phase 的 Retry 和 Checkpoint 如何实现？

**Retry 机制**:
```python
# devpal/core/openspec_phases/enhanced_scheduler.py
RETRY_CONFIG = {
    3: 2,  # Phase 3 (AI 设计) 最多重试 2 次
    4: 2,  # Phase 4 (AI 代码生成) 最多重试 2 次
  10: 1,  # Phase 10 (测试执行) 最多重试 1 次
}

def execute_phase_with_retry(phase, context):
    max_retries = RETRY_CONFIG.get(phase.num, 0)
    
    for attempt in range(max_retries + 1):
        try:
            result = phase.execute(context)
            if result.success:
              return result
        except Exception as e:
            if attempt < max_retries:
        print(f"[RETRY] Phase {phase.num} attempt {attempt+1}/{max_retries+1}")
                continue
            else:
                return PhaseResult.fail(str(e))
```

**Checkpoint 机制**:
```python
# devpal/core/openspec_phases/enhanced_scheduler.py
class CheckpointManager:
    """Checkpoint 管理器"""
    
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.checkpoints = self._load()
    
    def save(self, phase_num: int, success: bool, context: OpenSpecContext):
        """保存 checkpoint"""
        self.checkpoints[phase_num] = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
          "context_snapshot": {
                "structured_requirements": context.structured_requirements,
             "tech_design_content": context.tech_design_content,
                "generated_files": context.generated_files
           }
      }
        self._persist()
    
    def is_phase_completed(self, phase_num: int) -> bool:
        """检查阶段是否已完成"""
        return phase_num in self.checkpoints and self.checkpoints[phase_num]["success"]
    
    def restore_context(self, phase_num: int) -> dict:
        """恢复上下文""
        return self.checkpoints[phase_num]["context_snapshot"]

# 使用 Checkpoint
def run_with_checkpoint(phases, context):
    checkpoint_mgr = CheckpointManager(".spec/checkpoint.json")
    
    for phase in phases:
        # 检查是否已完成
    if checkpoint_mgr.is_phase_completed(phase.num):
            print(f"[SKIP] Phase {phase.num} already completed (from checkpoint)")
            continue
        
        # 执行阶段
        result = phase.execute(context)
     
      # 保存 checkpoint
        checkpoint_mgr.save(phase.num, result.success, context)
```

**Resume 使用场景**:
```bash
# 首次运行，Phase 6 失败
python run_ai_flow.py -r requirements/login.md
# Output: Phase 1-5 完成，Phase 6 失败

# 修复问题后，从 Phase 6 恢复
python run_ai_flow.py -r requirements/login.md --resume
# 自动跳过 Phase 1-5，从 Phase 6 开始
```

---

## Q6: Phase Pipeline 的性能优化？

**优化策略**:

### 1. Phase 4/5 多智能体并行
```python
# 顺序生成: 10 files × 30s = 300s
# 并行生成: 10 files / 4 agents × 30s = 75s
# 加速比: 4x
```

### 2. Prompt Caching
```python
# Phase 4 生成 10 个文件
# System Prompt (cached): 2000 tokens
# Tech Design (cached): 5000 tokens
# 每个文件任务: 500 tokens

# 无缓存: 10 × (2000 + 5000 + 500) = 75,000 tokens
# 有缓存: (2000 + 5000) × (cache_write + 9 × cache_read) + 10 × 500 = 12,000 tokens
# 节省: 84%
```

### 3. Phase Skip Rules
```python
# installer 项目跳过 Phase 3/5-7/9-10
# 从 11 phases → 5 phases
# 时间节省: ~60%
```

### 4. 增量执行（未来）
```python
# 只重新执行变更影响的 Phase
# 例如：需求变更只影响 Phase 1/3/4
# 跳过 Phase 2/5-11
```

---

## 面试展示脚本

**开场**:
"OpenSpec 11-Phase Pipeline 是DevPalAgent 实现确定性生成的核心，它将需求转换为可交付软件的标准化流程。"

**技术深度展示**:
1. "11 个阶段覆盖从需求到交付的完整流程：Parse → Design → Code → Test → Report"
2. "Phase 4/5 支持多智能体并行，4x 加速"
3. "Phase Skip Rules: 根据项目类型和语言智能跳过不需要的阶段"
4. "Retry + Checkpoint: 保证可恢复性，失败后从断点继续"

**代码展示**:
- `devpal/core/openspec_phases/` - 各 Phase 实现
- `devpal/core/openspec_phases/enhanced_scheduler.py` - 调度器
- `devpal/core/openspec_phases/phase_skip_rules.py` - 跳过规则

**亮点总结**:
- 🎯 **确定性**: 11 阶段标准化流程
- ⚡ **高性能**: Multi-Agent 并行 + Prompt Caching，4-12x 加速
- 🔄 **可恢复**: Checkpoint/Resume 机制
- 🎛️ **可配置**: Phase Skip Rules 适配不同项目类型
