#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件驱动型新闻分析脚本 - CPU 版本
不需要 BitsAndBytes，可以在任何环境运行（但速度较慢）
"""

import os
import sys
import argparse
import pandas as pd
import torch
from datetime import datetime, timedelta
from pathlib import Path
import platform
import json
import re

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformers import AutoModelForCausalLM, AutoTokenizer

# ==================== 模型配置 ====================

MAX_INPUT_TOKENS = 20000
MAX_INPUT_CHARS = 15000

# [保持与原脚本相同的 PROMPT 定义]
EVENT_ANALYSIS_PROMPT = """你是一位专业的事件驱动型股票交易策略分析师。你的任务是从新闻数据中提取对股价有**重大影响**的事件。

**分析对象**: {symbol} ({name})
**分析周期**: {period_start} 至 {period_end}
{batch_info}

**新闻数据**:
{news_data}

**分析要求**:

1. **事实优先**: 只关注已发生的事实性事件，忽略预测、观点、分析师评级变化

2. **重大影响**: 只提取对股价有实质性影响的事件。分为以下类型：

   **A. 常规重大事件**:
   - 财报发布（业绩超预期/不及预期）
   - 重大合同、订单、合作
   - 产品发布、技术突破
   - 并购、重组、分拆
   - 监管行动、诉讼裁决
   - 高管变动、战略调整
   - 重大投资、融资

   **B. 黑天鹅/突发事件** (⚠️ 重点关注):
   - 安全事故（工厂爆炸、火灾、重大伤亡、数据泄露）
   - 产品质量危机（大规模召回、严重安全漏洞、致命缺陷）
   - 供应链中断（关键供应商倒闭/停产、原材料断供）
   - 网络安全事件（黑客攻击、系统瘫痪、勒索软件）
   - 自然灾害影响（地震、洪水、疫情导致的停产/关闭）
   - 竞争对手的颠覆性举动（可能改变市场格局）

   **C. 舆情/声誉危机** (⚠️ 重点关注):
   - 公关危机（CEO/高管丑闻、企业不当行为曝光）
   - 大规模消费者抵制运动
   - 病毒式传播的负面舆论（社交媒体风暴）
   - 重大劳工纠纷（大规模罢工、工会冲突）
   - 环境污染事故或ESG重大争议
   - 虚假广告、欺诈指控

   **D. 政治/地缘/监管风险** (⚠️ 重点关注):
   - 贸易政策突变（关税加征、贸易禁令）
   - 政府制裁、出口管制
   - 地缘政治冲突直接影响（战争、外交危机）
   - 行业监管政策突然收紧/放松
   - 反垄断调查、政府介入
   - 国家安全审查、强制剥离资产
   - 重大政策变化（税收、补贴、行业准入）

   **判断标准**:
   - 事件是否会导致股价**单日波动 > 5%**？
   - 事件是否会影响公司**未来 1-2 个季度的业绩**？
   - 事件是否会改变市场对公司的**长期预期**？

   如果答案是"是"，则提取；否则忽略。

3. **事件归类**: 将相关新闻归为同一事件，例如：
   - 多条新闻报道同一财报 → 归为一个"Q3财报"事件
   - 多条新闻提到同一产品发布 → 归为一个"产品发布"事件

4. **排除内容**:
   - 单纯的分析师评级调整（如"XX维持买入评级"）
   - 预测性内容（"预计将..."、"可能会..."）
   - 市场情绪、技术分析
   - 无实质内容的消息

5. **情感色彩**: 判断事件对股价的影响（正面/中性/负面）

**输出格式** (JSON数组，每个事件一个对象):

```json
[
  {{
    "event_start": "2024-11-08 10:55:00",
    "event_end": "2024-11-09 15:30:00",
    "event_description": "苹果公布2024财年Q4财报，营收949亿美元同比增长6%，iPhone营收463亿美元超预期，净利润147亿美元。财报显示服务业务持续增长，但大中华区营收下降。整体业绩超华尔街预期，股价影响偏正面。",
    "earliest_news_title": "Apple Reports Fourth Quarter Results",
    "earliest_news_date": "2024-11-08 10:55:00",
    "related_count": 5,
    "chg_in_5": 2.5,
    "chg_in_10": 5.3,
    "source": "Apple Newsroom"
  }}
]
```

**重要**:
- 如果本批次新闻中没有符合条件的重大事件，返回空数组: []
- 只返回JSON数组，不要任何其他文字
- event_description 需要高度概括，包含关键数据和情感倾向
- earliest_news_title、earliest_news_date、chg_in_5、chg_in_10、source 必须来自实际新闻数据
- related_count 是被归类到该事件的新闻条数

请开始分析:"""

MERGE_EVENTS_PROMPT = """你是一位专业的事件驱动型股票交易策略分析师。现在需要合并多个批次分析得到的事件。

**分析对象**: {symbol} ({name})
**分析周期**: {period_start} 至 {period_end}

**各批次提取的事件**:
{events_json}

**任务**:
1. 检查是否有重复或相关的事件需要合并
2. 如果多个事件实际上是同一事件，合并它们：
   - 使用最早的 event_start
   - 使用最晚的 event_end
   - 合并 event_description（保持简洁，150字内）
   - 使用最早的新闻作为 earliest_news
   - related_count 为所有相关事件的 related_count 之和
   - chg_in_5, chg_in_10, source 使用 earliest_news 对应的值

3. 如果事件确实是不同的事件，保持分离

**输出格式**:
返回合并后的JSON数组，格式同输入。只返回JSON，不要其他文字。

合并后的事件:"""


def get_model_path():
    """获取默认模型路径"""
    system = platform.system()
    if system == "Windows":
        return "D:/models/qwen2.5-3b"
    else:
        return str(Path.home() / "models" / "qwen2.5-3b")


def load_model_cpu(model_path: str):
    """
    加载 Qwen 模型到 CPU (无量化)

    Args:
        model_path: 模型路径

    Returns:
        model, tokenizer
    """
    print(f"正在加载模型: {model_path}")
    print(f"⚠️  CPU 模式 (无量化) - 速度较慢但兼容性好")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型路径不存在: {model_path}")

    # 加载 tokenizer
    print("加载 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True
    )

    # 加载模型到 CPU
    print("加载模型到 CPU (这可能需要 2-5 分钟)...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="cpu",
        trust_remote_code=True,
        torch_dtype=torch.float32,  # CPU 使用 float32
        low_cpu_mem_usage=True
    )

    print(f"✅ 模型加载完成!")
    print(f"模型上下文长度: 32K tokens")
    print(f"建议单批次输入上限: {MAX_INPUT_CHARS} 字符")

    return model, tokenizer


def calculate_week_period(date: pd.Timestamp) -> tuple:
    """计算周期: 上周六 00:00 - 下周五 23:59"""
    weekday = date.weekday()

    if weekday == 6:
        days_to_last_saturday = 1
    else:
        days_to_last_saturday = (weekday + 2) % 7
        if days_to_last_saturday == 0:
            days_to_last_saturday = 7

    period_start = date - pd.Timedelta(days=days_to_last_saturday)
    period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)

    days_to_next_friday = (4 - weekday) % 7
    if days_to_next_friday == 0 and weekday != 4:
        days_to_next_friday = 7
    elif weekday == 4:
        days_to_next_friday = 0

    period_end = date + pd.Timedelta(days=days_to_next_friday)
    period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return period_start, period_end


def format_news_for_prompt(news_df: pd.DataFrame) -> str:
    """将新闻数据格式化为 prompt 输入"""
    lines = []
    for idx, row in news_df.iterrows():
        line = f"[{row['date']}] {row['title']}"
        if pd.notna(row.get('chg_in_5')):
            line += f" | 5日涨跌: {row['chg_in_5']:.2f}%"
        if pd.notna(row.get('chg_in_10')):
            line += f" | 10日涨跌: {row['chg_in_10']:.2f}%"
        if pd.notna(row.get('source')):
            line += f" | 来源: {row['source']}"
        lines.append(line)

    return "\n".join(lines)


def generate_response(model, tokenizer, prompt: str, max_tokens: int = 2048) -> str:
    """生成响应"""
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.3,
            top_p=0.8,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_text = tokenizer.decode(
        outputs[0][len(inputs["input_ids"][0]):],
        skip_special_tokens=True
    )

    del inputs, outputs

    return generated_text.strip()


def parse_events_json(response_text: str) -> list:
    """从 LLM 响应中解析 JSON 事件数组"""
    try:
        events = json.loads(response_text)
        if isinstance(events, list):
            return events
    except json.JSONDecodeError:
        pass

    json_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
    matches = re.findall(json_pattern, response_text, re.DOTALL)
    if matches:
        try:
            events = json.loads(matches[0])
            if isinstance(events, list):
                return events
        except json.JSONDecodeError:
            pass

    start_idx = response_text.find('[')
    end_idx = response_text.rfind(']')
    if start_idx != -1 and end_idx != -1:
        try:
            events = json.loads(response_text[start_idx:end_idx+1])
            if isinstance(events, list):
                return events
        except json.JSONDecodeError:
            pass

    print(f"警告: 无法解析 JSON 响应:\n{response_text[:500]}")
    return []


def analyze_period_events(
    model, tokenizer, symbol, name,
    period_start, period_end, news_df, max_tokens
):
    """分析单个周期的新闻，提取事件"""
    news_text = format_news_for_prompt(news_df)

    if len(news_text) <= MAX_INPUT_CHARS:
        prompt = EVENT_ANALYSIS_PROMPT.format(
            symbol=symbol, name=name,
            period_start=period_start.strftime('%Y-%m-%d'),
            period_end=period_end.strftime('%Y-%m-%d'),
            batch_info="", news_data=news_text
        )

        print(f"  单批次处理 {len(news_df)} 条新闻...")
        response = generate_response(model, tokenizer, prompt, max_tokens)
        events = parse_events_json(response)
        return events

    else:
        print(f"  新闻数据较大，采用分批处理...")
        num_news = len(news_df)
        batch_size = max(1, int(MAX_INPUT_CHARS / (len(news_text) / num_news)))
        batch_size = min(batch_size, num_news)

        all_events = []
        num_batches = (num_news + batch_size - 1) // batch_size

        for i in range(0, num_news, batch_size):
            batch_news = news_df.iloc[i:i+batch_size]
            batch_text = format_news_for_prompt(batch_news)

            batch_info = f"\n**注意**: 这是第 {i//batch_size + 1}/{num_batches} 批次，本批次包含 {len(batch_news)} 条新闻。"

            prompt = EVENT_ANALYSIS_PROMPT.format(
                symbol=symbol, name=name,
                period_start=period_start.strftime('%Y-%m-%d'),
                period_end=period_end.strftime('%Y-%m-%d'),
                batch_info=batch_info, news_data=batch_text
            )

            print(f"    批次 {i//batch_size + 1}/{num_batches}: {len(batch_news)} 条新闻...")
            response = generate_response(model, tokenizer, prompt, max_tokens)
            batch_events = parse_events_json(response)

            if batch_events:
                all_events.extend(batch_events)
                print(f"      提取了 {len(batch_events)} 个事件")

        if len(all_events) > 0:
            print(f"  正在合并 {len(all_events)} 个事件...")
            # 简单合并，不再调用模型
            return all_events
        else:
            return []


def process_stock_news(input_csv, output_dir, model_path, max_tokens):
    """处理股票新闻数据，提取事件"""
    model, tokenizer = load_model_cpu(model_path)

    print(f"\n正在读取数据: {input_csv}")
    df = pd.read_csv(input_csv)

    required_cols = ['symbol', 'name', 'date', 'title', 'source']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"缺少必需列: {missing_cols}")

    df['date'] = pd.to_datetime(df['date'])

    symbol = df['symbol'].iloc[0]
    name = df['name'].iloc[0]

    print(f"股票代码: {symbol}")
    print(f"公司名称: {name}")
    print(f"新闻总数: {len(df)}")
    print(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")

    df['period_start'] = df['date'].apply(lambda x: calculate_week_period(x)[0])
    df['period_end'] = df['date'].apply(lambda x: calculate_week_period(x)[1])

    periods = df.groupby(['period_start', 'period_end'])
    print(f"\n共有 {len(periods)} 个周期")

    all_events = []

    for (period_start, period_end), period_df in periods:
        print(f"\n{'='*60}")
        print(f"周期: {period_start.strftime('%Y-%m-%d')} 至 {period_end.strftime('%Y-%m-%d')}")
        print(f"新闻数量: {len(period_df)}")

        events = analyze_period_events(
            model, tokenizer, symbol, name,
            period_start, period_end, period_df, max_tokens
        )

        if events:
            print(f"提取了 {len(events)} 个重大事件")

            for event in events:
                event_row = {
                    'symbol': symbol,
                    'name': name,
                    'period_start': period_start.strftime('%Y-%m-%d'),
                    'period_end': period_end.strftime('%Y-%m-%d'),
                    'event_start': event.get('event_start', ''),
                    'event_end': event.get('event_end', ''),
                    'event_description': event.get('event_description', ''),
                    'earliest_news': event.get('earliest_news_title', ''),
                    'related_count': event.get('related_count', 1),
                    'chg_in_5': event.get('chg_in_5', None),
                    'chg_in_10': event.get('chg_in_10', None),
                    'source': event.get('source', '')
                }
                all_events.append(event_row)
        else:
            print("未提取到重大事件")

    if all_events:
        output_df = pd.DataFrame(all_events)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{symbol}.csv")
        output_df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"\n{'='*60}")
        print(f"✅ 处理完成!")
        print(f"总共提取了 {len(all_events)} 个事件")
        print(f"输出文件: {output_file}")
    else:
        print(f"\n{'='*60}")
        print(f"⚠️ 未提取到任何事件")


def main():
    parser = argparse.ArgumentParser(
        description="事件驱动型新闻分析 - CPU 版本 (无需量化库)"
    )

    parser.add_argument('--input', type=str, required=True,
                       help='输入 CSV 文件路径')
    parser.add_argument('--output-dir', type=str,
                       default='D:\\GitHub\\LocalFinData\\data\\events',
                       help='输出目录')
    parser.add_argument('--model-path', type=str, default=None,
                       help=f'模型路径 (默认: {get_model_path()})')
    parser.add_argument('--max-tokens', type=int, default=2048,
                       help='最大生成 tokens')

    args = parser.parse_args()

    model_path = args.model_path if args.model_path else get_model_path()

    print("="*60)
    print("事件驱动型新闻分析脚本 - CPU 版本")
    print("="*60)
    print(f"模型: Qwen2.5-3B (CPU, 无量化)")
    print(f"模型路径: {model_path}")
    print(f"输入文件: {args.input}")
    print(f"输出目录: {args.output_dir}")
    print(f"⚠️  注意: CPU 模式速度较慢")
    print("="*60)

    if not os.path.exists(model_path):
        print(f"\n❌ 错误: 模型路径不存在: {model_path}")
        return

    if not os.path.exists(args.input):
        print(f"\n❌ 错误: 输入文件不存在: {args.input}")
        return

    process_stock_news(
        input_csv=args.input,
        output_dir=args.output_dir,
        model_path=model_path,
        max_tokens=args.max_tokens
    )


if __name__ == "__main__":
    main()
