# 新闻事件聚合脚本使用说明

## 功能简介

`aggregate_news_events.py` 脚本用于将新闻按交易周聚合，并使用 Qwen 大模型识别和总结重要事件。

## 核心功能

1. **交易周划分**：自动按美国股市交易周划分新闻（周五收盘16:00 ET为周期结束）
2. **智能聚合**：考虑新闻来源权重，过滤噪音新闻
3. **事件识别**：使用 Qwen 模型识别主要事件，去除重复报道
4. **量化评估**：计算事件聚集度（0-1分数）和价格影响

## 交易周划分规则

- **周期**：周五美东时间16:00收盘后 → 下周五16:00收盘
- **时区**：自动处理夏令时（3月-11月）和冬令时切换
- **美东时间**：
  - 夏令时：UTC-4
  - 冬令时：UTC-5

## 新闻来源权重

脚本内置了主流财经媒体的权重评分：

| 来源 | 权重 |
|------|------|
| Bloomberg / Reuters | 1.0 |
| Wall Street Journal / Financial Times | 0.95 |
| CNBC | 0.85 |
| Yahoo Finance / MarketWatch | 0.75 |
| Seeking Alpha | 0.65 |
| Moomoo News / Benzinga | 0.6 |
| The Motley Fool | 0.5 |
| 其他 | 0.5 |

## 使用方法

### 1. 测试单个股票（推荐先测试）

```bash
# 激活环境
conda activate news-qwen

# 处理 AAL 股票（测试模式，只处理第一周）
python Scripts/aggregate_news_events.py \
    --model-path D:/models/Qwen2.5-7B-Instruct \
    --stock AAL \
    --test
```

### 2. 处理单个股票的所有数据

```bash
python Scripts/aggregate_news_events.py \
    --model-path D:/models/Qwen2.5-7B-Instruct \
    --stock AAL
```

### 3. 批量处理所有股票

```bash
python Scripts/aggregate_news_events.py \
    --model-path D:/models/Qwen2.5-7B-Instruct \
    --all
```

## 参数说明

- `--model-path`: Qwen 模型路径（必需）
- `--stock`: 要处理的股票代码（默认 AAL）
- `--all`: 处理 News 文件夹下所有股票
- `--test`: 测试模式，每个股票只处理第一周（默认开启）

## 输出格式

脚本会在 `Events/{股票代码}/` 文件夹下生成 `{股票代码}_events.csv`，包含以下字段：

| 字段 | 说明 |
|------|------|
| stock_symbol | 股票代码 |
| stock_name | 股票名称 |
| week_start | 交易周开始时间 |
| week_end | 交易周结束时间 |
| event_summary | 事件总结（简洁描述） |
| earliest_time | 事件最早发生时间 |
| concentration_score | 聚集程度（0-1） |
| related_news_count | 相关新闻数量 |
| total_news_count | 本周总新闻数量 |
| weighted_concentration | 加权聚集度（考虑来源权重） |
| chg_in_5 | 未来5天价格变化 |
| chg_in_10 | 未来10天价格变化 |

## 输出示例

```csv
stock_symbol,stock_name,week_start,week_end,event_summary,earliest_time,concentration_score,related_news_count,total_news_count,weighted_concentration,chg_in_5,chg_in_10
AAL,American Airlines,2024-11-04,2024-11-08 16:00:00,"摩根士丹利维持买入评级，目标价$18，超预期业绩推动",2024-11-07 06:31:00,0.85,5,8,0.78,3.2,5.1
```

## 工作流程

1. **读取数据**：加载 `News/{股票代码}.csv`
2. **周期划分**：根据美国股市交易时间自动分周
3. **构建 Prompt**：为每周新闻生成分析提示
4. **模型推理**：使用 Qwen 7B (4bit) 分析事件
5. **结果解析**：提取 JSON 格式的分析结果
6. **保存输出**：生成 `Events/{股票代码}/{股票代码}_events.csv`

## 系统要求

- **Python**: 3.10+
- **GPU 显存**: 至少 8GB（4bit量化）
- **依赖包**:
  - transformers >= 4.40.0
  - torch (CUDA版本)
  - pandas
  - pytz
  - bitsandbytes

## 注意事项

1. **首次运行**：建议使用 `--test` 模式先测试一个股票的第一周
2. **处理时间**：根据新闻数量，每周约需 5-15 秒
3. **显存占用**：4bit 量化后约占用 4-6GB 显存
4. **错误处理**：如果某周解析失败，会记录日志并使用默认值

## 故障排除

### 问题1：模型加载失败

```bash
# 确认模型路径正确
ls D:/models/Qwen2.5-7B-Instruct

# 应该看到：config.json, model.safetensors 等文件
```

### 问题2：显存不足

- 确保没有其他程序占用GPU
- 尝试关闭其他应用释放显存
- 检查 GPU 显存：`nvidia-smi`

### 问题3：CSV 读取错误

- 确认 `News/` 文件夹存在
- 确认 CSV 文件包含必需列：symbol, name, date, title, source

## 下一步优化

- [ ] 添加进度条显示
- [ ] 支持断点续传
- [ ] 并行处理多个股票
- [ ] 添加结果验证和质量检查
- [ ] 支持自定义新闻来源权重

## 联系方式

如有问题，请提交 Issue 到项目仓库。
