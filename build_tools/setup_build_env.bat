@echo off
REM ==========================================
REM Universal Build Environment Setup Script
REM Configures Visual Studio environment for any C++ project
REM ========================

setlocal enabledelayedexpansion

if "%~1"=="--quiet" (
    set "QUIET_MODE=1"
) else (
    set "QUIET_MODE=0"
    echo ============================
    echo  Build Environment Setup
    echo ============================================
    echo.
)

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "CACHE_FILE=%SCRIPT_DIR%.vs_cache.txt"

REM Check if we have a cached VS path
if exist "%CACHE_FILE%" (
    if "%QUIET_MODE%"=="0" echo [INFO] Using cached Visual Studio path...

    REM Read cached values
    set /p VCVARS=<"%CACHE_FILE%"

    if exist "!VCVARS!" (
        if "%QUIET_MODE%"=="0" (
         echo [INFO] Cached path: !VCVARS!
          echo [INFO] Setting up Visual Studio environment...
            echo.
        )
        goto :setup_env
    ) else (
        if "%QUIET_MODE%"=="0" echo [WARNING] Cached path is invalid, re-detecting...
        del "%CACHE_FILE%" 2>nul
    )
)

REM Find Visual Studio
if "%QUIET_MODE%"=="0" (
    call "%SCRIPT_DIR%find_vs.bat"
) else (
    call "%SCRIPT_DIR%find_vs.bat" --quiet
)

if %errorlevel% neq 0 (
    echo [ERROR] Failed to locate Visual Studio
    exit /b 1
)

REM find_vs.bat outputs: VCVARS_PATH, VS_YEAR, VS_VERSION (one per line)
REM We need to capture the first line (VCVARS path)
for /f "delims=" %%i in ('call "%SCRIPT_DIR%find_vs.bat" --quiet') do (
    if not defined VCVARS set "VCVARS=%%i"
)

REM Cache the path for next time
echo !VCVARS!>"%CACHE_FILE%"

:setup_env
if not exist "%VCVARS%" (
    echo [ERROR] vcvars path is invalid: %VCVARS%
    del "%CACHE_FILE%" 2>nul
    exit /b 1
)

REM Call vcvars to setup environment
call "%VCVARS%" >nul 2>&1

if %errorlevel% neq 0 (
    echo [ERROR] Failed to setup Visual Studio environment
    exit /b 1
)

if "%QUIET_MODE%"=="0" (
    echo.
    echo [SUCCESS] Build environment ready!
    echo =======================================
    echo.
)

REM Verify compiler is available
where cl.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Compiler (cl.exe) not found in PATH
    echo [ERROR] vcvars may have failed to setup environment
    exit /b 1
)

if "%QUIET_MODE%"=="0" (
    echo [INFO] Compiler:
    cl.exe 2>&1 | findstr /C:"Compiler Version"
    echo.

    REM Verify CMake is available
    where cmake.exe >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARNING] CMake not found in PATH
        echo [WARNING] Please install CMake or add it to PATH
    ) else (
        echo [INFO] CMake:
        cmake --version | findstr /C:"cmake version"
    )

  echo.
    echo ========================================
)

exit /b 0
