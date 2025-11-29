#!/bin/bash
# 配置国内镜像源（加速下载）

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo " 配置国内镜像源（加速下载）"
echo "=========================================="
echo

echo -e "${BLUE}[1/4] 配置 pip 镜像源...${NC}"
echo

echo "选择 pip 镜像源:"
echo "1. 清华大学镜像（推荐）"
echo "2. 阿里云镜像"
echo "3. 中国科技大学镜像"
echo "4. 豆瓣镜像"
echo "5. 跳过 pip 配置"
echo
read -p "请选择 (1-5): " pip_choice

case $pip_choice in
    1)
        PIP_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
        PIP_NAME="清华大学"
        ;;
    2)
        PIP_URL="https://mirrors.aliyun.com/pypi/simple"
        PIP_NAME="阿里云"
        ;;
    3)
        PIP_URL="https://pypi.mirrors.ustc.edu.cn/simple"
        PIP_NAME="中国科技大学"
        ;;
    4)
        PIP_URL="https://pypi.douban.com/simple"
        PIP_NAME="豆瓣"
        ;;
    *)
        echo -e "${YELLOW}[跳过] pip 镜像配置${NC}"
        PIP_URL=""
        ;;
esac

if [ -n "$PIP_URL" ]; then
    echo
    echo -e "${GREEN}配置 pip 使用 $PIP_NAME 镜像...${NC}"
    pip config set global.index-url "$PIP_URL"
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn
    pip config set install.trusted-host mirrors.aliyun.com
    pip config set install.trusted-host pypi.mirrors.ustc.edu.cn
    pip config set install.trusted-host pypi.douban.com
    echo -e "${GREEN}[✓] pip 镜像源已设置为: $PIP_NAME${NC}"
fi

echo
echo -e "${BLUE}[2/4] 配置 conda 镜像源...${NC}"
echo

echo "选择 conda 镜像源:"
echo "1. 清华大学镜像（推荐）"
echo "2. 中国科技大学镜像"
echo "3. 跳过 conda 配置"
echo
read -p "请选择 (1-3): " conda_choice

case $conda_choice in
    1)
        echo
        echo -e "${GREEN}配置 conda 使用清华大学镜像...${NC}"
        conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
        conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
        conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
        conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/pro
        conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
        conda config --set show_channel_urls yes
        echo -e "${GREEN}[✓] conda 镜像源已设置为: 清华大学${NC}"
        ;;
    2)
        echo
        echo -e "${GREEN}配置 conda 使用中国科技大学镜像...${NC}"
        conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/main
        conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/free
        conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/r
        conda config --set show_channel_urls yes
        echo -e "${GREEN}[✓] conda 镜像源已设置为: 中国科技大学${NC}"
        ;;
    *)
        echo -e "${YELLOW}[跳过] conda 镜像配置${NC}"
        ;;
esac

echo
echo -e "${BLUE}[3/4] 配置 Hugging Face 镜像...${NC}"
echo

echo "选择 Hugging Face 镜像:"
echo "1. HF-Mirror（推荐）"
echo "2. ModelScope（阿里云，最快）"
echo "3. 不配置（使用官方源）"
echo
read -p "请选择 (1-3): " hf_choice

case $hf_choice in
    1)
        echo
        echo -e "${GREEN}配置环境变量使用 HF-Mirror...${NC}"

        # 检测 shell 类型
        if [ -n "$BASH_VERSION" ]; then
            SHELL_RC="$HOME/.bashrc"
        elif [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
        else
            SHELL_RC="$HOME/.bashrc"
        fi

        # 添加环境变量
        if ! grep -q "HF_ENDPOINT" "$SHELL_RC"; then
            echo 'export HF_ENDPOINT="https://hf-mirror.com"' >> "$SHELL_RC"
            echo -e "${GREEN}[✓] HF_ENDPOINT 已添加到 $SHELL_RC${NC}"
            echo -e "${YELLOW}[提示] 运行以下命令使其生效: source $SHELL_RC${NC}"
        else
            echo -e "${YELLOW}[提示] HF_ENDPOINT 已存在于 $SHELL_RC${NC}"
        fi

        # 当前会话设置
        export HF_ENDPOINT="https://hf-mirror.com"
        echo -e "${GREEN}[✓] 当前会话已设置 HF_ENDPOINT${NC}"
        ;;
    2)
        echo
        echo -e "${YELLOW}[提示] ModelScope 无需配置环境变量${NC}"
        echo -e "${YELLOW}[提示] 使用以下命令下载模型:${NC}"
        echo "python download_qwen3_model.py --source modelscope"
        ;;
    *)
        echo -e "${YELLOW}[跳过] Hugging Face 镜像配置${NC}"
        ;;
esac

echo
echo -e "${BLUE}[4/4] 安装必要的库...${NC}"
echo

read -p "是否安装 modelscope 和 huggingface-hub? (y/n): " install_libs
if [[ $install_libs =~ ^[Yy]$ ]]; then
    echo
    echo "安装 modelscope..."
    pip install modelscope
    echo
    echo "安装 huggingface-hub..."
    pip install huggingface-hub
    echo
    echo -e "${GREEN}[✓] 必要的库已安装${NC}"
fi

echo
echo "=========================================="
echo -e "${GREEN} 配置完成！${NC}"
echo "=========================================="
echo

echo "当前配置:"
echo

echo -e "${BLUE}[pip 配置]${NC}"
pip config list
echo

echo -e "${BLUE}[conda 配置]${NC}"
conda config --show channels 2>/dev/null || echo "conda 未配置或未安装"
echo

echo -e "${BLUE}[环境变量]${NC}"
echo "HF_ENDPOINT: ${HF_ENDPOINT:-(未设置)}"
echo

echo "=========================================="
echo -e "${BLUE} 使用说明${NC}"
echo "=========================================="
echo

echo "1. 下载模型（自动选择最快源）:"
echo "   python download_qwen3_model.py"
echo

echo "2. 使用 ModelScope（推荐国内用户）:"
echo "   python download_qwen3_model.py --source modelscope"
echo

echo "3. 使用 HF-Mirror:"
echo "   python download_qwen3_model.py --source hf-mirror"
echo

echo "4. 安装 Python 包:"
echo "   pip install -r requirements.txt"
echo

echo "5. 安装 PyTorch (CUDA 12.1):"
echo "   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
echo
