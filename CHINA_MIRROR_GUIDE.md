# 国内镜像源配置指南

## 🚀 快速开始

### 一键配置所有镜像源（推荐）

**Windows:**
```cmd
setup_china_mirrors.bat
```

**Linux/Mac:**
```bash
chmod +x setup_china_mirrors.sh
./setup_china_mirrors.sh
```

这将自动配置：
- ✅ pip 镜像源
- ✅ conda 镜像源
- ✅ Hugging Face 镜像源
- ✅ 安装必要的库

---

## 📥 下载模型（推荐方式）

### 方案 1: 使用 ModelScope（最快，推荐！）⭐

**ModelScope（魔搭社区）是阿里巴巴的模型平台，在中国大陆速度最快！**

```bash
# 自动安装 modelscope（如果未安装）
pip install modelscope

# 下载模型
python download_qwen3_model.py --source modelscope
```

**优点：**
- ✅ 国内服务器，速度最快
- ✅ 稳定可靠
- ✅ 无需配置代理

### 方案 2: 使用 HF-Mirror

```bash
python download_qwen3_model.py --source hf-mirror
```

### 方案 3: 自动选择（智能）

```bash
# 自动尝试 ModelScope -> HF-Mirror -> Hugging Face
python download_qwen3_model.py
```

---

## 🔧 手动配置镜像源

### 1. pip 镜像源

#### 清华大学镜像（推荐）

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 阿里云镜像

```bash
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple
```

#### 中国科技大学镜像

```bash
pip config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple
```

#### 临时使用（单次安装）

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### 2. conda 镜像源

#### 清华大学镜像（推荐）

```bash
# 添加镜像源
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r

# 显示频道 URL
conda config --set show_channel_urls yes
```

#### 中国科技大学镜像

```bash
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/free
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/r
conda config --set show_channel_urls yes
```

#### 查看当前配置

```bash
conda config --show channels
```

#### 恢复默认源

```bash
conda config --remove-key channels
```

---

### 3. Hugging Face 镜像

#### 方法 1: 设置环境变量（推荐）

**Windows (PowerShell):**
```powershell
# 临时设置（当前会话）
$env:HF_ENDPOINT = "https://hf-mirror.com"

# 永久设置
[System.Environment]::SetEnvironmentVariable('HF_ENDPOINT', 'https://hf-mirror.com', 'User')
```

**Windows (CMD):**
```cmd
# 临时设置
set HF_ENDPOINT=https://hf-mirror.com

# 永久设置
setx HF_ENDPOINT "https://hf-mirror.com"
```

**Linux/Mac:**
```bash
# 临时设置
export HF_ENDPOINT="https://hf-mirror.com"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export HF_ENDPOINT="https://hf-mirror.com"' >> ~/.bashrc
source ~/.bashrc
```

#### 方法 2: 使用命令行参数

```bash
python download_qwen3_model.py --source hf-mirror
```

#### 方法 3: 使用 ModelScope（无需配置）

```bash
python download_qwen3_model.py --source modelscope
```

---

## 📊 镜像源速度对比（中国大陆）

| 镜像源 | 速度 | 稳定性 | 推荐度 |
|--------|------|--------|--------|
| **ModelScope** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ 强烈推荐 |
| HF-Mirror | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ 推荐 |
| 清华 pip | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ 推荐 |
| 阿里云 pip | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ 推荐 |
| Hugging Face 官方 | ⭐⭐ | ⭐⭐⭐ | ❌ 慢 |

---

## 💡 完整安装流程（推荐）

### Windows 用户

```cmd
# 1. 配置镜像源
setup_china_mirrors.bat

# 2. 创建 conda 环境
conda create -n news-qwen python=3.10 -y
conda activate news-qwen

# 3. 安装 PyTorch (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. 安装其他依赖
pip install -r requirements.txt

# 5. 下载模型（使用 ModelScope）
python download_qwen3_model.py --source modelscope
```

### Linux/Mac 用户

```bash
# 1. 配置镜像源
chmod +x setup_china_mirrors.sh
./setup_china_mirrors.sh

# 2. 创建 conda 环境
conda create -n news-qwen python=3.10 -y
conda activate news-qwen

# 3. 安装 PyTorch (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. 安装其他依赖
pip install -r requirements.txt

# 5. 下载模型（使用 ModelScope）
python download_qwen3_model.py --source modelscope
```

---

## 🎯 常见问题

### Q1: ModelScope 下载失败怎么办？

**解决方案：**

```bash
# 1. 确保已安装 modelscope
pip install modelscope

# 2. 使用 HF-Mirror 作为备选
python download_qwen3_model.py --source hf-mirror

# 3. 或使用自动模式（会自动尝试多个源）
python download_qwen3_model.py
```

### Q2: pip 安装包速度慢？

**解决方案：**

```bash
# 临时使用镜像源
pip install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或永久配置
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q3: conda 下载慢？

**解决方案：**

```bash
# 配置清华镜像
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --set show_channel_urls yes

# 清除缓存
conda clean -i
```

### Q4: 如何验证镜像源是否生效？

**pip 镜像：**
```bash
pip config list
# 应该显示: global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'
```

**conda 镜像：**
```bash
conda config --show channels
# 应该显示配置的镜像 URL
```

**Hugging Face 镜像：**
```bash
# Windows (PowerShell)
$env:HF_ENDPOINT

# Linux/Mac
echo $HF_ENDPOINT
# 应该显示: https://hf-mirror.com
```

### Q5: ModelScope 和 Hugging Face 的模型一样吗？

**是的！** ModelScope 上的模型都是从 Hugging Face 同步的，质量和版本都相同，只是服务器在国内，下载更快。

---

## 📦 可用的下载源

### 1. ModelScope（魔搭社区）

- **官网**: https://www.modelscope.cn
- **特点**: 阿里巴巴运营，国内最快
- **使用**: `--source modelscope`

### 2. HF-Mirror

- **官网**: https://hf-mirror.com
- **特点**: Hugging Face 镜像站
- **使用**: `--source hf-mirror`

### 3. Hugging Face 官方

- **官网**: https://huggingface.co
- **特点**: 原始官方源
- **使用**: `--source huggingface`

---

## 🔄 切换下载源

### 临时切换（单次使用）

```bash
# 使用 ModelScope
python download_qwen3_model.py --source modelscope

# 使用 HF-Mirror
python download_qwen3_model.py --source hf-mirror

# 使用官方源
python download_qwen3_model.py --source huggingface
```

### 永久切换（修改环境变量）

编辑 `download_qwen3_model.py` 中的默认值，或设置环境变量 `HF_ENDPOINT`。

---

## 🎉 推荐配置（最佳实践）

### 国内用户推荐配置

```bash
# 1. pip 使用清华镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 2. conda 使用清华镜像
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main

# 3. 模型下载使用 ModelScope
python download_qwen3_model.py --source modelscope
```

### 国外用户推荐配置

```bash
# 使用官方源即可
pip install -r requirements.txt
python download_qwen3_model.py --source huggingface
```

---

## 📞 获取帮助

如果遇到问题：

1. 查看错误信息
2. 尝试其他镜像源
3. 检查网络连接
4. 查看项目 README.md

---

## 🔗 相关链接

- **清华大学开源软件镜像站**: https://mirrors.tuna.tsinghua.edu.cn
- **阿里云镜像**: https://developer.aliyun.com/mirror
- **ModelScope**: https://www.modelscope.cn
- **HF-Mirror**: https://hf-mirror.com

---

祝您使用愉快！🎉
