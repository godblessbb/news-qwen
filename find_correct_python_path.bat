@echo off
chcp 65001 >nul
echo ==========================================
echo 查找正确的 Python 解释器路径
echo ==========================================
echo.

echo [检查 1] 检查 Miniconda3 (大写) 目录...
if exist "C:\Users\user\Miniconda3" (
    echo [找到] C:\Users\user\Miniconda3

    if exist "C:\Users\user\Miniconda3\python.exe" (
        echo [✓] 基础解释器: C:\Users\user\Miniconda3\python.exe
        "C:\Users\user\Miniconda3\python.exe" --version
    )

    if exist "C:\Users\user\Miniconda3\envs" (
        echo.
        echo [✓] 找到 envs 目录，列出所有环境:
        dir /B "C:\Users\user\Miniconda3\envs"

        if exist "C:\Users\user\Miniconda3\envs\news-qwen\python.exe" (
            echo.
            echo [✓✓✓ 找到目标解释器!]
            echo 路径: C:\Users\user\Miniconda3\envs\news-qwen\python.exe
            echo.
            "C:\Users\user\Miniconda3\envs\news-qwen\python.exe" --version
            echo.
            echo ==========================================
            echo 请在 PyCharm 中使用这个路径:
            echo C:\Users\user\Miniconda3\envs\news-qwen\python.exe
            echo ==========================================
        )
    )
) else (
    echo [未找到] C:\Users\user\Miniconda3
)

echo.
echo.
echo [检查 2] 检查 miniconda3 (小写) 目录...
if exist "C:\Users\user\miniconda3" (
    echo [找到] C:\Users\user\miniconda3

    if exist "C:\Users\user\miniconda3\python.exe" (
        echo [✓] 基础解释器: C:\Users\user\miniconda3\python.exe
        "C:\Users\user\miniconda3\python.exe" --version
    )

    if exist "C:\Users\user\miniconda3\envs" (
        echo.
        echo [✓] 找到 envs 目录，列出所有环境:
        dir /B "C:\Users\user\miniconda3\envs"

        if exist "C:\Users\user\miniconda3\envs\news-qwen\python.exe" (
            echo.
            echo [✓✓✓ 找到目标解释器!]
            echo 路径: C:\Users\user\miniconda3\envs\news-qwen\python.exe
            echo.
            "C:\Users\user\miniconda3\envs\news-qwen\python.exe" --version
            echo.
            echo ==========================================
            echo 请在 PyCharm 中使用这个路径:
            echo C:\Users\user\miniconda3\envs\news-qwen\python.exe
            echo ==========================================
        )
    )
) else (
    echo [未找到] C:\Users\user\miniconda3
)

echo.
echo.
echo [检查 3] 使用 conda 命令查找环境...
conda env list 2>nul
if errorlevel 1 (
    echo [提示] conda 命令不可用
) else (
    echo.
    echo [提示] 从上面的列表中找到 news-qwen 环境的完整路径
)

echo.
echo.
echo [检查 4] 验证 news-qwen 环境中的包...
if exist "C:\Users\user\Miniconda3\envs\news-qwen\python.exe" (
    echo 使用路径: C:\Users\user\Miniconda3\envs\news-qwen\python.exe
    "C:\Users\user\Miniconda3\envs\news-qwen\python.exe" -m pip list 2>nul | findstr /C:"torch" /C:"vllm" /C:"transformers"
)

if exist "C:\Users\user\miniconda3\envs\news-qwen\python.exe" (
    echo 使用路径: C:\Users\user\miniconda3\envs\news-qwen\python.exe
    "C:\Users\user\miniconda3\envs\news-qwen\python.exe" -m pip list 2>nul | findstr /C:"torch" /C:"vllm" /C:"transformers"
)

echo.
echo ==========================================
echo 完成!
echo ==========================================
pause
