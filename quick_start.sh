#!/bin/bash
# Qwen3 14B + vLLM 快速启动脚本

set -e

echo "=========================================="
echo "Qwen3 14B + vLLM 快速启动"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo -e "\n${YELLOW}检查 Python 版本...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 检查 CUDA
echo -e "\n${YELLOW}检查 CUDA...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo -e "${GREEN}✓ CUDA 可用${NC}"
else
    echo -e "${RED}✗ 未检测到 CUDA${NC}"
    echo "警告：vLLM 需要 CUDA 支持"
fi

# 检查依赖
echo -e "\n${YELLOW}检查 Python 依赖...${NC}"
if python3 -c "import vllm" 2>/dev/null; then
    echo -e "${GREEN}✓ vLLM 已安装${NC}"
else
    echo -e "${RED}✗ vLLM 未安装${NC}"
    read -p "是否现在安装依赖？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "安装依赖..."
        pip install -r requirements.txt
    else
        echo "请先运行: pip install -r requirements.txt"
        exit 1
    fi
fi

# 检查模型
echo -e "\n${YELLOW}检查模型文件...${NC}"
if [ -d "$HOME/models/qwen3-14b" ] || [ -d "D:/models/qwen3-14b" ] 2>/dev/null; then
    echo -e "${GREEN}✓ 模型文件存在${NC}"
else
    echo -e "${RED}✗ 模型文件不存在${NC}"
    read -p "是否现在下载模型？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "下载模型..."
        python3 download_qwen3_model.py --mirror
    else
        echo "请先运行: python3 download_qwen3_model.py"
        exit 1
    fi
fi

# 选择运行模式
echo -e "\n${YELLOW}请选择运行模式：${NC}"
echo "1) 单次测试"
echo "2) 批量测试"
echo "3) 交互模式"
echo "4) 运行示例"
read -p "输入选项 (1-4): " choice

case $choice in
    1)
        echo -e "\n${GREEN}启动单次测试...${NC}"
        python3 vllm_inference.py
        ;;
    2)
        echo -e "\n${GREEN}启动批量测试...${NC}"
        python3 vllm_inference.py --batch-test
        ;;
    3)
        echo -e "\n${GREEN}启动交互模式...${NC}"
        python3 vllm_inference.py --interactive
        ;;
    4)
        echo -e "\n${GREEN}运行示例...${NC}"
        python3 batch_inference_example.py --examples
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}完成！${NC}"
