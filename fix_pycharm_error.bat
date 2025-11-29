@echo off
chcp 65001 >nul
echo ==========================================
echo 修复 PyCharm 解释器配置问题
echo ==========================================
echo.

echo [步骤 1] 验证 Python 解释器可用性
echo.
set PYTHON_PATH=C:\Users\user\miniconda3\envs\news-qwen\python.exe

if exist "%PYTHON_PATH%" (
    echo [✓] Python 解释器存在
    echo 路径: %PYTHON_PATH%
    echo.
    echo 测试运行:
    "%PYTHON_PATH%" --version
    echo.
    "%PYTHON_PATH%" -c "import sys; print('Python 可执行:', sys.executable)"
    echo.
    echo [✓] Python 解释器工作正常
) else (
    echo [✗] Python 解释器不存在
    echo 请先创建 news-qwen 环境
    pause
    exit /b 1
)

echo.
echo ==========================================
echo [步骤 2] 清理方案
echo ==========================================
echo.
echo 请按照以下步骤操作:
echo.
echo 方案 1: 清除 PyCharm 缓存 (推荐首先尝试)
echo ------------------------------------------------
echo 1. 关闭 PyCharm (如果正在运行)
echo 2. 在 PyCharm 中: File -^> Invalidate Caches / Restart
echo 3. 选择 "Invalidate and Restart"
echo 4. 重启后重新添加解释器
echo.
echo.
echo 方案 2: 手动清理 PyCharm 缓存目录
echo ------------------------------------------------
echo.

set CACHE_DIR=%LOCALAPPDATA%\JetBrains\PyCharm2025.2
set CONFIG_DIR=%APPDATA%\JetBrains\PyCharm2025.2

echo PyCharm 缓存目录:
if exist "%CACHE_DIR%" (
    echo [找到] %CACHE_DIR%
    echo.
    set /p CLEAR_CACHE="是否删除缓存目录? (y/n): "
    if /i "%CLEAR_CACHE%"=="y" (
        echo 关闭 PyCharm...
        taskkill /F /IM pycharm64.exe 2>nul
        timeout /t 2 /nobreak >nul
        echo 删除缓存...
        rd /s /q "%CACHE_DIR%" 2>nul
        echo [✓] 缓存已清理
    )
) else (
    echo [未找到] %CACHE_DIR%
)

echo.
echo PyCharm 配置目录:
if exist "%CONFIG_DIR%" (
    echo [找到] %CONFIG_DIR%
) else (
    echo [未找到] %CONFIG_DIR%
)

echo.
echo.
echo 方案 3: 以管理员身份运行 PyCharm
echo ------------------------------------------------
echo 1. 关闭当前 PyCharm
echo 2. 右键 PyCharm 图标
echo 3. 选择 "以管理员身份运行"
echo 4. 重新配置解释器
echo.
echo.
echo 方案 4: 重新安装 PyCharm (最后手段)
echo ------------------------------------------------
echo 如果以上方法都不行，考虑重新安装 PyCharm
echo.
echo.
echo ==========================================
echo [步骤 3] 重新配置解释器的正确方法
echo ==========================================
echo.
echo 清理缓存后，按以下步骤配置:
echo.
echo 1. 打开 PyCharm
echo 2. File -^> Settings (Ctrl+Alt+S)
echo 3. Project: news-qwen -^> Python Interpreter
echo 4. 点击 ⚙️ -^> Add...
echo 5. 选择 "System Interpreter" (左侧)
echo 6. 点击 "..." 浏览按钮
echo 7. 粘贴路径: %PYTHON_PATH%
echo 8. 点击 OK
echo.
echo.
echo ==========================================
echo [步骤 4] 创建测试脚本验证
echo ==========================================
echo.

set TEST_FILE=%~dp0test_pycharm_python.py

echo 创建测试脚本: %TEST_FILE%
(
echo import sys
echo import os
echo.
echo print^("="*60^)
echo print^("Python 环境测试"^)
echo print^("="*60^)
echo print^(f"Python 版本: {sys.version}"^)
echo print^(f"Python 路径: {sys.executable}"^)
echo print^(f"当前工作目录: {os.getcwd^(^)}"^)
echo print^("="*60^)
echo.
echo # 测试导入
echo packages = ['torch', 'vllm', 'transformers', 'numpy']
echo for package in packages:
echo     try:
echo         module = __import__^(package^)
echo         version = getattr^(module, '__version__', 'unknown'^)
echo         print^(f"✓ {package}: {version}"^)
echo     except ImportError:
echo         print^(f"✗ {package}: 未安装"^)
) > "%TEST_FILE%"

echo [✓] 测试脚本已创建
echo.
echo 使用 Python 直接运行测试:
"%PYTHON_PATH%" "%TEST_FILE%"

echo.
echo.
echo ==========================================
echo 完成!
echo ==========================================
echo.
echo 下一步操作:
echo 1. 关闭此窗口
echo 2. 清除 PyCharm 缓存 (方案 1 或 2)
echo 3. 重启 PyCharm
echo 4. 重新添加解释器 (使用路径: %PYTHON_PATH%)
echo 5. 运行 test_pycharm_python.py 验证
echo.
pause
