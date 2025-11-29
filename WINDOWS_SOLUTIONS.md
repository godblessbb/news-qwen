# Windows 系统运行 Qwen3 + vLLM 解决方案

## ⚠️ 问题说明

**vLLM 官方不支持 Windows 系统！**

您遇到的错误：
```
error: could not create 'build\bdist.win-amd64\wheel\...'
No such file or directory
```

这是因为：
1. ❌ vLLM 官方只支持 Linux
2. ❌ Windows 文件路径长度限制
3. ❌ 缺少 Linux 特定的编译工具

---

## ✅ 解决方案（3 种选择）

### 方案 1: 使用 WSL2（推荐，完整 vLLM 功能）⭐⭐⭐⭐⭐

**优点：**
- ✅ 完整的 vLLM 高性能推理
- ✅ 完全兼容 Linux 工具链
- ✅ 可以访问 Windows 文件系统
- ✅ GPU 直通支持（CUDA）

**缺点：**
- ⚠️ 需要 Windows 10/11 专业版
- ⚠️ 需要重启电脑
- ⚠️ 占用额外磁盘空间

#### 安装步骤

##### 1. 启用 WSL2

打开 **PowerShell**（管理员权限）：

```powershell
# 启用 WSL
wsl --install

# 重启电脑
Restart-Computer
```

##### 2. 安装 Ubuntu

重启后，再次打开 PowerShell：

```powershell
# 安装 Ubuntu（推荐）
wsl --install -d Ubuntu-22.04

# 设置用户名和密码（按提示操作）
```

##### 3. 在 WSL2 中安装 CUDA

在 WSL2 Ubuntu 终端中：

```bash
# 更新包管理器
sudo apt update && sudo apt upgrade -y

# 安装 CUDA Toolkit（WSL 版本）
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-1

# 配置环境变量
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

##### 4. 安装 Conda

```bash
# 下载 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 安装
bash Miniconda3-latest-Linux-x86_64.sh -b

# 初始化
~/miniconda3/bin/conda init bash
source ~/.bashrc
```

##### 5. 创建环境并安装依赖

```bash
# 克隆或访问 Windows 的项目目录
# WSL2 可以访问 Windows 文件：/mnt/c/Users/user/Documents/GitHub/news-qwen
cd /mnt/c/Users/user/Documents/GitHub/news-qwen

# 创建 conda 环境
conda create -n news-qwen python=3.10 -y
conda activate news-qwen

# 配置国内镜像（可选）
./setup_china_mirrors.sh

# 安装 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装 vLLM（在 WSL2 中可以成功安装！）
pip install vllm

# 安装其他依赖
pip install -r requirements.txt
```

##### 6. 下载模型并运行

```bash
# 下载模型（使用 ModelScope）
python download_qwen3_model.py --source modelscope

# 运行推理
python vllm_inference.py --batch-test
```

---

### 方案 2: 使用 transformers 库（简单，性能较低）⭐⭐⭐⭐

**优点：**
- ✅ 原生 Windows 支持
- ✅ 无需 WSL2
- ✅ 安装简单

**缺点：**
- ❌ 性能比 vLLM 低 5-10 倍
- ❌ 吞吐量较低
- ❌ 不支持高级优化

#### 安装步骤

##### 1. 修改 requirements.txt

编辑 `requirements.txt`，**注释掉 vLLM**：

```txt
# Qwen3 14B + vLLM 项目依赖

# vLLM - 高性能推理引擎（Windows 不支持）
# vllm>=0.6.0

# Hugging Face 库
transformers>=4.40.0
huggingface-hub>=0.23.0
tokenizers>=0.19.0

# ModelScope - 魔搭社区（国内下载推荐）
modelscope>=1.11.0

# 其他依赖
numpy>=1.24.0
accelerate>=0.30.0
sentencepiece>=0.2.0
bitsandbytes>=0.41.0  # 用于量化
```

##### 2. 安装依赖

```powershell
# 激活环境
conda activate news-qwen

# 安装 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装其他依赖
pip install transformers huggingface-hub tokenizers modelscope numpy accelerate sentencepiece
```

##### 3. 下载模型

```powershell
# 使用 ModelScope（国内快）
python download_qwen3_model.py --source modelscope
```

##### 4. 使用新的推理脚本

```powershell
# 单次测试
python transformers_inference.py

# 交互模式
python transformers_inference.py --interactive

# 批量测试
python transformers_inference.py --batch-test

# 使用量化（节省显存）
python transformers_inference.py --load-in-8bit --interactive
```

---

### 方案 3: 使用远程 Linux 服务器（最佳性能）⭐⭐⭐⭐⭐

**优点：**
- ✅ 完整 vLLM 性能
- ✅ 可以使用更强大的 GPU
- ✅ 不占用本地资源

**缺点：**
- ⚠️ 需要云服务器（有费用）
- ⚠️ 需要网络连接

#### 推荐的云服务商

| 服务商 | GPU 选项 | 价格（参考） | 备注 |
|--------|----------|------------|------|
| AutoDL | A100/V100 | ¥2-8/小时 | 国内，速度快 |
| 矩池云 | A100/V100 | ¥2-6/小时 | 国内，按需付费 |
| 阿里云 | T4/V100 | ¥5-15/小时 | 稳定 |
| 腾讯云 | T4/V100 | ¥5-15/小时 | 稳定 |

#### 使用步骤

1. **租用 GPU 服务器**（推荐 AutoDL）
2. **选择镜像**: Ubuntu 22.04 + PyTorch + CUDA
3. **上传项目代码**
4. **安装依赖并运行**

```bash
# SSH 连接到服务器后
git clone https://github.com/your-repo/news-qwen.git
cd news-qwen

conda create -n news-qwen python=3.10 -y
conda activate news-qwen

# 配置镜像
./setup_china_mirrors.sh

# 安装依赖
pip install torch torchvision torchaudio
pip install vllm
pip install -r requirements.txt

# 下载模型
python download_qwen3_model.py --source modelscope

# 运行
python vllm_inference.py --batch-test
```

---

## 📊 方案对比

| 特性 | WSL2 | transformers | 远程服务器 |
|------|------|--------------|-----------|
| **性能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **安装难度** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **费用** | 免费 | 免费 | 付费 |
| **吞吐量** | 高 | 低 | 高 |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 推荐选择

### 如果您是开发者/研究者：
**→ 使用 WSL2**（方案 1）
- 完整功能
- 一次配置，长期使用
- 本地运行，无网络依赖

### 如果您只是测试/学习：
**→ 使用 transformers**（方案 2）
- 快速上手
- 无需复杂配置
- 性能够用

### 如果您需要生产环境/大规模推理：
**→ 使用远程服务器**（方案 3）
- 最佳性能
- 灵活的 GPU 选择
- 按需付费

---

## 💡 快速决策流程

```
开始
  |
是否有 WSL2?
  |
 是 → 使用 WSL2（方案 1）
  |
 否 → 能否安装 WSL2?
        |
       是 → 安装 WSL2（方案 1）
        |
       否 → 只是测试?
              |
             是 → transformers（方案 2）
              |
             否 → 使用云服务器（方案 3）
```

---

## 🔧 当前推荐（针对您的情况）

**推荐使用方案 2: transformers 库**

因为：
1. ✅ 您已经有 conda 环境
2. ✅ 您在 Windows 上
3. ✅ 快速开始，无需重启

### 立即执行的命令：

```powershell
# 1. 激活环境
conda activate news-qwen

# 2. 安装依赖（不包括 vLLM）
pip install transformers huggingface-hub tokenizers modelscope numpy accelerate sentencepiece bitsandbytes

# 3. 下载模型
python download_qwen3_model.py --source modelscope

# 4. 运行测试
python transformers_inference.py --batch-test
```

---

## 📞 需要帮助？

- 查看 `transformers_inference.py --help`
- 查看 README.md
- 检查 CHINA_MIRROR_GUIDE.md（镜像配置）

---

## 🔗 相关资源

- **vLLM 官方文档**: https://docs.vllm.ai
- **WSL2 安装指南**: https://learn.microsoft.com/zh-cn/windows/wsl/install
- **transformers 文档**: https://huggingface.co/docs/transformers
- **AutoDL**: https://www.autodl.com

---

选择适合您的方案开始吧！🚀
