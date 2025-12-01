#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻事件聚合脚本
按交易周聚合新闻，使用 Qwen 模型识别和总结重要事件
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import re
from typing import List, Dict, Tuple
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
NEWS_DIR = PROJECT_ROOT / "News"
EVENTS_DIR = PROJECT_ROOT / "Events"

# 新闻来源权重（越重要权重越高）
SOURCE_WEIGHTS = {
    'Bloomberg': 1.0,
    'Reuters': 1.0,
    'Wall Street Journal': 0.95,
    'Financial Times': 0.95,
    'CNBC': 0.85,
    'Yahoo Finance': 0.75,
    'MarketWatch': 0.75,
    'Seeking Alpha': 0.65,
    'Moomoo News': 0.6,
    'Benzinga': 0.6,
    'The Motley Fool': 0.5,
    'default': 0.5  # 默认权重
}


def get_source_weight(source: str) -> float:
    """获取新闻来源权重"""
    for key, weight in SOURCE_WEIGHTS.items():
        if key.lower() in source.lower():
            return weight
    return SOURCE_WEIGHTS['default']


def get_trading_week_end(dt: datetime) -> datetime:
    """
    获取给定日期所在交易周的结束时间（周五美东时间16:00）
    考虑夏令时和冬令时

    美国夏令时：3月第二个周日 02:00 - 11月第一个周日 02:00
    """
    # 转换为美东时间
    eastern = pytz.timezone('US/Eastern')
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    dt_eastern = dt.astimezone(eastern)

    # 找到本周或下周的周五
    days_until_friday = (4 - dt_eastern.weekday()) % 7  # 4 = Friday
    if days_until_friday == 0 and dt_eastern.hour >= 16:
        # 如果已经是周五16点后，取下周五
        days_until_friday = 7

    friday = dt_eastern + timedelta(days=days_until_friday)
    # 设置为16:00收盘
    week_end = friday.replace(hour=16, minute=0, second=0, microsecond=0)

    return week_end


def assign_trading_weeks(df: pd.DataFrame) -> pd.DataFrame:
    """
    为每条新闻分配交易周
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # 为每条新闻计算其所属的交易周结束时间
    df['week_end'] = df['date'].apply(get_trading_week_end)

    # 按周分组
    df['week_id'] = df['week_end'].rank(method='dense').astype(int)

    return df


def load_qwen_model(model_path: str):
    """
    加载 Qwen 模型（4bit量化）
    """
    logger.info(f"正在加载模型: {model_path}")

    # 4bit 量化配置
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )

    # 加载 tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True
    )

    # 加载模型
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=quantization_config,
        device_map="auto",
        trust_remote_code=True
    )

    logger.info("模型加载完成")
    return model, tokenizer


def build_event_analysis_prompt(week_news: pd.DataFrame) -> str:
    """
    构建事件分析的 prompt
    """
    # 按时间排序
    week_news = week_news.sort_values('date')

    # 构建新闻列表
    news_list = []
    for idx, row in week_news.iterrows():
        source_weight = get_source_weight(row['source'])
        news_item = f"""
[{idx+1}] 时间: {row['date']}
    来源: {row['source']} (权重: {source_weight:.2f})
    标题: {row['title']}
"""
        news_list.append(news_item)

    news_text = "\n".join(news_list)

    # 获取价格变化信息
    avg_chg_5 = week_news['chg_in_5'].mean() if 'chg_in_5' in week_news.columns else 0
    avg_chg_10 = week_news['chg_in_10'].mean() if 'chg_in_10' in week_news.columns else 0

    prompt = f"""你是一个专业的金融分析师。请分析以下一个交易周内的新闻，识别并总结重要事件。

**分析要求：**
1. 识别主要事件（去除重复报道和噪音）
2. 判断事件的聚集程度（0-1分数，考虑新闻来源权重）
3. 确定事件的最早发生时间
4. 用简洁的事件式语言总结（包含关键数字和情绪词）

**本周新闻列表（共{len(week_news)}条）：**
{news_text}

**价格信息：**
- 未来5天平均变化: {avg_chg_5:.2f}%
- 未来10天平均变化: {avg_chg_10:.2f}%

**请按以下JSON格式输出（只输出JSON，不要其他文字）：**
{{
    "event_summary": "事件总结（简洁、事件式描述，包含关键数字）",
    "earliest_time": "最早发生时间（YYYY-MM-DD HH:MM:SS格式）",
    "concentration_score": 0.85,
    "related_news_count": 5,
    "total_news_count": {len(week_news)},
    "weighted_concentration": 0.78,
    "chg_in_5": {avg_chg_5:.4f},
    "chg_in_10": {avg_chg_10:.4f}
}}
"""
    return prompt


def parse_qwen_response(response: str) -> Dict:
    """
    解析 Qwen 的响应，提取 JSON
    """
    try:
        # 尝试直接解析
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        # 如果失败，尝试提取 JSON 部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return result
            except json.JSONDecodeError:
                pass

    # 如果都失败，返回默认值
    logger.warning("无法解析模型响应，返回默认值")
    return {
        "event_summary": "解析失败",
        "earliest_time": None,
        "concentration_score": 0.0,
        "related_news_count": 0,
        "total_news_count": 0,
        "weighted_concentration": 0.0,
        "chg_in_5": 0.0,
        "chg_in_10": 0.0
    }


def analyze_week_events(week_news: pd.DataFrame, model, tokenizer) -> Dict:
    """
    分析一个交易周的事件
    """
    # 构建 prompt
    prompt = build_event_analysis_prompt(week_news)

    # 准备消息
    messages = [
        {"role": "system", "content": "你是一个专业的金融分析师，擅长从新闻中提取关键事件。"},
        {"role": "user", "content": prompt}
    ]

    # 生成回复
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=512,
            temperature=0.3,
            top_p=0.8,
            do_sample=True
        )

    generated_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

    logger.info(f"模型响应: {response[:200]}...")

    # 解析响应
    result = parse_qwen_response(response)

    return result


def process_stock_file(csv_path: Path, model, tokenizer, test_mode: bool = True):
    """
    处理单个股票的CSV文件
    """
    stock_symbol = csv_path.stem
    logger.info(f"正在处理: {stock_symbol}")

    # 读取CSV
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"读取到 {len(df)} 条新闻")
    except Exception as e:
        logger.error(f"读取CSV失败: {e}")
        return

    # 检查必需列
    required_cols = ['symbol', 'name', 'date', 'title', 'source']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"缺少必需列: {missing_cols}")
        return

    # 分配交易周
    df = assign_trading_weeks(df)

    # 创建输出文件夹
    output_dir = EVENTS_DIR / stock_symbol
    output_dir.mkdir(exist_ok=True)

    # 按周分组处理
    events_data = []

    weeks = df.groupby('week_id')
    logger.info(f"共分为 {len(weeks)} 个交易周")

    for week_id, week_news in weeks:
        logger.info(f"处理第 {week_id} 周 ({len(week_news)} 条新闻)")

        # 使用 Qwen 分析
        event_info = analyze_week_events(week_news, model, tokenizer)

        # 添加元信息
        event_info['stock_symbol'] = df['symbol'].iloc[0]
        event_info['stock_name'] = df['name'].iloc[0] if 'name' in df.columns else ''
        event_info['week_start'] = week_news['date'].min().strftime('%Y-%m-%d')
        event_info['week_end'] = week_news['week_end'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')

        events_data.append(event_info)

        # 测试模式只处理第一周
        if test_mode:
            logger.info("测试模式：只处理第一周")
            break

    # 保存结果
    events_df = pd.DataFrame(events_data)
    output_file = output_dir / f"{stock_symbol}_events.csv"
    events_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f"结果已保存到: {output_file}")

    return events_df


def main():
    """
    主函数
    """
    import argparse

    parser = argparse.ArgumentParser(description='聚合新闻事件')
    parser.add_argument('--model-path', type=str, required=True, help='Qwen 模型路径')
    parser.add_argument('--stock', type=str, default='AAL', help='要处理的股票代码（默认AAL）')
    parser.add_argument('--all', action='store_true', help='处理所有股票')
    parser.add_argument('--test', action='store_true', default=True, help='测试模式（只处理每个股票的第一周）')

    args = parser.parse_args()

    # 加载模型
    model, tokenizer = load_qwen_model(args.model_path)

    if args.all:
        # 处理所有股票
        csv_files = list(NEWS_DIR.glob("*.csv"))
        logger.info(f"找到 {len(csv_files)} 个CSV文件")

        for csv_file in csv_files:
            try:
                process_stock_file(csv_file, model, tokenizer, test_mode=args.test)
            except Exception as e:
                logger.error(f"处理 {csv_file.name} 时出错: {e}")
                continue
    else:
        # 处理单个股票
        csv_file = NEWS_DIR / f"{args.stock}.csv"
        if not csv_file.exists():
            logger.error(f"文件不存在: {csv_file}")
            return

        process_stock_file(csv_file, model, tokenizer, test_mode=args.test)

    logger.info("处理完成！")


if __name__ == "__main__":
    main()
