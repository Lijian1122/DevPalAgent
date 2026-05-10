@echo off
REM ==================
REM Universal CMake Build Helper
REM Automatically detects VS and builds CMake projects
REM Usage: cmake_build.bat [source_dir] [build_dir] [config]
REM ===============================

setlocal enabledelayedexpansion

REM Parse arguments
set "SOURCE_DIR=%~1"
set "BUILD_DIR=%~2"
set "BUILD_CONFIG=%~3"

REM Set defaults
if "%SOURCE_DIR%"=="" set "SOURCE_DIR=."
if "%BUILD_DIR%"=="" set "BUILD_DIR=build"
if "%BUILD_CONFIG%"=="" set "BUILD_CONFIG=Release"

echo =========================
echo  Universal CMake Build Helper
echo ========================================
echo.
echo [INFO] Source directory: %SOURCE_DIR%
echo [INFO] Build directory:  %BUILD_DIR%
echo [INFO] Configuration:    %BUILD_CONFIG%
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Step 1: Setup build environment
echo [Step 1/4] Setting up build environment...
call "%SCRIPT_DIR%setup_build_env.bat" --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to setup build environment
    exit /b 1
)
echo [SUCCESS] Environment ready
echo.

REM Step 2: Detect CMake generator
echo [Step 2/4] Detecting CMake generator...

REM Get VS info from find_vs
for /f "tokens=1,2,3 delims= " %%a in ('call "%SCRIPT_DIR%find_vs.bat" --quiet') do (
    if not defined VCVARS_PATH set "VCVARS_PATH=%%a"
    if not defined VS_YEAR set "VS_YEAR=%%b"
    if not defined VS_VERSION set "VS_VERSION=%%c"
)

REM Map VS year to CMake generator
set "CMAKE_GENERATOR=Visual Studio 16 2019"

if "%VS_YEAR%"=="2022" set "CMAKE_GENERATOR=Visual Studio 17 2022"
if "%VS_YEAR%"=="2019" set "CMAKE_GENERATOR=Visual Studio 16 2019"
if "%VS_YEAR%"=="2017" set "CMAKE_GENERATOR=Visual Studio 15 2017"

echo [INFO] Detected Visual Studio %VS_YEAR%
echo [INFO] Using CMake generator: %CMAKE_GENERATOR%
echo.

REM Step 3: Configure with CMake
echo [Step 3/4] Configuring project with CMake...
echo ================================================

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

cmake -G "%CMAKE_GENERATOR%" -A x64 -S "%SOURCE_DIR%" -B "%BUILD_DIR%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] CMake configuration failed
    exit /b 1
)

echo [SUCCESS] Configuration complete
echo.

REM Step 4: Build the project
echo [Step 4/4] Building project...
echo ===============================

cmake --build "%BUILD_DIR%" --config %BUILD_CONFIG%
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed
    exit /b 1
)

echo.
echo [SUCCESS] Build complete!
echo.

REM Check for test executable
if exist "%BUILD_DIR%\%BUILD_CONFIG%\test_*.exe" (
    echo [INFO] Test executable found. Run tests with:
    echo        ctest -C %BUILD_CONFIG% --test-dir "%BUILD_DIR%"
    echo.
)

echo ==========================
exit /b 0
