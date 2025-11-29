@echo off
chcp 65001 >nul
REM PyCharm 解释器问题诊断脚本 (Windows)

echo ==========================================
echo PyCharm 解释器诊断工具
echo ==========================================
echo.

echo [1/7] 检查 Python...
python --version
if errorlevel 1 (
    echo [错误] Python 未安装或不在 PATH 中
    echo.
    echo 请安装 Python: https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    echo [成功] Python 已安装
)

echo.
echo [2/7] 检查 Python 路径...
where python
echo.

echo [3/7] 检查 Conda...
conda --version 2>nul
if errorlevel 1 (
    echo [警告] Conda 未安装或不在 PATH 中
    echo.
    echo 如果您使用 Conda，请确保 Anaconda/Miniconda 已添加到 PATH
) else (
    echo [成功] Conda 已安装
    echo.
    echo [4/7] 列出 Conda 环境...
    conda env list
)

echo.
echo [5/7] 检查常见 Python 安装位置...
echo.

set "FOUND=0"

if exist "%USERPROFILE%\anaconda3\python.exe" (
    echo [找到] %USERPROFILE%\anaconda3\python.exe
    "%USERPROFILE%\anaconda3\python.exe" --version
    set "FOUND=1"
)

if exist "%USERPROFILE%\miniconda3\python.exe" (
    echo [找到] %USERPROFILE%\miniconda3\python.exe
    "%USERPROFILE%\miniconda3\python.exe" --version
    set "FOUND=1"
)

if exist "C:\ProgramData\Anaconda3\python.exe" (
    echo [找到] C:\ProgramData\Anaconda3\python.exe
    "C:\ProgramData\Anaconda3\python.exe" --version
    set "FOUND=1"
)

if exist "C:\Python39\python.exe" (
    echo [找到] C:\Python39\python.exe
    set "FOUND=1"
)

if exist "C:\Python310\python.exe" (
    echo [找到] C:\Python310\python.exe
    set "FOUND=1"
)

if exist "C:\Python311\python.exe" (
    echo [找到] C:\Python311\python.exe
    set "FOUND=1"
)

if %FOUND%==0 (
    echo [警告] 未在常见位置找到 Python
)

echo.
echo [6/7] 检查 PyCharm 配置目录...
if exist "%APPDATA%\JetBrains" (
    echo [找到] %APPDATA%\JetBrains
    dir /B "%APPDATA%\JetBrains\PyCharm*" 2>nul
    if errorlevel 1 (
        echo [提示] 未找到 PyCharm 配置
    )
) else (
    echo [提示] PyCharm 配置目录不存在
)

echo.
echo [7/7] 运行详细诊断...
echo.
python diagnose_python_env.py
if errorlevel 1 (
    echo.
    echo [提示] 如果诊断脚本运行失败，请手动运行:
    echo python diagnose_python_env.py
)

echo.
echo ==========================================
echo 诊断完成
echo ==========================================
echo.
echo 请根据以上信息进行修复，详细步骤请参考:
echo fix_pycharm_interpreter.md
echo.

pause
