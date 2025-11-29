@echo off
REM Qwen3 14B + vLLM 快速启动脚本 (Windows)

echo ==========================================
echo Qwen3 14B + vLLM 快速启动
echo ==========================================

REM 检查 Python
echo.
echo 检查 Python 版本...
python --version
if errorlevel 1 (
    echo [错误] 未找到 Python
    echo 请安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

REM 检查 CUDA
echo.
echo 检查 CUDA...
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
if errorlevel 1 (
    echo [警告] 未检测到 CUDA
    echo vLLM 需要 CUDA 支持
)

REM 检查依赖
echo.
echo 检查 Python 依赖...
python -c "import vllm" 2>nul
if errorlevel 1 (
    echo [错误] vLLM 未安装
    set /p install="是否现在安装依赖？(y/n): "
    if /i "%install%"=="y" (
        echo 安装依赖...
        pip install -r requirements.txt
    ) else (
        echo 请先运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
) else (
    echo [成功] vLLM 已安装
)

REM 检查模型
echo.
echo 检查模型文件...
if exist "D:\models\qwen3-14b" (
    echo [成功] 模型文件存在
) else (
    echo [错误] 模型文件不存在
    set /p download="是否现在下载模型？(y/n): "
    if /i "%download%"=="y" (
        echo 下载模型...
        python download_qwen3_model.py --mirror
    ) else (
        echo 请先运行: python download_qwen3_model.py
        pause
        exit /b 1
    )
)

REM 选择运行模式
echo.
echo 请选择运行模式：
echo 1) 单次测试
echo 2) 批量测试
echo 3) 交互模式
echo 4) 运行示例
set /p choice="输入选项 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 启动单次测试...
    python vllm_inference.py
) else if "%choice%"=="2" (
    echo.
    echo 启动批量测试...
    python vllm_inference.py --batch-test
) else if "%choice%"=="3" (
    echo.
    echo 启动交互模式...
    python vllm_inference.py --interactive
) else if "%choice%"=="4" (
    echo.
    echo 运行示例...
    python batch_inference_example.py --examples
) else (
    echo [错误] 无效选项
    pause
    exit /b 1
)

echo.
echo 完成！
pause
