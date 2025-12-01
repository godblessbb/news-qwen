#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按交易周期处理新闻事件脚本
读取新闻CSV文件，按交易周期（周五到周五）分组，使用大模型分析并生成事件摘要
"""

import os
import sys
import logging
import argparse
import json
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== PROMPT 模板配置区域 ====================
# 您可以在这里修改大模型的分析提示词

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
# 4-bit量化建议：10-20条
# 8-bit量化建议：8-15条
# 无量化建议：5-10条
MAX_NEWS_PER_BATCH = 15

# ==================== 结束配置区域 ====================


def get_trading_week(date: datetime) -> Tuple[datetime, datetime]:
    """
    计算给定日期所属的交易周期（周五收盘后到下周五收盘前）

    Args:
        date: 输入日期

    Returns:
        (start_date, end_date) 交易周的开始和结束日期
    """
    # 获取星期几（0=周一, 4=周五, 6=周日）
    weekday = date.weekday()

    # 找到本周五
    days_until_friday = (4 - weekday) % 7
    this_friday = date + timedelta(days=days_until_friday)

    # 如果是周五及之前，交易周是上周五到本周五
    # 如果是周六日，交易周是本周五到下周五
    if weekday <= 4:  # 周一到周五
        start_friday = this_friday - timedelta(days=7)
        end_friday = this_friday
    else:  # 周六日
        start_friday = this_friday
        end_friday = this_friday + timedelta(days=7)

    # 设置时间为收盘时间（美股收盘 16:00 EST，这里简化为当天结束）
    start_date = start_friday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_friday.replace(hour=23, minute=59, second=59, microsecond=999999)

    return start_date, end_date


def load_qwen_model(
    model_path: str,
    device: str = "auto",
    load_in_4bit: bool = False,
    load_in_8bit: bool = False
) -> Tuple:
    """
    加载 Qwen 模型和 tokenizer

    Args:
        model_path: 模型路径
        device: 设备
        load_in_4bit: 是否使用 4-bit 量化
        load_in_8bit: 是否使用 8-bit 量化

    Returns:
        (model, tokenizer) 元组
    """
    logger.info(f"正在加载模型: {model_path}")

    # 检查是否为本地路径
    is_local_path = (
        os.path.sep in model_path or
        "/" in model_path and not model_path.count("/") == 1 or
        ":" in model_path or
        model_path.startswith(".") or
        model_path.startswith("~")
    )

    if is_local_path:
        model_path_obj = Path(model_path).expanduser().resolve()
        if not model_path_obj.exists():
            raise FileNotFoundError(f"模型路径不存在: {model_path}")
        model_path = str(model_path_obj)
        logger.info(f"检测到本地模型路径: {model_path}")

    load_kwargs = {"trust_remote_code": True}

    # 加载 tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path, **load_kwargs)

    # 确定设备
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info(f"目标设备: {device}")

    # 加载模型
    logger.info("加载模型（可能需要几分钟）...")
    model_kwargs = {**load_kwargs}

    if load_in_4bit:
        logger.info("使用 4-bit 量化加载")
        model_kwargs["load_in_4bit"] = True
        model_kwargs["device_map"] = "auto"
    elif load_in_8bit:
        logger.info("使用 8-bit 量化加载")
        model_kwargs["load_in_8bit"] = True
        model_kwargs["device_map"] = "auto"
    else:
        model_kwargs["torch_dtype"] = torch.float16 if device == "cuda" else torch.float32
        model_kwargs["device_map"] = device if device != "cpu" else None

    model = AutoModelForCausalLM.from_pretrained(model_path, **model_kwargs)

    if device == "cpu" and not (load_in_4bit or load_in_8bit):
        model = model.to("cpu")

    logger.info(f"✓ 模型加载完成")

    return model, tokenizer


def generate_response(
    model,
    tokenizer,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7
) -> str:
    """生成模型响应"""
    inputs = tokenizer(prompt, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=0.8,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_text = tokenizer.decode(
        outputs[0][len(inputs["input_ids"][0]):],
        skip_special_tokens=True
    )

    return generated_text.strip()


def read_news_csv(csv_path: str) -> pd.DataFrame:
    """读取新闻CSV文件"""
    logger.info(f"读取CSV文件: {csv_path}")

    df = pd.read_csv(csv_path)

    # 转换日期列
    df['date'] = pd.to_datetime(df['date'])

    logger.info(f"共读取 {len(df)} 条新闻记录")
    logger.info(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")

    return df


def group_by_trading_week(df: pd.DataFrame) -> Dict[Tuple[datetime, datetime], pd.DataFrame]:
    """
    按交易周期分组新闻

    Args:
        df: 新闻数据框

    Returns:
        字典，键为 (start_date, end_date)，值为该周期的新闻数据框
    """
    logger.info("按交易周期分组新闻...")

    # 为每条新闻计算所属交易周期
    df['trading_week'] = df['date'].apply(get_trading_week)

    # 按交易周期分组
    grouped = {}
    for week, group in df.groupby('trading_week'):
        grouped[week] = group.sort_values('date')

    logger.info(f"共识别 {len(grouped)} 个交易周期")

    return grouped


def analyze_trading_week(
    model,
    tokenizer,
    symbol: str,
    name: str,
    start_date: datetime,
    end_date: datetime,
    news_df: pd.DataFrame,
    max_tokens: int = 512
) -> str:
    """
    分析单个交易周期的新闻

    Args:
        model: 模型实例
        tokenizer: Tokenizer实例
        symbol: 股票代码
        name: 公司名称
        start_date: 周期开始日期
        end_date: 周期结束日期
        news_df: 该周期的新闻数据
        max_tokens: 最大生成令牌数

    Returns:
        事件总结文本
    """
    news_count = len(news_df)
    logger.info(f"分析 {symbol} 交易周期 {start_date.date()} 至 {end_date.date()}，共 {news_count} 条新闻")

    # 如果新闻数量超过批次限制，分批处理
    if news_count > MAX_NEWS_PER_BATCH:
        logger.info(f"新闻数量 ({news_count}) 超过批次限制 ({MAX_NEWS_PER_BATCH})，将分批处理")

        summaries = []
        for i in range(0, news_count, MAX_NEWS_PER_BATCH):
            batch_df = news_df.iloc[i:i + MAX_NEWS_PER_BATCH]
            batch_num = i // MAX_NEWS_PER_BATCH + 1
            total_batches = (news_count + MAX_NEWS_PER_BATCH - 1) // MAX_NEWS_PER_BATCH

            logger.info(f"  处理批次 {batch_num}/{total_batches} ({len(batch_df)} 条新闻)")

            summary = _analyze_news_batch(
                model, tokenizer, symbol, name,
                start_date, end_date, batch_df, max_tokens
            )
            summaries.append(summary)

        # 如果有多个批次，合并总结
        if len(summaries) > 1:
            logger.info("合并多个批次的分析结果...")
            combined_summary = _merge_summaries(
                model, tokenizer, symbol, name,
                start_date, end_date, summaries, max_tokens
            )
            return combined_summary
        else:
            return summaries[0]
    else:
        # 单批次处理
        return _analyze_news_batch(
            model, tokenizer, symbol, name,
            start_date, end_date, news_df, max_tokens
        )


def _analyze_news_batch(
    model, tokenizer, symbol, name,
    start_date, end_date, news_df, max_tokens
) -> str:
    """分析单批次新闻"""
    # 构建新闻列表文本
    news_list = ""
    for idx, row in news_df.iterrows():
        news_date = row['date'].strftime('%Y-%m-%d')
        title = row['title']
        source = row.get('source', '未知来源')
        news_list += f"- [{news_date}] {title} (来源: {source})\n"

    # 使用模板生成prompt
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        symbol=symbol,
        name=name,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        news_list=news_list.strip()
    )

    # 生成分析
    summary = generate_response(model, tokenizer, prompt, max_tokens=max_tokens)

    return summary


def _merge_summaries(
    model, tokenizer, symbol, name,
    start_date, end_date, summaries, max_tokens
) -> str:
    """合并多个批次的总结"""
    merge_prompt = f"""你是一位专业的金融分析师。以下是关于 {symbol} ({name}) 在交易周期 {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} 的多个新闻批次分析：

{chr(10).join([f"{i+1}. {summary}" for i, summary in enumerate(summaries)])}

请将以上分析合并为一个简洁的事件总结（150字以内），要求：
1. 使用实时性陈述（过去时态）
2. 包含重要数据和数字
3. 包含情感属性关键词
4. 突出对股价的潜在影响

请直接返回事件总结文本。
"""

    merged = generate_response(model, tokenizer, merge_prompt, max_tokens=max_tokens)
    return merged


def process_news_file(
    model,
    tokenizer,
    input_csv: str,
    output_dir: str,
    max_tokens: int = 512
) -> str:
    """
    处理新闻CSV文件，生成按交易周期的事件摘要

    Args:
        model: 模型实例
        tokenizer: Tokenizer实例
        input_csv: 输入CSV文件路径
        output_dir: 输出目录
        max_tokens: 最大生成令牌数

    Returns:
        输出CSV文件路径
    """
    # 读取数据
    df = read_news_csv(input_csv)

    # 按交易周期分组
    grouped = group_by_trading_week(df)

    # 准备输出
    output_records = []

    # 处理每个交易周期
    for (start_date, end_date), week_df in sorted(grouped.items()):
        # 获取股票信息
        symbol = week_df['symbol'].iloc[0]
        name = week_df['name'].iloc[0]

        # 获取价格变化（取平均值或最新值）
        chg_in_5 = week_df['chg_in_5'].mean() if 'chg_in_5' in week_df.columns else None
        chg_in_10 = week_df['chg_in_10'].mean() if 'chg_in_10' in week_df.columns else None

        # 分析该周期新闻
        event_details = analyze_trading_week(
            model, tokenizer, symbol, name,
            start_date, end_date, week_df, max_tokens
        )

        # 添加到输出记录
        output_records.append({
            'symbol': symbol,
            'name': name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'chg_in_5': chg_in_5 if pd.notna(chg_in_5) else '',
            'chg_in_10': chg_in_10 if pd.notna(chg_in_10) else '',
            'event_details': event_details
        })

        logger.info(f"✓ 完成交易周期 {start_date.date()} 至 {end_date.date()}")

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成输出文件名
    input_filename = Path(input_csv).stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_path / f"{input_filename}_events_{timestamp}.csv"

    # 写入CSV
    logger.info(f"写入结果到: {output_file}")

    output_df = pd.DataFrame(output_records)
    output_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    logger.info(f"✓ 处理完成，共生成 {len(output_records)} 条事件记录")

    return str(output_file)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="按交易周期处理新闻事件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python process_news_by_trading_week.py --input news.csv --model-path D:/models/qwen2.5-7b --load-in-4bit
  python process_news_by_trading_week.py --input news.csv --model-path D:/models/qwen2.5-7b --output-dir ./results
        """
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="输入CSV文件路径（包含新闻数据）"
    )

    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="模型路径（本地路径或 HuggingFace 模型 ID）"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="Events",
        help="输出目录（默认：Events）"
    )

    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="设备选择（默认：auto）"
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="最大生成令牌数（默认：512）"
    )

    parser.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="使用 4-bit 量化（降低显存需求）"
    )

    parser.add_argument(
        "--load-in-8bit",
        action="store_true",
        help="使用 8-bit 量化（降低显存需求）"
    )

    args = parser.parse_args()

    # 检查输入文件
    if not Path(args.input).exists():
        logger.error(f"输入文件不存在: {args.input}")
        sys.exit(1)

    # 加载模型
    try:
        model, tokenizer = load_qwen_model(
            args.model_path,
            args.device,
            load_in_4bit=args.load_in_4bit,
            load_in_8bit=args.load_in_8bit
        )
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 处理文件
    try:
        output_file = process_news_file(
            model, tokenizer,
            args.input,
            args.output_dir,
            max_tokens=args.max_tokens
        )

        logger.info(f"\n{'='*60}")
        logger.info(f"处理完成！")
        logger.info(f"输出文件: {output_file}")
        logger.info(f"{'='*60}")

    except Exception as e:
        logger.error(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
