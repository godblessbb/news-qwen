@echo off
chcp 65001 >nul
echo ==========================================
echo 配置国内镜像源（加速下载）
echo ==========================================
echo.

echo [1/4] 配置 pip 镜像源...
echo.

echo 选择 pip 镜像源:
echo 1. 清华大学镜像（推荐）
echo 2. 阿里云镜像
echo 3. 中国科技大学镜像
echo 4. 豆瓣镜像
echo 5. 跳过 pip 配置
echo.
set /p pip_choice="请选择 (1-5): "

if "%pip_choice%"=="1" (
    set PIP_URL=https://pypi.tuna.tsinghua.edu.cn/simple
    set PIP_NAME=清华大学
) else if "%pip_choice%"=="2" (
    set PIP_URL=https://mirrors.aliyun.com/pypi/simple
    set PIP_NAME=阿里云
) else if "%pip_choice%"=="3" (
    set PIP_URL=https://pypi.mirrors.ustc.edu.cn/simple
    set PIP_NAME=中国科技大学
) else if "%pip_choice%"=="4" (
    set PIP_URL=https://pypi.douban.com/simple
    set PIP_NAME=豆瓣
) else (
    echo [跳过] pip 镜像配置
    goto conda_config
)

echo.
echo 配置 pip 使用 %PIP_NAME% 镜像...
pip config set global.index-url %PIP_URL%
pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn
pip config set install.trusted-host mirrors.aliyun.com
pip config set install.trusted-host pypi.mirrors.ustc.edu.cn
pip config set install.trusted-host pypi.douban.com

echo [✓] pip 镜像源已设置为: %PIP_NAME%
echo.

:conda_config
echo.
echo [2/4] 配置 conda 镜像源...
echo.

echo 选择 conda 镜像源:
echo 1. 清华大学镜像（推荐）
echo 2. 中国科技大学镜像
echo 3. 跳过 conda 配置
echo.
set /p conda_choice="请选择 (1-3): "

if "%conda_choice%"=="1" (
    echo.
    echo 配置 conda 使用清华大学镜像...
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/pro
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
    conda config --set show_channel_urls yes
    echo [✓] conda 镜像源已设置为: 清华大学
) else if "%conda_choice%"=="2" (
    echo.
    echo 配置 conda 使用中国科技大学镜像...
    conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/main
    conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/free
    conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/r
    conda config --set show_channel_urls yes
    echo [✓] conda 镜像源已设置为: 中国科技大学
) else (
    echo [跳过] conda 镜像配置
)

echo.
echo [3/4] 配置 Hugging Face 镜像...
echo.

echo 选择 Hugging Face 镜像:
echo 1. HF-Mirror（推荐）
echo 2. ModelScope（阿里云，最快）
echo 3. 不配置（使用官方源）
echo.
set /p hf_choice="请选择 (1-3): "

if "%hf_choice%"=="1" (
    echo.
    echo 配置环境变量使用 HF-Mirror...
    setx HF_ENDPOINT "https://hf-mirror.com"
    echo [✓] HF_ENDPOINT 已设置为: https://hf-mirror.com
    echo [提示] 重启终端后生效，或在当前会话中运行:
    echo set HF_ENDPOINT=https://hf-mirror.com
) else if "%hf_choice%"=="2" (
    echo.
    echo [提示] ModelScope 无需配置环境变量
    echo [提示] 使用以下命令下载模型:
    echo python download_qwen3_model.py --source modelscope
) else (
    echo [跳过] Hugging Face 镜像配置
)

echo.
echo [4/4] 安装必要的库...
echo.

set /p install_libs="是否安装 modelscope 和 huggingface-hub? (y/n): "
if /i "%install_libs%"=="y" (
    echo.
    echo 安装 modelscope...
    pip install modelscope
    echo.
    echo 安装 huggingface-hub...
    pip install huggingface-hub
    echo.
    echo [✓] 必要的库已安装
)

echo.
echo ==========================================
echo 配置完成！
echo ==========================================
echo.
echo 当前配置:
echo.

echo [pip 配置]
pip config list
echo.

echo [conda 配置]
conda config --show channels
echo.

echo [环境变量]
echo HF_ENDPOINT: %HF_ENDPOINT%
echo.

echo ==========================================
echo 使用说明
echo ==========================================
echo.
echo 1. 下载模型（自动选择最快源）:
echo    python download_qwen3_model.py
echo.
echo 2. 使用 ModelScope（推荐国内用户）:
echo    python download_qwen3_model.py --source modelscope
echo.
echo 3. 使用 HF-Mirror:
echo    python download_qwen3_model.py --source hf-mirror
echo.
echo 4. 安装 Python 包:
echo    pip install -r requirements.txt
echo.
echo 5. 安装 PyTorch (CUDA 12.1):
echo    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
echo.

pause
