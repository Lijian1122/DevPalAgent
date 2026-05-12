@echo off
REM ==============================================
REM   DevPal - 通用 CMake Windows 编译脚本 v2.0
REM   支持 Visual Studio 2017/2019/2022
REM ==============================================
setlocal enabledelayedexpansion

echo.
echo ==================================================
echo   DevPal CMake 通用编译脚本 v2.0
echo ==================================================
echo.

REM ==============================================
REM 参数处理
REM ==============================================
set "SOURCE_DIR=%~1"
set "BUILD_TYPE=Release"
set "CLEAN_BUILD=0"
set "RUN_AFTER=0"

REM 显示帮助信息
if /i "%~1"=="/h" goto Help
if /i "%~1"=="-h" goto Help
if /i "%~1"=="--help" goto Help

REM 解析参数
:ParseArgs
if "%~1"=="" goto ArgsDone
if /i "%~1"=="--clean" set CLEAN_BUILD=1
if /i "%~1"=="--debug" set BUILD_TYPE=Debug
if /i "%~1"=="--release" set BUILD_TYPE=Release
if /i "%~1"=="--run" set RUN_AFTER=1
if /i "%~2"=="" goto ArgsDone
shift
goto ParseArgs
:ArgsDone

REM 如果没有指定源目录，使用当前目录
if "%SOURCE_DIR%"=="" set "SOURCE_DIR=%CD%"
if not exist "%SOURCE_DIR%\CMakeLists.txt" (
    if exist "%SOURCE_DIR%\..\CMakeLists.txt" (
        set "SOURCE_DIR=%SOURCE_DIR%\.."
    )
)

REM 转换成绝对路径
for %%i in ("%SOURCE_DIR%") do set "SOURCE_DIR=%%~fi"
echo [配置] 源码目录: %SOURCE_DIR%

REM 检查 CMakeLists.txt
if not exist "%SOURCE_DIR%\CMakeLists.txt" (
    echo [错误] 找不到 CMakeLists.txt 文件！
    echo        请在包含 CMakeLists.txt 的目录下运行此脚本
    pause
    exit /b 1
)
echo [成功] 找到 CMakeLists.txt
echo.

REM ==============================================
REM Step 1: 自动检测 Visual Studio 版本
REM ==============================================
echo [步骤 1/5] 检测 Visual Studio 版本...
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "VS_VERSION="
set "VS_GENERATOR="
set "VS_YEAR="
set "VCVARS_PATH="

if exist "%VSWHERE%" (
    REM 检测 VS 2022 (Version 17)
    for /f "usebackq delims=" %%i in (`"%VSWHERE%" -version 17 -property installationPath 2^>nul`) do (
        set "VS_VERSION=17"
        set "VS_YEAR=2022"
        set "VS_GENERATOR=Visual Studio 17 2022"
        set "VCVARS_PATH=%%i"
    )
    REM 检测 VS 2019 (Version 16)
    if "!VS_VERSION!"=="" (
        for /f "usebackq delims=" %%i in (`"%VSWHERE%" -version 16 -property installationPath 2^>nul`) do (
            set "VS_VERSION=16"
            set "VS_YEAR=2019"
            set "VS_GENERATOR=Visual Studio 16 2019"
            set "VCVARS_PATH=%%i"
        )
    )
    REM 检测 VS 2017 (Version 15)
    if "!VS_VERSION!"=="" (
        for /f "usebackq delims=" %%i in (`"%VSWHERE%" -version 15 -property installationPath 2^>nul`) do (
            set "VS_VERSION=15"
            set "VS_YEAR=2017"
            set "VS_GENERATOR=Visual Studio 15 2017"
            set "VCVARS_PATH=%%i"
        )
    )
)

if "!VS_VERSION!"=="" (
    echo [错误] 未找到 Visual Studio 2017/2019/2022！
    echo        请先安装 Visual Studio。
    pause
    exit /b 1
)

echo [成功] 检测到 Visual Studio !VS_YEAR! (!VS_GENERATOR!)
echo        安装路径: !VCVARS_PATH!
echo.

REM ==============================================
REM Step 2: 设置 MSVC 编译环境
REM ==============================================
echo [步骤 2/5] 设置 MSVC x64 编译环境...
if exist "!VCVARS_PATH!\VC\Auxiliary\Build\vcvars64.bat" (
    call "!VCVARS_PATH!\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    echo [成功] MSVC x64 编译环境已设置
) else (
    echo [警告] 未找到 vcvars64.bat，尝试继续...
)
echo.

REM ==============================================
REM Step 3: 准备构建目录
REM ==============================================
echo [步骤 3/5] 准备构建目录...
set "BUILD_DIR=%SOURCE_DIR%\build"

if %CLEAN_BUILD%==1 (
    if exist "%BUILD_DIR%" (
        echo [信息] 清理旧的构建目录...
        rmdir /s /q "%BUILD_DIR%" 2>nul
    )
)

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
cd /d "%BUILD_DIR%"
echo [成功] 构建目录: %BUILD_DIR%
echo.

REM ==============================================
REM Step 4: CMake 配置
REM ==============================================
echo [步骤 4/5] CMake 配置项目...
echo        生成器: !VS_GENERATOR!
echo        平台: x64
echo        配置: %BUILD_TYPE%
echo.

cmake "%SOURCE_DIR%" -G "!VS_GENERATOR!" -A x64 -DCMAKE_BUILD_TYPE=%BUILD_TYPE%

if errorlevel 1 (
    echo.
    echo ==================================================
    echo   [错误] CMake 配置失败！
    echo ==================================================
    cd /d "%SOURCE_DIR%"
    pause
    exit /b 1
)

echo.
echo [成功] CMake 配置完成
echo.

REM ==============================================
REM Step 5: 编译项目
REM ==============================================
echo [步骤 5/5] 开始编译项目...
echo.

cmake --build . --config %BUILD_TYPE% --parallel %NUMBER_OF_PROCESSORS%

if errorlevel 1 (
    echo.
    echo ==================================================
    echo   [错误] 编译失败！请检查上面的错误信息
    echo ==================================================
    cd /d "%SOURCE_DIR%"
    pause
    exit /b 1
)

echo.
echo ==================================================
echo   [成功] 编译完成！
echo ==================================================
echo.

REM ==============================================
REM 查找并显示可执行文件
REM ==============================================
echo 查找可执行文件...
set "EXE_PATH="

REM 在多个可能的位置查找 exe
if exist "bin\%BUILD_TYPE%\*.exe" (
    for %%f in (bin\%BUILD_TYPE%\*.exe) do set "EXE_PATH=%%f"
)
if exist "bin\*.exe" (
    for %%f in (bin\*.exe) do set "EXE_PATH=%%f"
)
if exist "%BUILD_TYPE%\*.exe" (
    for %%f in (%BUILD_TYPE%\*.exe) do set "EXE_PATH=%%f"
)

if defined EXE_PATH (
    echo        可执行文件: !EXE_PATH!
    echo.
) else (
    echo        [警告] 未找到可执行文件
    echo.
)

REM ==============================================
REM 运行程序（如果指定了 --run 参数）
REM ==============================================
if %RUN_AFTER%==1 (
    if defined EXE_PATH (
        echo ==================================================
        echo   运行程序: !EXE_PATH!
        echo ==================================================
        echo.
        "!EXE_PATH!"
        echo.
        echo ==================================================
        echo   程序已退出
        echo ==================================================
    ) else (
        echo [警告] 无法自动运行，未找到可执行文件
    )
) else (
    echo 使用方法:
    echo   运行程序: !EXE_PATH!
    echo   或者重新运行: %~nx0 --run
)

cd /d "%SOURCE_DIR%"
echo.
pause
exit /b 0

:Help
echo.
echo 使用方法:
echo   %~nx0 [源码目录] [选项]
echo.
echo 选项:
echo   --clean      清理旧构建后重新编译
echo   --debug      Debug 模式编译
echo   --release    Release 模式编译（默认）
echo   --run        编译完成后自动运行
echo   -h, --help   显示此帮助信息
echo.
echo 示例:
echo   %~nx0                  # 编译当前目录
echo   %~nx0 --clean          # 清理后编译
echo   %~nx0 --run            # 编译并运行
echo   %~nx0 C:\my_project   # 编译指定目录
echo.
pause
exit /b 0
