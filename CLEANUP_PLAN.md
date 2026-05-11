# DevPalAgent 项目清理计划

## 🗑️ 建议删除的文件

### 临时测试脚本（可删除）
```
fix_agent_engine_msvc.py
fix_msvc.py
fix_msvc_compile.py
fix_msvc_final.py
insert_phase3.py
phase_6_11_implementation.py
test_cpp_compile.py
test_new_11_phase_workflow.py
test_openspec_11_phases.py
```

### 临时文档/报告（可删除）
```
CMAKE_OPTIMIZATION_PLAN.md
COMPILE_VERIFICATION_REPORT.md
MCP_MULTI_AGENT_ANALYSIS.md
MSVC_FIX_GUIDE.md
OPENSPEC_OPTIMIZATION_PLAN.md
P0_TASK_COMPLETION_REPORT.md
README_UPDATE_SUMMARY.md
```

### 备份文件（可删除）
```
README.md.backup
README_v1.0.md
```

### 临时目录（可删除）
```
.spec/
authentication_user_system/  (如果是测试项目)
spec_first_framework/  (如果未使用)
src/  (如果是临时测试代码)
```

---

## ✅ 应该保留的文件

### 核心文件
```
README.md  (主文档)
QUICKSTART.md  (快速开始指南)
BUILD_TOOLS_SUMMARY.md  (构建工具说明)
requirements.txt  (Python依赖)
.gitignore
```

### 核心目录
```
devpal/  (核心代码)
build_tools/  (通用构建工具)
cpp_authentication_system/  (示例项目)
docs/  (文档目录)
config/  (配置文件)
data/  (数据文件)
plugins/  (插件)
requirements/  (需求文档)
```

---

## 📋 清理命令

### 方案 A：安全删除（推荐）
逐个确认后删除：

```bash
# 1. 删除临时测试脚本
rm -i fix_*.py insert_phase3.py phase_6_11_implementation.py test_*.py

# 2. 删除临时文档
rm -i CMAKE_OPTIMIZATION_PLAN.md COMPILE_VERIFICATION_REPORT.md
rm -i MCP_MULTI_AGENT_ANALYSIS.md MSVC_FIX_GUIDE.md
rm -i OPENSPEC_OPTIMIZATION_PLAN.md P0_TASK_COMPLETION_REPORT.md
rm -i README_UPDATE_SUMMARY.md

# 3. 删除备份文件
rm -i README.md.backup README_v1.0.md

# 4. 删除临时目录
rm -rf .spec/
rm -rf authentication_user_system/  # 如果确认不需要
rm -rf spec_first_framework/  # 如果确认不需要
```

### 方案 B：批量删除
一次性删除所有临时文件：

```bash
# 创建备份（可选）
mkdir -p ../devpal_cleanup_backup
cp -r . ../devpal_cleanup_backup/

# 批量删除
rm -f fix_*.py insert_phase3.py phase_6_11_implementation.py test_*.py
rm -f CMAKE_OPTIMIZATION_PLAN.md COMPILE_VERIFICATION_REPORT.md
rm -f MCP_MULTI_AGENT_ANALYSIS.md MSVC_FIX_GUIDE.md
rm -f OPENSPEC_OPTIMIZATION_PLAN.md P0_TASK_COMPLETION_REPORT.md
rm -f README_UPDATE_SUMMARY.md README.md.backup README_v1.0.md
rm -rf .spec/ authentication_user_system/ spec_first_framework/
```

---

## 🔍 清理前检查

### 检查文件是否被使用
```bash
# 检查是否有代码引用这些文件
grep -r "fix_msvc" devpal/
grep -r "test_cpp_compile" devpal/
grep -r "authentication_user_system" devpal/
```

### 检查 Git 状态
```bash
git status
git diff
```

---

## 📊 预期效果

### 清理前
- 文件数：~30+ 个根目录文件
- 目录数：~18 个
- 混乱度：高

### 清理后
- 文件数：~10 个核心文件
- 目录数：~10 个核心目录
- 混乱度：低
- 项目结构清晰

---

## ⚠️ 注意事项

1. **备份重要数据**
   - 清理前先备份整个项目
   - 或使用 Git 提交当前状态

2. **确认文件用途**
   - 如果不确定某个文件是否需要，先保留
   - 可以移到 `archive/` 目录而不是直接删除

3. **检查依赖关系**
   - 确保删除的文件没有被其他代码引用
   - 运行测试确保功能正常

---

## 🎯 推荐的项目结构

清理后的理想结构：

```
DevPalAgent/
├── README.md
├── QUICKSTART.md
├── BUILD_TOOLS_SUMMARY.md
├── requirements.txt
├── .gitignore
│
├── devpal/            # 核心代码
│   ├── core/
│   ├── tools/
│   └── utils/
│
├── build_tools/         # 通用构建工具
│   ├── find_vs.bat
│   ├── setup_build_env.bat
│   ├── cmake_build.bat
│   └── README.md
│
├── cpp_authentication_system/  # 示例项目
│   ├── src/
│   ├── include/
│   ├── tests/
│   ├── docs/
│   ├── build.bat
│   ├── CMakeLists.txt
│   └── README.md
│
├── docs/                # 文档
│   ├── OPENSPEC_WORKFLOW_OPTIMIZATION.md
│   └── OPENSPEC_WORKFLOW_FIX_SUMMARY.md
│
├── config/        # 配置
├── data/          # 数据
├── plugins/        # 插件
└── requirements/        # 需求文档
```

---

**创建日期：** 2026-05-10  
**状态：** 待执行
