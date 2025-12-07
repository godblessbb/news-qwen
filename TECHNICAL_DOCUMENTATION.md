# News-Qwen 项目完整技术文档

> **版本**: 1.0
> **最后更新**: 2025-12-07
> **目的**: 使用 Qwen 大语言模型处理金融新闻数据，按交易周期生成事件摘要

---

## 目录

1. [项目概述](#项目概述)
2. [技术架构](#技术架构)
3. [环境配置](#环境配置)
4. [核心组件详解](#核心组件详解)
5. [数据格式规范](#数据格式规范)
6. [API 接口规范](#api-接口规范)
7. [工作流程](#工作流程)
8. [使用示例](#使用示例)
9. [性能优化](#性能优化)
10. [故障排除](#故障排除)

---

## 项目概述

### 主要功能

本项目使用 Qwen2.5-3B 大语言模型处理金融新闻数据，主要实现：

1. **按交易周期聚合新闻**：周五收盘 → 下周五收盘为一个交易周期
2. **智能事件摘要生成**：使用大模型分析新闻，生成结构化事件摘要
3. **批量处理与内存管理**：支持大规模新闻数据处理（已测试 5860+ 条新闻）
4. **HTTP API 服务**：提供标准 REST API，方便其他项目调用

### 技术栈

- **语言**: Python 3.8+
- **LLM 框架**: Transformers (HuggingFace)
- **模型**: Qwen2.5-3B-Instruct (默认 4-bit 量化)
- **量化技术**: BitsAndBytes (NF4 4-bit 量化)
- **API 框架**: FastAPI + Uvicorn
- **数据处理**: Pandas
- **硬件**: CUDA GPU (推荐) 或 CPU

---

## 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户/其他项目                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   API Server         │
          │  (api_server.py)     │
          │  - FastAPI           │
          │  - Port: 8000        │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Model Inference    │
          │  - Qwen2.5-3B        │
          │  - 4-bit Quantized   │
          │  - VRAM: 2-3GB       │
          └──────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌────────────────┐      ┌──────────────────┐
│ News Processor │      │  Direct Inference │
│ (Scripts/*.py) │      │ (transformers_    │
│                │      │  inference.py)    │
└────────┬───────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐
│  CSV Files      │
│  - Input: News  │
│  - Output:Events│
└─────────────────┘
```

### 核心模块

1. **API 服务层** (`api_server.py`)
   - 提供 HTTP REST API
   - 管理模型生命周期
   - 处理并发请求

2. **推理引擎** (`transformers_inference.py`)
   - 封装 Transformers 模型加载
   - 支持文本生成和对话模式
   - 内存管理和设备映射

3. **新闻处理器** (`Scripts/process_news_by_trading_week.py`)
   - 交易周期计算
   - 批量新闻分析
   - 分层合并策略

4. **配置管理** (`config.yaml`)
   - 集中化配置
   - 模型路径、量化参数
   - API 服务参数

---

## 环境配置

### 1. 系统要求

#### 硬件要求

- **GPU (推荐)**:
  - NVIDIA GPU with CUDA support
  - 显存: ≥ 3GB (4-bit 量化)
  - 显存: ≥ 8GB (8-bit 量化)
  - 显存: ≥ 16GB (无量化)

- **CPU (备选)**:
  - 内存: ≥ 16GB
  - 处理速度较慢（约 GPU 的 1/10）

#### 软件要求

- Python 3.8 - 3.11
- CUDA 11.8+ (GPU 模式)
- Windows 10/11 或 Linux

### 2. 依赖安装

#### 步骤 1: 克隆或下载项目

```bash
git clone <repository-url>
cd news-qwen
```

#### 步骤 2: 创建虚拟环境 (推荐)

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 步骤 3: 安装 PyTorch

**根据您的 CUDA 版本选择：**

```bash
# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CPU only
pip install torch torchvision torchaudio
```

#### 步骤 4: 安装项目依赖

```bash
pip install -r requirements.txt
```

**主要依赖列表**:

```
transformers>=4.40.0
huggingface-hub>=0.23.0
tokenizers>=0.19.0
accelerate>=0.30.0
bitsandbytes>=0.41.0  # Windows 用户可能需要 bitsandbytes-windows
pandas>=2.0.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
requests>=2.31.0
pyyaml>=6.0
```

### 3. 模型下载

#### 方式 1: 使用 HuggingFace Hub (推荐)

```bash
# 安装 huggingface-cli
pip install huggingface-hub

# 下载模型到指定目录
huggingface-cli download Qwen/Qwen2.5-3B-Instruct \
  --local-dir D:/models/qwen2.5-3b \
  --local-dir-use-symlinks False
```

#### 方式 2: 使用 ModelScope (国内用户)

```bash
pip install modelscope

python -c "
from modelscope import snapshot_download
snapshot_download('qwen/Qwen2.5-3B-Instruct', cache_dir='D:/models/qwen2.5-3b')
"
```

#### 方式 3: 手动下载

访问 [HuggingFace Model Hub](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) 手动下载所有文件到本地目录。

**必需文件**:
- `config.json`
- `model.safetensors` (或 `pytorch_model.bin`)
- `tokenizer.json`
- `tokenizer_config.json`
- `vocab.json`
- `merges.txt`

### 4. 配置文件设置

编辑 `config.yaml`:

```yaml
model:
  path: "D:/models/qwen2.5-3b"  # 修改为您的实际路径
  load_in_4bit: true             # 默认 4-bit 量化
  load_in_8bit: false
  device: "auto"

api:
  host: "0.0.0.0"
  port: 8000

generation:
  max_tokens: 512
  temperature: 0.7
  top_p: 0.8
```

---

## 核心组件详解

### 1. API Server (`api_server.py`)

#### 功能描述

提供 HTTP REST API 服务，允许其他项目通过 HTTP 请求调用 Qwen 模型。

#### 配置区域 (代码行 19-40)

```python
# 默认模型路径
DEFAULT_MODEL_PATH = "D:/models/qwen2.5-3b"

# 默认量化设置
DEFAULT_LOAD_IN_4BIT = True   # 默认启用 4-bit 量化
DEFAULT_LOAD_IN_8BIT = False

# 默认设备
DEFAULT_DEVICE = "auto"

# API 服务配置
API_HOST = "0.0.0.0"
API_PORT = 8000
```

#### 核心函数

**1. `load_model()` (行 100-162)**

- 功能: 加载模型和 tokenizer
- 参数:
  - `model_path`: 模型路径
  - `load_in_4bit`: 是否 4-bit 量化
  - `load_in_8bit`: 是否 8-bit 量化
  - `device`: 设备选择

**技术细节**:

```python
# 本地路径检测逻辑
is_local_path = (
    os.path.sep in model_path or
    "/" in model_path and not model_path.count("/") == 1 or
    ":" in model_path or
    model_path.startswith(".") or
    model_path.startswith("~")
)

# 4-bit 量化配置
if load_in_4bit:
    model_kwargs["load_in_4bit"] = True
    model_kwargs["device_map"] = "auto"
```

**2. `/generate` 端点 (行 193-248)**

- 功能: 文本生成接口
- 方法: POST
- 请求体:
  ```json
  {
    "prompt": "输入文本",
    "max_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.8
  }
  ```
- 响应体:
  ```json
  {
    "generated_text": "生成的文本",
    "prompt_tokens": 10,
    "generated_tokens": 100,
    "total_tokens": 110
  }
  ```

**3. `/chat` 端点 (行 251-318)**

- 功能: 对话接口
- 方法: POST
- 请求体:
  ```json
  {
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "max_tokens": 256,
    "temperature": 0.7,
    "top_p": 0.8
  }
  ```

#### 启动方式

```bash
# 使用默认配置 (4-bit 量化)
python api_server.py

# 自定义模型路径
python api_server.py --model-path D:/models/qwen2.5-3b

# 禁用量化
python api_server.py --no-4bit

# 更改端口
python api_server.py --port 8080

# 仅本机访问
python api_server.py --host 127.0.0.1
```

---

### 2. Transformers Inference (`transformers_inference.py`)

#### 功能描述

直接使用 Transformers 库进行推理的脚本，支持交互模式和批量测试。

#### 核心类: `Qwen3Inference`

**初始化 (行 34-106)**

```python
class Qwen3Inference:
    def __init__(
        self,
        model_path: str = None,
        device: str = "auto",
        load_in_8bit: bool = False,
        load_in_4bit: bool = True,  # 默认 4-bit
    ):
```

**关键技术点**:

1. **BitsAndBytesConfig 配置** (行 72-89)

```python
if load_in_4bit:
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",           # NormalFloat 4-bit
        bnb_4bit_compute_dtype=torch.float16, # 计算精度
        bnb_4bit_use_double_quant=True        # 双重量化
    )
    kwargs["quantization_config"] = quantization_config
    kwargs["device_map"] = "auto"
```

**2. `generate()` 方法 (行 108-158)**

- 功能: 批量文本生成
- 参数:
  - `prompts`: 输入提示列表
  - `temperature`: 温度参数 (0-2)
  - `top_p`: Top-p 采样 (0-1)
  - `max_tokens`: 最大生成长度

**3. `chat()` 方法 (行 160-201)**

- 功能: 对话模式生成
- 自动应用 chat template

#### 启动方式

```bash
# 交互模式 (默认 4-bit 量化)
python transformers_inference.py --interactive

# 批量测试模式
python transformers_inference.py --batch-test

# 禁用 4-bit 量化
python transformers_inference.py --no-4bit --interactive

# 使用 8-bit 量化
python transformers_inference.py --load-in-8bit --interactive

# CPU 模式
python transformers_inference.py --device cpu --interactive
```

---

### 3. News Processor (`Scripts/process_news_by_trading_week.py`)

#### 功能描述

读取新闻 CSV 文件，按交易周期分组，使用 LLM 生成事件摘要，输出结构化 CSV。

#### 核心配置 (行 26-50)

```python
# Prompt 模板
ANALYSIS_PROMPT_TEMPLATE = """你是一位专业的金融分析师。请分析以下关于 {symbol} ({name}) 在交易周期 {start_date} 至 {end_date} 的新闻事件。

新闻列表：
{news_list}

请提供简洁的事件总结，要求：
1. 使用实时性陈述（过去时态）
2. 包含重要数据和数字
3. 包含情感属性关键词（正面/负面/中性）
4. 突出对股价的潜在影响
5. 控制在150字以内

请直接返回事件总结文本，不需要JSON格式。
"""

# 批次配置
MAX_NEWS_PER_BATCH = 15  # 单批次最大新闻数
```

#### 关键函数

**1. `calculate_trading_week()` (行 203-239)**

计算交易周期的核心算法：

```python
def calculate_trading_week(date: pd.Timestamp) -> tuple:
    """
    计算交易周期 (周五到周五)

    规则:
    - 周一至周五的新闻 -> 归入上周五至本周五
    - 周六至周日的新闻 -> 归入本周五至下周五
    """
    weekday = date.weekday()  # 0=周一, 6=周日

    if weekday < 5:  # 周一到周五
        # 找到上周五
        days_since_friday = (weekday + 3) % 7
        start_date = date - pd.Timedelta(days=days_since_friday)

        # 找到本周五
        days_to_friday = (4 - weekday) % 7
        end_date = date + pd.Timedelta(days=days_to_friday)
    else:  # 周六或周日
        # 找到本周五
        days_since_friday = weekday - 4
        start_date = date - pd.Timedelta(days=days_since_friday)

        # 找到下周五
        end_date = start_date + pd.Timedelta(days=7)

    return start_date, end_date
```

**2. `generate_response()` (行 158-194)**

调用 LLM 生成文本，包含 GPU 缓存清理：

```python
def generate_response(model, tokenizer, prompt, max_tokens=512):
    """生成响应并清理 GPU 缓存"""
    inputs = tokenizer(prompt, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.8,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_text = tokenizer.decode(
        outputs[0][len(inputs["input_ids"][0]):],
        skip_special_tokens=True
    )

    # 清理显存 - 防止 OOM
    del inputs, outputs
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return generated_text.strip()
```

**3. `_merge_summaries()` (行 325-391)**

分层合并策略，防止大批次合并时 CUDA OOM：

```python
def _merge_summaries(
    model, tokenizer, symbol, name,
    start_date, end_date, summaries, max_tokens
) -> str:
    """
    分层合并多个批次的总结

    如果批次 > 8，采用两层合并：
    1. 第一层：每 8 个摘要合并为 1 个
    2. 第二层：合并所有组摘要为最终结果
    """
    MAX_SUMMARIES_PER_MERGE = 8

    if len(summaries) <= MAX_SUMMARIES_PER_MERGE:
        # 直接合并
        merge_prompt = f"""..."""
        return generate_response(model, tokenizer, merge_prompt, max_tokens)

    # 第一层：分组合并
    merged_groups = []
    for i in range(0, len(summaries), MAX_SUMMARIES_PER_MERGE):
        group = summaries[i:i + MAX_SUMMARIES_PER_MERGE]
        group_merged = generate_response(model, tokenizer, merge_prompt, max_tokens)
        merged_groups.append(group_merged)

    # 第二层：最终合并
    final_merged = generate_response(model, tokenizer, final_prompt, max_tokens)
    return final_merged
```

**4. `analyze_trading_week()` (行 242-323)**

分析单个交易周期的新闻：

```python
def analyze_trading_week(
    model, tokenizer, symbol, name,
    start_date, end_date, news_items, max_tokens
) -> str:
    """
    分析单个交易周期的新闻

    工作流程:
    1. 如果新闻 <= 15 条，直接分析
    2. 如果新闻 > 15 条，分批处理
    3. 合并所有批次的分析结果
    """
    if len(news_items) <= MAX_NEWS_PER_BATCH:
        # 直接分析
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(...)
        return generate_response(model, tokenizer, prompt, max_tokens)

    # 分批处理
    summaries = []
    num_batches = (len(news_items) + MAX_NEWS_PER_BATCH - 1) // MAX_NEWS_PER_BATCH

    for i in range(0, len(news_items), MAX_NEWS_PER_BATCH):
        batch = news_items[i:i + MAX_NEWS_PER_BATCH]
        batch_summary = generate_response(model, tokenizer, batch_prompt, max_tokens)
        summaries.append(batch_summary)

    # 合并批次
    return _merge_summaries(model, tokenizer, symbol, name,
                           start_date, end_date, summaries, max_tokens)
```

#### 使用方式

```bash
# 基本用法 (默认 4-bit 量化)
python Scripts/process_news_by_trading_week.py \
    --input data/AAL_news.csv \
    --model-path D:/models/qwen2.5-3b \
    --load-in-4bit

# 指定输出目录
python Scripts/process_news_by_trading_week.py \
    --input data/AAL_news.csv \
    --model-path D:/models/qwen2.5-3b \
    --output-dir ./Events \
    --load-in-4bit

# 使用 8-bit 量化
python Scripts/process_news_by_trading_week.py \
    --input data/AAL_news.csv \
    --model-path D:/models/qwen2.5-3b \
    --load-in-8bit

# CPU 模式
python Scripts/process_news_by_trading_week.py \
    --input data/AAL_news.csv \
    --model-path D:/models/qwen2.5-3b \
    --device cpu
```

---

## 数据格式规范

### 输入 CSV 格式

**必需列**:

| 列名 | 数据类型 | 说明 | 示例 |
|------|---------|------|------|
| `symbol` | string | 股票代码 | "AAL" |
| `name` | string | 公司名称 | "American Airlines" |
| `date` | datetime | 新闻日期时间 | "2024-11-07 06:31:00" |
| `title` | string | 新闻标题 | "Morgan Stanley Maintains AAL" |

**可选列**:

| 列名 | 数据类型 | 说明 | 示例 |
|------|---------|------|------|
| `source` | string | 新闻来源 | "Moomoo News" |
| `chg_in_5` | float | 5日涨跌幅 (%) | 2.5 |
| `chg_in_10` | float | 10日涨跌幅 (%) | 5.3 |

**示例 CSV**:

```csv
symbol,name,date,title,source,chg_in_5,chg_in_10
AAL,American Airlines,2024-11-07 06:31:00,"Morgan Stanley Maintains AAL",Moomoo News,2.5,5.3
AAL,American Airlines,2024-11-08 09:15:00,"AAL Q3 Earnings Beat Estimates",Bloomberg,3.2,6.1
```

### 输出 CSV 格式

| 列名 | 数据类型 | 说明 | 示例 |
|------|---------|------|------|
| `symbol` | string | 股票代码 | "AAL" |
| `name` | string | 公司名称 | "American Airlines" |
| `start_date` | date | 交易周期开始日期 | "2024-11-01" |
| `end_date` | date | 交易周期结束日期 | "2024-11-08" |
| `chg_in_5` | float | 5日平均涨跌幅 | 2.85 |
| `chg_in_10` | float | 10日平均涨跌幅 | 5.7 |
| `event_details` | string | LLM 生成的事件摘要 | "美国航空本周..." |

**示例输出**:

```csv
symbol,name,start_date,end_date,chg_in_5,chg_in_10,event_details
AAL,American Airlines,2024-11-01,2024-11-08,2.85,5.7,"美国航空本周获多家机构维持买入评级，目标价18美元。公司公布Q3财报超预期，营收增长12%达XX亿美元。燃油成本上涨对盈利构成压力。整体情感偏正面，对股价有积极影响。"
```

**输出文件命名**:

```
Events/{输入文件名}_events_{时间戳}.csv

示例: Events/AAL_news_events_20241207_143022.csv
```

---

## API 接口规范

### 基础信息

- **Base URL**: `http://localhost:8000`
- **协议**: HTTP/1.1
- **内容类型**: `application/json`
- **字符编码**: UTF-8

### 端点列表

#### 1. 根端点

**GET /**

```bash
curl http://localhost:8000/
```

**响应**:

```json
{
  "message": "Qwen Model API",
  "status": "running",
  "docs": "/docs",
  "model_loaded": true
}
```

#### 2. 健康检查

**GET /health**

```bash
curl http://localhost:8000/health
```

**响应**:

```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda:0"
}
```

#### 3. 文本生成

**POST /generate**

**请求示例** (Python):

```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={
        "prompt": "请介绍人工智能",
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.8
    }
)

result = response.json()
print(result['generated_text'])
```

**请求示例** (cURL):

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "请介绍人工智能",
    "max_tokens": 256,
    "temperature": 0.7,
    "top_p": 0.8
  }'
```

**请求参数**:

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt` | string | 是 | - | 输入提示文本 |
| `max_tokens` | integer | 否 | 512 | 最大生成令牌数 (1-2048) |
| `temperature` | float | 否 | 0.7 | 温度参数 (0-2) |
| `top_p` | float | 否 | 0.8 | Top-p 采样 (0-1) |

**响应示例**:

```json
{
  "generated_text": "人工智能（Artificial Intelligence，AI）是计算机科学的一个分支...",
  "prompt_tokens": 10,
  "generated_tokens": 156,
  "total_tokens": 166
}
```

#### 4. 对话接口

**POST /chat**

**请求示例** (Python):

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "messages": [
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ],
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.8
    }
)

result = response.json()
print(result['reply'])
```

**请求参数**:

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `messages` | array | 是 | - | 对话历史 |
| `max_tokens` | integer | 否 | 512 | 最大生成令牌数 |
| `temperature` | float | 否 | 0.7 | 温度参数 |
| `top_p` | float | 否 | 0.8 | Top-p 采样 |

**消息格式**:

```json
{
  "role": "user",      // "user", "assistant", "system"
  "content": "文本内容"
}
```

**响应示例**:

```json
{
  "reply": "你好！我是Qwen，一个大型语言模型...",
  "prompt_tokens": 15,
  "generated_tokens": 85,
  "total_tokens": 100
}
```

**多轮对话示例**:

```python
# 第一轮
response1 = requests.post(
    "http://localhost:8000/chat",
    json={
        "messages": [
            {"role": "user", "content": "什么是机器学习？"}
        ]
    }
)

# 第二轮 - 包含上下文
response2 = requests.post(
    "http://localhost:8000/chat",
    json={
        "messages": [
            {"role": "user", "content": "什么是机器学习？"},
            {"role": "assistant", "content": response1.json()['reply']},
            {"role": "user", "content": "请举个例子"}
        ]
    }
)
```

### 错误响应

**格式**:

```json
{
  "detail": "错误描述信息"
}
```

**HTTP 状态码**:

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 422 | 请求参数验证失败 |
| 500 | 服务器内部错误 |
| 503 | 模型未加载 |

---

## 工作流程

### 完整处理流程

```
1. 准备阶段
   ├─ 安装依赖
   ├─ 下载模型到本地
   └─ 配置 config.yaml

2. 启动 API 服务 (可选)
   ├─ python api_server.py
   └─ 访问 http://localhost:8000/docs 查看文档

3. 处理新闻数据
   ├─ 准备输入 CSV (包含 symbol, name, date, title)
   ├─ 运行处理脚本
   │   python Scripts/process_news_by_trading_week.py \
   │       --input data/news.csv \
   │       --model-path D:/models/qwen2.5-3b \
   │       --load-in-4bit
   └─ 获取输出 CSV (Events/news_events_*.csv)

4. 数据分析
   ├─ 读取输出 CSV
   ├─ 按交易周期分析事件
   └─ 与股价数据关联分析
```

### 交易周期计算示例

```
输入新闻日期: 2024-11-07 (周四)

计算步骤:
1. 检测星期几: weekday = 3 (周四)
2. 因为是工作日 (weekday < 5):
   - 找上周五: 2024-11-07 - 3天 = 2024-11-01 (周五)
   - 找本周五: 2024-11-07 + 1天 = 2024-11-08 (周五)
3. 交易周期: 2024-11-01 至 2024-11-08

输出: start_date=2024-11-01, end_date=2024-11-08
```

### 批量处理与合并逻辑

```
假设某交易周期有 32 条新闻，MAX_NEWS_PER_BATCH=15

步骤 1: 分批处理
├─ Batch 1: 新闻 1-15  → 摘要 A
├─ Batch 2: 新闻 16-30 → 摘要 B
└─ Batch 3: 新闻 31-32 → 摘要 C

步骤 2: 合并摘要 (因为只有 3 个 < 8)
└─ 直接合并 [A, B, C] → 最终摘要

假设某交易周期有 166 条新闻 (实际遇到的情况)

步骤 1: 分批处理
├─ Batch 1-11: 15条/批 → 摘要 1-11
└─ Batch 12: 1条 → 摘要 12

步骤 2: 第一层合并 (MAX_SUMMARIES_PER_MERGE=8)
├─ Group 1: 摘要 1-8  → 组摘要 G1
└─ Group 2: 摘要 9-12 → 组摘要 G2

步骤 3: 第二层合并
└─ 合并 [G1, G2] → 最终摘要
```

---

## 使用示例

### 示例 1: 使用 API 进行新闻分析

**Python 客户端示例**:

```python
import requests
import pandas as pd

# API 配置
API_BASE_URL = "http://localhost:8000"

def analyze_news_batch(news_items, symbol, name):
    """分析一批新闻"""
    # 构造 prompt
    news_list = "\n".join([
        f"{i+1}. {item['title']}"
        for i, item in enumerate(news_items)
    ])

    prompt = f"""你是一位专业的金融分析师。请分析以下关于 {symbol} ({name}) 的新闻：

{news_list}

请提供简洁的事件总结（150字以内），包含：
1. 关键事件
2. 重要数据
3. 情感倾向
4. 对股价的潜在影响
"""

    # 调用 API
    response = requests.post(
        f"{API_BASE_URL}/generate",
        json={
            "prompt": prompt,
            "max_tokens": 256,
            "temperature": 0.7
        }
    )

    return response.json()['generated_text']

# 示例使用
news_items = [
    {"title": "Morgan Stanley Maintains AAL"},
    {"title": "AAL Q3 Earnings Beat Estimates"},
    {"title": "Fuel Costs Rise for Airlines"}
]

summary = analyze_news_batch(news_items, "AAL", "American Airlines")
print(summary)
```

### 示例 2: 处理完整的新闻 CSV

**步骤 1: 准备数据**

```python
import pandas as pd

# 创建示例数据
data = {
    'symbol': ['AAL'] * 10,
    'name': ['American Airlines'] * 10,
    'date': pd.date_range('2024-11-01', periods=10, freq='6H'),
    'title': [
        "Morgan Stanley Maintains AAL",
        "AAL Q3 Earnings Beat Estimates",
        "Fuel Costs Rise for Airlines",
        # ... 更多新闻
    ],
    'source': ['Moomoo News'] * 10,
    'chg_in_5': [2.5, 3.2, 1.8, ...],
    'chg_in_10': [5.3, 6.1, 4.2, ...]
}

df = pd.DataFrame(data)
df.to_csv('data/AAL_news.csv', index=False)
```

**步骤 2: 运行处理脚本**

```bash
python Scripts/process_news_by_trading_week.py \
    --input data/AAL_news.csv \
    --model-path D:/models/qwen2.5-3b \
    --load-in-4bit \
    --output-dir ./Events
```

**步骤 3: 读取结果**

```python
import pandas as pd

# 读取生成的事件 CSV
events_df = pd.read_csv('Events/AAL_news_events_20241207_143022.csv')

# 查看结果
for _, row in events_df.iterrows():
    print(f"交易周期: {row['start_date']} - {row['end_date']}")
    print(f"事件摘要: {row['event_details']}")
    print(f"5日涨跌幅: {row['chg_in_5']}%")
    print("-" * 60)
```

### 示例 3: 集成到量化交易系统

```python
import pandas as pd
import requests
from datetime import datetime, timedelta

class NewsEventAnalyzer:
    """新闻事件分析器"""

    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url

    def get_weekly_events(self, symbol, start_date, end_date):
        """获取特定周期的新闻事件摘要"""
        # 从数据库或 CSV 读取新闻
        news_df = pd.read_csv(f'data/{symbol}_news.csv')
        news_df['date'] = pd.to_datetime(news_df['date'])

        # 筛选日期范围
        mask = (news_df['date'] >= start_date) & (news_df['date'] <= end_date)
        weekly_news = news_df[mask]

        if len(weekly_news) == 0:
            return None

        # 调用 API 分析
        news_list = "\n".join([
            f"{i+1}. {row['title']}"
            for i, row in weekly_news.iterrows()
        ])

        prompt = f"""分析以下关于 {symbol} 的新闻（{start_date} 至 {end_date}）：

{news_list}

要求：简洁总结（100字内），包含情感倾向和对股价的影响。
"""

        response = requests.post(
            f"{self.api_url}/generate",
            json={"prompt": prompt, "max_tokens": 200}
        )

        return response.json()['generated_text']

    def calculate_event_impact_score(self, event_summary):
        """根据事件摘要计算影响分数"""
        # 简单示例：基于关键词
        positive_keywords = ['超预期', '增长', '买入', '上涨', '正面']
        negative_keywords = ['下跌', '亏损', '负面', '风险', '压力']

        score = 0
        for keyword in positive_keywords:
            if keyword in event_summary:
                score += 1
        for keyword in negative_keywords:
            if keyword in event_summary:
                score -= 1

        return score

# 使用示例
analyzer = NewsEventAnalyzer()

# 获取上周的事件
last_friday = datetime.now().date() - timedelta(days=datetime.now().weekday() + 3)
this_friday = last_friday + timedelta(days=7)

event_summary = analyzer.get_weekly_events('AAL', last_friday, this_friday)
impact_score = analyzer.calculate_event_impact_score(event_summary)

print(f"事件摘要: {event_summary}")
print(f"影响分数: {impact_score}")
```

---

## 性能优化

### 1. 显存优化

#### 量化技术对比

| 量化方式 | 显存需求 | 推理速度 | 精度损失 | 推荐场景 |
|---------|---------|---------|---------|---------|
| 无量化 (FP16) | ~16GB | 最快 | 无 | 大显存 GPU |
| 8-bit | ~8GB | 较快 | 极小 | 中等显存 GPU |
| 4-bit (NF4) | ~3GB | 中等 | 小 | 小显存 GPU (推荐) |

#### BitsAndBytes 配置详解

**4-bit 量化 (推荐)**:

```python
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",           # NormalFloat 4-bit
    bnb_4bit_compute_dtype=torch.float16, # 计算时使用 FP16
    bnb_4bit_use_double_quant=True        # 嵌套量化，进一步节省显存
)
```

**8-bit 量化**:

```python
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_enable_fp32_cpu_offload=True  # CPU offload
)
```

### 2. 批量处理优化

#### 最佳批次大小

根据 GPU 显存调整 `MAX_NEWS_PER_BATCH`:

| GPU 显存 | 量化方式 | 推荐批次大小 |
|---------|---------|-------------|
| 3-4GB | 4-bit | 10-15 条 |
| 6-8GB | 8-bit | 15-20 条 |
| 12GB+ | 无量化 | 20-30 条 |

**修改批次大小**:

编辑 `Scripts/process_news_by_trading_week.py`:

```python
# 行 42
MAX_NEWS_PER_BATCH = 15  # 修改为适合您 GPU 的值
```

### 3. GPU 缓存管理

**手动清理 GPU 缓存**:

```python
import torch

# 在生成后立即清理
del inputs, outputs
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

**监控 GPU 使用**:

```bash
# 实时监控
watch -n 1 nvidia-smi

# 或使用 Python
import torch
print(f"已分配: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
print(f"已缓存: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
```

### 4. 并发优化

#### API 服务并发

使用 Gunicorn 启动多 worker (需要足够显存):

```bash
pip install gunicorn

# 4 个 worker (每个加载一次模型)
gunicorn api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300
```

**注意**: 每个 worker 独立加载模型，需要 `worker数量 × 单模型显存`。

### 5. 推理加速

#### 减少生成长度

```python
# 如果不需要很长的摘要
max_tokens = 256  # 替代默认的 512
```

#### 使用 Flash Attention (可选)

```bash
pip install flash-attn --no-build-isolation
```

```python
# 加载模型时
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    attn_implementation="flash_attention_2",
    ...
)
```

---

## 故障排除

### 问题 1: ModuleNotFoundError

**错误**:

```
ModuleNotFoundError: No module named 'fastapi'
```

**解决**:

```bash
pip install fastapi uvicorn pydantic requests pyyaml
```

或完整安装:

```bash
pip install -r requirements.txt
```

---

### 问题 2: CUDA Out of Memory

**错误**:

```
torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate 4.16 GiB
```

**解决方案**:

**1. 使用 4-bit 量化**:

```bash
python api_server.py --model-path D:/models/qwen2.5-3b
# 默认已启用 4-bit
```

**2. 减小批次大小**:

编辑 `Scripts/process_news_by_trading_week.py`:

```python
MAX_NEWS_PER_BATCH = 10  # 从 15 降低到 10
```

**3. 清理 GPU 缓存**:

```python
import torch
torch.cuda.empty_cache()
```

**4. 使用更小的模型**:

从 14B 模型换到 3B 模型 (已默认配置)。

**5. CPU 模式** (最后手段):

```bash
python api_server.py --device cpu
```

---

### 问题 3: 模型加载失败

**错误**:

```
FileNotFoundError: 模型路径不存在: D:/models/qwen2.5-3b
```

**解决**:

1. **检查路径**:

```bash
# Windows (PowerShell)
Test-Path "D:\models\qwen2.5-3b"

# Linux
ls -la ~/models/qwen2.5-3b
```

2. **重新下载模型**:

```bash
huggingface-cli download Qwen/Qwen2.5-3B-Instruct \
  --local-dir D:/models/qwen2.5-3b \
  --local-dir-use-symlinks False
```

3. **更新配置**:

编辑 `config.yaml` 或使用命令行参数:

```bash
python api_server.py --model-path /path/to/your/model
```

---

### 问题 4: BitsAndBytes 相关错误

**错误 (Windows)**:

```
ImportError: DLL load failed while importing bitsandbytes
```

**解决**:

```bash
# 卸载标准版本
pip uninstall bitsandbytes

# 安装 Windows 特定版本
pip install bitsandbytes-windows
```

**错误 (Linux)**:

```
ValueError: Some modules are dispatched on the CPU or the disk
```

**解决**: 确保使用 `BitsAndBytesConfig` 对象而非布尔标志:

```python
# ❌ 错误方式
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    load_in_4bit=True  # 已废弃
)

# ✅ 正确方式
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True
)

model = AutoModelForCausalLM.from_pretrained(
    model_path,
    quantization_config=quantization_config,
    device_map="auto"
)
```

---

### 问题 5: 端口被占用

**错误**:

```
OSError: [Errno 98] Address already in use
```

**解决**:

**方式 1: 更改端口**:

```bash
python api_server.py --port 8001
```

**方式 2: 停止占用进程** (Linux):

```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

**方式 2: 停止占用进程** (Windows):

```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 杀死进程
taskkill /PID <PID> /F
```

---

### 问题 6: HuggingFace 连接问题

**错误**:

```
requests.exceptions.ConnectionError: HTTPSConnectionPool
```

**解决**:

**方式 1: 使用本地路径**:

```bash
# 确保模型已下载到本地
python api_server.py --model-path D:/models/qwen2.5-3b
```

**方式 2: 配置代理** (如需要):

```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

**方式 3: 使用 ModelScope** (国内):

```python
from modelscope import snapshot_download

snapshot_download(
    'qwen/Qwen2.5-3B-Instruct',
    cache_dir='D:/models/qwen2.5-3b'
)
```

---

### 问题 7: 交易周期计算错误

**问题**: 新闻被分配到错误的交易周期

**调试步骤**:

```python
import pandas as pd
from datetime import datetime

def test_trading_week_calculation():
    """测试交易周期计算"""
    test_dates = [
        "2024-11-04",  # 周一
        "2024-11-07",  # 周四
        "2024-11-08",  # 周五
        "2024-11-09",  # 周六
    ]

    for date_str in test_dates:
        date = pd.to_datetime(date_str)
        start, end = calculate_trading_week(date)
        print(f"{date_str} ({date.day_name()}): {start} - {end}")

test_trading_week_calculation()
```

**预期输出**:

```
2024-11-04 (Monday): 2024-11-01 - 2024-11-08
2024-11-07 (Thursday): 2024-11-01 - 2024-11-08
2024-11-08 (Friday): 2024-11-01 - 2024-11-08
2024-11-09 (Saturday): 2024-11-08 - 2024-11-15
```

---

## 附录

### A. 完整命令参考

#### API Server

```bash
# 完整参数列表
python api_server.py \
  --model-path D:/models/qwen2.5-3b \
  --host 0.0.0.0 \
  --port 8000 \
  --no-4bit \           # 禁用 4-bit (默认启用)
  --load-in-8bit \      # 使用 8-bit 量化
  --device auto         # auto/cuda/cpu
```

#### Transformers Inference

```bash
# 完整参数列表
python transformers_inference.py \
  --model-path D:/models/qwen2.5-3b \
  --device auto \
  --no-4bit \           # 禁用 4-bit
  --load-in-8bit \      # 使用 8-bit
  --interactive         # 交互模式
  --batch-test          # 批量测试
```

#### News Processor

```bash
# 完整参数列表
python Scripts/process_news_by_trading_week.py \
  --input data/news.csv \
  --model-path D:/models/qwen2.5-3b \
  --output-dir ./Events \
  --device auto \
  --max-tokens 512 \
  --load-in-4bit        # 4-bit 量化
  --load-in-8bit        # 8-bit 量化 (与4-bit互斥)
```

### B. 环境变量

```bash
# HuggingFace 缓存目录
export HF_HOME=/path/to/cache

# Transformers 缓存
export TRANSFORMERS_CACHE=/path/to/cache

# CUDA 设备
export CUDA_VISIBLE_DEVICES=0

# 代理设置
export HTTP_PROXY=http://proxy:8080
export HTTPS_PROXY=http://proxy:8080
```

### C. 项目文件结构

```
news-qwen/
├── api_server.py                 # API 服务主文件
├── transformers_inference.py     # 直接推理脚本
├── api_client_example.py         # API 客户端示例
├── config.yaml                   # 配置文件
├── requirements.txt              # Python 依赖
├── API_GUIDE.md                  # API 使用指南
├── TECHNICAL_DOCUMENTATION.md    # 技术文档 (本文件)
│
├── Scripts/
│   ├── process_news_by_trading_week.py   # 新闻处理脚本
│   ├── aggregate_news_events.py          # 事件聚合脚本
│   └── README.md                         # 脚本说明
│
├── Events/                       # 输出目录 (自动创建)
│   └── *.csv                     # 生成的事件 CSV
│
└── data/                         # 数据目录 (用户创建)
    └── *.csv                     # 输入新闻 CSV
```

### D. 技术术语表

| 术语 | 说明 |
|------|------|
| **LLM** | Large Language Model (大语言模型) |
| **Quantization** | 量化，降低模型精度以节省显存 |
| **4-bit NF4** | NormalFloat 4-bit 量化，平衡精度和显存 |
| **BitsAndBytes** | CUDA 量化库 |
| **Device Map** | 设备映射，自动分配模型层到 GPU/CPU |
| **Token** | 令牌，文本的最小单位 |
| **Temperature** | 温度参数，控制生成随机性 (0-2) |
| **Top-p** | 核采样，控制生成多样性 (0-1) |
| **Trading Week** | 交易周期，周五至周五 |
| **Event Summary** | 事件摘要，LLM 生成的新闻总结 |
| **Hierarchical Merge** | 分层合并，防止大批次 OOM |

### E. 参考资源

- **Qwen 官方文档**: https://github.com/QwenLM/Qwen
- **Transformers 文档**: https://huggingface.co/docs/transformers
- **BitsAndBytes**: https://github.com/TimDettmers/bitsandbytes
- **FastAPI 文档**: https://fastapi.tiangolo.com/
- **Pandas 文档**: https://pandas.pydata.org/docs/

---

## 更新日志

### v1.0 (2025-12-07)

- ✅ 初始版本
- ✅ 默认使用 Qwen2.5-3B 模型
- ✅ 默认启用 4-bit 量化
- ✅ API 服务完整实现
- ✅ 新闻按交易周期处理
- ✅ 分层合并策略防止 OOM
- ✅ 完整文档和示例

---

**文档结束**

如有任何问题，请查阅故障排除章节或联系技术支持。
