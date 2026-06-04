# Quick Reference - Architecture Diagram Versions

## 📊 快速选择指南

### 🎯 推荐：v3 高清版（面试/演示专用）

**文件**: [01_system_architecture_v3.md](./01_system_architecture_v3.md)  
**PNG**: [01_system_architecture_v3-diagram-1.png](./01_system_architecture_v3-diagram-1.png)  
**大小**: 867KB  
**分辨率**: 2400x3200 @ 2x scale

#### ✨ 核心特性
- ✅ **超大字体**: 22px 基础字体，投影清晰可读
- ✅ **超粗边框**: 4px 边框，层次分明
- ✅ **双语标签**: 中英文对照（如：`任务规划 / Task Planning`）
- ✅ **高对比度**: 鲜艳 Material Design 色系
- ✅ **多行留白**: 节点内增加空白，视觉舒适
- ✅ **高分辨率**: 2x Retina 支持，打印/投影完美

#### 🎬 适用场景
- 🎤 **面试演示**: 投影仪/大屏幕展示（⭐⭐⭐⭐⭐）
- 📄 **简历/作品集**: PDF 嵌入（⭐⭐⭐⭐⭐）
- 📊 **PPT 演示**: PowerPoint/Keynote 插入（⭐⭐⭐⭐⭐）
- 🖨️ **打印文档**: A3/A4 纸张输出（⭐⭐⭐⭐⭐）
- 📱 **移动端**: 手机/平板查看（⭐⭐⭐⭐⭐）

#### 🔧 生成命令
```bash
cd docs/interview_qa/diagrams
mmdc -i 01_system_architecture_v3.md \
     -o 01_system_architecture_v3-diagram-1.png \
     -w 2400 -H 3200 -s 2 -b transparent
```

---

## 📦 备选：v2 优化版（GitHub 展示）

**文件**: [01_system_architecture_v2.md](./01_system_architecture_v2.md)  
**PNG**: [01_system_architecture_v2-diagram-1.png](./01_system_architecture_v2-diagram-1.png)  
**大小**: 57KB  
**分辨率**: 默认

#### 特性
- 18px 字体 + emoji 图标
- 3px 边框
- 中等亮度色系

#### 适用场景
- GitHub README（加载快）
- 快速预览
- 网页展示

---

## 📚 原始：v1 基础版（存档）

**文件**: [01_system_architecture.md](./01_system_architecture.md)  
**PNG**: [01_system_architecture-diagram-1.png](./01_system_architecture-diagram-1.png)  
**大小**: 52KB  
**分辨率**: 默认

#### 特性
- 默认字体（14px）
- 2px 边框
- 浅色系

#### 适用场景
- 存档参考
- 不推荐使用

---

## 📐 尺寸对比

| 版本 | 文件大小 | 字体 | 边框 | 投影清晰度 | 推荐度 |
|-----|---------|------|------|-----------|--------|
| v1  | 52KB    | 14px | 2px  | ⭐        | ⭐     |
| v2  | 57KB    | 18px | 3px  | ⭐⭐      | ⭐⭐⭐ |
| v3  | 867KB   | 22px | 4px  | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎨 颜色方案（v3）
```
UI Layer       : #F06292 (粉红) - 用户界面
Agent Layer    : #4FC3F7 (天蓝) - 智能体
OpenSpec       : #FFB74D (橙色) - 核心流程
Phase Execution: #BA68C8 (紫色) - 工作流
Multi-Agent    : #81C784 (绿色) - 并行执行
Core Services  : #FFF176 (黄色) - 核心服务
Memory         : #FF8A65 (橙红) - 记忆系统
Storage        : #4DB6AC (青色) - 存储层
```

---

## 🚀 快速使用

### 面试演示（3 步搞定）

```bash
# 1. 生成高清 PNG
cd docs/interview_qa/diagrams
mmdc -i 01_system_architecture_v3.md -o my_diagram.png -w 2400 -H 3200 -s 2

# 2. 插入 PPT/PDF
# 直接拖拽 my_diagram.png 到 PowerPoint/PDF

# 3. 开始演讲！
# 投影仪上字体清晰可读 ✨
```

### GitHub 展示

```markdown
# 在你的 README.md 中
![DevPalAgent Architecture](./docs/interview_qa/diagrams/01_system_architecture_v3-diagram-1.png)
```

### 手机查看

直接访问 GitHub 仓库，点击 PNG 文件即可查看高清图片。

---

## 📞 问题排查

### Q: 图片太大，加载慢？
**A**: 使用 v2 版本（57KB），或者压缩 v3（`pngquant 01_system_architecture_v3-diagram-1.png`）

### Q: 字体还是看不清？
**A**: 
1. 检查是否使用 v3 版本（867KB）
2. 尝试更大分辨率：`-w 3600 -H 4800 -s 3`
3. 确认投影仪分辨率设置（建议 1920x1080 以上）

### Q: 颜色打印效果不好？
**A**: 使用彩色打印机，选择"高质量"模式，推荐 A3 纸张

### Q: 需要修改内容？
**A**: 
1. 编辑 `01_system_architecture_v3.md` 文件
2. 重新运行 `mmdc` 命令生成 PNG
3. 保持字体大小（22px）和边框（4px）不变

---

## 🔗 相关文档

- [VERSION_COMPARISON.md](./VERSION_COMPARISON.md) - 详细版本对比
- [OPTIMIZATION_NOTES.md](./OPTIMIZATION_NOTES.md) - 优化记录
- [README.md](./README.md) - 完整架构图索引

---

## 📅 更新日志

### 2026-06-04
- ✅ 创建 v3 高清版本
- ✅ 字体增大到 22px
- ✅ 边框加粗到 4px
- ✅ 添加双语标签
- ✅ 输出高分辨率 PNG (867KB)
- ✅ 对标 doc2.0/01_OpenSpec_Architecture_Overview.png

---

**推荐版本**: v3 ⭐⭐⭐  
**文件**: `01_system_architecture_v3-diagram-1.png` (867KB)  
**用途**: 面试/演示/打印/PPT  
**清晰度**: ⭐⭐⭐
