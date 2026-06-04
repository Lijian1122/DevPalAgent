# 如何使用优化后的架构图

## 🎯 快速开始

### 方式 1: 直接使用 PNG 文件

所有图表已生成高清 PNG，直接使用即可：

```
docs/interview_qa/diagrams/
├── 01_system_architecture_v11-diagram-1.png    # 系统架构
├── 02_openspec_pipeline-diagram-1.png        # OpenSpec 流程
├── 03_multi_agent-diagram-1.png                # 多智能体
├── 04_quality_gate_v11-diagram-1.png           # 质量门禁 ⭐
└── 05_eventbus-diagram-1.png                 # 事件总线
```

### 方式 2: 修改后重新生成

1. 编辑对应的 `.md` 文件
2. 运行生成命令：
```bash
# 单个图表
node ~/.claude/skills/mermaid-to-png/mermaid-to-png-v11.js <file>.md --style=v11

# 或批量重新生成所有
cd docs/interview_qa/diagrams
./regenerate_all_v11.sh
```

## 📊 各图表使用指南

### 01. System Architecture（系统架构）

**文件**: `01_system_architecture_v11-diagram-1.png` (1.2MB)  
**尺寸**: 3600x4800 @ 3x (纵向)

**适用场景**:
- ✅ 整体架构讲解（15 分钟面试）
- ✅ 系统设计面试
- ✅ 技术选型说明

**使用建议**:
- 从上往下讲解 8 层架构
- 重点：双链路（Agent + OpenSpec）
- 亮点：Multi-Agent 并行、EventBus

### 02. OpenSpec 11-Phase Pipeline（OpenSpec 流程）

**文件**: `02_openspec_pipeline-diagram-1.png` (723KB)  
**尺寸**: 3600x4800 @ 3x (纵向)

**适用场景**:
- ✅ 工作流设计讲解（30 分钟面试）
- ✅ 确定性流程说明
- ✅ Self-Healing 机制演示

**使用建议**:
- 强调 11 阶段完整性
- 重点：Phase 4/5 Multi-Agent 并行
- 亮点：Quality Gate + Self-Healing
### 03. Multi-Agent Architecture（多智能体）

**文件**: `03_multi_agent-diagram-1.png` (1.1MB)  
**尺寸**: 3600x4800 @ 3x (纵向)

**适用场景**:
- ✅ 并行计算讲解
- ✅ 性能优化说明
- ✅ 分布式协调演示

**使用建议**:
- 强调 3.3x 加速比
- 重点：依赖分析 + 拓扑排序
- 亮点：动态 Agent Pool (4-16)

### 04. Quality Gate（质量门禁）⭐

**文件**: `04_quality_gate_v11-diagram-1.png` (830KB)  
**尺寸**: 4800x2400 @ 3x (横向) ⭐

**适用场景**:
- ✅ 质量保障体系讲解
- ✅ 静态分析说明
- ✅ 验证流程演示

**使用建议**:
- 从左往右讲解 4 层验证
- 重点：早失败机制（L1→L2→L3→L4）
- 亮点：Self-Healing + Critique Phase

**特别说明**:
- ⭐ 使用横向布局，完美适配 16:9 投影
- ⭐ 文件最小（830KB），加载快
- ⭐ 推荐优先使用此版本

### 05. EventBus（事件总线）

**文件**: `05_eventbus-diagram-1.png` (726KB)  
**尺寸**: 3600x4800 @ 3x (纵向)

**适用场景**:
- ✅ 事件驱动架构讲解
- ✅ 可观测性设计说明
- ✅ 监控告警演示

**使用建议**:
- 强调 Pub-Sub 解耦
- 重点：4 类事件（Workflow/Phase/Agent/Tool）
- 亮点：外部集成（Datadog/Slack/Prometheus）

## 💼 面试场景使用

### 15 分钟面试

**推荐组合**: 01 + 04

```
1. 系统架构（01）: 5 分钟
   - 8 层架构概览
   - 双链路设计
   
2. Quality Gate（04）: 7 分钟 ⭐
   - 4 层验证流程
   - Self-Healing 机制
   
3. Q&A: 3 分钟
```

**投影设置**: 16:9 模式，图 04 横向显示效果最佳

### 30 分钟面试

**推荐组合**: 01 + 02 + 04

```
1. 系统架构（01）: 8 分钟
2. OpenSpec 流程（02）: 12 分钟
3. Quality Gate（04）: 7 分钟 ⭐
4. Q&A: 3 分钟
```

### 45 分钟+ 深度面试

**推荐组合**: 全部 5 张

```
1. 系统架构（01）: 10 分钟
2. OpenSpec 流程（02）: 12 分钟
3. Multi-Agent（03）: 10 分钟
4. Quality Gate（04）: 8 分钟 ⭐
5. EventBus（05）: 5 分钟
6. Q&A: 自由
```

## 🖥️ 投影使用技巧

### 投影仪设置

1. **分辨率**: 设置为 1920x1080 或更高
2. **模式**: 演示模式 / Presentation Mode
3. **亮度**: 调整到最佳可见度

### 展示顺序

**推荐流程**:
```
整体架构（01）→ 核心流程（02）→ 并行优化（03）→ 质量保障（04）→ 可观测性（05）
```

**故事线**:
> DevPalAgent 采用 8 层双链路架构（01），核心是 OpenSpec 11-Phase 确定性流程（02），其中 Phase 4/5 支持 Multi-Agent 并行执行（03），生成的代码通过 Quality Gate 四层验证（04），整个过程通过 EventBus 实现完整可观测（05）。

### 互动技巧

**图 01 (系统架构)**:
- 问："你们看到这个架构有什么特点？"
- 引导：双链路设计

**图 04 (Quality Gate)** ⭐:
- 问："如果 L2 验证失败会怎样？"
- 答：早失败机制，立即终止

## 📄 文档集成

### Markdown 文档

```markdown
# DevPalAgent 架构

## 系统整体架构

![System Architecture](./docs/interview_qa/diagrams/01_system_architecture_v11-diagram-1.png)

## Quality Gate 验证流程

![Quality Gate](./docs/interview_qa/diagrams/04_quality_gate_v11-diagram-1.png)
```

### PPT/Keynote

1. 插入 → 图片
2. 选择对应的 PNG 文件
3. 调整大小到全屏
4. （可选）添加动画效果

### PDF 简历/作品集

1. Word/Pages 中插入图片
2. 调整到页面宽度
3. 导出为 PDF
4. 完成

## 🔄 更新维护

### 修改图表内容

1. 编辑对应的 `.md` 文件（如 `04_quality_gate_v11.md`）
2. 修改 Mermaid 代码
3. 重新生成：

```bash
# Quality Gate (横向)
node ~/.claude/skills/mermaid-to-png/mermaid-to-png-v11.js \
    04_quality_gate_v11.md \
    . \
    --width=4800 \
    --height=2400 \
    --scale=3 \
    --background=white

# 其他图表 (纵向)
node ~/.claude/skills/mermaid-to-png/mermaid-to-png-v11.js \
    <file>.md \
    . \
    --style=v11
```

### 批量更新

修改多个文件后，一键重新生成所有：

```bash
cd docs/interview_qa/diagrams
./regenerate_all_v11.sh
```

## 📚 参考文档

### 样式指南

- [STYLE_GUIDE_V11.md](~/.claude/skills/mermaid-to-png/STYLE_GUIDE_V11.md) - 完整样式指南
- [TEMPLATE_V11.md](~/.claude/skills/mermaid-to-png/TEMPLATE_V11.md) - 可复用模板
- [QUICK_REFERENCE.md](~/.claude/skills/mermaid-to-png/QUICK_REFERENCE.md) - 快速参考

### 优化文档

- [OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md) - 优化总结
- [04_QUALITY_GATE_OPTIMIZATION.md](./04_QUALITY_GATE_OPTIMIZATION.md) - Quality Gate 优化说明
- [V11_GENERATION_REPORT.md](./V11_GENERATION_REPORT.md) - 生成报告

## ❓ 常见问题

### Q: 哪个版本适合面试？
**A**: 全部 v11 版本都适合。特别推荐 **04 Quality Gate v11** 横向版本，16:9 投影效果最佳。

### Q: 文件太大怎么办？
**A**: v11 版本都是高清图（3x scale），文件较大是正常的。如需压缩：
```bash
pngquant <file>.png --quality=80-95 --output compressed.png
```

### Q: 如何在暗色主题中使用？
**A**: v11 使用纯白背景 + 深色节点，在暗色主题中对比度很高，效果很好。

### Q: 可以导出 SVG 吗？
**A**: 可以，使用 mmdc 直接导出 SVG：
```bash
mmdc -i <file>.md -o output.svg
```

## ✅ 检查清单

使用前检查：

- [ ] 图表版本是否为 v11
- [ ] 文件大小是否合理（< 2MB）
- [ ] 分辨率是否足够（3x scale）
- [ ] 背景是否纯白
- [ ] 投影仪设置是否正确（16:9）

---

**最后更新**: 2026-06-04  
**推荐版本**: 全部 v11 优化版  
**特别推荐**: 04 Quality Gate v11 (横向布局) ⭐
