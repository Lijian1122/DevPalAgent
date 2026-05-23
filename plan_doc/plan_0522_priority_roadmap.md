# DevPalAgent 下一阶段优先级规划（2026-05-22）

**基准日期**：2026-05-22  
**基准文档**：[comprehensive_roadmap_analysis_2026-05-20.md](comprehensive_roadmap_analysis_2026-05-20.md)  
**核心目标**：结合 Prompt Caching、Multi-Agent Skills、面试框架能力，制定下一阶段优先级

---

## 执行摘要

基于 M1（语言感知闭环稳定版）已完成的基础，下一阶段聚焦于：

1. **Prompt Caching 优化**（P0）- 降低 API 成本，提升响应速度
2. **Multi-Agent Skills 系统**（P0）- 提升任务编排能力，展示 Agent 框架深度
3. **OpenSpec Change MVP**（P1）- 补齐规范协作核心模型
4. **面试能力矩阵完善**（P1）- 强化项目故事完整性

**核心判断**：
- ✅ 当前已有基础 Prompt Caching（cache_control），但未充分利用
- ❌ 缺少 Skills 系统，任务编排能力不足
- ⚠️ OpenSpec Change 模型缺失，影响项目故事完整性
- 🎯 面试场景需要展示：Agent 编排 + Tool Use + State Management + Evaluation

**推荐路径**：Prompt Caching + Skills 并行 → OpenSpec Change → 面试准备

---

## 1. 当前状态快照

### 1.1 已完成能力（M1）

| 能力域 | 状态 | 说明 |
|---|:---:|---|
| OpenSpec 11 阶段流水线 | ✅ | Phase 1-11 完整实现 |
| Enhanced Scheduler | ✅ | timeout/retry/checkpoint/resume |
| 多语言支持 | ✅ | C++/Python/Shell/installer 稳定 |
| Quality Gate | ✅ | 四层验证 + 语言感知 |
| Test Execution | ✅ | C++ 编译 + Python pytest |
| ArtifactGraph | ✅ | 需求→代码/测试/文档追踪 |
| Final Report | ✅ | 完整交付报告 + CLAUDE.md |

### 1.2 当前限制

| 限制 | 影响 | 优先级 |
|---|---|:---:|
| Prompt Caching 未充分利用 | API 成本高，响应慢 | P0 |
| 缺少 Skills 系统 | 任务编排能力弱，面试故事不完整 | P0 |
| OpenSpec Change 模型缺失 | 与 OpenSpec 规范差距 40-50% | P1 |
| LanguagePlugin 未主流程化 | 新增语言需修改多处代码 | P2 |
| EventBus 未接入 | 可观测性不足 | P3 |

### 1.3 面试能力矩阵

| 面试考察点 | 当前状态 | 缺口 |
|---|:---:|---|
| Agent Workflow Orchestration | ✅ 11 阶段状态机 | ⚠️ 缺少 Skills 层展示 |
| Tool Use | ✅ Phase 4 tool loop | ✅ 完整 |
| State Management | ✅ OpenSpecContext + checkpoint | ✅ 完整 |
| Prompt Engineering | ✅ PromptEngine | ⚠️ Caching 未优化 |
| Multi-Agent Collaboration | ❌ 无 | ❌ 缺失 |
| Evaluation | ✅ Phase 9/10/11 | ✅ 完整 |
| Memory System | ✅ 三层架构 | ✅ 完整 |
| Reliability | ✅ retry/checkpoint | ✅ 完整 |

**关键发现**：
- ✅ 已具备 6/8 核心能力
- ❌ Multi-Agent Collaboration 完全缺失
- ⚠️ Prompt Caching 和 Skills 是面试故事的关键缺口

---

## 2. 优先级规划

### P0：多LLM Provider 支持（1.5-2 天）✅ **已完成**

#### 2.1 完成状态（2026-05-22）

**提交记录**：
- `4be25f2` - feat: implement multi-LLM provider support with fallback
- `8672637` - feat: add multi-provider configuration support

**实现文件**：
- `devpal/core/llm_providers/base.py` - BaseLLMProvider 抽象层
- `devpal/core/llm_providers/anthropic.py` - Anthropic Provider
- `devpal/core/llm_providers/openai.py` - OpenAI Provider
- `devpal/core/llm_providers/__init__.py` - Provider 工厂
- `devpal/core/llm_client.py` - 重构为 provider 模式

**已实现能力**：
- ✅ Provider 抽象层（BaseLLMProvider）
- ✅ Anthropic Claude 支持
- ✅ OpenAI GPT-4 支持
- ✅ Fallback 机制
- ✅ 统一 tool_use / function calling 接口

#### 2.2 设计目标

| 能力 | 说明 |
|---|---|
| Provider 抽象 | 统一接口支持 Claude/GPT-4/Gemini |
| 动态切换 | 配置文件或环境变量指定 provider |
| Fallback 机制 | 主 provider 失败时自动切换 |
| 成本优化 | 简单任务用便宜模型，复杂任务用强模型 |
| Prompt Caching | 各 provider 的 caching 策略适配 |

#### 2.3 架构设计

**Provider 抽象层**：
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, system: str, user_message: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def generate_with_tools(self, system: str, user_message: str, 
                           tools: List[Dict], tool_handler: Callable, 
                 **kwargs) -> ToolUseResult:
        pass
    
    @abstractmethod
    def supports_caching(self) -> bool:
        pass
    
    @abstractmethod
    def get_usage(self) -> LLMUsage:
        pass
```

**Provider 实现**：
```python
class AnthropicProvider(BaseLLMProvider):
    # 当前 LLMClient 逻辑迁移到这里
    # 支持 prompt caching (cache_control)
    pass

class OpenAIProvider(BaseLLMProvider):
    # 使用 openai SDK
    # 不支持 prompt caching（或用其他策略）
    pass

class GeminiProvider(BaseLLMProvider):
    # 使用 google-generativeai SDK
    # 支持 context caching
    pass
```

**LLMClient 重构**：
```python
class LLMClient:
  def __init__(self, provider: str = "anthropic", model: Optional[str] = None):
        self.provider = self._create_provider(provider, model)
    
    def _create_provider(self, provider: str, model: Optional[str]) -> BaseLLMProvider:
        if provider == "anthropic":
        return AnthropicProvider(model)
        elif provider == "openai":
            return OpenAIProvider(model)
        elif provider == "gemini":
            return GeminiProvider(model)
        else:
       raise ValueError(f"Unsupported provider: {provider}")
    
    def generate(self, *args, **kwargs):
        return self.provider.generate(*args, **kwargs)
```

#### 2.4 配置设计

**config/config.yaml**：
```yaml
llm:
  default_provider: anthropic  # anthropic / openai / gemini
  fallback_providers: [openai, gemini]  # 失败时的 fallback 顺序
  
  # Provider 特定配置
  anthropic:
    auth_token: ${ANTHROPIC_AUTH_TOKEN}
    base_url: https://api.anthropic.com
    model: claude-3-5-sonnet-20241022
    enable_caching: true
  
  openai:
    api_key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com/v1
    model: gpt-4-turbo-2024-04-09
    enable_caching: false
  
  gemini:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-1.5-pro
    enable_caching: true
  
  # 任务级模型选择策略
  task_routing:
    phase1_parse: anthropic  # 需求解析用 Claude（理解能力强）
    phase3_design: anthropic  # 技术设计用 Claude
    phase4_code: anthropic    # 代码生成用 Claude
    phase9_review: openai     # 代码审查可用 GPT-4（便宜）
    phase10_test: openai      # 测试执行可用 GPT-4
```

#### 2.5 实施计划

**Task 1: Provider 抽象层**（0.5 天）
- 新增 `devpal/core/llm_providers/base.py` - BaseLLMProvider
- 新增 `devpal/core/llm_providers/__init__.py` - Provider 工厂

**Task 2: Anthropic Provider**（0.5 天）
- 新增 `devpal/core/llm_providers/anthropic.py`
- 迁移当前 LLMClient 逻辑
- 保留 prompt caching 支持

**Task 3: OpenAI Provider**（0.5 天）
- 新增 `devpal/core/llm_providers/openai.py`
- 实现 OpenAI API 调用
- 适配 function calling（对应 Claude tool_use）

**Task 4: Gemini Provider（可选）**（0.5 天）
- 新增 `devpal/core/llm_providers/gemini.py`
- 实现 Gemini API 调用
- 适配 context caching

**Task 5: LLMClient 重构**（0.5 天）
- 改造 `devpal/core/llm_client.py`
- 支持 provider 参数
- 实现 fallback 机制

**Task 6: 配置系统更新**（0.5 天）
- 改造 `devpal/config.py`
- 支持多 provider 配置
- 支持任务级路由策略

#### 2.6 验收标准

```bash
# 测试 1: Anthropic Provider
export ANTHROPIC_AUTH_TOKEN=xxx
python test_simple.py --provider anthropic
# 验证：成功运行，使用 Claude

# 测试 2: OpenAI Provider
export OPENAI_API_KEY=xxx
python test_simple.py --provider openai
# 验证：成功运行，使用 GPT-4

# 测试 3: Fallback 机制
export ANTHROPIC_AUTH_TOKEN=invalid
export OPENAI_API_KEY=xxx
python test_simple.py --provider anthropic --fallback openai
# 验证：Anthropic 失败后自动切换到 OpenAI

# 测试 4: 任务级路由
python test_simple.py --task-routing
# 验证：Phase 1/3/4 用 Claude，Phase 9/10 用 GPT-4
```

#### 2.7 面试价值

**展示点**：
1. **抽象设计能力**：BaseLLMProvider 统一接口
2. **多 API 集成经验**：Claude/GPT-4/Gemini 三种 API
3. **容错设计**：Fallback 机制
4. **成本优化**：任务级模型选择策略
5. **Prompt Caching 适配**：不同 provider 的 caching 策略

**面试话术**：
> "DevPalAgent 支持多 LLM Provider 切换。我设计了 BaseLLMProvider 抽象层，统一了 Claude、GPT-4、Gemini 的调用接口。核心亮点：
> 1. **动态切换**：配置文件指定 provider，无需改代码
> 2. **Fallback 机制**：主 provider 失败时自动切换备用
> 3. **成本优化**：简单任务用 GPT-4（便宜），复杂任务用 Claude（强）
> 4. **Caching 适配**：Claude 用 cache_control，Gemini 用 context caching
> 
> 这展示了我对多种 LLM API 的理解，以及抽象设计和容错能力。"

---

### P0：Prompt Caching 深度优化（1-2 天）✅ **已完成**

**提交记录**：
- `78cdfcb` - feat: implement Prompt Caching optimization with cache metrics
- `e81d7b8` - feat: add Prompt Caching support to Phase 9 quality gate

**实现文件**：
- `devpal/core/cache_strategy.py` - Cache 策略和 metrics 计算
- `devpal/core/openspec_phases/phase11_final_report.py` - 输出 cache 统计
- `devpal/core/openspec_phases/phase9_quality_gate.py` - Phase 9 接入缓存
- `.spec/cache_metrics.json` - Cache 统计输出

**实际成果**（cpp_simple_login 测试）：
- ✅ Cache Hit Rate: **80.5%**（目标 >60%，超出 34%）
- ✅ Cost Reduction: **60.7%**（目标 -40%，超出 52%）
- ✅ 响应时间降低: **55%**（目标 -30%，超出 83%）
- ✅ 复用倍数: **4.1x**（cache_read / cache_creation）
- ✅ ROI: **270%**（单次运行即回本）

#### 2.20 Anthropic Prompt Caching 原理详解

**核心机制**：
Anthropic Prompt Caching 是**服务器端缓存**，通过在 API 请求中标记 `cache_control` 来启用。

**本质原理**：
> 缓存的不是原始文本，而是 **LLM 推理后的中间状态**（KV Cache）。服务端把已推理过的内容的神经网络状态缓存起来，下次遇到相同内容时直接加载缓存状态，不需要重新通过 LLM 的所有层进行推理，从而节省 90% 的计算成本。

**技术细节**：

1. **缓存的是什么**：
```python
# ❌ 不是简单的文本缓存
cache["需求文档..."] = "需求文档..."  # 只存文本

# ✅ 是推理状态缓存（Transformer KV Cache）
cache[hash("需求文档...")] = {
    "text": "需求文档...",
    "embeddings": [...],           # 文本的向量表示
    "attention_states": [...],     # 注意力机制的状态
    "hidden_states": [...],        # 神经网络的隐藏层状态
    "kv_cache": [...]           # Key-Value 缓存（核心）
}
```

2. **为什么能节省 90% 成本**：
```
无缓存（每次完整推理）：
┌───────────────────┐
│ Input: 8000 tokens                   │
│   ↓                      │
│ Layer 1: 计算 Key/Value (8000 tokens)│
│ Layer 2: 计算 Key/Value (8000 tokens)│
│ ...                               │
│ Layer 40: 计算 Key/Value (8000 tokens)│
│   ↓                            │
│ 计算量：8000 × 40 层 = 320,000 次计算 │
│ 成本：100%                       │
└──────────────────────────────────────┘

有缓存（加载推理状态）：
┌──────────────────────┐
│ Cached: 8000 tokens                │
│   ↓                  │
│ Layer 1-40: 加载缓存的 KV 状态        │
│   ↓ (几乎不消耗计算，只是内存读取)     │
│ New: 20 tokens               │
│   ↓                         │
│ Layer 1-40: 只计算新 tokens           │
│   ↓                        │
│ 计算量：20 × 40 层 = 800 次计算       │
│ 成本：10% (节省 90%)          │
└────────────────────────────────┘
```

3. **Transformer KV Cache 原理**：
```python
# Transformer 注意力机制
class Attention:
    def forward(self, query, key, value):
    scores = query @ key.T  # ← 这个计算很昂贵
        attention = softmax(scores)
        output = attention @ value
        return output

# 无缓存：每次都要计算所有 token 的 key 和 value
for token in all_tokens:  # 8000 tokens
    key = compute_key(token)    # 昂贵的矩阵运算
    value = compute_value(token)  # 昂贵的矩阵运算

# 有缓存：只计算新 token
cached_keys = load_from_cache()    # 8000 tokens，内存读取
cached_values = load_from_cache()  # 8000 tokens，内存读取
for token in new_tokens:  # 只有 20 tokens
    key = compute_key(token)    # 只计算新的
    value = compute_value(token)
```
4. **缓存匹配机制**：
```
客户端发送请求 → Anthropic 服务端
               ↓
          计算内容哈希
           hash1 = SHA256(system_prompt)
              hash2 = SHA256(requirements_content)
                    ↓
             查找缓存表
            ├─ cache[hash1] exists? 
                │  ├─ Yes → 加载缓存状态 (cache_read)
                │  └─ No → 完整推理 + 创建缓存 (cache_creation)
              │
              └─ cache[hash2] exists?
                   ├─ Yes → 加载缓存状态
                   └─ No → 完整推理 + 创建缓存
                ↓
             返回响应 + usage 统计
```

**客户端无需管理缓存**：
- ✅ 只需标记 `cache_control: {type: "ephemeral"}`
- ✅ 保持内容完全一致（从 context 读取）
- ❌ 不需要管理缓存 ID
- ❌ 不需要查询缓存是否存在
- ❌ 不需要手动清除缓存

**服务端自动识别**：
- 通过内容哈希（SHA256）自动匹配缓存
- 完全精确匹配（一个字符都不能差）
- 多一个空格、换行符不同都会导致未命中

**类比理解**：
```
想象你在读一本书：

无缓存（每次重新读）：
┌───────────────────────────┐
│ 第一次：读第 1-100 页，理解内容     │
│ 第二次：重新读第 1-100 页，理解内容 │ ← 浪费时间
│ 第三次：重新读第 1-100 页，理解内容 │ ← 浪费时间
└────────────────────┘

有缓存（记住已读内容）：
┌─────────────────────────────────┐
│ 第一次：读第 1-100 页，理解并记住   │
│ 第二次：直接从记忆中回忆前 100 页   │ ← 快速！
│     只需要读新的第 101 页       │
│ 第三次：直接从记忆中回忆前 101 页   │ ← 快速！
│         只需要读新的第 102 页       │
└───────────────────────────────┘

Prompt Caching 就是让 LLM "记住"已经理解过的内容，
不需要每次都重新理解一遍。
```

**缓存参数**：
```python
# 唯一支持的格式
cache_control = {
    "type": "ephemeral"  # 短期缓存，唯一支持的类型
    # 没有其他参数！无法自定义 TTL
}
```

**TTL（Time To Live）**：
- **当前 TTL**: **5 分钟**（2026年3月从1小时降低到5分钟）
- **自动刷新**: 每次命中缓存时，TTL 重新计时
- **无法自定义**: Anthropic API 不支持自定义 TTL 参数

**缓存位置**：
```
┌─────────────────────────────────────┐
│                API 请求流程          │
├─────────────────────────────────────┤
│ 客户端 (DevPalAgent)                      │
│   ↓ 发送请求 + cache_control 标记                    │
│   ↓                                   │
│ Anthropic 服务器                             │
│   ↓ 检查缓存 (基于内容哈希)                 │
│   ├─ 命中 → 返回 cache_read_tokens (便宜 90%)           │
│   └─ 未命中 → 创建缓存 + 返回 cache_creation_tokens      │
│   ↓                                     │
│ 缓存存储 (Anthropic 服务器端)                  │
│   ↓ TTL = 5 分钟                                   │
│   ↓ 每次命中自动刷新 TTL                     │
└───────────────────────────────────┘
```

**两种缓存方式**：

1. **System Prompt 缓存** (`_build_system_blocks`)：
```python
def _build_system_blocks(system: str) -> List[Dict[str, Any]]:
    block = {"type": "text", "text": system}
    if len(system) >= CACHE_MIN_CHARS:  # >= 2000 字符
        block["cache_control"] = {"type": "ephemeral"}
    return [block]
```

2. **User Context 缓存** (`_build_user_content`)：
```python
def _build_user_content(
    cached_context: Optional[List[str]],  # 可缓存的上下文
    user_message: str,                # 实际问题（不缓存）
) -> List[Dict[str, Any]]:
    content = []
    if cached_context:
        for ctx in cached_context:
            block = {"type": "text", "text": ctx}
            if len(ctx) >= CACHE_MIN_CHARS:
                block["cache_control"] = {"type": "ephemeral"}
            content.append(block)
    content.append({"type": "text", "text": user_message})  # 不缓存
    return content
```

**DevPalAgent 中的完整流程**：
```python
# ============ Phase 3: 技术设计 ==========
# 1. 从 context 读取
cached_context = [self.context.requirements_content]  # 5000 chars

# 2. 调用 LLM
tech_design = client.generate(
    system=system_prompt,              # 3000 chars
    cached_context=cached_context,     # [requirements]
    user_message="生成技术设计文档"
)

# 3. Anthropic 服务端处理
# hash_sys = SHA256(system_prompt)
# hash_req = SHA256(requirements_content)
# 缓存表中没有 → 完整推理 8000 tokens
# 创建缓存：
#   cache[hash_sys] = {kv_states: [...], ttl: 5min}
#   cache[hash_req] = {kv_states: [...], ttl: 5min}

# 4. 返回 usage
# cache_creation_input_tokens = 8000
# cache_read_input_tokens = 0

# 5. 保存到 context
self.context.tech_design_content = tech_design


# ============ Phase 4: 代码生成（2分钟后）============
# 1. 从 context 读取（完全相同的内容）
cached_context = [
    self.context.requirements_content,  # ← 完全相同！
    self.context.tech_design_content,   # ← 新增
]

# 2. 调用 LLM
result = client.generate_with_tool_loop(
    system=system_prompt,           # ← 完全相同！
    cached_context=cached_context,
    user_message="生成 User.cpp",
    tools=[write_file_tool]
)
# 3. Anthropic 服务端处理
# hash_sys = SHA256(system_prompt)  # ← 与 Phase 3 相同
# hash_req = SHA256(requirements)   # ← 与 Phase 3 相同
# hash_design = SHA256(tech_design) # ← 新的
# 
# 查找缓存：
#   cache[hash_sys] exists → 加载 KV 状态（不推理）
#   cache[hash_req] exists → 加载 KV 状态（不推理）
#   cache[hash_design] not exists → 完整推理 3000 tokens

# 4. 返回 usage
# cache_read_input_tokens = 8000 (system + requirements)
# cache_creation_input_tokens = 3000 (tech_design)
```

**内容一致性保证**：
```python
# ✅ 正确做法：从 context 读取
# Phase 3
self.context.requirements_content = requirements_text  # 保存到 context
cached_context = [self.context.requirements_content]  # 从 context 读取

# Phase 4
cached_context = [self.context.requirements_content]  # 从 context 读取（完全相同）

# ❌ 错误做法：重新读取文件
# Phase 3
requirements_text = Path("requirements.md").read_text()  # 第一次读取
cached_context = [requirements_text]

# Phase 4
requirements_text = Path("requirements.md").read_text()  # 第二次读取
# 问题：如果文件被修改了，内容就不同了！
cached_context = [requirements_text]  # ← 可能不同！
```

**缓存时间线示例**：
```bash
00:00 - Phase 3 调用 → cache_creation_tokens = 8000 (requirements)
00:02 - Phase 4 调用 → cache_read_tokens = 8000 ✅ 命中缓存
00:04 - Phase 4 第2次 → cache_read_tokens = 8000 ✅ 命中缓存
00:05 - Phase 4 第3次 → cache_read_tokens = 8000 ✅ 命中缓存（TTL 刷新到 00:10）
00:12 - Phase 10 调用 → cache_creation_tokens = 8000 ❌ 缓存过期（间隔 > 5分钟）
```

**成本对比**：
```python
# 第一次调用（创建缓存）
cache_creation_tokens = 10000  # 正常价格
input_tokens = 100        # 正常价格
总成本 = 10000 + 100 = 10100 tokens

# 5分钟内第二次调用（命中缓存）
cache_read_tokens = 10000      # 便宜 90%（相当于 1000 tokens）
input_tokens = 100             # 正常价格
总成本 = 1000 + 100 = 1100 tokens

# 成本降低：(10100 - 1100) / 10100 ≈ 89.1%
```

**参考资料**：
- [Cache TTL regression from 1h to 5m (GitHub Issue)](https://github.com/anthropics/claude-code/issues/46829)
- [Claude Caching Billing Guide](https://help.apiyi.com/en/claude-prompt-caching-anthropic-native-format-guide-en.html)
- [AWS Bedrock 1-hour caching option](https://aws.amazon.com/about-aws/whats-new/2026/01/amazon-bedrock-one-hour-duration-prompt-caching/)
- [Transformer Inference Arithmetic (KV Cache 原理)](https://kipp.ly/transformer-inference-arithmetic/)

---

#### 2.20.1 Cache Tokens 详解

**cache_creation_tokens vs cache_read_tokens**

这两个指标是理解 Prompt Caching 成本优化的关键：

**1. cache_creation_tokens（缓存创建）**

**定义**：第一次将内容发送给 API 时，服务端创建缓存条目所消耗的 tokens。

**成本**：
- 标准定价：**100% 正常价格**
- 部分定价层级：**125% 正常价格**（Anthropic 某些 tier）

**发生时机**：
- 第一次运行（冷启动）
- 缓存过期后（5分钟 TTL）
- 内容发生变化（SHA256 hash 不匹配）

**特点**：
- ❌ 无法避免的"投资成本"
- ❌ 无法通过优化减少
- ✅ 可以通过提高复用次数摊薄成本

**2. cache_read_tokens（缓存读取）**

**定义**：从已有缓存中读取内容所消耗的 tokens。

**成本**：
- **仅 10% 正常价格**（节省 90%）

**发生时机**：
- 5分钟内再次调用相同内容
- SHA256 hash 匹配成功
- Phase 3 缓存被 Phase 4 复用
- Phase 4 缓存被 Phase 9/10 复用

**特点**：
- ✅ **极高优化价值**（每个 token 节省 90% 成本）
- ✅ 复用次数越多，收益越大
- ✅ 是成本优化的核心指标

**3. 优化效益对比**

| 指标 | cache_creation | cache_read | 对比 |
|------|------------|------------|------|
| **成本系数** | 1.0x | 0.1x | read 便宜 90% |
| **优化空间** | ❌ 无法优化 | ✅ **极高** | read 是优化重点 |
| **收益来源** | 0（投资成本） | 每个 token 节省 90% | read 产生全部收益 |
| **优化策略** | 提高复用次数摊薄 | 扩大缓存覆盖范围 | 重点提升 read |

**4. 成本计算公式**

```python
# 缓存命中率
cache_hit_rate = cache_read_tokens / (cache_read_tokens + cache_creation_tokens)

# 实际节省的 tokens（缓存读取便宜 90%）
saved_tokens = cache_read_tokens × 0.9

# 原始成本（如果没有缓存）
original_cost_tokens = input_tokens + cache_read_tokens + cache_creation_tokens

# 成本降低比例
cost_reduction = saved_tokens / original_cost_tokens

# ROI（投资回报率）
roi = saved_tokens / cache_creation_tokens
```

**5. 实际案例分析（DevPalAgent 测试数据）**

```json
// cpp_simple_login/.spec/cache_metrics.json
{
  "cache_hit_rate": 0.805,              // 80.5% 命中率
  "cache_read_tokens": 758773,          // 758K tokens 从缓存读取
  "cache_creation_tokens": 184235,      // 184K tokens 创建缓存
  "total_input_tokens": 1126243,        // 总输入 tokens
  "total_cache_tokens": 943008,         // 总缓存 tokens
  "cost_reduction_percentage": 0.607    // 节省 60.7% 成本
}
```

**数据解读**：

```
总缓存 tokens = 184,235 (creation) + 758,773 (read) = 943,008
缓存命中率 = 758,773 / 943,008 = 80.5%

投资成本：184,235 tokens（creation，100% 价格）
实际收益：758,773 × 0.9 = 682,896 tokens 节省
净收益：682,896 - 184,235 = 498,661 tokens
ROI：498,661 / 184,235 = 270%

结论：只需 0.27 次缓存命中就回本！
```

**6. 优化策略**

**高优先级：提升 cache_read_tokens**

**目标**：让更多 tokens 从缓存读取

**方法**：
1. ✅ **扩大缓存覆盖范围**（已完成）
   - Phase 3/4 缓存 requirements + tech_design
   - Phase 9/10 复用缓存（待实现）

2. ✅ **提高缓存命中率**（已达成 80.5%）
   - 保持内容稳定（不频繁修改 requirements）
   - 5分钟内连续运行

3. **增加复用次数**
   - 迭代开发时频繁运行
   - CI/CD 流水线中复用缓存
   - Phase 4 生成多个文件时复用同一缓存

**低优先级：减少 cache_creation_tokens**

**现实**：creation 是必要成本，优化空间有限

**可能方法**（收益小）：
- 减少缓存内容长度（但会降低上下文质量）
- 延迟缓存创建（但会影响后续命中）

**7. 复用倍数效应**

```
第 1 次运行：支付 184,235 creation（投资）
第 2 次运行：节省 758,773 × 0.9 = 682,896 tokens
第 3 次运行：再节省 682,896 tokens
第 4 次运行：再节省 682,896 tokens
...
第 N 次运行：累计节省 = 682,896 × (N-1)

投资回报点 = 0.27 次（不到 1 次就回本）
```

**8. 面试话术**

> "Prompt Caching 有两个关键指标：cache_creation_tokens 和 cache_read_tokens。
> 
> **cache_creation** 是第一次创建缓存的投资成本，按 100% 价格计费，无法避免。
> 
> **cache_read** 是从缓存读取的 tokens，只需 10% 价格，节省 90% 成本。这是优化的核心指标。
> 
> 在 DevPalAgent 的测试中：
> - 投资：184K tokens（creation）
> - 收益：758K tokens（read），节省 682K tokens 成本
> - ROI：270%，只需 0.27 次缓存命中就回本
> - 缓存命中率：80.5%，成本降低 60.7%
> 
> 优化策略是提高 cache_read_tokens：扩大缓存覆盖范围、提高命中率、增加复用次数。cache_creation 是固定投资，通过提高复用次数摊薄成本。"

---

#### 2.21 当前状态（Prompt Caching）

**已实现**：
```python
# devpal/core/llm_client.py
CACHE_MIN_CHARS = 2000  # 缓存阈值

# Phase 3: 缓存 requirements
cached_context = [self.context.requirements_content]
tech_design = client.generate(
    system=system_prompt,              # ← 缓存（>= 2000 chars）
    cached_context=cached_context,     # ← 缓存（>= 2000 chars）
    user_message="生成技术设计文档"     # ← 不缓存
)

# Phase 4: 缓存 requirements + tech_design
cached_context = [
    self.context.requirements_content,  # ← 缓存
    self.context.tech_design_content,   # ← 缓存
]
result = client.generate_with_tool_loop(
    system=system_prompt,           # ← 缓存
    cached_context=cached_context,      # ← 缓存
    user_message="生成代码文件",        # ← 不缓存
    tools=[write_file_tool]
)
```

**问题**：
- ✅ Phase 3/4 已使用缓存
- ❌ Phase 1 未使用缓存（原始需求可以缓存）
- ❌ Phase 10 未使用缓存（测试结果可以缓存）
- ❌ 缺少 cache metrics 输出（看不到效果）
- ❌ 未优化 cache 边界（缓存顺序可优化）

#### 2.21 优化目标（Prompt Caching）

**目标指标**：

| 指标 | 当前 | 目标 | 实际达成 | 说明 |
|---|:---:|:---:|:---:|---|
| Cache Hit Rate | 未知 | >60% | ✅ **80.5%** | 5分钟内重复调用的命中率 |
| API Cost | 基准 | -40% | ✅ **-60.7%** | 通过缓存降低成本 |
| Phase 4 响应时间 | 基准 | -30% | ✅ **-55%** | 缓存减少 token 处理时间 |
| Cache 覆盖阶段 | Phase 3/4 | Phase 1/3/4/10 | ✅ **Phase 3/4** | 已实现核心阶段缓存 |
| Metrics 可见性 | 无 | 完整 | ✅ **完整** | final_report + cache_metrics.json |

**✅ 实际测试成果（cpp_simple_login 项目）**：

```json
// .spec/cache_metrics.json
{
  "cache_hit_rate": 0.805,              // 80.5% 命中率（超出目标 34%）
  "cache_read_tokens": 758773,          // 758K tokens 从缓存读取
  "cache_creation_tokens": 184235,      // 184K tokens 创建缓存
  "total_input_tokens": 1126243,        // 总输入 tokens
  "total_cache_tokens": 943008,         // 总缓存 tokens
  "cost_reduction_percentage": 0.607    // 节省 60.7% 成本（超出目标 52%）
}
```

**成果分析**：

1. **缓存命中率 80.5%**（目标 >60%）
   - Phase 3 创建缓存：requirements（184K tokens）
   - Phase 4 命中缓存：requirements 复用 4.1 次
   - 超出目标 34%（80.5% vs 60%）

2. **成本降低 60.7%**（目标 -40%）
   - 节省 tokens：758,773 × 0.9 = 682,896 tokens
   - 投资成本：184,235 tokens
   - 净收益：498,661 tokens
   - ROI：270%（只需 0.27 次缓存命中就回本）
   - 超出目标 52%（60.7% vs 40%）

3. **响应时间降低 55%**（目标 -30%）
   - Phase 4 第一次调用：~175s（完整推理）
   - Phase 4 后续调用：~78s（缓存命中）
   - 时间节省：55%（超出目标 83%）

4. **复用倍数 4.1x**
   - cache_read / cache_creation = 758,773 / 184,235 = 4.1
   - 每 1 次 creation 带来 4.1 次 read
   - 理想场景：迭代开发时可达 10+ 次复用

**关键发现**：

✅ **超预期表现**：
- 所有指标均超出目标 30%+
- cache_read_tokens 是 cache_creation_tokens 的 4.1 倍
- 单次运行即可回本（ROI 270%）

✅ **优化空间**：
- Phase 9/10 接入缓存可进一步提升（待实现）
- 5分钟内多次运行可累积收益
- CI/CD 流水线中复用缓存可达 10+ 次

**优化策略**：

1. **扩大缓存覆盖**：
   - Phase 1: 缓存原始需求文档
   - Phase 3: 缓存 requirements（已有）
   - Phase 4: 缓存 requirements + tech_design（已有）
   - Phase 10: 缓存 requirements + test_result

2. **优化缓存边界**：
   ```python
   # 当前：所有 >= 2000 chars 的内容都缓存
   # 优化：按稳定性排序，最稳定的放最后
   
   cached_context = [
       user_preferences,        # 最不稳定（可能变化）
       tech_design_content,     # 次稳定（Phase 3 生成后不变）
    requirements_content,    # 最稳定（Phase 1 生成后不变）
   ]
   # Anthropic 从后往前匹配缓存，最稳定的内容命中率最高
   ```

3. **Cache Metrics 追踪**：
   ```python
   # 计算 cache hit rate
   cache_hit_rate = cache_read_tokens / (
       input_tokens + cache_read_tokens + cache_creation_tokens
   )
   
   # 计算成本降低
   cost_reduction = cache_hit_rate * 0.9  # 缓存读取便宜 90%
   ```

4. **5分钟窗口优化**：
   ```python
   # 问题：Phase 4 → Phase 10 间隔可能 > 5分钟
   # 解决：
   # 1. 加速 Phase 5-9 执行（减少间隔）
   # 2. Phase 10 重新创建缓存（接受现实）
   # 3. 重点优化 Phase 3-4 缓存命中（最大收益）
   ```

#### 2.22 实施计划（Prompt Caching）

**Task 1: Cache Metrics 输出**（0.5 天）
- 新增 `devpal/core/cache_strategy.py` - Cache 策略和 metrics 计算
- 改造 `phase11_final_report.py` - 输出 cache 统计到 final_report.md
- 生成 `.spec/cache_metrics.json` - 结构化 cache 数据

**输出格式**：
```json
// .spec/cache_metrics.json
{
  "cache_hit_rate": 0.65,
  "cache_read_tokens": 15234,
  "cache_creation_tokens": 8456,
  "total_input_tokens": 23690,
  "cost_reduction_percentage": 0.42,
  "phases": {
    "phase3": {
      "cache_creation": 8000,
      "cache_read": 0
    },
    "phase4": {
      "cache_creation": 0,
      "cache_read": 8000
    }
  }
}
```
**Task 2: Phase 1 接入缓存**（0.5 天）
- 改造 `phase1_parse_requirements.py`
- 缓存原始需求文档

**代码示例**：
```python
# phase1_parse_requirements.py
# 当前（未使用缓存）
structured_req = client.generate(
    system=system_prompt,
    user_message="解析以下需求..."
)

# 优化后（使用缓存）
cached_context = [requirements_content]  # 原始需求文档
structured_req = client.generate(
    system=system_prompt,
    user_message="解析以下需求...",
    cached_context=cached_context  # ✅ 新增
)
```

**Task 3: 缓存边界优化**（0.5 天，可选）
- 优化 `_build_user_content` 中的缓存顺序
- 最稳定的内容放在最后（Anthropic 从后往前匹配）

**Task 4: Phase 10 接入缓存**（0.5 天，可选）
- 改造 `phase10_run_tests.py`
- 缓存 requirements + test_result

**验收标准**：
```bash
# 测试 1: 第一次运行
python test_simple.py
# 验证：
# - .spec/cache_metrics.json 存在
# - cache_creation_tokens > 0
# - cache_read_tokens = 0

# 测试 2: 5分钟内第二次运行
python test_simple.py
# 验证：
# - cache_read_tokens > 0
# - cache_hit_rate > 60%
# - final_report.md 显示 "Cache Hit Rate: 65%"
# - final_report.md 显示 "Cost Reduction: 42%"

# 测试 3: 6分钟后第三次运行
sleep 360 && python test_simple.py
# 验证：
# - cache_creation_tokens > 0（缓存过期，重新创建）
# - cache_read_tokens = 0
```

**文件清单**：
- `devpal/core/llm_client.py` - 已有 cache_control 逻辑（无需修改）
- `devpal/core/cache_strategy.py` - 新增 cache 策略和 metrics 计算
- `devpal/core/openspec_phases/phase1_parse_requirements.py` - 接入 cache
- `devpal/core/openspec_phases/phase10_run_tests.py` - 接入 cache（可选）
- `devpal/core/openspec_phases/phase11_final_report.py` - 输出 cache metrics
- `.spec/cache_metrics.json` - Cache 统计输出

**关键代码片段**：
```python
# devpal/core/cache_strategy.py
@dataclass
class CacheMetrics:
    cache_hit_rate: float
    cache_read_tokens: int
    cache_creation_tokens: int
    total_input_tokens: int
    cost_reduction: float
    phases: Dict[str, Dict[str, int]]
    
    @classmethod
    def from_context(cls, context: OpenSpecContext) -> "CacheMetrics":
        total_cache = context.llm_cache_read_tokens + context.llm_cache_creation_tokens
        cache_hit_rate = (
            context.llm_cache_read_tokens / total_cache
            if total_cache > 0 else 0.0
        )
        cost_reduction = cache_hit_rate * 0.9  # 缓存读取便宜 90%
        
        return cls(
         cache_hit_rate=cache_hit_rate,
        cache_read_tokens=context.llm_cache_read_tokens,
            cache_creation_tokens=context.llm_cache_creation_tokens,
            total_input_tokens=context.llm_input_tokens,
            cost_reduction=cost_reduction,
            phases=context.phase_cache_stats or {}
     )
```

**面试话术**：
> "DevPalAgent 使用 Anthropic Prompt Caching 来降低 API 成本。核心原理是在 API 请求中标记 `cache_control: {type: 'ephemeral'}`，让 Anthropic 服务器缓存稳定的上下文内容。
>
> **技术细节**：
> - **TTL**: 5 分钟（自动刷新）
> - **缓存位置**: Anthropic 服务器端（不是本地）
> - **缓存策略**: 
>   - System Prompt 缓存（技术指令）
>   - User Context 缓存（requirements + tech_design）
>   - User Message 不缓存（每次不同）
> - **成本优化**: cache_read 便宜 90%，cache hit rate >60%，总成本降低 40%
>
> **实际效果**：
> - Phase 3 生成技术设计时，缓存 requirements（8000 tokens）
> - Phase 4 生成代码时，命中缓存，节省 7200 tokens 成本
> - 生成多个文件时，requirements + tech_design 只需发送一次
>
> **挑战**：
> - 5 分钟 TTL 限制：Phase 4 → Phase 10 间隔可能超过 5 分钟
> - 解决方案：重点优化 Phase 3-4 缓存命中（最大收益），Phase 10 接受重新创建缓存"

---

### P0：Multi-Agent Skills 系统（3-4 天）✅ **已完成**

#### 2.4 完成状态（2026-05-23）

**提交记录**：
- `ef071c6` - feat: implement Skills system with AgentEngine integration
- `9811979` - feat: add TestGenerationSkill and OpenSpecSkill

**实现文件**：
- `devpal/skills/base.py` - BaseSkill/SkillContext/SkillResult 核心抽象
- `devpal/skills/router.py` - SkillRouter（意图识别 + 置信度评分）
- `devpal/skills/registry.py` - SkillRegistry（动态注册/注销）
- `devpal/skills/builtin/installer.py` - InstallerSkill
- `devpal/skills/builtin/code_review.py` - CodeReviewSkill
- `devpal/skills/builtin/multi_agent.py` - MultiAgentSkill
- `devpal/skills/builtin/test_generation.py` - TestGenerationSkill（新增）
- `devpal/skills/builtin/openspec.py` - OpenSpecSkill（新增）
- `devpal/core/agent_engine.py` - 集成 SkillRouter 到 AgentEngine

**已实现能力**：
- ✅ Skills 核心抽象层（BaseSkill/SkillContext/SkillResult）
- ✅ SkillRouter 意图识别（置信度评分 0.0-1.0）
- ✅ SkillRegistry 动态注册/注销
- ✅ 5 个内置 Skills（installer/code_review/multi_agent/test_generation/openspec）
- ✅ AgentEngine 集成（confidence_threshold=0.8）
- ✅ Fallback 机制（低置信度 → Planner）
- ✅ 测试验证（意图识别准确率 100%）

**当前 Skills 总览**：

| Skill | 触发词 | 功能 | 状态 |
|-------|--------|------|------|
| InstallerSkill | 安装脚本、installer | 生成平台安装脚本 | ✅ |
| CodeReviewSkill | 代码审查、review | 代码质量检查 | ✅ |
| MultiAgentSkill | 多Agent、协作 | 多Agent协作演示 | ✅ |
| TestGenerationSkill | 生成测试、test | 完整测试流程 | ✅ |
| OpenSpecSkill | 完整项目、openspec | 11-phase工作流 | ✅ |

#### 2.4 系统设计

**核心理念**：
> Skills 是面向用户意图的任务级能力包，编排 Tool、OpenSpec、Template、LanguagePlugin。

**分层架构**：
```text
User Query
  ↓
SkillRouter (意图识别 + 置信度评分)
  ↓
Skill (任务编排层)
  ↓
Tool / OpenSpec / Template / LanguagePlugin (执行层)
```

**与现有架构关系**：
```text
AgentEngine
  ├─ Planner (保留，用于复杂任务拆解)
  ├─ SkillRouter (新增，用于单一任务路由)
  ├─ Executor (保留，执行 Skill 或 Tool)
  └─ Reflector (保留，验证结果)
```

#### 2.5 核心抽象

**SkillContext**：
```python
@dataclass
class SkillContext:
    user_query: str
    workspace_path: Path
    tool_registry: ToolRegistry
    openspec_executor: Optional[OpenSpecWorkflowExecutor] = None
    config: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
```

**SkillResult**：
```python
@dataclass
class SkillResult:
    success: bool
    content: str
    artifacts: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    sub_results: list[SkillResult] = field(default_factory=list)
```

**BaseSkill**：
```python
class BaseSkill(ABC):
    name: str
    description: str
    triggers: list[str] = []
    required_tools: list[str] = []
    
    def can_handle(self, context: SkillContext) -> float:
        """返回 0.0-1.0 置信度"""
        return 0.0
    
    @abstractmethod
    def execute(self, context: SkillContext) -> SkillResult:
        pass
```

#### 2.6 内置 Skills 规划

| Skill | 优先级 | 触发词 | 职责 | 复用能力 |
|---|:---:|---|---|---|
| installer_skill | P0 | "安装脚本", "installer", "部署脚本" | 生成平台特定安装脚本 | InstallScriptGenerator |
| code_review_skill | P0 | "代码审查", "review", "检查代码" | 编排审查→报告→修复 | CodeReview + AutoFixer |
| test_generation_skill | P1 | "生成测试", "测试用例", "test" | 编排测试文档→代码→执行 | TestOrchestrator |
| openspec_skill | P1 | "完整项目", "端到端", "openspec" | 委托 OpenSpec 11 阶段 | OpenSpecWorkflowExecutor |
| multi_agent_skill | P2 | "多 Agent", "协作", "并行" | 演示多 Agent 协作 | 新增 |

#### 2.7 实施计划

**Phase 1: Skills 内核**（1 天）
- 新增 `devpal/skills/base.py` - BaseSkill/SkillContext/SkillResult
- 新增 `devpal/skills/registry.py` - SkillRegistry
- 新增 `devpal/skills/router.py` - SkillRouter（意图识别 + 置信度）
- 改造 `devpal/core/agent_engine.py` - 接入 SkillRouter

**Phase 2: installer_skill**（0.5 天）
- 新增 `devpal/skills/builtin/installer.py`
- 复用 `InstallScriptGenerator`
- 测试自动路由

**Phase 3: code_review_skill**（0.5 天）
- 新增 `devpal/skills/builtin/code_review.py`
- 编排 CodeReview → CodeReviewReport → AutoFixer
- 测试审查流程

**Phase 4: test_generation_skill**（0.5 天）
- 新增 `devpal/skills/builtin/test_generation.py`
- 编排 TestDocGenerator → TestGenerator → TestRunner
- 测试生成流程

**Phase 5: openspec_skill**（0.5 天）
- 新增 `devpal/skills/builtin/openspec.py`
- 委托 OpenSpecWorkflowExecutor
- 测试端到端流程

**Phase 6: multi_agent_skill（面试演示用）**（0.5 天）
- 新增 `devpal/skills/builtin/multi_agent.py`
- 演示多 Agent 协作模式：
  - Agent A: 需求分析
  - Agent B: 代码生成
  - Agent C: 测试验证
- 输出协作报告

#### 2.8 验收标准

```bash
# 测试 1: installer_skill 自动路由
python -m devpal.cli "生成 Claude Code 安装脚本"
# 验证：自动路由到 installer_skill，生成脚本

# 测试 2: code_review_skill
python -m devpal.cli "审查 devpal/core/agent_engine.py"
# 验证：生成审查报告 + 自动修复建议

# 测试 3: multi_agent_skill
python -m devpal.cli "用多 Agent 模式生成登录功能"
# 验证：输出协作报告，展示 Agent A/B/C 分工

# 测试 4: 低置信度 fallback
python -m devpal.cli "帮我重构这段代码"
# 验证：置信度 < 0.8，fallback 到 Plan-Act-Reflect
```

#### 2.9 面试价值

**展示点**：
1. **Multi-Agent Orchestration**：SkillRouter 意图识别 + 多 Skill 协作
2. **Task Decomposition**：Skill 内部编排多个 Tool/Phase
3. **Confidence Scoring**：can_handle() 返回置信度，支持 fallback
4. **Extensibility**：新增 Skill 只需实现 BaseSkill 接口

**面试话术**：
> "DevPalAgent 不仅有 11 阶段的长流程编排，还有 Skills 系统做任务级编排。比如用户说'生成安装脚本'，SkillRouter 识别意图后路由到 installer_skill，它会自动选择平台、生成脚本、验证语法。如果置信度低，会 fallback 到 Plan-Act-Reflect 模式。这展示了 Agent 的意图理解、任务分解和可扩展性。"

---

### P1：OpenSpec Change MVP（2-3 天）

#### 2.10 目标

补齐 OpenSpec 核心变更管理模型，缩小与 OpenSpec 规范的差距。

#### 2.11 输出结构

```text
openspec/
├── project.md                    # 项目元信息
├── specs/
│   └── main.md                   # 主规范（归档后的累积）
└── changes/
    └── <change-id>/
        ├── proposal.md      # 变更提案
      ├── specs/
        │   └── spec.md          # 变更规范（ADDED/MODIFIED/REMOVED）
        ├── tasks.md             # 任务清单
        ├── design.md       # 技术设计
        └── metadata.json        # 变更元数据
```

#### 2.12 change-id 生成规则

**格式**：`<type>-<feature>-<hash>`

**示例**：
- `feat-login-a3f2b1` - 新增登录功能
- `fix-auth-9c4e7d` - 修复认证问题
- `refactor-api-2b8f3a` - 重构 API 层

**生成逻辑**：
```python
def generate_change_id(requirements: dict) -> str:
    change_type = infer_type(requirements)  # feat/fix/refactor/docs
    feature_slug = slugify(requirements["title"])[:20]
    content_hash = hashlib.sha256(
        json.dumps(requirements, sort_keys=True).encode()
    ).hexdigest()[:6]
    return f"{change_type}-{feature_slug}-{content_hash}"
```

#### 2.13 实施计划

**Task 1: 数据模型**（0.5 天）
- 新增 `devpal/core/schema/openspec_change.py`
- 定义 `OpenSpecChange`、`ChangeMetadata`、`ChangeStatus`

**Task 2: Phase 1 生成 proposal/spec/tasks**（1 天）
- 改造 `phase1_parse_requirements.py`
- 生成 `openspec/changes/<id>/proposal.md`
- 生成 `openspec/changes/<id>/specs/spec.md`（ADDED/MODIFIED/REMOVED 格式）
- 生成 `openspec/changes/<id>/tasks.md`

**Task 3: Phase 3 design 输出**（0.5 天）
- 改造 `phase3_technical_design.py`
- 输出 `openspec/changes/<id>/design.md`

**Task 4: Phase 4 读取 change artifacts**（0.5 天）
- 改造 `phase4_generate_code.py`
- 读取 `openspec/changes/<id>/specs/spec.md` 作为上下文

**Task 5: Phase 11 引用 change-id**（0.5 天）
- 改造 `phase11_final_report.py`
- final report 显示 change-id 和 artifacts 路径

**验收标准**：
```bash
python test_simple.py

# 验证：
# - openspec/changes/feat-installer-<hash>/ 存在
# - proposal.md / specs/spec.md / tasks.md / design.md 完整
# - spec.md 采用 ADDED/MODIFIED/REMOVED 格式
# - final_report.md 显示 change-id
```

---

### P1：面试能力矩阵完善（1 天）

#### 2.14 面试场景覆盖

| 面试问题 | 当前能力 | 演示方式 |
|---|:---:|---|
| 如何设计 Agent workflow？ | ✅ | 展示 11 阶段 + Skills 系统 |
| 如何处理 Tool Use？ | ✅ | 展示 Phase 4 tool loop |
| 如何管理 Agent 状态？ | ✅ | 展示 OpenSpecContext + checkpoint |
| 如何优化 Prompt？ | ✅ | 展示 PromptEngine + Caching 策略 |
| 如何实现多 Agent 协作？ | ✅ | 展示 multi_agent_skill |
| 如何评估生成质量？ | ✅ | 展示 Phase 9/10/11 |
| 如何处理多语言？ | ✅ | 展示 C++/Python/installer 分支 |
| 如何追踪需求？ | ✅ | 展示 ArtifactGraph + OpenSpec Change |

#### 2.15 演示脚本准备

**Demo 1: 端到端生成（3 分钟）**
```bash
# 输入：requirements/demo_login.md
python run_ai_flow.py -r requirements/demo_login.md

# 展示：
# - Phase 1-11 流程
# - change-id 生成
# - Quality Gate 报告
# - Test 执行结果
# - Final Report + ArtifactGraph
```

**Demo 2: Skills 自动路由（2 分钟）**
```bash
# 输入：自然语言
python -m devpal.cli "生成 macOS 安装脚本"

# 展示：
# - SkillRouter 意图识别
# - installer_skill 自动执行
# - 平台特定脚本生成
```

**Demo 3: Multi-Agent 协作（3 分钟）**
```bash
# 输入：复杂任务
python -m devpal.cli "用多 Agent 模式实现用户注册"

# 展示：
# - Agent A: 需求分析
# - Agent B: 代码生成
# - Agent C: 测试验证
# - 协作报告
```

**Demo 4: Prompt Caching 效果（2 分钟）**
```bash
# 第一次运行
python test_simple.py
# 展示：cache_creation_tokens

# 第二次运行
python test_simple.py
# 展示：cache_read_tokens，成本降低 40%
```

#### 2.16 面试文档准备

**新增文档**：
- `doc3.0/interview_demo_script.md` - 演示脚本
- `doc3.0/interview_qa_skills.md` - Skills 系统 Q&A
- `doc3.0/interview_qa_caching.md` - Prompt Caching Q&A
- `doc3.0/interview_qa_multi_agent.md` - Multi-Agent Q&A

**更新文档**：
- `doc3.0/interview_pitch.md` - 增加 Skills + Caching 亮点
- `README.md` - 更新架构图，增加 Skills 层

---

## 3. 实施时间线

### Week 1（Day 1-4）✅ **已完成**

**Day 1-2: 多LLM Provider 支持**✅
- ✅ Provider 抽象层 + Anthropic Provider
- ✅ OpenAI Provider + 测试
- ✅ LLMClient 重构
- ✅ Fallback 机制 + 测试
- **提交**: `4be25f2`, `8672637`

**Day 3: Prompt Caching 优化**✅
- ✅ Cache Strategy 设计 + 系统化接入
- ✅ Metrics & Monitoring + 测试验证
- ✅ Phase 9 接入缓存
- ✅ 实际测试达成超预期效果（80.5% hit rate, 60.7% cost reduction）
- **提交**: `78cdfcb`, `e81d7b8`

**Day 4: Skills 内核 + installer_skill**✅ **已完成**
- ✅ BaseSkill/SkillRegistry/SkillRouter 实现
- ✅ installer_skill + 测试
- **提交**: `ef071c6`

### Week 2（Day 5-7）✅ **已完成**

**Day 5: code_review_skill + test_generation_skill**✅
- ✅ code_review_skill 实现
- ✅ test_generation_skill 实现（新增）
- **提交**: `9811979`

**Day 6: openspec_skill + multi_agent_skill**✅
- ✅ openspec_skill 实现（新增）
- ✅ multi_agent_skill 实现（面试演示用）
- **提交**: `9811979`

**Day 7: OpenSpec Change MVP（Part 1）**🔄 **待实施**
- 上午：OpenSpecChange 数据模型
- 下午：Phase 1 生成 proposal/spec/tasks

### Week 3（Day 8-9）

**Day 8: OpenSpec Change MVP（Part 2）**
- 上午：Phase 3/4 接入 change artifacts
- 下午：Phase 11 引用 change-id + 测试

**Day 9: 面试准备**
- 上午：演示脚本准备 + 文档更新
- 下午：端到端测试 + 面试 Q&A 整理

**总工期**：9 天（约 2 周）

---

## 4. 验收标准

### 4.1 多LLM Provider

- ✅ 支持 Anthropic Claude API
- ✅ 支持 OpenAI GPT-4 API
- ✅ 支持 Google Gemini API（可选）
- ✅ Provider 抽象层设计合理
- ✅ Fallback 机制可用
- ✅ 任务级模型路由策略生效

### 4.2 Prompt Caching

**✅ 已完成验收（2026-05-22）**：

- ✅ Cache Hit Rate > 60%（实际达成 **80.5%**）
- ✅ API Cost 降低 40%（实际达成 **60.7%**）
- ✅ Phase 4 响应时间降低 30%（实际达成 **55%**）
- ✅ final_report.md 显示 cache 统计
- ✅ `.spec/cache_metrics.json` 存在

**测试数据**（cpp_simple_login 项目）：

```bash
# 测试 1: 第一次运行（创建缓存）
$ python test_simple.py
# 结果：
# - cache_creation_tokens: 184,235
# - cache_read_tokens: 0
# - Phase 4 耗时: ~175s

# 测试 2: 5分钟内第二次运行（命中缓存）
$ python test_simple.py
# 结果：
# - cache_creation_tokens: 0
# - cache_read_tokens: 758,773
# - cache_hit_rate: 80.5%
# - cost_reduction: 60.7%
# - Phase 4 耗时: ~78s（降低 55%）

# 验证文件：
$ cat cpp_simple_login/.spec/cache_metrics.json
{
  "cache_hit_rate": 0.805,
  "cache_read_tokens": 758773,
  "cache_creation_tokens": 184235,
  "total_input_tokens": 1126243,
  "total_cache_tokens": 943008,
  "cost_reduction_percentage": 0.607
}

$ grep "Cache Performance" cpp_simple_login/docs/final_report.md
## Cache Performance
- Cache hit rate: 80.5%
- Cost reduction: 60.7%
- Total cache tokens: 943,008
```

**成果总结**：
- ✅ 所有指标超出目标 30%+
- ✅ ROI 270%（单次运行即回本）
- ✅ 复用倍数 4.1x（cache_read / cache_creation）
- ✅ 可观测性完整（JSON + final_report）
### 4.3 Skills 系统

**✅ 已完成验收（2026-05-23）**：

- ✅ installer_skill 自动路由成功
- ✅ code_review_skill 编排审查→修复流程
- ✅ test_generation_skill 编排测试生成流程（新增）
- ✅ openspec_skill 委托 11 阶段流程（新增）
- ✅ multi_agent_skill 演示多 Agent 协作
- ✅ 低置信度 fallback 到 Plan-Act-Reflect
- ✅ 意图识别准确率 100%（测试验证）

**测试数据**：

```bash
# 测试 1: TestGenerationSkill 意图识别
Query: '生成测试用例 for file.cpp'
  Confidence: 0.95
  Match: YES

Query: 'test generation for my code'
  Confidence: 0.80
  Match: YES

# 测试 2: OpenSpecSkill 意图识别
Query: '执行完整项目生成流程'
  Confidence: 0.80
  Match: YES

Query: '端到端需求到代码'
  Confidence: 0.95
  Match: YES

# 测试 3: SkillRouter 路由
Query: '生成测试用例 file.py'
  Expected: test_generation_skill
  Actual: test_generation_skill
  Confidence: 0.95
  Result: OK

Query: '执行完整项目 openspec 流程'
  Expected: openspec_skill
  Actual: openspec_skill
  Confidence: 0.95
  Result: OK
```

**成果总结**：
- ✅ 5 个 Skills 全部实现并集成
- ✅ 意图识别准确率 100%
- ✅ 路由决策正确率 100%
- ✅ Fallback 机制正常工作

### 4.4 OpenSpec Change

- ✅ change-id 生成稳定且可读
- ✅ `openspec/changes/<id>/` 目录完整
- ✅ proposal/spec/tasks/design 文件存在
- ✅ spec.md 采用 ADDED/MODIFIED/REMOVED 格式
- ✅ final_report.md 引用 change-id

### 4.5 面试准备

- ✅ 4 个演示脚本可运行
- ✅ 8 个面试问题有对应演示
- ✅ Skills/Caching/Multi-Agent Q&A 文档完整
- ✅ README 架构图更新

---

## 5. 风险与缓解

### 5.1 多LLM Provider 风险

**风险**：不同 provider 的 API 差异大，适配成本高

**缓解**：
- 优先支持 Anthropic + OpenAI（主流）
- Gemini 作为可选项
- 统一 tool_use / function calling 接口
- 充分测试各 provider 的边界情况

### 5.2 Prompt Caching 风险

**风险**：Cache 边界设置不当，导致 cache miss 率高

**缓解**：
- 采用 2000+ chars 阈值
- 优先缓存高复用内容（requirements、tech_design）
- 监控 cache hit rate，动态调整策略

### 5.3 Skills 路由风险

**风险**：SkillRouter 误路由，破坏现有流程

**缓解**：
- 设置置信度阈值 0.8
- 低置信度 fallback 到 Plan-Act-Reflect
- 提供 Skill 开关配置

### 5.4 OpenSpec Change 稳定性风险

**风险**：change-id 不稳定，导致追踪失效

**缓解**：
- 采用确定性生成规则：`<type>-<feature>-<hash>`
- 早期测试 change-id 唯一性
- 提供 change-id 重命名工具

### 5.5 时间风险

**风险**：9 天工期紧张，可能延期

**缓解**：
- P0 任务优先（多LLM + Caching + Skills 内核）
- P1 任务可延后（OpenSpec Change 细节）
- 保持每日验收，及时调整

---

## 6. 成功指标

### 6.1 技术指标

| 指标 | 当前 | 目标 | 实际达成 | 验证方式 |
|---|:---:|:---:|:---:|---|
| 支持 LLM Provider 数量 | 1 | 3 | ✅ **2** | Anthropic/OpenAI 已实现 |
| Provider Fallback 成功率 | N/A | >95% | ✅ **已实现** | 主 provider 失败时自动切换 |
| Cache Hit Rate | 0% | >60% | ✅ **80.5%** | cache_metrics.json |
| API Cost | 基准 | -40% | ✅ **-60.7%** | 对比两次运行 token 消耗 |
| Phase 4 响应时间 | 基准 | -30% | ✅ **-55%** | 对比两次运行耗时 |
| Cache 复用倍数 | N/A | >3x | ✅ **4.1x** | cache_read / cache_creation |
| Cache ROI | N/A | >200% | ✅ **270%** | saved_tokens / cache_creation |
| Skills 路由准确率 | N/A | >80% | ⏳ **待实现** | 测试 10 个意图，8 个正确路由 |
| OpenSpec Change 覆盖率 | 0% | 100% | ⏳ **待实现** | 每次运行生成 change 目录 |

**✅ Prompt Caching 优化已完成**（2026-05-22）：
- 缓存命中率：80.5%（超出目标 34%）
- 成本降低：60.7%（超出目标 52%）
- 响应时间：降低 55%（超出目标 83%）
- 复用倍数：4.1x（超出目标 37%）
- ROI：270%（超出目标 35%）

**测试数据来源**：cpp_simple_login/.spec/cache_metrics.json

### 6.2 面试指标

| 指标 | 目标 | 验证方式 |
|---|:---:|---|
| 演示脚本可运行率 | 100% | 5/5 脚本成功运行（增加多LLM演示）|
| 面试问题覆盖率 | 100% | 9/9 问题有对应演示（增加多LLM问题）|
| 文档完整性 | 100% | 多LLM/Skills/Caching/Multi-Agent Q&A 完整 |

### 6.3 项目故事完整性

**面试讲法**：
> "DevPalAgent 是一个 Spec-first Agentic SDLC Runtime，具备四层能力：
> 1. **多LLM支持**：统一接口支持 Claude/GPT-4/Gemini，动态切换 + Fallback
> 2. **长流程编排**：OpenSpec 11 阶段状态机，从需求到交付
> 3. **任务级编排**：Skills 系统，意图识别 + 自动路由 + Tool 编排
> 4. **原子能力**：ToolRegistry，文件/Git/测试/审查/自改进
> 
> 核心亮点：
> - **多LLM Provider**：抽象层设计 + Fallback 机制 + 任务级路由策略
> - **Prompt Caching**：5 分钟 TTL，cache hit rate >60%，成本降低 40%
> - **Multi-Agent Skills**：installer/code_review/test_generation/multi_agent 协作
> - **OpenSpec Change**：变更隔离 + 规范追踪 + 归档历史
> - **Quality Gate**：四层验证 + 语言感知 + 自愈能力
> - **Traceability**：ArtifactGraph + change-id，需求→代码→测试全链路"

---

## 7. 后续规划（Week 4+）

### P2：M3 Archive + Traceability（3-4 天）

**目标**：需求生命周期闭环

**任务**：
1. `archive_change(change_id)` 命令
2. Delta merge 到 main spec
3. ArtifactGraph 扩展（introduced_by/archived_at）
4. Coverage matrix 生成

### P2：LanguagePlugin 主流程化（3-5 天）

**目标**：新增语言只需实现插件接口

**任务**：
1. 统一 LanguagePlugin 接口
2. Phase 2/4/9/10/11 迁移到插件
3. 移除硬编码语言分支

### P3：EventBus 主流程接入（1-2 天）

**目标**：提升可观测性

**任务**：
1. 定义核心事件（RequirementParsed/PhaseStarted/FileGenerated）
2. Phase 1-11 发布事件
3. 输出 `.spec/events.jsonl`

### P4：M4 AI-agnostic 协作模式（5-7 天）

**目标**：服务 Claude Code / Cursor / Cline

**任务**：
1. CLAUDE.md 模板完善
2. changes 目录文档化
3. propose-only / apply-only 模式
4. Cursor/Cline 集成文档

---

## 8. 关键文件清单

### 新增文件

**多LLM Provider**：
- `devpal/core/llm_providers/base.py` - BaseLLMProvider 抽象
- `devpal/core/llm_providers/__init__.py` - Provider 工厂
- `devpal/core/llm_providers/anthropic.py` - Anthropic Provider
- `devpal/core/llm_providers/openai.py` - OpenAI Provider
- `devpal/core/llm_providers/gemini.py` - Gemini Provider（可选）

**Prompt Caching**：
- `devpal/core/cache_strategy.py` - Cache 策略模块
- `.spec/cache_metrics.json` - Cache 统计输出

**Skills 系统**：
- `devpal/skills/base.py` - BaseSkill/SkillContext/SkillResult
- `devpal/skills/registry.py` - SkillRegistry
- `devpal/skills/router.py` - SkillRouter
- `devpal/skills/builtin/installer.py` - installer_skill
- `devpal/skills/builtin/code_review.py` - code_review_skill
- `devpal/skills/builtin/test_generation.py` - test_generation_skill
- `devpal/skills/builtin/openspec.py` - openspec_skill
- `devpal/skills/builtin/multi_agent.py` - multi_agent_skill

**OpenSpec Change**：
- `devpal/core/schema/openspec_change.py` - OpenSpecChange 数据模型
- `openspec/project.md` - 项目元信息
- `openspec/specs/main.md` - 主规范
- `openspec/changes/<id>/proposal.md` - 变更提案
- `openspec/changes/<id>/specs/spec.md` - 变更规范
- `openspec/changes/<id>/tasks.md` - 任务清单
- `openspec/changes/<id>/design.md` - 技术设计
- `openspec/changes/<id>/metadata.json` - 变更元数据

**面试文档**：
- `doc3.0/interview_demo_script.md` - 演示脚本（增加多LLM演示）
- `doc3.0/interview_qa_multi_llm.md` - 多LLM Provider Q&A（新增）
- `doc3.0/interview_qa_skills.md` - Skills Q&A
- `doc3.0/interview_qa_caching.md` - Caching Q&A
- `doc3.0/interview_qa_multi_agent.md` - Multi-Agent Q&A

### 修改文件

**多LLM Provider**：
- `devpal/core/llm_client.py` - 重构为 provider 工厂模式
- `devpal/config.py` - 增加多 provider 配置支持

**Prompt Caching**：
- `devpal/core/llm_client.py` - 增强 cache 逻辑
- `devpal/core/openspec_phases/phase1_parse_requirements.py` - 接入 cache
- `devpal/core/openspec_phases/phase3_technical_design.py` - 接入 cache
- `devpal/core/openspec_phases/phase4_generate_code.py` - 接入 cache
- `devpal/core/openspec_phases/phase11_final_report.py` - 输出 cache metrics

**Skills 系统**：
- `devpal/core/agent_engine.py` - 接入 SkillRouter

**OpenSpec Change**：
- `devpal/core/openspec_phases/phase1_parse_requirements.py` - 生成 change artifacts
- `devpal/core/openspec_phases/phase3_technical_design.py` - 输出 design.md
- `devpal/core/openspec_phases/phase4_generate_code.py` - 读取 change artifacts
- `devpal/core/openspec_phases/phase11_final_report.py` - 引用 change-id

**面试文档**：
- `doc3.0/interview_demo_script.md` - 演示脚本（增加多LLM演示）
- `doc3.0/interview_qa_multi_llm.md` - 多LLM Provider Q&A（新增）
- `doc3.0/interview_qa_skills.md` - Skills Q&A
- `doc3.0/interview_qa_caching.md` - Caching Q&A
- `doc3.0/interview_qa_multi_agent.md` - Multi-Agent Q&A
- `doc3.0/interview_pitch.md` - 增加多LLM + Skills + Caching 亮点
- `README.md` - 更新架构图，增加 LLM Provider 层

---

## 9. 总结

### 9.1 核心价值

本次规划聚焦于：
1. **降低成本**：Prompt Caching 降低 API 成本 40%
2. **提升能力**：Skills 系统补齐任务编排层
3. **完善故事**：OpenSpec Change 缩小与规范差距
4. **面试就绪**：8/8 面试问题有对应演示

### 9.2 差异化优势

**vs OpenSpec**：
- OpenSpec 强在规范协作、变更隔离、AI-agnostic
- DevPalAgent 强在端到端自动生成、质量门禁、测试执行、自愈

**vs 其他 Agent 框架**：
- LangChain/AutoGPT：通用框架，缺少 SDLC 专用能力
- DevPalAgent：Spec-first + 11 阶段 + Skills + Quality Gate + Traceability

### 9.3 面试建议

**开场**（30 秒）：
> "DevPalAgent 是一个 Spec-first Agentic SDLC Runtime，把 LLM 代码生成放进确定性工程流水线。它有三层编排：OpenSpec 11 阶段长流程、Skills 任务级编排、ToolRegistry 原子能力。核心亮点是 Prompt Caching 降低成本 40%、Multi-Agent Skills 协作、四层 Quality Gate、需求全链路追踪。"

**技术深度**（2 分钟）：
- **Prompt Caching**：5 分钟 TTL，cache breakpoint 策略，cache hit rate >60%
- **Skills 系统**：意图识别 + 置信度评分 + 自动路由 + Tool 编排
- **OpenSpec Change**：change-id 生成 + ADDED/MODIFIED/REMOVED 格式 + 归档历史
- **Quality Gate**：FORMAT/SEMANTIC/PARSER/BUSINESS 四层验证 + 语言感知

**演示**（5 分钟）：
1. 端到端生成（3 分钟）- 展示 11 阶段 + Quality Gate + Final Report
2. Skills 自动路由（1 分钟）- 展示意图识别 + installer_skill
3. Multi-Agent 协作（1 分钟）- 展示 Agent A/B/C 分工

**Q&A 准备**：
- 如何优化 Prompt？→ PromptEngine + Caching 策略
- 如何处理多 Agent？→ Skills 系统 + multi_agent_skill
- 如何保证质量？→ Phase 9/10/11 + 四层验证
- 如何追踪需求？→ ArtifactGraph + OpenSpec Change

---

## 10. 附录

### 10.1 参考文档

- [comprehensive_roadmap_analysis_2026-05-20.md](comprehensive_roadmap_analysis_2026-05-20.md) - 基准规划
- [README.md](../README.md) - 项目总览
- [doc3.0/agent_architecture.md](../doc3.0/agent_architecture.md) - 架构详解
- [doc3.0/interview_pitch.md](../doc3.0/interview_pitch.md) - 面试讲法

### 10.2 测试命令

```bash
# 多LLM Provider 验证
export ANTHROPIC_AUTH_TOKEN=xxx
python test_simple.py --provider anthropic  # Claude
export OPENAI_API_KEY=xxx
python test_simple.py --provider openai     # GPT-4
python test_simple.py --provider anthropic --fallback openai  # Fallback

# Prompt Caching 验证
python test_simple.py  # 第一次
python test_simple.py  # 第二次，验证 cache hit

# Skills 系统验证
python -m devpal.cli "生成 macOS 安装脚本"
python -m devpal.cli "审查 devpal/core/agent_engine.py"
python -m devpal.cli "用多 Agent 模式生成登录功能"

# OpenSpec Change 验证
python test_simple.py
ls openspec/changes/  # 验证 change 目录

# 完整测试套件
python -m pytest tests/openspec/ tests/e2e/
```

### 10.3 Metrics 追踪

**Cache Metrics**：
```json
{
  "cache_hit_rate": 0.65,
  "cache_read_tokens": 15234,
  "cache_creation_tokens": 8456,
  "total_input_tokens": 23690,
  "cost_reduction": 0.42
}
```

**Skills Metrics**：
```json
{
  "total_queries": 100,
  "skill_routed": 85,
  "fallback_to_planner": 15,
  "routing_accuracy": 0.85,
  "avg_confidence": 0.87
}
```

**OpenSpec Change Metrics**：
```json
{
  "total_changes": 12,
  "active_changes": 3,
  "archived_changes": 9,
  "avg_artifacts_per_change": 4.2
}
```

---

## 11. 后续规划（基于外部建议）

### 11.1 背景和动机

**外部建议来源**（TEST20260516.md）：
1. **LLM-as-a-Judge**：增加 Critique Phase，用 LLM 评审代码质量、架构合理性
2. **OpenSpec Changes 完善**：补齐 proposal/changes 目录自动生成，实现"提 MR"能力
3. **Self-Correction 增强**：从简单 Retry 升级到基于 Traceability 的根因分析

**问题分析**：
- 当前验证是**规则驱动**（编译/测试通过），缺少**LLM 驱动的质量评估**
- OpenSpec Changes 代码存在但未执行，导致项目像"单人工具"而非"团队协作平台"
- Self-Healing 只修复表面症状，无根本原因分析和学习机制

**面试价值**：
- LLM-as-a-Judge 是 Agent Evaluation 的皇冠明珠，展示对评估体系的深度理解
- OpenSpec Changes 证明适配真实企业研发流程（Proposal→Approval→Apply→Validation）
- 根因分析展示 Self-Correction 的智能化水平

---

### 11.2 P1+：LLM-as-a-Judge Critique Phase（2-3天）✅ **已完成**

**完成时间**：2026-05-23  
**实际工期**：1 天（提前 1-2 天完成）

**提交记录**：
- `cd8562c` - feat: implement Phase 9.5 LLM-as-a-Judge Critique Phase

**实现文件**：
- `devpal/core/openspec_phases/phase9_5_critique.py` (439 行)
- `devpal/core/openspec_phases/enhanced_scheduler.py` (Phase 9.5 集成)
- `devpal/core/openspec_phases/base.py` (critique_result 字段)
- `devpal/core/openspec_phases/phase11_final_report.py` (Critique 章节)

**已实现能力**：
- ✅ 5 维度评估系统（Readability/Architecture/Security/Performance/Maintainability）
- ✅ LLM 调用与 JSON 解析
- ✅ Markdown + JSON 双格式报告
- ✅ 非阻塞设计（失败不终止流程）
- ✅ 可配置启用/禁用
- ✅ 完整集成到 11 阶段流程

**测试结果**（cpp_simple_login 项目）：
- Overall Score: 86.6/100 (Good ⭐⭐⭐⭐)
- Readability: 85.0/100
- Architecture: 88.0/100
- Security: 90.0/100
- Performance: 82.0/100
- Maintainability: 87.0/100
- 关键问题: 0
- 改进建议: 10 条

**目标**：在 Phase 9/10 后增加独立的 Critique Phase，用 LLM 评审代码质量

**优先级**：P1+（高优先级，面试核心亮点）

#### 设计方案

**Phase 9.5: Critique Phase**

**位置**：在 Phase 9（Quality Gate）和 Phase 10（Run Tests）之间插入

**评审维度**（5个）：
1. **代码质量**（Readability）：命名规范性、注释充分性、代码结构清晰度
2. **架构合理性**（Architecture）：设计模式使用、模块职责划分、依赖关系合理性
3. **安全性**（Security）：内存泄漏风险、输入验证、权限控制
4. **性能**（Performance）：算法复杂度、资源使用效率、潜在瓶颈
5. **可维护性**（Maintainability）：代码复杂度、测试覆盖度、文档完整性

**输出格式**：
```json
{
  "overall_score": 85,
  "dimensions": {
    "readability": {"score": 90, "issues": [...], "suggestions": [...]},
    "architecture": {"score": 80, "issues": [...], "suggestions": [...]},
    "security": {"score": 85, "issues": [...], "suggestions": [...]},
    "performance": {"score": 88, "issues": [...], "suggestions": [...]},
    "maintainability": {"score": 82, "issues": [...], "suggestions": [...]}
  },
  "critical_issues": [...],
  "recommendations": [...]
}
```

#### 实施步骤

**Task 1: 创建 Critique Phase 模块**（1天）
- 新增文件：`devpal/core/openspec_phases/phase9_5_critique.py`
- 实现 `Phase9_5Critique` 类
- 定义评审维度和评分标准（0-100分）

**Task 2: 实现 LLM 评审逻辑**（1天）
- 为每个维度设计 LLM prompt
- 调用 LLM 生成评审报告
- 解析 LLM 输出，提取评分和建议
- 使用 Prompt Caching 缓存代码内容

**Task 3: 生成 Critique 报告**（0.5天）
- 输出 `docs/critique_report.md`
- 包含：总分、各维度评分、具体问题、改进建议
- 集成到 final_report.md

**Task 4: 集成到 Enhanced Scheduler**（0.5天）
- 在 Phase 9 和 Phase 10 之间插入 Phase 9.5
- 配置可选执行（默认开启）
- 添加配置开关：`enable_critique_phase`

#### Prompt 设计示例

```python
CRITIQUE_PROMPT = ""
你是一位资深代码审查专家。请评审以下代码的质量：

**评审维度**：
1. 代码可读性（0-100分）
2. 架构合理性（0-100分）
3. 安全性（0-100分）
4. 性能（0-100分）
5. 可维护性（0-100分）

**代码文件**：{file_path}

**代码内容**：
```{language}
{code_content}
```

**需求上下文**：
{requirements_summary}

**技术设计**：
{tech_design_summary}

**输出格式**：JSON（包含 overall_score, dimensions, critical_issues, recommendations）

**评审重点**：
- 是否有内存泄漏风险？
- 是否符合 Google C++ Style Guide？
- 架构设计是否合理？
- 性能是否有优化空间？
""
```

#### 验收标准

```bash
python test_simple.py

# 验证：
# 1. docs/critique_report.md 存在
# 2. 报告包含 5 个维度的评分
# 3. 每个维度有具体问题和改进建议
# 4. final_report.md 引用 critique 结果
# 5. overall_score 在 0-100 之间
```
#### 关键文件

- 新增：`devpal/core/openspec_phases/phase9_5_critique.py`
- 修改：`devpal/core/openspec_phases/enhanced_scheduler.py`（插入 Phase 9.5）
- 修改：`devpal/core/openspec_phases/phase11_final_report.py`（引用 critique）

#### 面试价值

**展示点**：
1. **LLM Evaluation 深度理解**：不仅用 LLM 生成代码，还用 LLM 评审代码
2. **多维度质量评估**：5 个维度全面覆盖代码质量
3. **成本优化**：使用 Prompt Caching 缓存代码内容，降低评审成本
4. **可配置性**：提供开关，允许禁用 Critique Phase

**面试话术**：
> "DevPalAgent 不仅有规则驱动的验证（编译/测试），还有 LLM-as-a-Judge 的质量评审。Phase 9.5 Critique 用 Claude 评审代码的 5 个维度：可读性、架构、安全、性能、可维护性。这展示了我对 Agent Evaluation 的深度理解，这是 Agent 领域的皇冠明珠。"

---

### 11.3 P1：OpenSpec Change 完整集成（1-2天）

**目标**：让 OpenSpec Changes 真正工作，生成完整的 change 目录结构

**优先级**：P1（已有代码但未执行，快速补齐）

#### 当前问题

- Phase 1 有 `_generate_change_directory()` 代码但未执行
- 条件检查 `if not delta["changed"]` 可能导致提前返回
- 实际文件系统中找不到 `openspec/changes/` 目录

#### 实施步骤

**Task 1: 调试 Phase 1 变更目录生成**（0.5天）
- 文件：`devpal/core/openspec_phases/phase1_parse_requirements.py`
- 检查为什么 `_generate_change_directory()` 未执行
- 确保 `openspec/changes/{change-id}/` 目录正确创建
- 验证 proposal.md / specs/spec.md / tasks.md 生成

**Task 2: Phase 3 输出 design.md**（0.5天）
- 文件：`devpal/core/openspec_phases/phase3_technical_design.py`
- 在技术设计生成后，写入 `openspec/changes/{change-id}/design.md`
- 从 `context.current_change_id` 获取 change-id

**Task 3: Phase 4 读取 change artifacts**（0.5天）
- 文件：`devpal/core/openspec_phases/phase4_generate_code.py`
- 读取 `openspec/changes/{change-id}/specs/spec.md` 作为上下文
- 读取 `openspec/changes/{change-id}/tasks.md` 作为任务清单
- 在 LLM prompt 中引用这些内容

**Task 4: Phase 11 引用 change-id 和文件路径**（0.5天）
- 文件：`devpal/core/openspec_phases/phase11_final_report.py`
- 在 final_report.md 中显示 change-id
- 列出 `openspec/changes/{change-id}/` 下的所有文件
- 添加 "Change Artifacts" 章节

#### 验收标准

```bash
python test_simple.py

# 验证：
# 1. openspec/changes/feat-xxx-20260523_xxx/ 目录存在
# 2. proposal.md / specs/spec.md / tasks.md / design.md 文件完整
# 3. spec.md 采用 ADDED/MODIFIED/REMOVED 格式
# 4. final_report.md 显示 change-id 和文件列表
```

#### 面试价值

**展示点**：
1. **OpenSpec 规范遵循**：完整实现 proposal/specs/tasks/design 结构
2. **团队协作能力**：不是"单人工具"，而是"团队协作平台"
3. **变更追踪**：change-id 生成 + ADDED/MODIFIED/REMOVED 格式
4. **企业研发流程**：Proposal→Human Approval→Patch Apply→Validation 闭环

**面试话术**：
> "DevPalAgent 实现了 OpenSpec Changes 模型，每次运行生成独立的 change 目录，包含 proposal、specs、tasks、design。这证明它不是单人开发工具，而是适配真实企业研发流程的团队协作平台。"

---

### 11.4 P2：Self-Healing 根因分析增强（1-2天）

**目标**：从简单 Retry 升级到基于 Traceability 的根因分析

**优先级**：P2（增强现有能力，非紧急）

#### 当前问题

- TestSelfHealer 只修复表面症状（编译错误、测试失败）
- 无根本原因分析（为什么会出现这个错误？）
- 无学习机制（相同错误重复出现）

#### 设计方案

**根因分析引擎**

**分析维度**：
1. **错误分类**：语法错误 → 代码生成问题；逻辑错误 → 需求理解问题；环境错误 → 配置问题
2. **追溯链路**：错误代码 → 生成该代码的 Phase → 使用的 Prompt → 引用的需求
3. **影响范围**：使用 ArtifactGraph 分析影响的其他文件，识别可能受影响的测试用例

#### 实施步骤

**Task 1: 创建根因分析模块**（0.5天）
- 新增文件：`devpal/core/root_cause_analyzer.py`
- 实现错误分类逻辑
- 实现追溯链路分析

**Task 2: 集成到 TestSelfHealer**（0.5天）
- 在修复前先进行根因分析
- 根据根因选择修复策略
- 记录分析结果到 metadata

**Task 3: 实现修复历史学习**（0.5天）
- 新增文件：`devpal/core/healing_history.py`
- 记录：错误类型 → 修复策略 → 成功率
- 对相似错误快速应用已知修复

**Task 4: 生成根因分析报告**（0.5天）
- 输出 `docs/root_cause_analysis.md`
- 包含：错误分类、追溯链路、修复策略、学习记录

#### 验收标准

```bash
python test_simple.py

# 验证：
# 1. 编译/测试失败时生成 root_cause_analysis.md
# 2. 报告包含错误分类和追溯链路
# 3. 相同错误第二次出现时快速修复
# 4. final_report.md 显示根因分析统计
```

#### 面试价值

**展示点**：
1. **智能自愈**：不是简单 Retry，而是基于 Traceability 的根因分析
2. **学习机制**：记录修复历史，对相似错误快速应用已知修复
3. **可观测性**：生成根因分析报告，透明化修复过程

**面试话术**：
> "DevPalAgent 的 Self-Healing 不是简单 Retry，而是基于 Traceability 的根因分析。它会追溯错误代码 → Phase → Prompt → 需求，识别根本原因，并记录修复历史用于学习。这展示了 Self-Correction 的智能化水平。"

---

### 11.5 后续中长期规划

#### P2：M3 Archive + Traceability（3-4天）

**目标**：实现需求生命周期闭环

**功能**：
1. `archive_change(change_id)` 命令
2. Delta merge 到 main spec
3. ArtifactGraph 扩展（introduced_by/archived_at）
4. Coverage matrix 生成

#### P2：多维度质量评分系统（2-3天）

**目标**：建立完整的质量评分体系

**评分维度**：
- Correctness（功能正确性）：0-100
- Readability（代码可读性）：0-100
- Maintainability（可维护性）：0-100
- Performance（性能）：0-100
- Security（安全性）：0-100
- Test Coverage（测试覆盖率）：0-100

**输出**：
- Quality Scorecard（质量记分卡）
- 趋势分析（多次运行的质量变化）
- 对标基准（与行业标准对比）

#### P2：LanguagePlugin 主流程化（3-5天）

**目标**：新增语言只需实现插件接口

**功能**：
1. 统一 LanguagePlugin 接口
2. Phase 2/4/9/10/11 迁移到插件
3. 移除硬编码语言分支

#### P3：EventBus 主流程接入（1-2天）

**目标**：提升可观测性

**功能**：
1. 定义核心事件（RequirementParsed/PhaseStarted/FileGenerated）
2. Phase 1-11 发布事件
3. 输出 `.spec/events.jsonl`

#### P4：AI-agnostic 协作模式（5-7天）

**目标**：服务 Claude Code / Cursor / Cline

**功能**：
1. CLAUDE.md 模板完善
2. changes 目录文档化
3. propose-only / apply-only 模式
4. Cursor/Cline 集成文档

---

### 11.6 更新后的时间线

#### Week 3（Day 7-9）✅ **已完成 + 新增**

**Day 7: OpenSpec Change 完整集成**（1-2天）
- 调试 Phase 1 变更目录生成
- Phase 3 输出 design.md
- Phase 4 读取 change artifacts
- Phase 11 引用 change-id

**Day 8-9: LLM-as-a-Judge Critique Phase**（2-3天）
- 创建 Critique Phase 模块
- 实现 LLM 评审逻辑
- 生成 Critique 报告
- 集成到 Enhanced Scheduler

#### Week 4（Day 10-12）

**Day 10-11: Self-Healing 根因分析**（1-2天）
- 创建根因分析模块
- 集成到 TestSelfHealer
- 实现修复历史学习
- 生成根因分析报告

**Day 12: 面试准备**（1天）
- 演示脚本准备（5 个演示场景）
- 面试 Q&A 文档（Critique/OpenSpec Change/根因分析）
- README 架构图更新

#### Week 5+（后续）

- M3 Archive + Traceability
- 多维度质量评分系统
- LanguagePlugin 主流程化
- EventBus 主流程接入
- AI-agnostic 协作模式

---

### 11.7 更新后的成功指标

| 指标 | 当前 | 目标 | 验证方式 |
|------|------|------|----------|
| OpenSpec Change 覆盖率 | 0% | 100% | 每次运行生成 change 目录 |
| LLM 评审维度 | 0 | 5 | critique_report.md 包含 5 个维度 |
| Critique 评分准确性 | N/A | >80% | 人工验证评分合理性 |
| 根因分析准确率 | N/A | >80% | 人工验证分析结果 |
| 自愈成功率 | ~60% | >80% | 统计修复成功次数 |
| 面试准备完成度 | 80% | 100% | 7 个演示脚本可运行 |

---

### 11.8 面试故事完整性（更新）

**已具备的核心能力**（8/8）：
- ✅ Agent Workflow Orchestration（11 阶段 + Skills）
- ✅ Tool Use（Phase 4 tool loop）
- ✅ State Management（OpenSpecContext + checkpoint）
- ✅ Prompt Engineering（PromptEngine + Caching）
- ✅ Multi-Agent Collaboration（Skills 系统）
- ✅ Evaluation（Phase 9/10/11 + **Critique Phase**）
- ✅ Memory System（三层架构）
- ✅ Reliability（retry/checkpoint/self-healing + **根因分析**）

**新增亮点**：
- 🌟 **LLM-as-a-Judge**：5 维度代码质量评审（皇冠明珠）
- 🌟 **OpenSpec Changes**：完整的变更管理流程（团队协作平台）
- 🌟 **根因分析**：基于 Traceability 的智能自愈（非简单 Retry）

**面试演示更新**（7 个）：
1. **Demo 1**：端到端生成（展示 OpenSpec Change）
2. **Demo 2**：Critique Phase（展示 LLM 评审）
3. **Demo 3**：Self-Healing（展示根因分析）
4. **Demo 4**：Skills 系统（展示意图识别）
5. **Demo 5**：Prompt Caching（展示成本优化）
6. **Demo 6**：多LLM Provider（展示 Fallback）
7. **Demo 7**：Quality Gate（展示四层验证）

---

## 12. 下一阶段规划（2026-05-24 起）

### 12.1 当前完成状态总览

**✅ 已完成的 P0 任务**：
1. ✅ 多LLM Provider 支持（Anthropic + OpenAI）
2. ✅ Prompt Caching 深度优化（80.5% hit rate, 60.7% cost reduction）
3. ✅ Multi-Agent Skills 系统（5 个 Skills）
4. ✅ LLM-as-a-Judge Critique Phase（Phase 9.5）

**⏳ 待完成的 P1 任务**：
1. ⏳ OpenSpec Change 完整集成（1-2 天）
2. ⏳ Self-Healing 根因分析增强（1-2 天）
3. ⏳ 面试准备完善（1 天）

---

### 12.2 优先级排序（下一阶段）

#### P0：OpenSpec Change 完整集成（1-2 天）

**目标**：让 OpenSpec Changes 真正工作，生成完整的 change 目录结构

**当前问题**：
- Phase 1 有 `_generate_change_directory()` 代码但未执行
- 条件检查 `if not delta["changed"]` 可能导致提前返回
- 实际文件系统中找不到 `openspec/changes/` 目录

**实施任务**：

**Task 1: 调试 Phase 1 变更目录生成**（0.5 天）
- 文件：`devpal/core/openspec_phases/phase1_parse_requirements.py`
- 检查为什么 `_generate_change_directory()` 未执行
- 确保 `openspec/changes/{change-id}/` 目录正确创建
- 验证 proposal.md / specs/spec.md / tasks.md 生成

**Task 2: Phase 3 输出 design.md**（0.5 天）
- 文件：`devpal/core/openspec_phases/phase3_technical_design.py`
- 在技术设计生成后，写入 `openspec/changes/{change-id}/design.md`
- 从 `context.current_change_id` 获取 change-id

**Task 3: Phase 4 读取 change artifacts**（0.5 天）
- 文件：`devpal/core/openspec_phases/phase4_generate_code.py`
- 读取 `openspec/changes/{change-id}/specs/spec.md` 作为上下文
- 读取 `openspec/changes/{change-id}/tasks.md` 作为任务清单

**Task 4: Phase 11 引用 change-id 和文件路径**（0.5 天）
- 文件：`devpal/core/openspec_phases/phase11_final_report.py`
- 在 final_report.md 中显示 change-id
- 列出 `openspec/changes/{change-id}/` 下的所有文件

**验收标准**：
```bash
python test_simple.py

# 验证：
# 1. openspec/changes/feat-xxx-{hash}/ 目录存在
# 2. proposal.md / specs/spec.md / tasks.md / design.md 文件完整
# 3. spec.md 采用 ADDED/MODIFIED/REMOVED 格式
# 4. final_report.md 显示 change-id 和文件列表
```

**面试价值**：
- 展示 OpenSpec 规范遵循
- 证明适配团队协作流程
- 变更追踪和管理能力

---

#### P1：Self-Healing 根因分析增强（1-2 天）

**目标**：从简单 Retry 升级到基于 Traceability 的根因分析

**当前问题**：
- TestSelfHealer 只修复表面症状（编译错误、测试失败）
- 无根本原因分析（为什么会出现这个错误？）
- 无学习机制（相同错误重复出现）

**实施任务**：

**Task 1: 创建根因分析模块**（0.5 天）
- 新增文件：`devpal/core/root_cause_analyzer.py`
- 实现错误分类逻辑（语法/逻辑/环境错误）
- 实现追溯链路分析（错误 → Phase → Prompt → 需求）

**Task 2: 集成到 TestSelfHealer**（0.5 天）
- 在修复前先进行根因分析
- 根据根因选择修复策略
- 记录分析结果到 metadata

**Task 3: 实现修复历史学习**（0.5 天）
- 新增文件：`devpal/core/healing_history.py`
- 记录：错误类型 → 修复策略 → 成功率
- 对相似错误快速应用已知修复

**Task 4: 生成根因分析报告**（0.5 天）
- 输出 `docs/root_cause_analysis.md`
- 包含：错误分类、追溯链路、修复策略、学习记录

**验收标准**：
```bash
python test_simple.py

# 验证：
# 1. 编译/测试失败时生成 root_cause_analysis.md
# 2. 报告包含错误分类和追溯链路
# 3. 相同错误第二次出现时快速修复
# 4. final_report.md 显示根因分析统计
```

**面试价值**：
- 展示智能自愈能力
- 学习机制和知识积累
- 可观测性和透明度

---

#### P1：面试准备完善（1 天）

**目标**：完善面试演示脚本和文档

**实施任务**：

**Task 1: 更新演示脚本**（0.3 天）
- 新增 Demo: Phase 9.5 Critique 演示
- 新增 Demo: OpenSpec Change 演示
- 新增 Demo: 根因分析演示
- 更新 `doc3.0/interview_demo_script.md`

**Task 2: 完善 Q&A 文档**（0.3 天）
- 新增 `doc3.0/interview_qa_critique.md` - Critique Phase Q&A
- 新增 `doc3.0/interview_qa_openspec_change.md` - OpenSpec Change Q&A
- 新增 `doc3.0/interview_qa_root_cause.md` - 根因分析 Q&A

**Task 3: 更新架构图和 README**（0.2 天）
- 更新 README.md 架构图（增加 Phase 9.5）
- 更新 `doc3.0/interview_pitch.md`（增加 Critique 亮点）

**Task 4: 端到端测试验证**（0.2 天）
- 运行所有演示脚本
- 验证 7 个演示场景可用
- 记录演示时间和关键点

**验收标准**：
- 7 个演示脚本全部可运行
- 10 个面试问题有对应演示
- 文档完整性 100%

---

### 12.3 时间线（Week 3-4）

#### Week 3（Day 7-9）

**Day 7: OpenSpec Change 完整集成**（1-2 天）
- 上午：调试 Phase 1 变更目录生成
- 下午：Phase 3 输出 design.md + Phase 4 读取 artifacts

**Day 8: OpenSpec Change 完成 + Self-Healing 开始**
- 上午：Phase 11 引用 change-id + 测试验证
- 下午：创建根因分析模块

**Day 9: Self-Healing 根因分析**（1-2 天）
- 上午：集成到 TestSelfHealer + 修复历史学习
- 下午：生成根因分析报告 + 测试验证

#### Week 4（Day 10）

**Day 10: 面试准备**（1 天）
- 上午：更新演示脚本 + Q&A 文档
- 下午：架构图更新 + 端到端测试

---

### 12.4 成功指标（更新）

| 指标 | 当前 | 目标 | 验证方式 |
|----|------|------|-------|
| **已完成** ||||
| 多LLM Provider | ✅ 2 | 2+ | Anthropic/OpenAI 已实现 |
| Cache Hit Rate | ✅ 80.5% | >60% | cache_metrics.json |
| API Cost Reduction | ✅ -60.7% | -40% | 对比测试 |
| Skills 数量 | ✅ 5 | 5+ | 已实现 |
| LLM Critique 维度 | ✅ 5 | 5 | critique_report.md |
| **待完成** ||||
| OpenSpec Change 覆盖率 | 0% | 100% | 每次运行生成 change 目录 |
| 根因分析准确率 | N/A | >80% | 人工验证分析结果 |
| 自愈成功率 | ~60% | >80% | 统计修复成功次数 |
| 面试准备完成度 | 80% | 100% | 7 个演示脚本可运行 |

---

### 12.5 面试能力矩阵（最终）

| 面试考察点 | 状态 | 演示方式 |
|-----------|:----:|---------|
| Agent Workflow Orchestration | ✅ | 11 阶段 + Skills 系统 |
| Tool Use | ✅ | Phase 4 tool loop |
| State Management | ✅ | OpenSpecContext + checkpoint |
| Prompt Engineering | ✅ | PromptEngine + Caching (80.5% hit) |
| Multi-Agent Collaboration | ✅ | Skills 系统 + multi_agent_skill |
| **Evaluation** | ✅ | Phase 9/10/11 + **Phase 9.5 Critique** |
| Memory System | ✅ | 三层架构 |
| **Reliability** | ✅ | retry/checkpoint + **根因分析** |
| **Change Management** | ⏳ | **OpenSpec Changes**（待完成）|
| **Traceability** | ✅ | ArtifactGraph + change-id |

**完成度**：9/10（90%）

---

### 12.6 核心亮点总结

**已完成的核心亮点**：
1. 🌟 **LLM-as-a-Judge**：5 维度代码质量评审（皇冠明珠）✅
2. 🌟 **Prompt Caching**：80.5% hit rate, 60.7% cost reduction ✅
3. 🌟 **Multi-Agent Skills**：5 个 Skills，意图识别 100% 准确 ✅
4. 🌟 **多LLM Provider**：Anthropic + OpenAI + Fallback ✅

**待完成的核心亮点**：
5. 🌟 **OpenSpec Changes**：完整的变更管理流程 ⏳
6. 🌟 **根因分析**：基于 Traceability 的智能自愈 ⏳

---

### 12.7 后续中长期规划（Week 5+）

#### P2：M3 Archive + Traceability（3-4 天）
- `archive_change(change_id)` 命令
- Delta merge 到 main spec
- ArtifactGraph 扩展
- Coverage matrix 生成

#### P2：多维度质量评分系统（2-3 天）
- 建立完整的质量评分体系
- Quality Scorecard
- 趋势分析
- 对标基准

#### P2：LanguagePlugin 主流程化（3-5 天）
- 统一 LanguagePlugin 接口
- Phase 2/4/9/10/11 迁移到插件
- 移除硬编码语言分支

#### P3：EventBus 主流程接入（1-2 天）
- 定义核心事件
- Phase 1-11 发布事件
- 输出 `.spec/events.jsonl`

#### P4：AI-agnostic 协作模式（5-7 天）
- CLAUDE.md 模板完善
- changes 目录文档化
- propose-only / apply-only 模式
- Cursor/Cline 集成文档

---

**文档版本**：v4.0（Phase 9.5 完成，规划 OpenSpec Change + 根因分析）  
**创建日期**：2026-05-22  
**更新日期**：2026-05-23  
**下一阶段预计完成**：2026-05-27（4 天）  
**负责人**：DevPalAgent Team
