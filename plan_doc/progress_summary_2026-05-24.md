# LanguagePlugin 和 EventBus 集成进度总结

**日期**: 2026-05-24  
**任务**: 完成 LanguagePlugin 主流程化 + EventBus 接入  
**当前状态**: Phase 4/9/10 重构进行中,遇到技术困难

---

## 执行摘要

**进度**: 约 40% 完成  
**状态**: 🔄 进行中  
**预计剩余时间**: 1-2 天

**关键成果**:
- ✅ LanguagePlugin 接口扩展完成(5 个新方法)
- ✅ Phase 2 重构完成
- 🔄 Phase 4/9/10 重构进行中
- ⏸️ EventBus 集成待开始

**当前挑战**:
- Edit 工具字符串匹配问题
- Python 缩进错误
- Phase 4 重构复杂度较高

---

## 详细进度

### ✅ 已完成任务

#### 1. 统一语言表示
- 移除 `is_cpp` 冗余字段
- 添加向后兼容的 `@property`
- 所有 Phase 统一使用 `context.language`

#### 2. 扩展 LanguagePlugin 接口
在 `devpal/core/schema/languages/base.py` 中添加了 5 个新方法:
- `get_required_files_template()` - Phase 4 使用
- `get_test_command()` - Phase 10 使用
- `get_build_command()` - Phase 10 使用
- `get_quality_checks()` - Phase 9 使用
- `get_project_structure()` - Phase 2 使用

#### 3. Phase 2 重构
- ✅ 使用 LanguagePlugin 获取项目结构
- ✅ 代码位置: `phase2_create_structure.py:72-85`
- ✅ 测试通过

### 🔄 进行中任务

#### Phase 4 重构 (phase4_generate_code.py)

**目标**: 使用 LanguagePlugin 替换硬编码的语言分支

**需要重构的位置**:
```python
# 第 253-272 行
language = self.context.language
if language == "cpp":
    file_instruction = "Use write_file for each .h/.cpp."
  infra_files_list = "CMakeLists.txt, README.md, ..."
elif language == "python":
    ...
```

**重构方案**:
```python
# 使用 LanguagePlugin
plugin = self._get_language_plugin()
required_files = plugin.get_required_files_template()
infra_files_list = ", ".join(required_files.keys())
```

**当前状态**: 
- ❌ 多次尝试使用 Edit 工具失败
- ❌ 字符串匹配问题
- ❌ 缩进错误

**下一步**:
- 方案 A: 使用 Python 脚本进行重构
- 方案 B: 采用更小粒度的修改
- 方案 C: 先完成 Phase 9/10,积累经验后再处理

#### Phase 9 重构 (phase9_quality_gate.py)

**目标**: 使用 LanguagePlugin 替换硬编码的质量检查逻辑

**需要重构的位置**:
1. 第 142-210 行: 语言特定的质量检查
2. 第 459 行: `is_cpp` 使用
3. 第 466-471 行: 硬编码的语言分支

**重构方案**:
```python
# 移除 is_cpp
language = self.context.language

# 使用 LanguagePlugin
plugin = self._get_language_plugin()
if plugin:
    # 使用插件的质量检查
    quality_checks = plugin.get_quality_checks()
```

**当前状态**: 待开始

#### Phase 10 重构 (phase10_run_tests.py)

**目标**: 使用 LanguagePlugin 获取测试命令和构建命令

**需要重构的位置**:
1. 第 59-88 行: 硬编码的测试文件模式
2. 第 90-152 行: `_run_python_tests()` 方法
3. 第 154-411 行: `_run_cpp_tests()` 方法

**重构方案**:
```python
# 使用 LanguagePlugin
plugin = self._get_language_plugin()
test_command = plugin.get_test_command(project_dir)
build_command = plugin.get_build_command(project_dir)
```

**当前状态**: 待开始

### ⏸️ 待开始任务

#### EventBus 集成

**Phase 1**: 发布 RequirementChangedEvent
**Phase 4**: 发布 FileChangedEvent, ArtifactDiscoveredEvent
**Phase 9**: 发布 ValidationCompletedEvent
**Phase 10**: 发布 StepExecutedEvent, ValidationCompletedEvent
**Phase 11**: 发布 WorkflowCompletedEvent

---

## 技术难点分析

### 1. Edit 工具字符串匹配失败

**问题描述**:
- 多次尝试使用 Edit 工具,即使复制了准确的文本,仍然出现"String to replace not found"错误
- 尝试次数: 10+ 次
- 失败率: 100%

**可能原因**:
1. 不可见字符(空格/制表符混用)
2. 文件编码问题
3. 文件被 linter 自动修改
4. 复制粘贴时引入了额外字符

**已尝试的解决方案**:
- ✅ 使用 `cat -A` 查看准确内容
- ✅ 使用 `sed` 提取准确文本
- ❌ 仍然无法匹配

**下一步解决方案**:
1. **使用 Python 脚本**: 直接读取文件,修改后写回
2. **使用 sed/awk**: 基于行号进行替换
3. **手动编辑**: 在 IDE 中手动修改(最后手段)

### 2. Python 缩进错误

**问题描述**:
- 手动编写的代码经常出现缩进错误
- Python 对缩进非常敏感
- IDE 诊断显示大量缩进相关错误

**解决方案**:
1. 从现有代码中复制粘贴
2. 使用 Python 脚本生成代码
3. 减少新增代码量

### 3. Phase 4 重构复杂度

**问题描述**:
- Phase 4 的代码生成逻辑较复杂
- 涉及多个语言分支
- 需要保持向后兼容

**解决方案**:
1. 先完成简单的 Phase 9/10
2. 积累经验后再处理 Phase 4
3. 采用渐进式重构策略

---

## 调整后的执行计划

### 阶段 1: 完成 Phase 10 重构 (优先级最高)

**原因**: 
- Phase 10 的重构相对简单
- 主要是替换测试命令和构建命令
- 可以快速验证 LanguagePlugin 的可行性

**步骤**:
1. 添加 `_get_language_plugin()` 辅助方法
2. 在 `execute()` 中使用 plugin 获取测试命令
3. 简化 `_run_python_tests()` 和 `_run_cpp_tests()`
4. 运行测试验证

**预计时间**: 2-3 小时

### 阶段 2: 完成 Phase 9 重构

**步骤**:
1. 移除 `is_cpp` 使用
2. 使用 LanguagePlugin 替换硬编码分支
3. 保持现有的质量检查逻辑(暂不使用 `get_quality_checks()`)
4. 运行测试验证

**预计时间**: 2-3 小时

### 阶段 3: 完成 Phase 4 重构

**步骤**:
1. 使用 Python 脚本进行重构
2. 或者采用更简单的内联方式
3. 充分测试

**预计时间**: 3-4 小时

### 阶段 4: EventBus 集成

**步骤**:
1. Phase 1: RequirementChangedEvent
2. Phase 4: FileChangedEvent, ArtifactDiscoveredEvent
3. Phase 9: ValidationCompletedEvent
4. Phase 10: StepExecutedEvent
5. Phase 11: WorkflowCompletedEvent

**预计时间**: 4-5 小时

---

## 测试策略

### 单元测试
- [ ] 测试 LanguagePlugin 的各个方法
- [ ] 测试 Phase 的语言切换逻辑

### 集成测试
- [ ] 运行现有的 e2e 测试
- [ ] 确保 installer 项目测试通过
- [ ] 测试 Python 项目
- [ ] 测试 Shell 项目

### 回归测试
- [ ] 确保 C++ 项目功能正常
- [ ] 验证代码生成质量
- [ ] 验证测试执行

---

## 风险评估

### 高风险 🔴
- **Phase 4 重构**: 可能影响代码生成逻辑
- **缓解措施**: 充分测试,保持向后兼容

### 中风险 🟡
- **Phase 9/10 重构**: 有现有测试覆盖
- **缓解措施**: 渐进式重构,每步验证

### 低风险 🟢
- **EventBus 集成**: 主要是添加事件发布
- **缓解措施**: 不影响核心逻辑

---

## 经验教训

### 1. Edit 工具的局限性
- Edit 工具对字符串匹配非常严格
- 不适合大段代码的替换
- 建议使用 Python 脚本或 sed/awk

### 2. 渐进式重构的重要性
- 不要一次性修改太多代码
- 每次修改后立即验证
- 保持小步快跑

### 3. 测试驱动开发
- 先写测试,再重构
- 确保每次修改都有测试覆盖
- 避免引入回归问题

---

## 下一步行动

### 立即行动 (今天)
1. ✅ 完成进度总结文档
2. 🔄 开始 Phase 10 重构
   - 使用 Python 脚本或更简单的方法
   - 避免使用 Edit 工具进行大段替换

### 短期目标 (本周)
1. 完成 Phase 9/10 重构
2. 开始 Phase 4 重构
3. 运行集成测试

### 中期目标 (下周)
1. 完成 Phase 4 重构
2. 完成 EventBus 集成
3. 完成所有测试

---

## 总结

**当前进度**: 40% 完成

**关键里程碑**:
- ✅ LanguagePlugin 接口设计完成
- ✅ Phase 2 重构完成
- 🔄 Phase 4/9/10 重构进行中
- ⏸️ EventBus 集成待开始

**主要挑战**:
- Edit 工具使用困难
- Phase 4 重构复杂度高

**调整策略**:
- 优先完成简单的 Phase 10
- 使用 Python 脚本替代 Edit 工具
- 采用渐进式重构策略

**预计完成时间**: 1-2 天
