# 事件驱动型新闻分析脚本使用指南

## 脚本概述

`extract_news_events.py` 是一个专门设计的事件驱动型股票新闻分析工具，使用 Qwen2.5-3B 大语言模型从新闻数据中提取对股价有**重大影响**的事件。

## 核心特性

### 1. 模型配置

- **模型**: Qwen2.5-3B-Instruct
- **量化**: 默认 4-bit (NF4) 量化
- **显存需求**: 约 2-3GB
- **上下文长度**: 32K tokens
- **实际输入能力**:
  - 中文: 约 24,000-28,000 字
  - 英文: 约 24,000 词
  - 脚本设置单批次上限: 15,000 字符 (保守值)

### 2. 周期定义

**与之前脚本的重要区别**:
- 之前: 周五到周五
- **现在: 上周六 00:00 - 下周五 23:59**

#### 周期计算示例

```
输入日期: 2024-11-13 (周三)

计算逻辑:
1. 找上周六: 2024-11-09 (周六) 00:00:00
2. 找下周五: 2024-11-15 (周五) 23:59:59

周期: 2024-11-09 至 2024-11-15
```

更多示例:
```
2024-11-07 (周四) → 周期: 2024-11-02 (六) 至 2024-11-08 (五)
2024-11-08 (周五) → 周期: 2024-11-02 (六) 至 2024-11-08 (五)
2024-11-09 (周六) → 周期: 2024-11-09 (六) 至 2024-11-15 (五)
2024-11-10 (周日) → 周期: 2024-11-09 (六) 至 2024-11-15 (五)
```

### 3. 智能分批处理

脚本会自动检测新闻数据量:

- **数据量 < 15,000 字符**: 单批次处理
- **数据量 > 15,000 字符**: 自动分批处理
  - 每批次不超过 15,000 字符
  - 批次间的事件会自动合并去重

### 4. 事件提取逻辑

#### 提取标准 (只关注重大事件)

✅ **提取这些**:
- 财报发布 (业绩超预期/不及预期)
- 重大合同、订单、合作
- 产品发布、技术突破
- 并购、重组、分拆
- 监管行动、诉讼裁决
- 高管变动、战略调整
- 重大投资、融资
- 行业政策变化 (直接影响公司)

❌ **排除这些**:
- 单纯的分析师评级调整 ("XX维持买入评级")
- 预测性内容 ("预计将..."、"可能会...")
- 市场情绪、技术分析
- 无实质内容的消息

#### 事件归类

脚本会智能归类相关新闻:

```
示例 1: 财报相关
- "Apple Reports Q4 Results" (11-08 10:55)
- "Apple Beats Earnings Estimates" (11-08 11:20)
- "Apple Q4 Revenue Up 6%" (11-08 14:30)
→ 归类为 1 个 "Q4财报" 事件, related_count=3

示例 2: 产品发布
- "Apple Announces iPhone 16" (11-10 09:00)
- "iPhone 16 Features AI Chip" (11-10 09:15)
→ 归类为 1 个 "iPhone 16发布" 事件, related_count=2
```

### 5. Prompt 设计

脚本使用精心设计的两阶段 prompt:

**阶段 1: 事件提取** (`EVENT_ANALYSIS_PROMPT`)
- 强调"事实优先"、"重大影响"
- 明确排除分析师评级、预测性内容
- 要求区分事实和观点
- 要求归类相关新闻
- 输出结构化 JSON

**阶段 2: 事件合并** (`MERGE_EVENTS_PROMPT`)
- 检测跨批次的重复事件
- 智能合并相关事件
- 保持数据一致性

## 数据格式

### 输入 CSV 格式

**必需列**:
| 列名 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `symbol` | string | 股票代码 | "AAPL" |
| `name` | string | 公司名称 | "Apple Inc." |
| `date` | datetime | 新闻日期时间 | "2024-11-08 10:55:00" |
| `title` | string | 新闻标题 | "Apple Reports Q4 Results" |
| `source` | string | 新闻来源 | "Apple Newsroom" |

**可选列** (会被使用):
| 列名 | 类型 | 说明 |
|------|------|------|
| `chg_in_5` | float | 5日涨跌幅 (%) |
| `chg_in_10` | float | 10日涨跌幅 (%) |

**示例输入**:
```csv
symbol,name,date,timestamp,previous,adj_date,date+5td,chg_in_5,chg_in_10,symbol_code,title,link,source
AAPL,Apple Inc.,2024-11-08 10:55:00,1699441200,145.23,2024-11-08,2024-11-15,2.5,5.3,AAPL,"Apple Reports Fourth Quarter Results",https://...,Apple Newsroom
AAPL,Apple Inc.,2024-11-08 11:20:00,1699442000,145.23,2024-11-08,2024-11-15,2.5,5.3,AAPL,"Apple Beats Earnings Estimates",https://...,Bloomberg
```

### 输出 CSV 格式

| 列名 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `symbol` | string | 股票代码 | "AAPL" |
| `name` | string | 公司名称 | "Apple Inc." |
| `period_start` | date | 周期开始日期 | "2024-11-02" |
| `period_end` | date | 周期结束日期 | "2024-11-08" |
| `event_start` | datetime | 最早提及该事件的新闻时间 | "2024-11-08 10:55:00" |
| `event_end` | datetime | 最晚提及该事件的新闻时间 | "2024-11-08 14:30:00" |
| `event_description` | string | 高度概括的事件描述 | "苹果公布2024财年Q4财报..." |
| `earliest_news` | string | 最早新闻的标题 | "Apple Reports Fourth Quarter Results" |
| `related_count` | integer | 相关新闻数量 | 5 |
| `chg_in_5` | float | 5日涨跌幅 (earliest_news对应) | 2.5 |
| `chg_in_10` | float | 10日涨跌幅 (earliest_news对应) | 5.3 |
| `source` | string | 新闻来源 (earliest_news对应) | "Apple Newsroom" |

**示例输出**:
```csv
symbol,name,period_start,period_end,event_start,event_end,event_description,earliest_news,related_count,chg_in_5,chg_in_10,source
AAPL,Apple Inc.,2024-11-02,2024-11-08,2024-11-08 10:55:00,2024-11-08 14:30:00,"苹果公布2024财年Q4财报，营收949亿美元同比增长6%，iPhone营收463亿美元超预期，净利润147亿美元。财报显示服务业务持续增长，但大中华区营收下降。整体业绩超华尔街预期，股价影响偏正面。",Apple Reports Fourth Quarter Results,5,2.5,5.3,Apple Newsroom
```

## 使用方法

### 基本用法

```bash
# AAPL 示例
python Scripts/extract_news_events.py \
    --input "D:\GitHub\LocalFinData\data\news\AAPL.csv" \
    --output-dir "D:\GitHub\LocalFinData\data\events"
```

### 完整参数

```bash
python Scripts/extract_news_events.py \
    --input "D:\GitHub\LocalFinData\data\news\AAPL.csv" \
    --output-dir "D:\GitHub\LocalFinData\data\events" \
    --model-path "D:/models/qwen2.5-3b" \
    --device auto \
    --max-tokens 2048
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | ✅ | 无 | 输入 CSV 文件路径 |
| `--output-dir` | ❌ | `D:\GitHub\LocalFinData\data\events` | 输出目录 |
| `--model-path` | ❌ | `D:/models/qwen2.5-3b` (Windows) | 模型路径 |
| `--device` | ❌ | `auto` | 设备 (auto/cuda/cpu) |
| `--max-tokens` | ❌ | 2048 | 最大生成 tokens |

### CPU 模式运行

如果 GPU 显存不足:

```bash
python Scripts/extract_news_events.py \
    --input "D:\GitHub\LocalFinData\data\news\AAPL.csv" \
    --device cpu
```

**注意**: CPU 模式较慢，但可用于测试。

## 运行示例

### 完整运行日志示例

```
============================================================
事件驱动型新闻分析脚本
============================================================
模型: Qwen2.5-3B (4-bit 量化)
模型路径: D:/models/qwen2.5-3b
输入文件: D:\GitHub\LocalFinData\data\news\AAPL.csv
输出目录: D:\GitHub\LocalFinData\data\events
设备: auto
模型上下文: 32K tokens (约 15,000-28,000 字)
============================================================
正在加载模型: D:/models/qwen2.5-3b
使用 4-bit 量化 (NF4)
模型加载完成!
模型上下文长度: 32K tokens
建议单批次输入上限: 15000 字符 (约 20000 tokens)

正在读取数据: D:\GitHub\LocalFinData\data\news\AAPL.csv
股票代码: AAPL
公司名称: Apple Inc.
新闻总数: 856
日期范围: 2024-01-05 08:30:00 至 2024-11-15 18:45:00

共有 45 个周期

============================================================
周期: 2024-01-06 (Saturday) 至 2024-01-12 (Friday)
新闻数量: 18
  单批次处理 18 条新闻...
提取了 2 个重大事件

============================================================
周期: 2024-01-13 (Saturday) 至 2024-01-19 (Friday)
新闻数量: 15
  单批次处理 15 条新闻...
提取了 1 个重大事件

...

============================================================
周期: 2024-11-09 (Saturday) 至 2024-11-15 (Friday)
新闻数量: 25
  单批次处理 25 条新闻...
提取了 3 个重大事件

============================================================
✅ 处理完成!
总共提取了 87 个事件
输出文件: D:\GitHub\LocalFinData\data\events\AAPL.csv
```

## 工作流程

```
1. 读取新闻 CSV
   ↓
2. 转换日期格式
   ↓
3. 计算每条新闻的周期 (上周六-下周五)
   ↓
4. 按周期分组
   ↓
5. 对每个周期:
   ├─ 格式化新闻数据
   ├─ 检查数据量
   ├─ 如果 < 15K 字符:
   │   └─ 单批次分析 → 提取事件
   └─ 如果 > 15K 字符:
       ├─ 分批分析 → 提取事件
       └─ 合并批次事件 → 去重
   ↓
6. 汇总所有事件
   ↓
7. 保存到输出 CSV
```

## 提示与最佳实践

### 1. 数据准备

✅ **建议**:
- 确保新闻标题完整且有意义
- 包含 `chg_in_5` 和 `chg_in_10` 数据 (可选但推荐)
- 新闻来源 `source` 填写完整

❌ **避免**:
- 标题过于简短或模糊
- 日期格式不正确
- 缺少必需列

### 2. 输出解读

**高质量事件的特征**:
- `event_description` 包含具体数据
- 明确的情感倾向 (正面/负面/中性)
- `related_count` > 1 (表示多条新闻验证)

**需要人工审核的情况**:
- `related_count` = 1 且描述模糊
- 事件时间跨度过大 (event_start 和 event_end 相差超过 7 天)

### 3. 性能优化

**加快处理速度**:
```bash
# 1. 确保使用 GPU
python Scripts/extract_news_events.py --input ... --device cuda

# 2. 减少生成长度 (如果不需要详细描述)
python Scripts/extract_news_events.py --input ... --max-tokens 1024
```

**降低显存占用**:
- 默认已使用 4-bit 量化 (最低显存)
- 如果仍不够，使用 CPU 模式

### 4. 批量处理多只股票

创建批处理脚本:

```bash
# process_all_stocks.sh
#!/bin/bash

STOCKS=("AAPL" "MSFT" "GOOGL" "AMZN" "TSLA")

for stock in "${STOCKS[@]}"; do
    echo "Processing $stock..."
    python Scripts/extract_news_events.py \
        --input "D:/GitHub/LocalFinData/data/news/$stock.csv" \
        --output-dir "D:/GitHub/LocalFinData/data/events"
done
```

## 故障排除

### 问题 1: 模型路径错误

**错误**:
```
FileNotFoundError: 模型路径不存在
```

**解决**:
```bash
# 检查路径
python -c "import os; print(os.path.exists('D:/models/qwen2.5-3b'))"

# 或手动指定
python Scripts/extract_news_events.py \
    --input ... \
    --model-path "你的实际路径"
```

### 问题 2: CUDA OOM

**错误**:
```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**解决**:
```bash
# 使用 CPU 模式
python Scripts/extract_news_events.py --input ... --device cpu
```

### 问题 3: JSON 解析失败

**现象**: 日志显示 "警告: 无法解析 JSON 响应"

**原因**: LLM 输出格式不符合预期

**解决**:
- 脚本会自动尝试多种解析方法
- 如果仍失败，检查生成的文本 (会打印前 500 字符)
- 可能需要调整 temperature 参数 (当前为 0.3)

### 问题 4: 未提取到事件

**现象**: 所有周期都显示 "未提取到重大事件"

**可能原因**:
1. 新闻确实不包含重大事件 (只有分析师评级等)
2. Prompt 过于严格
3. 模型未正确理解任务

**解决**:
- 检查输入新闻质量
- 查看脚本中的 `EVENT_ANALYSIS_PROMPT`，可以适当调整标准
- 尝试几个已知有重大事件的日期范围

## 与量化策略集成

### 示例: 事件驱动回测

```python
import pandas as pd

# 读取事件数据
events_df = pd.read_csv('D:/GitHub/LocalFinData/data/events/AAPL.csv')

# 读取股价数据
prices_df = pd.read_csv('D:/GitHub/LocalFinData/data/prices/AAPL.csv')
prices_df['date'] = pd.to_datetime(prices_df['date'])

# 分析事件对股价的影响
for _, event in events_df.iterrows():
    event_date = pd.to_datetime(event['event_start']).date()

    # 获取事件日期的股价
    price_on_event = prices_df[prices_df['date'] == event_date]

    if not price_on_event.empty:
        # 计算事件后 N 日收益
        future_prices = prices_df[prices_df['date'] > event_date].head(5)
        if not future_prices.empty:
            returns = (future_prices['close'].iloc[-1] / price_on_event['close'].iloc[0] - 1) * 100
            print(f"事件: {event['event_description'][:50]}...")
            print(f"5日收益: {returns:.2f}%")
            print()
```

## 高级定制

### 修改事件提取标准

编辑 `extract_news_events.py` 中的 `EVENT_ANALYSIS_PROMPT`:

```python
# 行 35-90
EVENT_ANALYSIS_PROMPT = """
你是一位专业的事件驱动型股票交易策略分析师...

# 在这里修改:
# 1. 提取标准 (第 2 点)
# 2. 事件归类逻辑 (第 3 点)
# 3. 排除内容 (第 4 点)
"""
```

### 修改周期定义

如果需要其他周期定义，修改 `calculate_week_period()` 函数:

```python
# 行 143-183
def calculate_week_period(date: pd.Timestamp) -> tuple:
    """
    当前: 上周六 - 下周五
    可修改为其他周期
    """
    # 在这里修改计算逻辑
```

### 调整批次大小

修改常量:

```python
# 行 20-21
MAX_INPUT_TOKENS = 20000  # 减小可降低 OOM 风险
MAX_INPUT_CHARS = 15000   # 减小可降低 OOM 风险
```

## 总结

这个脚本专门为事件驱动型交易策略设计，具有以下优势:

✅ **智能事件提取**: 只关注对股价有重大影响的事件
✅ **自动归类**: 将相关新闻归为同一事件
✅ **分批处理**: 自动处理大量新闻数据
✅ **结构化输出**: 便于后续量化分析
✅ **低显存需求**: 4-bit 量化，仅需 2-3GB 显存

适合用于:
- 事件驱动型量化策略
- 新闻情感分析
- 基本面事件研究
- 股票事件日历构建

---

**开始使用**: 运行 AAPL 测试
```bash
python Scripts/extract_news_events.py \
    --input "D:\GitHub\LocalFinData\data\news\AAPL.csv" \
    --output-dir "D:\GitHub\LocalFinData\data\events"
```
