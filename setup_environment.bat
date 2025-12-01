@echo off
REM Setup script for news-qwen conda environment on Windows
echo ========================================
echo  Qwen3-14B Environment Setup (Windows)
echo ========================================
echo.

REM Check if conda is available
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: conda not found. Please install Miniconda or Anaconda first.
    echo Download from: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo Step 1: Creating conda environment...
echo.

REM Check if environment.yml exists
if exist environment.yml (
    echo Using environment.yml to create environment...
    conda env create -f environment.yml
) else (
    echo Creating environment manually...
    conda create -n news-qwen python=3.10 -y
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to create conda environment.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Close this window and open a new PowerShell/CMD window
echo 2. Activate the environment:
echo    conda activate news-qwen
echo.
echo 3. Install PyTorch (choose based on your CUDA version):
echo.
echo    For CUDA 12.1+:
echo    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
echo.
echo    For CUDA 11.8:
echo    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
echo.
echo 4. Install project dependencies:
echo    pip install -r requirements_windows.txt
echo.
echo 5. Run a test:
echo    python transformers_inference.py --model-path D:/models/qwen3-14b --batch-test
echo.
pause
