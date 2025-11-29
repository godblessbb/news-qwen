#!/bin/bash
# PyCharm 解释器问题诊断脚本 (Linux/Mac)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo " PyCharm 解释器诊断工具"
echo "=========================================="
echo

echo -e "${BLUE}[1/8] 检查 Python...${NC}"
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo -e "${GREEN}✓ Python 已安装: $python_version${NC}"
    python3_path=$(which python3)
    echo -e "   路径: $python3_path"
else
    echo -e "${RED}✗ Python3 未找到${NC}"
fi

if command -v python &> /dev/null; then
    python_version=$(python --version)
    echo -e "${GREEN}✓ Python 已安装: $python_version${NC}"
    python_path=$(which python)
    echo -e "   路径: $python_path"
else
    echo -e "${YELLOW}⚠ Python (python) 未找到${NC}"
fi

echo
echo -e "${BLUE}[2/8] 检查所有 Python 路径...${NC}"
which -a python python3 2>/dev/null || echo -e "${YELLOW}未找到${NC}"

echo
echo -e "${BLUE}[3/8] 检查 Conda...${NC}"
if command -v conda &> /dev/null; then
    conda_version=$(conda --version)
    echo -e "${GREEN}✓ Conda 已安装: $conda_version${NC}"
    conda_path=$(which conda)
    echo -e "   路径: $conda_path"

    echo
    echo -e "${BLUE}[4/8] 列出 Conda 环境...${NC}"
    conda env list
else
    echo -e "${YELLOW}⚠ Conda 未安装或不在 PATH 中${NC}"
    echo -e "   如果已安装，请运行: conda init bash"
fi

echo
echo -e "${BLUE}[5/8] 检查环境变量...${NC}"
echo "PATH:"
echo "$PATH" | tr ':' '\n' | head -10
echo "..."
echo
echo "CONDA_PREFIX: ${CONDA_PREFIX:-(未设置)}"
echo "VIRTUAL_ENV: ${VIRTUAL_ENV:-(未设置)}"

echo
echo -e "${BLUE}[6/8] 检查常见 Python 安装位置...${NC}"

check_python_at() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓ 找到: $1${NC}"
        version=$("$1" --version 2>&1)
        echo -e "   版本: $version"
        return 0
    fi
    return 1
}

found=0

# Anaconda/Miniconda
check_python_at "$HOME/anaconda3/bin/python" && found=1
check_python_at "$HOME/anaconda3/bin/python3" && found=1
check_python_at "$HOME/miniconda3/bin/python" && found=1
check_python_at "$HOME/miniconda3/bin/python3" && found=1
check_python_at "/opt/anaconda3/bin/python" && found=1
check_python_at "/opt/miniconda3/bin/python" && found=1

# 系统 Python
check_python_at "/usr/bin/python3" && found=1
check_python_at "/usr/local/bin/python3" && found=1
check_python_at "/usr/bin/python" && found=1

if [ $found -eq 0 ]; then
    echo -e "${YELLOW}⚠ 未在常见位置找到 Python${NC}"
fi

echo
echo -e "${BLUE}[7/8] 检查 Conda 环境目录...${NC}"
if [ -d "$HOME/anaconda3/envs" ]; then
    echo -e "${GREEN}✓ 找到 Anaconda 环境目录${NC}"
    ls -1 "$HOME/anaconda3/envs" | head -10
elif [ -d "$HOME/miniconda3/envs" ]; then
    echo -e "${GREEN}✓ 找到 Miniconda 环境目录${NC}"
    ls -1 "$HOME/miniconda3/envs" | head -10
else
    echo -e "${YELLOW}⚠ 未找到 Conda 环境目录${NC}"
fi

echo
echo -e "${BLUE}[8/8] 检查 PyCharm 配置...${NC}"

if [ "$(uname)" == "Darwin" ]; then
    # macOS
    config_dir="$HOME/Library/Application Support/JetBrains"
    cache_dir="$HOME/Library/Caches/JetBrains"
else
    # Linux
    config_dir="$HOME/.config/JetBrains"
    cache_dir="$HOME/.cache/JetBrains"
fi

echo "配置目录: $config_dir"
echo "缓存目录: $cache_dir"

if [ -d "$config_dir" ]; then
    echo -e "${GREEN}✓ 找到 PyCharm 配置目录${NC}"
    ls -1 "$config_dir" | grep PyCharm
else
    echo -e "${YELLOW}⚠ PyCharm 配置目录不存在${NC}"
fi

echo
echo "=========================================="
echo -e "${BLUE} 运行详细诊断脚本...${NC}"
echo "=========================================="
echo

if [ -f "diagnose_python_env.py" ]; then
    python3 diagnose_python_env.py
else
    echo -e "${RED}✗ 诊断脚本不存在: diagnose_python_env.py${NC}"
fi

echo
echo "=========================================="
echo -e "${GREEN} 诊断完成${NC}"
echo "=========================================="
echo
echo "常见解决方案:"
echo "1. 清除 PyCharm 缓存:"
echo "   File -> Invalidate Caches / Restart"
echo
echo "2. 手动添加 Conda 环境到 PyCharm:"
echo "   Settings -> Project -> Python Interpreter -> Add"
echo "   选择 Conda Environment -> Existing environment"
echo
echo "3. 如果 Conda 不在 PATH 中:"
echo "   conda init bash"
echo "   source ~/.bashrc"
echo
echo "详细修复指南: fix_pycharm_interpreter.md"
echo
