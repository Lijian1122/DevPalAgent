@echo off
REM ==============
REM Universal Visual Studio Detection Script
REM Automatically finds and configures Visual Studio environment
REM Can be used by any C++ project
REM ==================================

setlocal enabledelayedexpansion

if "%~1"=="--quiet" (
    set "QUIET_MODE=1"
) else (
    set "QUIET_MODE=0"
    echo [INFO] Searching for Visual Studio installations...
)

REM Check for vswhere.exe (official VS locator tool)
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"

if exist "%VSWHERE%" (
    if "%QUIET_MODE%"=="0" echo [INFO] Using vswhere.exe to locate Visual Studio...

    REM Find latest VS installation with C++ tools
  for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
        set "VS_PATH=%%i"
    )

    if defined VS_PATH (
        if "%QUIET_MODE%"=="0" echo [SUCCESS] Found Visual Studio at: !VS_PATH!

        REM Detect VS version
        for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -property catalog_productDisplayVersion`) do (
            set "VS_VERSION=%%i"
        )
        if "%QUIET_MODE%"=="0" echo [INFO] Version: !VS_VERSION!

        REM Detect VS major version for CMake generator
        for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -property catalog_productLineVersion`) do (
            set "VS_YEAR=%%i"
        )

     REM Set vcvars path
        set "VCVARS=!VS_PATH!\VC\Auxiliary\Build\vcvars64.bat"

        if exist "!VCVARS!" (
            if "%QUIET_MODE%"=="0" echo [SUCCESS] Found vcvars64.bat

        REM Output results
            echo !VCVARS!
            echo !VS_YEAR!
            echo !VS_VERSION!

            REM Cache to file if requested
            if "%~2" neq "" (
       echo !VCVARS!>"%~2"
                echo !VS_YEAR!>>"%~2"
              echo !VS_VERSION!>>"%~2"
        )

            exit /b 0
        ) else (
          if "%QUIET_MODE%"=="0" echo [ERROR] vcvars64.bat not found at expected location
        )
    )
)

REM Fallback: Manual search for common VS installations
if "%QUIET_MODE%"=="0" echo [INFO] Falling back to manual search...

set "VS_YEARS=2022 2019 2017"
set "VS_EDITIONS=Professional Community Enterprise BuildTools"

for %%Y in (%VS_YEARS%) do (
    for %%E in (%VS_EDITIONS%) do (
        set "TEST_PATH=%ProgramFiles(x86)%\Microsoft Visual Studio\%%Y\%%E"
        if exist "!TEST_PATH!\VC\Auxiliary\Build\vcvars64.bat" (
      if "%QUIET_MODE%"=="0" echo [SUCCESS] Found Visual Studio %%Y %%E
            set "VCVARS=!TEST_PATH!\VC\Auxiliary\Build\vcvars64.bat"
          set "VS_YEAR=%%Y"

            REM Output results
            echo !VCVARS!
            echo %%Y
          echo %%Y.0.0

            REM Cache to file if requested
            if "%~2" neq "" (
              echo !VCVARS!>"%~2"
                echo %%Y>>"%~2"
                echo %%Y.0.0>>"%~2"
            )

            exit /b 0
        )
    )
)

REM Check for VS 2015 and older
if exist "%VS140COMNTOOLS%..\..\VC\vcvarsall.bat" (
    if "%QUIET_MODE%"=="0" echo [SUCCESS] Found Visual Studio 2015
    set "VCVARS=%VS140COMNTOOLS%..\..\VC\vcvarsall.bat"

    echo !VCVARS! x64
    echo 2015
    echo 2015.0.0

    if "%~2" neq "" (
        echo !VCVARS! x64>"%~2"
        echo 2015>>"%~2"
        echo 2015.0.0>>"%~2"
    )
    exit /b 0
)

if "%QUIET_MODE%"=="0" (
    echo [ERROR] No Visual Studio installation found!
    echo [ERROR] Please install Visual Studio 2017 or later with C++ tools
    echo [ERROR] Download from: https://visualstudio.microsoft.com/downloads/
)
exit /b 1
