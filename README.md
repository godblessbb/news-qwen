# Qwen3 14B + vLLM 高吞吐量推理系统

本项目提供了使用 vLLM 部署 Qwen3 14B 模型进行高效推理的完整解决方案。

## 功能特点

- 自动下载 Qwen3 14B 模型
- 支持 Windows（D盘）和 Linux 系统
- 使用 vLLM 实现高吞吐量推理
- 支持批量推理和交互式对话
- GPU 加速和多 GPU 张量并行

## 系统要求

### 硬件要求
- **GPU**: NVIDIA GPU，显存至少 28GB（推荐 A100/H100）
- **内存**: 至少 32GB RAM
- **存储**: 至少 50GB 可用空间

### 软件要求
- Python 3.8+
- CUDA 11.8+ 或 12.1+
- NVIDIA 驱动程序

## 安装步骤

### 1. 安装 PyTorch

根据您的 CUDA 版本安装 PyTorch：

```bash
# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. 安装项目依赖

```bash
pip install -r requirements.txt
```

## 使用指南

### 步骤 1: 下载模型

#### 基本用法（自动检测路径）

```bash
python download_qwen3_model.py
```

默认路径：
- **Windows**: `D:/models/qwen3-14b`
- **Linux/Mac**: `~/models/qwen3-14b`

#### 使用镜像站点（推荐中国大陆用户）

```bash
python download_qwen3_model.py --mirror
```

#### 自定义路径

```bash
python download_qwen3_model.py --output-dir /path/to/your/models
```

#### 下载其他模型

```bash
# 下载 Qwen2.5 7B
python download_qwen3_model.py --model-name Qwen/Qwen2.5-7B-Instruct

# 下载 Qwen2.5 72B
python download_qwen3_model.py --model-name Qwen/Qwen2.5-72B-Instruct
```

### 步骤 2: 运行推理

#### 1. 单次测试

```bash
python vllm_inference.py
```

#### 2. 批量推理测试（推荐）

```bash
python vllm_inference.py --batch-test
```

输出示例：
```
✓ 批量推理完成
总耗时: 5.23 秒
平均每条: 1.05 秒
吞吐量: 0.96 条/秒
```

#### 3. 交互模式

```bash
python vllm_inference.py --interactive
```

#### 4. 多 GPU 推理

```bash
# 使用 2 个 GPU
python vllm_inference.py --tensor-parallel-size 2 --batch-test

# 使用 4 个 GPU
python vllm_inference.py --tensor-parallel-size 4 --batch-test
```

#### 5. 自定义 GPU 内存使用

```bash
# 使用 80% GPU 内存
python vllm_inference.py --gpu-memory-utilization 0.8 --batch-test
```

#### 6. 指定模型路径

```bash
python vllm_inference.py --model-path /path/to/your/model --batch-test
```

## Python API 使用示例

### 基本使用

```python
from vllm_inference import Qwen3VLLMInference

# 初始化推理引擎
inference = Qwen3VLLMInference(
    tensor_parallel_size=1,
    gpu_memory_utilization=0.9
)

# 对话模式
messages = [
    [{"role": "user", "content": "什么是人工智能？"}],
    [{"role": "user", "content": "解释一下深度学习"}],
]

responses = inference.chat(messages, temperature=0.7, max_tokens=512)

for msg, response in zip(messages, responses):
    print(f"问题: {msg[0]['content']}")
    print(f"回答: {response}\n")
```

### 批量推理（高吞吐量）

```python
from vllm_inference import Qwen3VLLMInference

# 初始化
inference = Qwen3VLLMInference(tensor_parallel_size=2)

# 准备大量数据
messages_batch = [
    [{"role": "user", "content": f"问题 {i}"}]
    for i in range(100)
]

# 批量推理
responses = inference.chat(
    messages_batch,
    temperature=0.7,
    top_p=0.8,
    max_tokens=256
)

print(f"完成 {len(responses)} 条推理")
```

### 多轮对话

```python
from vllm_inference import Qwen3VLLMInference

inference = Qwen3VLLMInference()

# 构建对话历史
conversation = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么我可以帮助你的吗？"},
    {"role": "user", "content": "介绍一下 Python"}
]

responses = inference.chat([conversation])
print(responses[0])
```

## 性能优化建议

### 1. 多 GPU 配置

```bash
# 2 个 GPU，最佳性能
python vllm_inference.py --tensor-parallel-size 2 --gpu-memory-utilization 0.95
```

### 2. 批处理大小

- 批量大小越大，吞吐量越高
- 建议批量大小：16-64（取决于显存）

### 3. 序列长度

```python
# 限制最大序列长度以提高吞吐量
inference = Qwen3VLLMInference(max_model_len=8192)
```

### 4. 采样参数调整

```python
# 更快的生成速度
responses = inference.chat(
    messages,
    temperature=0.7,
    top_k=20,      # 降低 top_k
    max_tokens=256 # 限制生成长度
)
```

## 性能基准

在不同硬件配置下的性能参考：

| GPU 配置 | 批量大小 | 吞吐量 (tokens/s) | 延迟 (ms) |
|---------|---------|------------------|----------|
| 1x A100 80GB | 16 | ~2000 | ~150 |
| 2x A100 80GB | 32 | ~3500 | ~100 |
| 4x A100 80GB | 64 | ~6000 | ~80 |

## 常见问题

### Q1: 显存不足怎么办？

```bash
# 降低 GPU 内存使用率
python vllm_inference.py --gpu-memory-utilization 0.7

# 或使用量化版本（需要先下载量化模型）
python download_qwen3_model.py --model-name Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4
```

### Q2: 如何加速模型下载？

```bash
# 使用镜像站点
python download_qwen3_model.py --mirror

# 或手动设置环境变量
export HF_ENDPOINT=https://hf-mirror.com
python download_qwen3_model.py
```

### Q3: 如何监控 GPU 使用情况？

```bash
# 实时监控
watch -n 1 nvidia-smi

# 或使用 Python
pip install nvidia-ml-py3
```

### Q4: Windows 下 D 盘路径问题

确保 D 盘存在且有足够空间：

```bash
# PowerShell 中检查
Get-PSDrive D

# 或手动指定路径
python download_qwen3_model.py --output-dir E:/models/qwen3-14b
```

## 项目结构

```
news-qwen/
├── download_qwen3_model.py  # 模型下载脚本
├── vllm_inference.py        # vLLM 推理脚本
├── requirements.txt         # 依赖列表
└── README.md               # 使用说明
```

## 参考资料

- [vLLM 官方文档](https://docs.vllm.ai/)
- [Qwen 模型介绍](https://github.com/QwenLM/Qwen)
- [Hugging Face Hub](https://huggingface.co/Qwen)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
