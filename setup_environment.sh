#!/bin/bash
# Setup script for news-qwen conda environment on Linux/macOS

echo "========================================"
echo " Qwen3-14B Environment Setup (Linux)"
echo "========================================"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "ERROR: conda not found. Please install Miniconda or Anaconda first."
    echo "Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "Step 1: Creating conda environment..."
echo ""

# Check if environment.yml exists
if [ -f "environment.yml" ]; then
    echo "Using environment.yml to create environment..."
    conda env create -f environment.yml
else
    echo "Creating environment manually..."
    conda create -n news-qwen python=3.10 -y
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to create conda environment."
    exit 1
fi

echo ""
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the environment:"
echo "   conda activate news-qwen"
echo ""
echo "2. Install PyTorch (choose based on your CUDA version):"
echo ""
echo "   For CUDA 12.1+:"
echo "   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
echo ""
echo "   For CUDA 11.8:"
echo "   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
echo ""
echo "3. Install project dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "4. Run a test:"
echo "   python vllm_inference.py --model-path ~/models/qwen3-14b --batch-test"
echo ""
