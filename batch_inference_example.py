#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量推理示例 - 展示如何使用 vLLM 处理大规模数据
"""

import json
import time
from pathlib import Path
from typing import List, Dict
from vllm_inference import Qwen3VLLMInference


def load_data_from_file(file_path: str) -> List[str]:
    """
    从文件加载数据

    支持格式：
    - .txt: 每行一个问题
    - .json: JSON 数组或 JSONL 格式
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if file_path.suffix == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    elif file_path.suffix == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                raise ValueError("JSON 文件应包含一个数组")

    elif file_path.suffix == '.jsonl':
        questions = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    questions.append(obj.get('question', obj.get('text', '')))
        return questions

    else:
        raise ValueError(f"不支持的文件格式: {file_path.suffix}")


def save_results(results: List[Dict], output_file: str):
    """保存结果到文件"""
    output_path = Path(output_file)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✓ 结果已保存到: {output_path}")


def batch_inference_with_progress(
    inference: Qwen3VLLMInference,
    questions: List[str],
    batch_size: int = 32,
    **kwargs
) -> List[Dict]:
    """
    分批推理，带进度显示

    Args:
        inference: 推理引擎
        questions: 问题列表
        batch_size: 批量大小
        **kwargs: 传递给 generate 的参数

    Returns:
        结果列表
    """
    total = len(questions)
    results = []

    print(f"开始批量推理...")
    print(f"总数据量: {total}")
    print(f"批量大小: {batch_size}")
    print("=" * 60)

    start_time = time.time()

    for i in range(0, total, batch_size):
        batch_start = time.time()

        # 获取当前批次
        batch_questions = questions[i:i + batch_size]
        batch_messages = [
            [{"role": "user", "content": q}] for q in batch_questions
        ]

        # 推理
        batch_responses = inference.chat(batch_messages, **kwargs)

        # 记录结果
        for question, response in zip(batch_questions, batch_responses):
            results.append({
                "question": question,
                "response": response,
                "timestamp": time.time()
            })

        batch_time = time.time() - batch_start
        processed = min(i + batch_size, total)
        progress = (processed / total) * 100

        print(f"进度: {processed}/{total} ({progress:.1f}%) | "
              f"批次耗时: {batch_time:.2f}s | "
              f"速度: {len(batch_questions) / batch_time:.2f} 条/秒")

    total_time = time.time() - start_time

    print("=" * 60)
    print(f"✓ 批量推理完成！")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均速度: {total / total_time:.2f} 条/秒")

    return results


def example_news_classification():
    """示例：新闻分类"""
    print("\n示例 1: 新闻分类")
    print("-" * 60)

    # 模拟新闻数据
    news_titles = [
        "科技公司发布新款 AI 芯片，性能提升 50%",
        "足球世界杯决赛今晚上演，谁能夺冠？",
        "央行宣布降低存款准备金率 0.5 个百分点",
        "新冠疫苗第四针接种工作全面启动",
        "著名导演新作获得国际电影节大奖",
        "房地产市场出现回暖信号，成交量上涨",
        "研究发现新型材料可提高太阳能电池效率",
        "NBA 总决赛第七场，两队激烈角逐",
    ]

    # 初始化推理引擎
    inference = Qwen3VLLMInference()

    # 准备提示
    classification_prompts = []
    for title in news_titles:
        prompt = f"""请将以下新闻标题分类到合适的类别中。

新闻标题：{title}

可选类别：科技、体育、财经、健康、娱乐、房产

请只回答类别名称，不需要解释。"""
        classification_prompts.append([{"role": "user", "content": prompt}])

    # 批量推理
    responses = inference.chat(
        classification_prompts,
        temperature=0.1,  # 低温度，更确定的结果
        max_tokens=10
    )

    # 显示结果
    print("\n分类结果：")
    for title, category in zip(news_titles, responses):
        print(f"  {title}")
        print(f"  → {category.strip()}\n")


def example_summarization():
    """示例：批量摘要生成"""
    print("\n示例 2: 批量摘要生成")
    print("-" * 60)

    # 模拟文章数据
    articles = [
        "人工智能技术在近年来取得了突飞猛进的发展。从早期的专家系统到现在的深度学习，AI 已经在图像识别、自然语言处理、推荐系统等领域展现出强大的能力。特别是大语言模型的出现，让机器能够理解和生成人类语言，为各行各业带来了革命性的变化。",

        "气候变化是当今世界面临的最大挑战之一。全球变暖导致极端天气事件频发，冰川融化，海平面上升，给人类社会和自然生态系统带来严重威胁。各国政府和国际组织正在采取行动，通过减少碳排放、发展清洁能源、保护森林等措施来应对气候变化。",

        "量子计算被认为是下一代计算技术的重要方向。与传统计算机使用二进制比特不同，量子计算机利用量子比特，可以同时处于多个状态，从而实现并行计算。这使得量子计算机在处理某些特定问题时，能够展现出远超传统计算机的性能。",
    ]

    inference = Qwen3VLLMInference()

    # 准备提示
    summary_prompts = []
    for article in articles:
        prompt = f"请用一句话总结以下文章的主要内容：\n\n{article}"
        summary_prompts.append([{"role": "user", "content": prompt}])

    # 批量推理
    summaries = inference.chat(
        summary_prompts,
        temperature=0.3,
        max_tokens=100
    )

    # 显示结果
    print("\n摘要结果：")
    for i, (article, summary) in enumerate(zip(articles, summaries), 1):
        print(f"文章 {i}:")
        print(f"  原文: {article[:50]}...")
        print(f"  摘要: {summary.strip()}\n")


def example_sentiment_analysis():
    """示例：情感分析"""
    print("\n示例 3: 批量情感分析")
    print("-" * 60)

    # 模拟用户评论
    comments = [
        "这个产品太棒了！质量很好，物流也快，强烈推荐！",
        "价格有点贵，但是质量确实不错，总体满意。",
        "完全不值这个价格，质量很差，非常失望。",
        "客服态度很好，帮我解决了问题，点赞！",
        "收到的货和图片不一样，感觉被骗了。",
        "还可以吧，没什么特别的，也没什么缺点。",
    ]

    inference = Qwen3VLLMInference()

    # 准备提示
    sentiment_prompts = []
    for comment in comments:
        prompt = f"""分析以下评论的情感倾向。

评论：{comment}

请只回答：正面、负面或中性。"""
        sentiment_prompts.append([{"role": "user", "content": prompt}])

    # 批量推理
    sentiments = inference.chat(
        sentiment_prompts,
        temperature=0.1,
        max_tokens=10
    )

    # 显示结果和统计
    print("\n情感分析结果：")
    sentiment_count = {"正面": 0, "负面": 0, "中性": 0}

    for comment, sentiment in zip(comments, sentiments):
        sentiment = sentiment.strip()
        print(f"  评论: {comment}")
        print(f"  情感: {sentiment}\n")

        if "正面" in sentiment:
            sentiment_count["正面"] += 1
        elif "负面" in sentiment:
            sentiment_count["负面"] += 1
        else:
            sentiment_count["中性"] += 1

    print("统计结果：")
    for sentiment, count in sentiment_count.items():
        print(f"  {sentiment}: {count} ({count / len(comments) * 100:.1f}%)")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="批量推理示例")
    parser.add_argument(
        "--input-file",
        type=str,
        help="输入文件路径 (.txt, .json, .jsonl)"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="results.json",
        help="输出文件路径"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="批量大小"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="最大生成长度"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="温度参数"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="运行示例"
    )

    args = parser.parse_args()

    if args.examples:
        # 运行示例
        print("=" * 60)
        print("Qwen3 14B 批量推理示例")
        print("=" * 60)

        example_news_classification()
        example_summarization()
        example_sentiment_analysis()

    elif args.input_file:
        # 从文件加载数据并推理
        print("=" * 60)
        print("从文件批量推理")
        print("=" * 60)

        # 加载数据
        questions = load_data_from_file(args.input_file)
        print(f"✓ 已加载 {len(questions)} 条数据")

        # 初始化推理引擎
        inference = Qwen3VLLMInference()

        # 批量推理
        results = batch_inference_with_progress(
            inference,
            questions,
            batch_size=args.batch_size,
            max_tokens=args.max_tokens,
            temperature=args.temperature
        )

        # 保存结果
        save_results(results, args.output_file)

    else:
        parser.print_help()
        print("\n提示：使用 --examples 运行示例，或使用 --input-file 处理自己的数据")


if __name__ == "__main__":
    main()
