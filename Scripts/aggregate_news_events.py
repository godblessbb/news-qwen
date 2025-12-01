#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻事件聚合脚本
使用 Qwen 模型分析和聚合股票相关新闻事件
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import pandas as pd
import pytz

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_model_path(model_path: str) -> str:
    """
    规范化模型路径，处理 Windows 路径问题

    Args:
        model_path: 原始模型路径

    Returns:
        规范化后的路径
    """
    # 转换为 Path 对象
    path = Path(model_path)

    # 返回绝对路径字符串
    return str(path.resolve())


def is_local_path(model_path: str) -> bool:
    """
    检查是否为本地路径

    Args:
        model_path: 模型路径

    Returns:
        是否为本地路径
    """
    # 检查是否包含路径分隔符或驱动器号
    if '/' in model_path or '\\' in model_path:
        return True

    # 检查是否为绝对路径
    path = Path(model_path)
    if path.is_absolute():
        return True

    # 检查路径是否存在
    if path.exists():
        return True

    return False


def load_qwen_model(
    model_path: str,
    device: str = "auto",
    load_in_8bit: bool = False,
    load_in_4bit: bool = False
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    加载 Qwen 模型和 tokenizer

    Args:
        model_path: 模型路径（可以是本地路径或 HuggingFace 模型 ID）
        device: 设备
        load_in_8bit: 是否使用 8-bit 量化
        load_in_4bit: 是否使用 4-bit 量化

    Returns:
        (model, tokenizer) 元组
    """
    logger.info(f"正在加载模型: {model_path}")

    # 检查是否为本地路径
    local_path = is_local_path(model_path)

    if local_path:
        # 规范化本地路径
        normalized_path = normalize_model_path(model_path)
        logger.info(f"检测到本地路径: {normalized_path}")

        # 检查路径是否存在
        if not Path(normalized_path).exists():
            raise FileNotFoundError(
                f"模型路径不存在: {normalized_path}\n"
                f"请确保模型已下载到该路径"
            )

        model_path = normalized_path
        use_local_files_only = True
    else:
        logger.info(f"检测到 HuggingFace 模型 ID: {model_path}")
        use_local_files_only = False

    # 设置量化配置
    kwargs = {}
    if load_in_8bit:
        logger.info("使用 8-bit 量化")
        kwargs["load_in_8bit"] = True
    elif load_in_4bit:
        logger.info("使用 4-bit 量化")
        kwargs["load_in_4bit"] = True
    else:
        # 自动选择设备
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        kwargs["device_map"] = device

    logger.info(f"设备: {device}")

    # 加载 tokenizer
    logger.info("正在加载 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        local_files_only=use_local_files_only
    )

    # 加载模型
    logger.info("正在加载模型（可能需要几分钟）...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        trust_remote_code=True,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        local_files_only=use_local_files_only,
        **kwargs
    )

    logger.info("✓ 模型加载完成")

    return model, tokenizer


def generate_response(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    messages: List[Dict[str, str]],
    max_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.8
) -> str:
    """
    生成模型响应

    Args:
        model: 模型
        tokenizer: tokenizer
        messages: 对话消息列表
        max_tokens: 最大生成 token 数
        temperature: 温度参数
        top_p: top-p 采样参数

    Returns:
        生成的文本
    """
    # 使用 tokenizer 的 chat 模板
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # 编码输入
    inputs = tokenizer(prompt, return_tensors="pt")

    # 移动到正确的设备
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # 生成
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    # 解码输出
    generated_text = tokenizer.decode(
        outputs[0][len(inputs["input_ids"][0]):],
        skip_special_tokens=True
    )

    return generated_text


def analyze_news_events(
    news_data: List[Dict],
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    stock_symbol: str
) -> Dict:
    """
    分析新闻事件

    Args:
        news_data: 新闻数据列表
        model: 模型
        tokenizer: tokenizer
        stock_symbol: 股票代码

    Returns:
        分析结果字典
    """
    logger.info(f"正在分析 {stock_symbol} 的 {len(news_data)} 条新闻...")

    # 构建提示词
    news_text = "\n\n".join([
        f"标题: {item.get('title', 'N/A')}\n"
        f"摘要: {item.get('summary', 'N/A')}\n"
        f"时间: {item.get('timestamp', 'N/A')}"
        for item in news_data[:10]  # 限制前10条以避免过长
    ])

    prompt = f"""请分析以下关于 {stock_symbol} 股票的新闻，总结关键事件和趋势：

{news_text}

请提供：
1. 主要事件总结（3-5点）
2. 整体情绪倾向（正面/负面/中性）
3. 对股价的潜在影响

请用简洁的中文回答。"""

    messages = [
        {"role": "user", "content": prompt}
    ]

    # 生成分析
    analysis = generate_response(
        model, tokenizer, messages,
        max_tokens=1024,
        temperature=0.3  # 使用较低温度以获得更稳定的输出
    )

    return {
        "stock_symbol": stock_symbol,
        "news_count": len(news_data),
        "analysis_time": datetime.now(pytz.UTC).isoformat(),
        "analysis": analysis
    }


def load_test_news_data(stock_symbol: str) -> List[Dict]:
    """
    加载测试新闻数据

    Args:
        stock_symbol: 股票代码

    Returns:
        测试新闻数据列表
    """
    logger.info(f"加载 {stock_symbol} 的测试数据...")

    # 生成一些测试数据
    test_data = [
        {
            "title": f"{stock_symbol} 公布季度财报，营收超预期",
            "summary": f"{stock_symbol} 公司今日公布季度财报，营收同比增长15%，超出分析师预期。",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "title": f"{stock_symbol} 宣布新产品发布计划",
            "summary": f"{stock_symbol} 宣布将在下月发布新一代产品，预计将提升市场竞争力。",
            "timestamp": (datetime.now() - timedelta(hours=5)).isoformat()
        },
        {
            "title": f"分析师上调 {stock_symbol} 目标价",
            "summary": f"多家投行分析师上调 {stock_symbol} 目标价，平均上调幅度达10%。",
            "timestamp": (datetime.now() - timedelta(hours=8)).isoformat()
        },
        {
            "title": f"{stock_symbol} 获得重要合同",
            "summary": f"{stock_symbol} 获得一项重要合同，合同金额达5亿美元。",
            "timestamp": (datetime.now() - timedelta(hours=12)).isoformat()
        },
        {
            "title": f"{stock_symbol} CEO 接受采访谈未来战略",
            "summary": f"{stock_symbol} CEO 在接受采访时表示，公司将继续投资研发，扩大市场份额。",
            "timestamp": (datetime.now() - timedelta(hours=24)).isoformat()
        }
    ]

    logger.info(f"✓ 加载了 {len(test_data)} 条测试数据")

    return test_data


def save_analysis_results(results: Dict, output_file: str):
    """
    保存分析结果

    Args:
        results: 分析结果
        output_file: 输出文件路径
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ 分析结果已保存到: {output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="新闻事件聚合分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用本地模型分析测试数据
  python aggregate_news_events.py --model-path D:/models/Qwen2.5-7B-Instruct --stock AAPL --test

  # 使用 HuggingFace 模型
  python aggregate_news_events.py --model-path Qwen/Qwen2.5-7B-Instruct --stock TSLA --test

  # 使用量化模型节省显存
  python aggregate_news_events.py --model-path D:/models/Qwen2.5-7B-Instruct --stock AAPL --test --load-in-4bit
        """
    )

    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="模型路径（本地路径或 HuggingFace 模型 ID）"
    )
    parser.add_argument(
        "--stock",
        type=str,
        required=True,
        help="股票代码（如 AAPL, TSLA, AAL）"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="使用测试数据（用于演示）"
    )
    parser.add_argument(
        "--news-file",
        type=str,
        help="新闻数据文件路径（JSON 或 CSV 格式）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/news_analysis.json",
        help="输出文件路径（默认: output/news_analysis.json）"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="运行设备（默认: auto）"
    )
    parser.add_argument(
        "--load-in-8bit",
        action="store_true",
        help="使用 8-bit 量化（节省显存）"
    )
    parser.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="使用 4-bit 量化（节省更多显存）"
    )

    args = parser.parse_args()

    # 加载模型
    try:
        model, tokenizer = load_qwen_model(
            args.model_path,
            device=args.device,
            load_in_8bit=args.load_in_8bit,
            load_in_4bit=args.load_in_4bit
        )
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        sys.exit(1)

    # 加载新闻数据
    if args.test:
        news_data = load_test_news_data(args.stock)
    elif args.news_file:
        logger.info(f"从文件加载新闻数据: {args.news_file}")
        # TODO: 实现从文件加载新闻数据
        logger.error("暂不支持从文件加载，请使用 --test 参数")
        sys.exit(1)
    else:
        logger.error("请指定 --test 或 --news-file 参数")
        sys.exit(1)

    # 分析新闻
    try:
        results = analyze_news_events(
            news_data,
            model,
            tokenizer,
            args.stock
        )

        # 打印结果
        print("\n" + "=" * 60)
        print(f"新闻分析结果 - {args.stock}")
        print("=" * 60)
        print(f"\n分析的新闻数量: {results['news_count']}")
        print(f"分析时间: {results['analysis_time']}")
        print(f"\n分析结果:\n{results['analysis']}")
        print("\n" + "=" * 60)

        # 保存结果
        save_analysis_results(results, args.output)

        logger.info("✓ 分析完成")

    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
