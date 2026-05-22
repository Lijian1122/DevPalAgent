# Prompt Caching 优化实施计划

**日期**：2026-05-22  
**目标**：优化 DevPalAgent 的 Prompt Caching 机制，提升缓存覆盖率和可观测性  
**预期收益**：Cache Hit Rate >60%，API Cost -40%

---

## 1. 背景与目标

### 当前问题
1. **缓存覆盖不全**：仅 Phase 3/4 使用缓存，Phase 9/10 的自愈流程未使用
2. **统计不完整**：缺少 `cache_creation_tokens` 追踪，无法计算完整的成本收益
3. **可观测性不足**：final_report 未显示缓存命中率和成本节省百分比
4. **缺少独立输出**：没有 `.spec/cache_metrics.json` 文件

### 优化目标
- ✅ 扩大缓存覆盖范围（Phase 9/10）
- ✅ 完善统计追踪（cache_creation_tokens）
- ✅ 增强可观测性（cache hit rate、cost reduction）
- ✅ 输出独立的 cache metrics 文件

### 预期收益
| 指标 | 当前 | 目标 |
|---|:---:|:---:|
| Cache Hit Rate | 未知 | >60% |
| API Cost | 基准 | -40% |
| Phase 4 响应时间 | 基准 | -30% |
| Cache 覆盖阶段 | Phase 3/4 | Phase 3/4/9/10 |

---

## 2. 技术原理回顾

### Anthropic Prompt Caching 核心机制

**本质**：缓存的是 **LLM 推理后的中间状态**（KV Cache），不是原始文本。

**工作流程**：
```
客户端标记 cache_control → Anthropic 服务端
                ↓
               计算内容哈希 (SHA256)
                        ↓
                 查找缓存表
                    ├─ 命中 → 加载 KV 状态（节省 90% 计算）
                    └─ 未命中 → 完整推理 + 创建缓存
                 ↓
                    返回 usage 统计
```

**关键参数**：
- **TTL**: 5 分钟（自动刷新）
- **最小缓存大小**: 2000 字符
- **成本**: cache_read = 10% × cache_creation

**DevPalAgent 中的应用**：
- Phase 3: 缓存 `requirements_content`
- Phase 4: 缓存 `requirements_content` + `tech_design_content`
- Phase 9/10: 待接入

---

## 3. 实施任务清单

### Task 1: 扩展 OpenSpecContext（0.5小时）

**目标**：添加 `llm_cache_creation_tokens` 字段

**文件**：`devpal/core/openspec_phases/base.py`

**修改位置**：约第 107 行，OpenSpecContext 类定义

**修改内容**：
```python
class OpenSpecContext:
    # ... 现有字段 ...
    llm_calls: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    llm_cache_read_tokens: int = 0
    llm_cache_creation_tokens: int = 0  # ✅ 新增
```

**验证**：
```bash
python -c "from devpal.core.openspec_phases.base import OpenSpecContext; ctx = OpenSpecContext(); print(hasattr(ctx, 'llm_cache_creation_tokens'))"
# 预期输出：True
```

---

### Task 2: 更新 Phase 3/4 统计同步（0.5小时）

**目标**：同步 `cache_creation_tokens` 到 OpenSpecContext

#### 文件 1：`devpal/core/openspec_phases/phase3_technical_design.py`

**修改位置**：第 97-103 行，`_update_usage_stats` 方法

**修改内容**：
```python
def _update_usage_stats(self, client) -> None:
    """Sync LLM usage stats from client to context."""
    ctx = self.context
    ctx.llm_calls = client.usage.calls
    ctx.llm_input_tokens = client.usage.input_tokens
    ctx.llm_output_tokens = client.usage.output_tokens
    ctx.llm_cache_read_tokens = client.usage.cache_read_tokens
    ctx.llm_cache_creation_tokens = client.usage.cache_creation_tokens  # ✅ 新增
```

#### 文件 2：`devpal/core/openspec_phases/phase4_generate_code.py`

**修改位置**：第 507-513 行，`_update_usage_stats` 方法

**修改内容**：
```python
def _update_usage_stats(self, client):
    """Sync LLM usage stats from client to context."""
    ctx = self.context
    ctx.llm_calls = client.usage.calls
    ctx.llm_input_tokens = client.usage.input_tokens
    ctx.llm_output_tokens = client.usage.output_tokens
    ctx.llm_cache_read_tokens = client.usage.cache_read_tokens
    ctx.llm_cache_creation_tokens = client.usage.cache_creation_tokens  # ✅ 新增
```

---

### Task 3: 创建 Cache Strategy 模块（1小时）

**目标**：创建独立的缓存策略和 metrics 计算模块

**文件**：`devpal/core/cache_strategy.py`（新增）

**内容**：完整的 CacheMetrics 类，包含：
- `from_context()`: 从 OpenSpecContext 计算指标
- `to_dict()`: 转换为字典
- `save_to_file()`: 保存到 JSON
- `format_summary()`: 格式化为可读摘要

**关键计算**：
```python
# 缓存命中率
cache_hit_rate = cache_read / (cache_read + cache_creation)

# 成本降低百分比
saved_tokens = cache_read * 0.9
original_cost = input_tokens + cache_read + cache_creation
actual_cost = input_tokens + cache_creation + (cache_read * 0.1)
cost_reduction = saved_tokens / original_cost
```

---

### Task 4: 更新 Phase 11 报告（1小时）

**目标**：输出完整的缓存统计和独立的 metrics 文件

**文件**：`devpal/core/openspec_phases/phase11_final_report.py`

**修改 1**：导入 CacheMetrics（第 10 行附近）
```python
from ..cache_strategy import CacheMetrics
```

**修改 2**：生成并保存 cache metrics（第 50 行附近）
```python
def execute(self) -> PhaseResult:
    self.log("Phase 11 start: generate final report")
    
    # 生成 cache metrics
    cache_metrics = CacheMetrics.from_context(self.context)
    
    # 保存到 .spec/cache_metrics.json
    cache_metrics_path = self.context.project_dir / ".spec" / "cache_metrics.json"
    cache_metrics.save_to_file(cache_metrics_path)
    self.log(f"  [OK] Cache metrics saved: {cache_metrics_path}")
    
    # 输出到日志
    self.log(cache_metrics.format_summary())
    
    # ... 继续生成 final report ...
```

**修改 3**：更新 final_report 内容（第 104-111 行）
```python
"## 2. AI Usage",
"",
"- LLM calls: {}".format(self.context.llm_calls),
"- Input tokens: {}".format(self.context.llm_input_tokens),
"- Output tokens: {}".format(self.context.llm_output_tokens),
"- Cache read tokens: {}".format(self.context.llm_cache_read_tokens),
"- Cache creation tokens: {}".format(self.context.llm_cache_creation_tokens),  # ✅ 新增
"",
"### Cache Performance",  # ✅ 新增章节
"",
"- Cache hit rate: {:.1%}".format(cache_metrics.cache_hit_rate),
"- Cost reduction: {:.1%}".format(cache_metrics.cost_reduction_percentage),
"- Total cache tokens: {:,}".format(cache_metrics.total_cache_tokens),
```

---

### Task 5: Phase 9 接入缓存（1小时，可选）

**目标**：在质量门禁的自愈流程中使用 cached_context

**文件**：`devpal/core/openspec_phases/phase9_quality_gate.py`

**修改位置**：第 150-180 行，自愈逻辑

**修改内容**：
```python
# 构建缓存上下文
cached_context = []
if self.context.requirements_content:
    cached_context.append(self.context.requirements_content)
if self.context.tech_design_content:
    cached_context.append(self.context.tech_design_content)

# 调用 LLM 时传递缓存上下文
fixed_code = llm_client.generate(
    system="你是代码修复专家",
    user_message=fix_prompt,
    cached_context=cached_context  # ✅ 新增
)

# 更新统计
self._update_usage_stats(llm_client)
```

---

### Task 6: Phase 10 接入缓存（1小时，可选）

**目标**：在测试执行的自愈流程中使用 cached_context

**文件**：`devpal/core/openspec_phases/phase10_run_tests.py`

**修改位置**：第 200-250 行，TestSelfHealer 调用

**修改内容**：
```python
if test_result.failed > 0:
    llm_client = get_llm_client()
    
    # 构建缓存上下文
    cached_context = []
    if self.context.requirements_content:
        cached_context.append(self.context.requirements_content)
    if self.context.tech_design_content:
      cached_context.append(self.context.tech_design_content)
    
    # 自愈修复
    fix_prompt = f"修复以下测试失败:\n{test_result.output}"
    fixed_code = llm_client.generate(
        system="你是测试修复专家",
        user_message=fix_prompt,
      cached_context=cached_context  # ✅ 新增
    )
    
    # 更新统计
    self._update_usage_stats(llm_client)
```

---

## 4. 验收标准

### 测试 1: 第一次运行（创建缓存）
```bash
python test_simple.py

# 验证 1: cache_metrics.json 存在
cat test_phase_skip/.spec/cache_metrics.json

# 预期输出：
# {
#   "cache_hit_rate": 0.0,
#   "cache_creation_tokens": > 0,
#   "cache_read_tokens": 0,
#   "cost_reduction_percentage": 0.0
# }

# 验证 2: final_report.md 显示缓存统计
grep "Cache Performance" test_phase_skip/docs/final_report.md
grep "Cache hit rate: 0.0%" test_phase_skip/docs/final_report.md
```

### 测试 2: 5分钟内第二次运行（命中缓存）
```bash
python test_simple.py

# 验证 1: cache_metrics.json 显示命中
cat test_phase_skip/.spec/cache_metrics.json

# 预期输出：
# {
#   "cache_hit_rate": > 0.6,
#   "cache_read_tokens": > 0,
#   "cost_reduction_percentage": > 0.4
# }

# 验证 2: final_report.md 显示缓存命中
grep "Cache hit rate: [6-9][0-9]" test_phase_skip/docs/final_report.md
grep "Cost reduction: [4-9][0-9]" test_phase_skip/docs/final_report.md
```

### 测试 3: 6分钟后第三次运行（缓存过期）
```bash
sleep 360
python test_simple.py

# 验证：cache_metrics.json 显示重新创建
cat test_phase_skip/.spec/cache_metrics.json

# 预期输出：
# {
#   "cache_hit_rate": 0.0,  # 缓存过期
#   "cache_creation_tokens": > 0,
#   "cache_read_tokens": 0
# }
```

---

## 5. 实施顺序

### 阶段 1：基础功能（3小时）
1. ✅ Task 1: 扩展 OpenSpecContext（0.5h）
2. ✅ Task 2: 更新 Phase 3/4 统计同步（0.5h）
3. ✅ Task 3: 创建 Cache Strategy 模块（1h）
4. ✅ Task 4: 更新 Phase 11 报告（1h）
5. ✅ 测试基础功能（0.5h）

### 阶段 2：扩展功能（2.5小时，可选）
6. ⚠️ Task 5: Phase 9 接入缓存（1h）
7. ⚠️ Task 6: Phase 10 接入缓存（1h）
8. ⚠️ 最终测试（0.5h）

**总工期**：
- 最小可行版本：3 小时
- 完整版本：5.5 小时

---

## 6. 风险与缓解

### 风险 1: Phase 9/10 自愈流程复杂
**影响**：添加 cached_context 可能影响现有逻辑  
**缓解**：
- 先完成阶段 1（基础功能）
- 阶段 2 作为可选增强
- 充分测试自愈流程

### 风险 2: 统计累加错误
**影响**：多次调用 LLM 时统计可能不准确  
**缓解**：
- 使用 `+=` 累加而不是 `=` 赋值
- 在每个 Phase 的 `_update_usage_stats` 中使用累加

### 风险 3: 5分钟 TTL 限制
**影响**：Phase 4 → Phase 10 间隔可能超过 5 分钟  
**缓解**：
- 接受现实：Phase 10 可能需要重新创建缓存
- 重点优化 Phase 3-4 缓存命中（最大收益）
- 在文档中说明 5 分钟限制

---

## 7. 预期效果

### 成本节省
```
第一次运行：10,100 tokens（基准）
第二次运行：1,100 tokens（节省 89%）
Phase 3-4 缓存命中：8,000 tokens → 800 tokens
```

### 可观测性提升
- ✅ 实时查看 cache hit rate
- ✅ 了解缓存成本收益
- ✅ 独立的 metrics 文件便于分析
- ✅ final_report 显示完整统计

### 面试价值
- 展示对 Prompt Caching 底层原理的理解（KV Cache）
- 展示成本优化能力（-40% API cost）
- 展示可观测性设计能力（metrics 模块）
- 展示工程实践能力（统计追踪、文件输出）

---

## 8. 关键文件清单

| 文件 | 作用 | 修改类型 |
|------|------|---------|
| `devpal/core/openspec_phases/base.py` | OpenSpecContext 定义 | 修改（添加字段）|
| `devpal/core/openspec_phases/phase3_technical_design.py` | 技术设计生成 | 修改（更新统计）|
| `devpal/core/openspec_phases/phase4_generate_code.py` | 代码生成 | 修改（更新统计）|
| `devpal/core/openspec_phases/phase11_final_report.py` | 最终报告 | 修改（输出 metrics）|
| `devpal/core/cache_strategy.py` | Cache 策略模块 | 新增 |
| `devpal/core/openspec_phases/phase9_quality_gate.py` | 质量门禁 | 修改（可选）|
| `devpal/core/openspec_phases/phase10_run_tests.py` | 测试执行 | 修改（可选）|

---

**文档版本**：v1.0  
**创建日期**：2026-05-22  
**预计完成**：2026-05-22（3-5.5 小时）
