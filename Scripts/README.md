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

---

## process_news_by_trading_week.py

**按交易周期处理新闻事件脚本** - 读取新闻CSV文件，按交易周期（周五到周五）分组，使用大模型分析并生成事件摘要CSV文件。

### 功能特点

- ✅ **自动识别交易周期**：周五收盘后到下周五收盘前为一个周期
- ✅ **智能分批处理**：自动将大量新闻分批送入大模型分析
- ✅ **结果自动合并**：多批次分析结果智能合并为统一摘要
- ✅ **CSV输出**：结果保存为CSV文件，便于后续分析
- ✅ **可自定义Prompt**：在脚本中修改分析提示词模板
- ✅ **支持量化**：4-bit/8-bit量化降低显存需求

### 使用方法

#### 基本用法

```bash
# 使用4-bit量化处理新闻文件
python Scripts/process_news_by_trading_week.py \
    --input news_data.csv \
    --model-path D:/models/qwen2.5-7b \
    --load-in-4bit

# 指定输出目录
python Scripts/process_news_by_trading_week.py \
    --input news_data.csv \
    --model-path D:/models/qwen2.5-7b \
    --output-dir ./Events \
    --load-in-4bit
```

#### 使用8-bit量化

```bash
python Scripts/process_news_by_trading_week.py \
    --input news_data.csv \
    --model-path D:/models/qwen2.5-7b \
    --load-in-8bit
```

#### 使用CPU（无量化）

```bash
python Scripts/process_news_by_trading_week.py \
    --input news_data.csv \
    --model-path D:/models/qwen2.5-7b \
    --device cpu
```

### 输入CSV格式

脚本需要包含以下列的CSV文件：

| 列名 | 说明 | 必需 |
|------|------|------|
| `symbol` | 股票代码 | 是 |
| `name` | 公司名称 | 是 |
| `date` | 新闻日期时间 | 是 |
| `title` | 新闻标题 | 是 |
| `source` | 新闻来源 | 否 |
| `chg_in_5` | 5日涨跌幅 | 否 |
| `chg_in_10` | 10日涨跌幅 | 否 |

示例：
```csv
symbol,name,date,title,source,chg_in_5,chg_in_10
AAL,American Airlines,2024-11-07 06:31:00,"Morgan Stanley Maintains AAL",Moomoo News,2.5,5.3
```

### 输出CSV格式

生成的CSV文件包含以下列：

| 列名 | 说明 |
|------|------|
| `symbol` | 股票代码 |
| `name` | 公司名称 |
| `start_date` | 交易周期开始日期 |
| `end_date` | 交易周期结束日期 |
| `chg_in_5` | 5日平均涨跌幅 |
| `chg_in_10` | 10日平均涨跌幅 |
| `event_details` | 大模型生成的事件摘要 |

输出文件保存在 `Events/` 目录下，文件名格式：`{输入文件名}_events_{时间戳}.csv`

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | 是 | - | 输入CSV文件路径 |
| `--model-path` | 是 | - | 模型路径 |
| `--output-dir` | 否 | Events | 输出目录 |
| `--device` | 否 | auto | 设备选择 |
| `--max-tokens` | 否 | 512 | 最大生成令牌数 |
| `--load-in-4bit` | 否 | False | 使用4-bit量化 |
| `--load-in-8bit` | 否 | False | 使用8-bit量化 |

### 自定义分析Prompt

您可以在脚本顶部的**配置区域**修改Prompt模板：

```python
# ==================== PROMPT 模板配置区域 ====================

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

# 单批次处理的最大新闻条数（根据您的GPU显存调整）
MAX_NEWS_PER_BATCH = 15  # 可以调整这个值

# ==================== 结束配置区域 ====================
```

**修改位置**：
1. **Prompt模板**：修改 `ANALYSIS_PROMPT_TEMPLATE` 变量（第26-40行左右）
2. **批次大小**：修改 `MAX_NEWS_PER_BATCH` 变量（第42-46行左右）

**建议批次大小**：
- 4-bit量化：10-20条新闻/批次
- 8-bit量化：8-15条新闻/批次
- 无量化：5-10条新闻/批次

### 交易周期计算逻辑

脚本使用以下逻辑计算交易周期：

- **周一至周五**的新闻 → 归入**上周五至本周五**
- **周六至周日**的新闻 → 归入**本周五至下周五**

示例：
- 2024-11-07（周四）的新闻 → 交易周期：2024-11-01（上周五）至 2024-11-08（本周五）
- 2024-11-09（周六）的新闻 → 交易周期：2024-11-08（本周五）至 2024-11-15（下周五）

### 工作流程

1. **读取CSV** → 加载新闻数据
2. **分组** → 按交易周期分组新闻
3. **批次处理** → 如果单周期新闻过多，自动分批
4. **大模型分析** → 每个批次交给Qwen分析
5. **合并结果** → 多批次结果智能合并
6. **保存CSV** → 输出到Events文件夹

### 示例输出

```csv
symbol,name,start_date,end_date,chg_in_5,chg_in_10,event_details
AAL,American Airlines,2024-11-01,2024-11-08,2.5,5.3,"美国航空本周获多家机构维持买入评级，目标价18美元。公司公布Q3财报超预期，营收增长12%达XX亿美元。燃油成本上涨对盈利构成压力。整体情感偏正面。"
```

### 性能优化建议

1. **使用4-bit量化** - 显存需求降至3-4GB，适合大多数GPU
2. **调整批次大小** - 根据GPU显存调整 `MAX_NEWS_PER_BATCH`
3. **减少max-tokens** - 如果不需要很长的摘要，可以设为256或384

### 依赖要求

除了基本依赖外，还需要：

```bash
pip install pandas
pip install bitsandbytes  # 用于量化，Windows用户可能需要 bitsandbytes-windows
```
