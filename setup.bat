@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo   logtrim - Setup
echo ========================================
echo.

REM Check if Python is available (try python, then python3)
where python >nul 2>&1 && set PYTHON_CMD=python || where python3 >nul 2>&1 && set PYTHON_CMD=python3 || goto :python_not_found

if not defined PYTHON_CMD (
    echo [ERROR] Python not found.
    echo         Please install Python 3.9+ from https://python.org
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

%PYTHON_CMD% --version
echo [OK] Found Python

REM Check if venv already exists
if exist ".venv\Scripts\python.exe" (
    echo [INFO] Virtual environment already exists at .venv/
) else (
    echo [INFO] Creating virtual environment (.venv/)...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :venv_failed
)

echo [INFO] Activating virtual environment...
call "%~dp0.venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install logtrim using offline-safe method (--no-build-isolation uses bundled Python tools)
echo [INFO] Installing logtrim...
pip install --upgrade pip --quiet 2>nul || true
pip install --no-build-isolation -e . >nul 2>&1
if errorlevel 1 (
    echo [INFO] Trying non-editable install instead...
    pip install --no-build-isolation . >nul 2>&1
    if errorlevel 1 (
        REM Last resort: try with regular pip install
        pip install -e . >nul 2>&1
        if errorlevel 1 (
            echo [ERROR] Installation failed.
            echo.
            echo Troubleshooting:
            echo   1) Make sure setuptools is installed: python -m ensurepip --upgrade
            echo   2) Try running manually: pip install .
            pause
            exit /b 1
        )
    )
)

REM Verify installation
echo.
%PYTHON_CMD% -m logtrim --help >nul 2>&1
if errorlevel 0 (
    REM Create a permanent launcher so logtrim works from any terminal
    echo [INFO] Creating logtrim command launcher...
    echo @echo off >> "%~dp0logtrim.bat"
    echo set SCRIPT_DIR=%%~dp0 >> "%~dp0logtrim.bat"
    echo %%SCRIPT_DIR%%.venv\Scripts\python.exe -m logtrim %%* >> "%~dp0logtrim.bat"

    echo ========================================
    echo   Setup complete!
    echo ========================================
    echo.
    echo Run: logtrim.bat --input ^<your-log.txt^>
    echo Or :  .venv\Scripts\python.exe -m logtrim --input ^<your-log.txt^>
    echo.
) else (
    REM Try installing without editable mode as final fallback
    echo [INFO] Trying alternate install method...
    pip install --no-build-isolation . >nul 2>&1
    if errorlevel 0 (
        %PYTHON_CMD% -m logtrim --help >nul 2>&1
        if errorlevel 0 (
            echo [INFO] Creating logtrim command launcher...
            echo @echo off >> "%~dp0logtrim.bat"
            echo set SCRIPT_DIR=%%~dp0 >> "%~dp0logtrim.bat"
            echo %%SCRIPT_DIR%%.venv\Scripts\python.exe -m logtrim %%* >> "%~dp0logtrim.bat"

            echo ========================================
            echo   Setup complete!
            echo ========================================
            echo.
            echo Run: logtrim.bat --input ^<your-log.txt^>
            echo.
        ) else (
            echo [ERROR] Installation verification failed.
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] All installation methods failed.
        echo.
        echo Troubleshooting:
        echo   1) Make sure setuptools is installed: python -m ensurepip --upgrade
        echo   2) Activate venv manually and install:
        echo      call .venv\Scripts\activate.bat
        echo      pip install .
        pause
        exit /b 1
    )
)

goto :end

:python_not_found
echo [ERROR] Python not found.
echo         Please install Python 3.9+ from https://python.org
echo         Make sure to check "Add Python to PATH" during installation.
pause
exit /b 1

:venv_failed
echo [ERROR] Failed to create virtual environment.
echo.
echo Make sure ensurepip is available:
echo   python -m ensurepip --upgrade
echo.
echo If that doesn't work, install the venv module or try a full Python installation from python.org.
pause
exit /b 1

:end
endlocal
