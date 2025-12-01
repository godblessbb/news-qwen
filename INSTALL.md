# 安装指南

## 快速安装（3步走）

### 步骤 1：创建 Conda 环境

```bash
# 创建 Python 3.10 环境
conda create -n news-qwen python=3.10 -y

# 激活环境
conda activate news-qwen
```

### 步骤 2：安装 PyTorch（重要！必须先安装）

根据你的 CUDA 版本选择：

**CUDA 12.1+（推荐）：**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**CUDA 11.8：**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**不确定 CUDA 版本？** 运行 `nvidia-smi` 查看右上角的 CUDA Version。

### 步骤 3：安装项目依赖

```bash
pip install -r requirements.txt
```

---

## 验证安装

运行以下命令检查环境是否正确配置：

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}')"
```

**预期输出：**
```
PyTorch: 2.x.x+cu121
CUDA可用: True
```

如果显示 `CUDA可用: False`，说明安装了 CPU 版本的 PyTorch，需要重新安装 CUDA 版本。

---

## 国内用户加速（可选）

### 配置 Conda 镜像源

```bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
conda config --set show_channel_urls yes
```

### 配置 pip 镜像源

**清华源（推荐）：**
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

**阿里源：**
```bash
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
```

---

## 依赖说明

### 核心依赖
- `transformers` - Hugging Face 模型库
- `torch` - PyTorch 深度学习框架
- `pandas` - 数据处理
- `numpy` - 数值计算
- `pytz` - 时区处理

### 量化支持
- `bitsandbytes` - 4bit/8bit 模型量化

### 可选依赖
- `modelscope` - 魔搭社区模型下载（国内用户）
- `vllm` - 高性能推理（仅 Linux）

---

## 常见问题

### Q1: pip install 速度很慢？
使用国内镜像源（见上文）。

### Q2: bitsandbytes 安装失败？
Windows 用户可能遇到兼容性问题，可以尝试：
```bash
pip install bitsandbytes-windows
```
或者跳过量化，直接运行模型（需要更多显存）。

### Q3: 显存不足？
- 使用 4bit 量化：`--load-in-4bit`
- 关闭其他占用 GPU 的程序
- 使用较小的模型（如 Qwen2.5-7B）

### Q4: ImportError: No module named 'torch'？
请确保：
1. 已激活 `news-qwen` 环境：`conda activate news-qwen`
2. 已安装 PyTorch（步骤 2）

---

## 完整安装示例

### Windows PowerShell

```powershell
# 1. 创建环境
conda create -n news-qwen python=3.10 -y
conda activate news-qwen

# 2. 配置镜像（可选）
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 3. 安装 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. 安装依赖
pip install -r requirements.txt

# 5. 验证
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

### Linux/macOS

```bash
# 1. 创建环境
conda create -n news-qwen python=3.10 -y
conda activate news-qwen

# 2. 安装 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

---

## 下一步

安装完成后，查看：
- **快速测试**：`快速开始指南.md`
- **事件聚合脚本**：`Scripts/README.md`
- **完整文档**：`README.md`
