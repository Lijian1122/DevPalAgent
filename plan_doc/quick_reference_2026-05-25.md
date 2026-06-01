# LanguagePlugin 重构快速参考

**日期**: 2026-05-25  
**状态**: Phase 4 已完成,Phase 9/10 待应用

---

## 重构文件清单

### ✅ Phase 4 (phase4_generate_code.py)
- **参考文件**: `phase4_refactor.txt`
- **位置**: 第 253-272 行
- **改动**: 使用 LanguagePlugin 获取基础设施文件列表
- **状态**: ✅ 已完成

### 🔄 Phase 10 (phase10_run_tests.py)
- **参考文件**: `phase10_refactor.txt`
- **位置**: 第 58-88 行
- **改动**: 使用 LanguagePlugin 获取测试文件模式
- **状态**: ⏸️ 待应用

### 🔄 Phase 9 (phase9_quality_gate.py)
- **参考文件**: `phase9_refactor.txt`
- **位置 1**: 第 459 行 (移除 is_cpp)
- **位置 2**: 第 466-471 行 (统一使用 language)
- **状态**: ⏸️ 待应用

---

## 下一步行动

1. **应用 Phase 10 重构** (参考 phase10_refactor.txt)
2. **应用 Phase 9 重构** (参考 phase9_refactor.txt)
3. **运行测试验证**
4. **开始 EventBus 集成**

---

## 测试命令

```bash
# 语法检查
python -m py_compile devpal/core/openspec_phases/phase4_generate_code.py
python -m py_compile devpal/core/openspec_phases/phase9_quality_gate.py
python -m py_compile devpal/core/openspec_phases/phase10_run_tests.py

# 运行测试
python -m pytest tests/e2e/test_installer_e2e.py -v
python -m pytest tests/openspec/ -v
```
