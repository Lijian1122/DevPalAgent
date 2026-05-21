# 阶段跳过机制实现状态报告

**日期**: 2026-05-18  
**状态**: 部分完成，待测试

---

## 已完成的工作

### 1. 核心基础设施 ✅

**文件**: `devpal/core/openspec_phases/base.py`

- ✅ 在 `PhaseInterface` 基类中添加了 `should_skip()` 方法
- ✅ 在 `OpenSpecContext` 中添加了 `project_type` 和 `features` 字段
- ✅ 更新了 checkpoint 保存和恢复逻辑以包含新字段

```python
def should_skip(self) -> tuple:
    """判断是否应该跳过当前阶段
    
    Returns:
        (should_skip, reason): 是否跳过和跳过原因
    """
    return False, ""
```

### 2. 跳过规则定义 ✅

**文件**: `devpal/core/openspec_phases/phase_skip_rules.py`（新建）

定义了非 C++ 项目的跳过规则：

**安装脚本项目**（`'install' in features` 或 `project_type in ['installer', 'cli_tool', 'tooling']`）：
- ❌ Phase 3: 技术设计（不需要 AI 设计）
- ❌ Phase 5: 生成测试（不需要）
- ❌ Phase 6: CMake 配置（不是 C++ 项目）
- ❌ Phase 7: 测试文档（不需要）
- ❌ Phase 10: 编译运行测试（不是编译型项目）

**Python 项目**（`language == 'python'`）：
- ❌ Phase 6: CMake 配置（不是 C++ 项目）

### 3. Scheduler 集成 ✅

**文件**: `devpal/core/openspec_phases/enhanced_scheduler.py`

在阶段执行循环中添加了跳过检查：

```python
# 检查是否应该跳过此阶段（基于项目类型）
should_skip, skip_reason = phase.should_skip()
if should_skip:
    skip_msg = f"[SKIP] Phase {i} ({phase.phase_name}) - {skip_reason}"
    print(skip_msg)
    if context.logger:
        context.logger.info(skip_msg)
    # 记录跳过的阶段为成功（避免被视为失败）
    result = PhaseResult.ok(f"Skipped: {skip_reason}")
    context.set_phase_result(i, result)
    if self.checkpoint:
        self.checkpoint.save(i, True, context)
    continue
```

### 4. Phase 3 实现 ✅

**文件**: `devpal/core/openspec_phases/phase3_technical_design.py`

```python
def should_skip(self) -> tuple:
    """判断是否应该跳过当前阶段"""
    from .phase_skip_rules import should_skip_for_non_cpp_project
    return should_skip_for_non_cpp_project(self.phase_number, self.context)
```

---

## 待完成的工作

### 1. 其他阶段的 should_skip() 实现 ⏳

需要为以下阶段添加 `should_skip()` 方法：

- ⏳ **Phase 5**: `phase5_generate_tests.py`
- ⏳ **Phase 6**: `phase6_cmake_config.py`
- ⏳ **Phase 7**: `phase7_test_docs.py`
- ⏳ **Phase 10**: `phase10_run_tests.py`

每个阶段只需添加相同的方法：
```python
def should_skip(self) -> tuple:
    """判断是否应该跳过当前阶段"""
    from .phase_skip_rules import should_skip_for_non_cpp_project
    return should_skip_for_non_cpp_project(self.phase_number, self.context)
```

### 2. Phase 1 需求解析增强 ⏳

**文件**: `devpal/core/openspec_phases/phase1_parse_requirements.py`

需要在 Phase 1 中检测并设置 `context.features` 和 `context.project_type`：

```python
# 在 execute() 方法中添加
context.features = self._detect_features(requirements_content)
context.project_type = self._detect_project_type(requirements_content)

def _detect_features(self, content: str) -> List[str]:
    """检测项目特性"""
    features = []
    content_lower = content.lower()
    
    # 安装脚本特性
    install_keywords = ['install', 'installer', 'setup', 'deploy', 'script', '安装', '部署']
    if any(keyword in content_lower for keyword in install_keywords):
        features.append('install')
    
    # 其他特性...
    return features

def _detect_project_type(self, content: str) -> str:
    """检测项目类型"""
    content_lower = content.lower()
    
    if any(kw in content_lower for kw in ['installer', 'install script', '安装脚本']):
        return 'installer'
    
    return ''
```

---

## 测试计划

### 测试文件

已创建: `requirements/test_phase_skip.md`

### 测试步骤

1. **语法验证** ✅
   ```bash
   python -m py_compile devpal/core/openspec_phases/base.py
   python -m py_compile devpal/core/openspec_phases/phase_skip_rules.py
   python -m py_compile devpal/core/openspec_phases/enhanced_scheduler.py
   python -m py_compile devpal/core/openspec_phases/phase3_technical_design.py
   ```
   结果：✅ 所有文件语法正确

2. **完整流程测试** ⏳
   ```bash
   python run_ai_flow.py --requirements requirements/test_phase_skip.md --verbose
   ```
   
   预期结果：
   - Phase 1: 执行（解析需求）
   - Phase 2: 执行（创建结构）
   - Phase 3: **跳过** - "安装脚本项目不需要 AI 技术设计"
   - Phase 4: 执行（生成代码）
   - Phase 5: **跳过** - "安装脚本项目不需要生成测试代码"
   - Phase 6: **跳过** - "安装脚本项目不需要 CMake 配置"
   - Phase 7: **跳过** - "安装脚本项目不需要测试文档"
   - Phase 8: 执行（生成 README）
   - Phase 9: 执行（质量检查）
   - Phase 10: **跳过** - "安装脚本项目不需要编译和运行测试"
   - Phase 11: 执行（最终报告）

3. **日志验证** ⏳
   
   检查日志文件中是否包含跳过信息：
   ```bash
   grep "SKIP" <project_dir>/.logs/*.log
   ```

---

## 当前限制

1. **Phase 1 未完成**：目前 `context.features` 和 `context.project_type` 不会被自动设置
   - **影响**：跳过逻辑不会触发，因为这些字段为空
   - **解决方案**：需要完成 Phase 1 的增强

2. **部分阶段未实现**：Phase 5, 6, 7, 10 还没有 `should_skip()` 方法
   - **影响**：这些阶段会继续执行，即使应该跳过
   - **解决方案**：添加相同的 `should_skip()` 方法

---

## 下一步行动

### 优先级 P0（必须）

1. ✅ 完成 Phase 1 的特性检测和项目类型检测
2. ✅ 为 Phase 5, 6, 7, 10 添加 `should_skip()` 方法
3. ✅ 运行完整流程测试

### 优先级 P1（重要）

1. 验证日志输出正确
2. 验证 checkpoint 正确保存跳过的阶段
3. 测试 resume 功能是否正常工作

### 优先级 P2（可选）

1. 添加更多项目类型的跳过规则
2. 优化跳过原因的描述
3. 在最终报告中显示跳过的阶段统计

---

## 预期效果

完成后，用户运行安装脚本生成需求时：

```bash
python run_ai_flow.py --requirements requirements/claude_installer.md
```

输出示例：
```
==============================================
 OpenSpec - Requirements-Driven Development Workflow (Enhanced)
===================================
  Requirements: requirements/claude_installer.md
  Language: Python
  Timeout: Enabled
  Retry: Enabled
  Checkpoint: Enabled
===========================================

[Phase 1/11] Parse requirements
  [OK] 解析需求完成 (2 requirements)
  [INFO] 检测到特性: install
  [INFO] 项目类型: installer

[Phase 2/11] Create project structure
  [OK] 项目结构创建完成

[SKIP] Phase 3 (生成技术设计文档) - 安装脚本项目不需要 AI 技术设计

[Phase 4/11] Generate core code
  [OK] 应用模板: claude_cli_installer
  [OK] 生成文件: scripts/install_claude_cli.sh
  [OK] 生成文件: scripts/install_claude_cli.bat
  [OK] 生成文件: scripts/install_claude_cli.py

[SKIP] Phase 5 (生成测试) - 安装脚本项目不需要生成测试代码
[SKIP] Phase 6 (CMake 配置) - 安装脚本项目不需要 CMake 配置
[SKIP] Phase 7 (测试文档) - 安装脚本项目不需要测试文档

[Phase 8/11] README
  [OK] README 生成完成
[Phase 9/11] Quality gate
  [OK] 质量检查通过

[SKIP] Phase 10 (编译运行测试) - 安装脚本项目不需要编译和运行测试

[Phase 11/11] Final report
  [OK] 最终报告生成完成
  
总耗时: 45 秒（跳过了 5 个阶段，节省约 10 分钟）
```

---

## 总结

阶段跳过机制的核心框架已经实现完成，但还需要：
1. 完成 Phase 1 的特性检测
2. 为其余阶段添加 `should_skip()` 方法
3. 进行完整的集成测试

一旦完成这些步骤，系统将能够智能地跳过不必要的阶段，大幅提升非 C++ 项目（特别是安装脚本项目）的生成速度和用户体验。
