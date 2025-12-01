# Scripts Directory

This directory contains utility scripts for the news-qwen project.

## aggregate_news_events.py

新闻事件聚合脚本 - 使用 Qwen 模型分析和聚合新闻事件。

### 功能特点

- 支持本地模型路径（Windows 和 Linux）
- 支持 HuggingFace 模型 ID
- 自动检测 CUDA/CPU 设备
- JSON 格式输出
- 测试模式（内置示例数据）

### 使用方法

#### 基本用法（测试模式）

```bash
# Windows
python Scripts/aggregate_news_events.py --model-path D:/models/Qwen2.5-7B-Instruct --stock AAL --test

# Linux/Mac
python Scripts/aggregate_news_events.py --model-path ~/models/Qwen2.5-7B-Instruct --stock AAPL --test
```

#### 指定设备

```bash
# 使用 CUDA
python Scripts/aggregate_news_events.py --model-path D:/models/Qwen2.5-7B-Instruct --stock AAL --test --device cuda

# 使用 CPU
python Scripts/aggregate_news_events.py --model-path D:/models/Qwen2.5-7B-Instruct --stock AAL --test --device cpu
```

#### 保存结果到文件

```bash
python Scripts/aggregate_news_events.py \
    --model-path D:/models/Qwen2.5-7B-Instruct \
    --stock AAL \
    --test \
    --output results/aal_analysis.json
```

#### 使用 HuggingFace 模型

```bash
python Scripts/aggregate_news_events.py \
    --model-path Qwen/Qwen2.5-7B-Instruct \
    --stock AAL \
    --test
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--model-path` | 是 | - | 模型路径（本地路径或 HuggingFace ID）|
| `--stock` | 是 | - | 股票代码（如 AAL, AAPL）|
| `--device` | 否 | auto | 设备选择（auto/cuda/cpu）|
| `--max-tokens` | 否 | 2048 | 最大生成令牌数 |
| `--test` | 否 | False | 使用测试数据 |
| `--output` | 否 | - | 输出文件路径（JSON）|

### 输出格式

```json
{
  "summary": [
    "主要事件1",
    "主要事件2",
    "主要事件3"
  ],
  "sentiment": "正面/中性/负面",
  "impact": "对股价的影响分析",
  "confidence": 0.85,
  "stock": "AAL",
  "news_count": 4,
  "timestamp": "2024-10-25T10:30:00"
}
```

### 测试数据

脚本内置了以下股票的测试数据：

- **AAL** (American Airlines) - 4条新闻
- **AAPL** (Apple Inc.) - 3条新闻

其他股票代码将使用通用测试数据。

### 故障排除

#### Windows 路径问题

如果遇到路径识别错误，请确保：

1. 使用正斜杠 `/` 而不是反斜杠 `\`（如 `D:/models/...`）
2. 或使用双反斜杠 `\\`（如 `D:\\models\\...`）
3. 模型文件完整存在于指定路径

#### CUDA 内存不足

如果遇到 CUDA OOM 错误：

```bash
# 使用 CPU
python Scripts/aggregate_news_events.py --model-path ... --stock AAL --test --device cpu

# 或减少 max-tokens
python Scripts/aggregate_news_events.py --model-path ... --stock AAL --test --max-tokens 1024
```

### 依赖要求

- Python 3.8+
- PyTorch
- Transformers
- 其他依赖见项目根目录的 `requirements.txt`

### 后续开发

实时新闻获取功能正在开发中。当前版本仅支持测试模式（`--test`）。
