# DevPal Build Tools

通用的 C++ 项目构建工具集，自动检测 Visual Studio 并配置构建环境。

## 📦 工具列表

### 1. `find_vs.bat` - Visual Studio 自动检测

自动查找系统中安装的 Visual Studio，支持 VS 2015-2022。

**用法：**
```batch
# 标准模式（显示详细信息）
find_vs.bat

# 静默模式
find_vs.bat --quiet

# 保存结果到文件
find_vs.bat --quiet cache.txt
```

**输出格式：**
```
第1行: vcvars64.bat 的完整路径
第2行: VS 年份 (2019, 2022, etc.)
第3行: VS 版本号 (16.11.2, etc.)
```

**检测策略：**
1. 使用 `vswhere.exe`（官方工具，最可靠）
2. 手动搜索常见安装路径
3. 检查环境变量（兼容旧版本）

---

### 2. `setup_build_env.bat` - 构建环境配置

配置 Visual Studio 编译环境，设置必要的环境变量。

**用法：**
```batch
# 标准模式
setup_build_env.bat

# 静默模式
setup_build_env.bat --quiet
```

**功能：**
- ✅ 自动检测 Visual Studio
- ✅ 调用 vcvars64.bat 配置环境
- ✅ 验证编译器可用性
- ✅ 缓存 VS 路径加速后续调用
- ✅ 检查 CMake 是否可用

---

### 3. `cmake_build.bat` - CMake 构建助手

一键完成 CMake 项目的配置和构建。

**用法：**
```batch
# 使用默认参数（当前目录，build 文件夹，Release 配置）
cmake_build.bat

# 指定源目录和构建目录
cmake_build.bat . build

# 指定配置
cmake_build.bat . build Debug

# 完整参数
cmake_build.bat C:\MyProject C:\MyProject\build Release
```

**参数：**
- `[source_dir]` - CMake 源代码目录（默认：当前目录）
- `[build_dir]` - 构建输出目录（默认：build）
- `[config]` - 构建配置（默认：Release）

**自动功能：**
- ✅ 检测并配置 VS 环境
- ✅ 自动选择正确的 CMake Generator
  - VS 2022 → "Visual Studio 17 2022"
  - VS 2019 → "Visual Studio 16 2019"
  - VS 2017 → "Visual Studio 15 2017"
- ✅ 配置 x64 架构
- ✅ 执行完整构建流程

---

## 🚀 快速开始

### 在你的项目中使用

#### 方法 1：直接调用（推荐）

在你的项目根目录创建 `build.bat`：

```batch
@echo off
REM 调用 DevPal 构建工具
call C:\code\DevPalAgent\build_tools\cmake_build.bat . build Release

REM 运行测试（如果有）
if exist build\Release\test_*.exe (
    echo.
    echo Running tests...
    cd build
    ctest -C Release --output-on-failure
)

pause
```

#### 方法 2：添加到 PATH

将 `C:\code\DevPalAgent\build_tools` 添加到系统 PATH，然后在任何项目中：

```batch
# 直接使用
cmake_build.bat

# 或者只配置环境
setup_build_env.bat
cmake -G "Visual Studio 16 2019" -A x64 ..
cmake --build . --config Release
```

#### 方法 3：复制到项目

将需要的脚本复制到你的项目 `scripts/` 目录：

```batch
xcopy C:\code\DevPalAgent\build_tools\*.bat MyProject\scripts\
```

---

## 📋 系统要求

### 必需
- **Windows 10 或更高版本**
- **Visual Studio 2017 或更高版本**
  - 需要安装 "使用 C++ 的桌面开发" 工作负载
  - 包含 MSVC 编译器和 Windows SDK
- **CMake 3.14 或更高版本**（用于 cmake_build.bat）

### 推荐
- Visual Studio 2019 或 2022
- CMake 3.20+
- vswhere.exe（VS 2017+ 自带）

---

## 🔍 工作原理

### Visual Studio 检测流程

```
1. 检查 vswhere.exe
   ├─ 存在 → 查询最新的 VS 安装（带 C++ 工具）
   └─ 不存在 → 进入手动搜索

2. 手动搜索
   ├─ 搜索 VS 2022 (Professional/Community/Enterprise/BuildTools)
   ├─ 搜索 VS 2019 (同上)
   ├─ 搜索 VS 2017 (同上)
   └─ 检查 VS 2015 环境变量

3. 验证
   ├─ 检查 vcvars64.bat 是否存在
   ├─ 缓存路径到 .vs_cache.txt
   └─ 返回结果
```

### 环境配置流程

```
1. 读取缓存
   ├─ 存在且有效 → 使用缓存路径
   └─ 不存在/无效 → 重新检测

2. 调用 vcvars64.bat
   ├─ 设置编译器路径
   ├─ 设置 SDK 路径
   └─ 设置其他构建工具

3. 验证
   ├─ 检查 cl.exe 是否在 PATH
   ├─ 检查 CMake 是否可用
   └─ 返回状态
```

---

## 🎯 使用示例

### 示例 1：简单 CMake 项目

```batch
@echo off
REM MyProject\build.bat

echo Building MyProject...
call C:\code\DevPalAgent\build_tools\cmake_build.bat

echo.
echo Build complete! Executable: build\Release\MyApp.exe
pause
```

### 示例 2：带测试的项目

```batch
@echo off
REM MyProject\build.bat

REM 构建
call C:\code\DevPalAgent\build_tools\cmake_build.bat . build Release
if %errorlevel% neq 0 exit /b 1

REM 运行测试
echo.
echo Running tests...
cd build
ctest -C Release --output-on-failure
set TEST_RESULT=%errorlevel%

cd ..
if %TEST_RESULT% equ 0 (
    echo [SUCCESS] All tests passed!
) else (
    echo [FAILURE] Some tests failed!
)

pause
exit /b %TEST_RESULT%
```

### 示例 3：多配置构建

```batch
@echo off
REM build_all.bat - 构建 Debug 和 Release

echo Building Debug configuration...
call C:\code\DevPalAgent\build_tools\cmake_build.bat . build_debug Debug

echo.
echo Building Release configuration...
call C:\code\DevPalAgent\build_tools\cmake_build.bat . build_release Release

echo.
echo All builds complete!
pause
```

### 示例 4：手动控制

```batch
@echo off
REM 只配置环境，手动执行构建命令

call C:\code\DevPalAgent\build_tools\setup_build_env.bat --quiet

REM 现在可以使用 cl.exe, cmake 等工具
mkdir build
cd build
cmake -G "Visual Studio 16 2019" -A x64 ..
cmake --build . --config Release

REM 自定义后处理
copy Release\MyApp.exe ..\dist\
```

---

## 🛠️ 高级用法

### 在 CI/CD 中使用

```batch
@echo off
REM CI build script

REM 设置环境
call C:\code\DevPalAgent\build_tools\setup_build_env.bat --quiet || exit /b 1

REM 配置
cmake -G "Visual Studio 16 2019" -A x64 -S . -B build || exit /b 1

REM 构建
cmake --build build --config Release || exit /b 1

REM 测试
cd build
ctest -C Release --output-on-failure || exit /b 1

echo [CI] Build and test successful
exit /b 0
```

### 检测特定 VS 版本

```batch
@echo off
REM 检查是否有 VS 2019

call C:\code\DevPalAgent\build_tools\find_vs.bat --quiet > vs_info.txt
set /p VCVARS=<vs_info.txt

echo %VCVARS% | findstr "2019" >nul
if %errorlevel% equ 0 (
    echo Found VS 2019!
) else (
    echo VS 2019 not found, using: %VCVARS%
)

del vs_info.txt
```

### 清理缓存

```batch
@echo off
REM 清理 VS 检测缓存，强制重新检测

del C:\code\DevPalAgent\build_tools\.vs_cache.txt 2>nul
echo Cache cleared. Next build will re-detect Visual Studio.
```

---

## 🔧 故障排除

### 问题：找不到 Visual Studio

**症状：**
```
[ERROR] No Visual Studio installation found!
```

**解决方案：**
1. 确认已安装 Visual Studio 2017 或更高版本
2. 确认安装了 "使用 C++ 的桌面开发" 工作负载
3. 运行 Visual Studio Installer 验证安装
4. 手动运行 `find_vs.bat` 查看详细信息

### 问题：找到 VS 但编译器不可用

**症状：**
```
[ERROR] Compiler (cl.exe) not found in PATH
```

**解决方案：**
1. 删除缓存：`del build_tools\.vs_cache.txt`
2. 重新运行 `setup_build_env.bat`
3. 检查 vcvars64.bat 是否存在
4. 尝试手动运行 vcvars64.bat

### 问题：CMake 配置失败

**症状：**
```
[ERROR] CMake configuration failed
```

**解决方案：**
1. 确认 CMake 已安装并在 PATH 中
2. 检查 CMakeLists.txt 语法
3. 删除 build 目录重试
4. 查看详细错误信息

### 问题：缓存的 VS 路径无效

**症状：**
```
[WARNING] Cached path is invalid, re-detecting...
```

**原因：** VS 被卸载或移动

**解决方案：**
- 脚本会自动重新检测，无需手动操作
- 如果问题持续，手动删除 `.vs_cache.txt`

---

## 📊 支持的 Visual Studio 版本

| 版本 | 年份 | CMake Generator | 状态 |
|------|------|----------------|------|
| Visual Studio 2022 | 2022 | Visual Studio 17 2022 | ✅ 完全支持 |
| Visual Studio 2019 | 2019 | Visual Studio 16 2019 | ✅ 推荐使用 |
| Visual Studio 2017 | 2017 | Visual Studio 15 2017 | ✅ 最低要求 |
| Visual Studio 2015 | 2015 | Visual Studio 14 2015 | ⚠️ 有限支持 |

**注意：** VS 2015 及更早版本可能需要手动调整脚本。

---

## 🔄 更新和维护

### 添加新 VS 版本支持

编辑 `find_vs.bat`：

```batch
REM 在 VS_YEARS 中添加新年份
set "VS_YEARS=2024 2022 2019 2017"
```

编辑 `cmake_build.bat`：

```batch
REM 添加新的 generator 映射
if "%VS_YEAR%"=="2024" set "CMAKE_GENERATOR=Visual Studio 18 2024"
```

### 自定义检测逻辑

可以修改 `find_vs.bat` 中的搜索顺序或添加自定义路径：

```batch
REM 添加自定义搜索路径
if exist "D:\CustomVS\VC\Auxiliary\Build\vcvars64.bat" (
    set "VCVARS=D:\CustomVS\VC\Auxiliary\Build\vcvars64.bat"
    exit /b 0
)
```

---

## 📝 集成到其他项目

### 作为 Git Submodule

```bash
# 在你的项目中
git submodule add https://github.com/your-org/DevPalAgent.git external/DevPalAgent

# 使用
call external\DevPalAgent\build_tools\cmake_build.bat
```

### 作为独立工具包

```batch
REM 复制到项目
xcopy C:\code\DevPalAgent\build_tools MyProject\build_tools\ /E /I

REM 使用
call build_tools\cmake_build.bat
```

---

## ✅ 验证安装

运行测试脚本验证工具是否正常工作：

```batch
@echo off
echo Testing DevPal Build Tools...
echo.

echo [Test 1] Finding Visual Studio...
call C:\code\DevPalAgent\build_tools\find_vs.bat
if %errorlevel% neq 0 (
    echo [FAIL] VS detection failed
    exit /b 1
)
echo [PASS] VS detection successful
echo.

echo [Test 2] Setting up environment...
call C:\code\DevPalAgent\build_tools\setup_build_env.bat --quiet
if %errorlevel% neq 0 (
    echo [FAIL] Environment setup failed
  exit /b 1
)
echo [PASS] Environment setup successful
echo.

echo [Test 3] Checking compiler...
where cl.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Compiler not found
    exit /b 1
)
echo [PASS] Compiler available
echo.

echo ========================
echo All tests passed!
echo DevPal Build Tools are ready to use.
pause
```

---

## 📞 支持

如遇问题：

1. 查看本文档的故障排除部分
2. 运行 `find_vs.bat` 查看详细检测信息
3. 检查 Visual Studio 安装是否完整
4. 确认 CMake 版本符合要求

---

## 📄 许可证

这些工具是 DevPalAgent 项目的一部分，遵循项目许可证。

---

**版本：** 1.0  
**最后更新：** 2026-05-10  
**测试环境：** Windows 10/11, VS 2019/2022, CMake 3.23+
