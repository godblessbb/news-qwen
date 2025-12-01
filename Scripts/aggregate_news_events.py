#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻事件聚合脚本
使用 Qwen 模型分析和聚合新闻事件
"""

import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_qwen_model(model_path: str, device: str = "auto") -> Tuple:
    """
    加载 Qwen 模型和 tokenizer

    Args:
        model_path: 模型路径（支持本地路径和 HuggingFace 模型 ID）
        device: 设备（"cuda", "cpu", "auto"）

    Returns:
        (model, tokenizer) 元组
    """
    logger.info(f"正在加载模型: {model_path}")

    # 检查是否为本地路径
    model_path_obj = Path(model_path)
    is_local_path = model_path_obj.exists()

    # 加载参数
    load_kwargs = {
        "trust_remote_code": True,
    }

    # 如果是本地路径，添加 local_files_only 参数
    if is_local_path:
        logger.info(f"检测到本地模型路径: {model_path}")
        load_kwargs["local_files_only"] = True
        # 将路径转换为绝对路径字符串
        model_path = str(model_path_obj.resolve())

    # 加载 tokenizer
    try:
        logger.info("加载 tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            **load_kwargs
        )
    except Exception as e:
        logger.error(f"加载 tokenizer 失败: {e}")
        raise

    # 确定设备
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info(f"目标设备: {device}")

    # 加载模型
    try:
        logger.info("加载模型（可能需要几分钟）...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map=device if device != "cpu" else None,
            **load_kwargs
        )

        if device == "cpu":
            model = model.to("cpu")

        logger.info(f"✓ 模型加载完成，设备: {device}")

    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        raise

    return model, tokenizer


def generate_response(
    model,
    tokenizer,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 0.8
) -> str:
    """
    生成模型响应

    Args:
        model: 模型实例
        tokenizer: Tokenizer 实例
        prompt: 输入提示
        max_tokens: 最大生成令牌数
        temperature: 温度参数
        top_p: Top-p 采样参数

    Returns:
        生成的文本
    """
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
            eos_token_id=tokenizer.eos_token_id,
        )

    # 解码输出（只返回新生成的部分）
    generated_text = tokenizer.decode(
        outputs[0][len(inputs["input_ids"][0]):],
        skip_special_tokens=True
    )

    return generated_text


def aggregate_news_events(
    model,
    tokenizer,
    stock_symbol: str,
    news_items: List[Dict],
    max_tokens: int = 2048
) -> Dict:
    """
    聚合新闻事件

    Args:
        model: 模型实例
        tokenizer: Tokenizer 实例
        stock_symbol: 股票代码
        news_items: 新闻项列表
        max_tokens: 最大生成令牌数

    Returns:
        聚合结果字典
    """
    # 构建新闻文本
    news_text = ""
    for i, item in enumerate(news_items, 1):
        title = item.get("title", "")
        summary = item.get("summary", "")
        date = item.get("date", "")
        news_text += f"\n{i}. [{date}] {title}\n   {summary}\n"

    # 构建提示词
    prompt = f"""请分析以下关于股票 {stock_symbol} 的新闻，并总结关键事件：

{news_text}

请提供：
1. 主要事件摘要（3-5条）
2. 情感分析（正面/中性/负面）
3. 对股价的潜在影响

请以 JSON 格式输出结果：
{{
    "summary": ["事件1", "事件2", "事件3"],
    "sentiment": "正面/中性/负面",
    "impact": "影响说明",
    "confidence": 0.0-1.0
}}"""

    logger.info(f"正在分析 {len(news_items)} 条新闻...")

    # 生成响应
    response = generate_response(
        model,
        tokenizer,
        prompt,
        max_tokens=max_tokens,
        temperature=0.7,
        top_p=0.8
    )

    logger.info("分析完成")

    # 尝试解析 JSON 响应
    try:
        # 提取 JSON 部分（可能包含在 markdown 代码块中）
        response = response.strip()
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()

        result = json.loads(response)
        result["raw_response"] = response

    except json.JSONDecodeError as e:
        logger.warning(f"无法解析 JSON 响应: {e}")
        result = {
            "summary": ["解析失败"],
            "sentiment": "未知",
            "impact": "无法解析",
            "confidence": 0.0,
            "raw_response": response,
            "error": str(e)
        }

    return result


def get_test_news_data(stock_symbol: str) -> List[Dict]:
    """
    获取测试新闻数据

    Args:
        stock_symbol: 股票代码

    Returns:
        测试新闻列表
    """
    # 示例测试数据
    test_data = {
        "AAL": [
            {
                "title": "American Airlines报告Q3季度业绩超预期",
                "summary": "美国航空公司公布第三季度财报，营收同比增长12%，净利润达到5.5亿美元，超出分析师预期。",
                "date": "2024-10-25",
                "source": "Bloomberg"
            },
            {
                "title": "AAL宣布扩大欧洲航线网络",
                "summary": "美国航空宣布将在2024年增加15条新的跨大西洋航线，以满足不断增长的国际旅行需求。",
                "date": "2024-10-20",
                "source": "Reuters"
            },
            {
                "title": "燃油价格上涨对航空业构成压力",
                "summary": "原油价格近期持续上涨，预计将增加航空公司的运营成本，可能影响第四季度盈利能力。",
                "date": "2024-10-18",
                "source": "CNBC"
            },
            {
                "title": "American Airlines与飞行员工会达成新协议",
                "summary": "AAL与飞行员工会达成为期四年的新劳动合同，包括薪资上调和改善工作条件，有助于稳定运营。",
                "date": "2024-10-15",
                "source": "WSJ"
            }
        ],
        "AAPL": [
            {
                "title": "Apple发布iPhone 16系列，AI功能成亮点",
                "summary": "苹果公司发布最新iPhone 16系列，集成先进AI芯片和新功能，预计将推动销售增长。",
                "date": "2024-10-22",
                "source": "TechCrunch"
            },
            {
                "title": "苹果在中国市场份额下滑",
                "summary": "最新数据显示，苹果在中国智能手机市场份额同比下降3%，面临本土品牌激烈竞争。",
                "date": "2024-10-19",
                "source": "Financial Times"
            },
            {
                "title": "AAPL股价创历史新高",
                "summary": "受强劲财报和新品发布推动，苹果股价突破180美元，创下历史新高。",
                "date": "2024-10-16",
                "source": "MarketWatch"
            }
        ]
    }

    return test_data.get(stock_symbol, [
        {
            "title": f"{stock_symbol} 测试新闻1",
            "summary": "这是一条测试新闻摘要。",
            "date": "2024-10-25",
            "source": "测试来源"
        },
        {
            "title": f"{stock_symbol} 测试新闻2",
            "summary": "这是另一条测试新闻摘要。",
            "date": "2024-10-20",
            "source": "测试来源"
        }
    ])


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="新闻事件聚合脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
        help="股票代码（例如：AAPL, AAL）"
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
        default=2048,
        help="最大生成令牌数（默认：2048）"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="使用测试数据（不实际获取新闻）"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文件路径（JSON 格式）"
    )

    args = parser.parse_args()

    # 加载模型
    try:
        model, tokenizer = load_qwen_model(args.model_path, args.device)
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        sys.exit(1)

    # 获取新闻数据
    if args.test:
        logger.info(f"使用测试数据，股票代码: {args.stock}")
        news_items = get_test_news_data(args.stock)
    else:
        logger.error("实时新闻获取功能尚未实现，请使用 --test 参数")
        sys.exit(1)

    logger.info(f"共获取 {len(news_items)} 条新闻")

    # 聚合分析
    try:
        result = aggregate_news_events(
            model,
            tokenizer,
            args.stock,
            news_items,
            max_tokens=args.max_tokens
        )

        # 添加元数据
        result["stock"] = args.stock
        result["news_count"] = len(news_items)
        result["timestamp"] = datetime.now().isoformat()

        # 输出结果
        print("\n" + "=" * 60)
        print(f"股票代码: {args.stock}")
        print(f"新闻数量: {len(news_items)}")
        print("=" * 60)
        print("\n分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 保存到文件
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"结果已保存到: {output_path}")

    except Exception as e:
        logger.error(f"分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    logger.info("完成")


if __name__ == "__main__":
    main()
