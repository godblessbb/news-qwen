#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 vLLM 进行 Qwen3 14B 模型推理
支持高吞吐量的文本生成
"""

import os
import sys
import platform
from pathlib import Path
from typing import List, Optional
from vllm import LLM, SamplingParams


def get_model_path():
    """根据操作系统获取模型路径"""
    system = platform.system()

    if system == "Windows":
        model_dir = Path("D:/models/qwen3-14b")
    else:
        model_dir = Path.home() / "models" / "qwen3-14b"

    return str(model_dir)


class Qwen3VLLMInference:
    """Qwen3 14B vLLM 推理类"""

    def __init__(
        self,
        model_path: Optional[str] = None,
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.9,
        max_model_len: Optional[int] = None,
        trust_remote_code: bool = True
    ):
        """
        初始化 vLLM 引擎

        Args:
            model_path: 模型路径，默认自动检测
            tensor_parallel_size: 张量并行大小（GPU 数量）
            gpu_memory_utilization: GPU 内存利用率 (0-1)
            max_model_len: 最大模型长度
            trust_remote_code: 是否信任远程代码
        """
        if model_path is None:
            model_path = get_model_path()

        # 检查模型路径是否存在
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"模型路径不存在: {model_path}\n"
                f"请先运行 download_qwen3_model.py 下载模型"
            )

        print(f"加载模型: {model_path}")
        print(f"张量并行大小: {tensor_parallel_size}")
        print(f"GPU 内存利用率: {gpu_memory_utilization}")

        # 初始化 vLLM
        self.llm = LLM(
            model=model_path,
            tensor_parallel_size=tensor_parallel_size,
            gpu_memory_utilization=gpu_memory_utilization,
            max_model_len=max_model_len,
            trust_remote_code=trust_remote_code,
        )

        print("✓ 模型加载完成")

    def generate(
        self,
        prompts: List[str],
        temperature: float = 0.7,
        top_p: float = 0.8,
        top_k: int = 20,
        max_tokens: int = 512,
        repetition_penalty: float = 1.05,
        **kwargs
    ) -> List[str]:
        """
        生成文本

        Args:
            prompts: 输入提示列表
            temperature: 温度参数
            top_p: Top-p 采样
            top_k: Top-k 采样
            max_tokens: 最大生成长度
            repetition_penalty: 重复惩罚

        Returns:
            生成的文本列表
        """
        # 配置采样参数
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens,
            repetition_penalty=repetition_penalty,
            **kwargs
        )

        # 批量生成
        outputs = self.llm.generate(prompts, sampling_params)

        # 提取生成的文本
        results = []
        for output in outputs:
            generated_text = output.outputs[0].text
            results.append(generated_text)

        return results

    def chat(
        self,
        messages_list: List[List[dict]],
        temperature: float = 0.7,
        top_p: float = 0.8,
        max_tokens: int = 512,
        **kwargs
    ) -> List[str]:
        """
        对话模式生成

        Args:
            messages_list: 消息列表的列表，每个消息格式为:
                           [{"role": "user", "content": "你好"}]
            temperature: 温度参数
            top_p: Top-p 采样
            max_tokens: 最大生成长度

        Returns:
            生成的回复列表
        """
        # 将消息转换为提示格式
        prompts = []
        for messages in messages_list:
            # Qwen 模型的对话格式
            prompt = ""
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
                elif role == "user":
                    prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
                elif role == "assistant":
                    prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
            prompt += "<|im_start|>assistant\n"
            prompts.append(prompt)

        # 生成回复
        return self.generate(
            prompts=prompts,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stop=["<|im_end|>"],
            **kwargs
        )


def main():
    """主函数 - 示例用法"""
    import argparse

    parser = argparse.ArgumentParser(description="Qwen3 14B vLLM 推理")
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="模型路径（默认自动检测）"
    )
    parser.add_argument(
        "--tensor-parallel-size",
        type=int,
        default=1,
        help="张量并行大小（GPU 数量）"
    )
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=0.9,
        help="GPU 内存利用率 (0-1)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互模式"
    )
    parser.add_argument(
        "--batch-test",
        action="store_true",
        help="批量测试模式"
    )

    args = parser.parse_args()

    # 初始化推理引擎
    print("=" * 60)
    print("Qwen3 14B vLLM 推理引擎")
    print("=" * 60)

    inference = Qwen3VLLMInference(
        model_path=args.model_path,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
    )

    if args.interactive:
        # 交互模式
        print("\n进入交互模式（输入 'quit' 退出）")
        print("-" * 60)

        conversation = []
        while True:
            user_input = input("\n用户: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                break

            if not user_input:
                continue

            conversation.append({"role": "user", "content": user_input})

            # 生成回复
            responses = inference.chat([conversation])
            assistant_reply = responses[0]

            print(f"\n助手: {assistant_reply}")

            conversation.append({"role": "assistant", "content": assistant_reply})

    elif args.batch_test:
        # 批量测试模式
        print("\n批量推理测试")
        print("-" * 60)

        test_messages = [
            [{"role": "user", "content": "什么是人工智能？"}],
            [{"role": "user", "content": "请用一句话介绍量子计算"}],
            [{"role": "user", "content": "Python 和 JavaScript 的主要区别是什么？"}],
            [{"role": "user", "content": "如何提高深度学习模型的性能？"}],
            [{"role": "user", "content": "解释一下什么是大语言模型"}],
        ]

        print(f"开始批量推理，共 {len(test_messages)} 条...")

        import time
        start_time = time.time()

        responses = inference.chat(test_messages, max_tokens=256)

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"\n✓ 批量推理完成")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"平均每条: {elapsed_time / len(test_messages):.2f} 秒")
        print(f"吞吐量: {len(test_messages) / elapsed_time:.2f} 条/秒")

        print("\n结果展示:")
        print("=" * 60)
        for i, (messages, response) in enumerate(zip(test_messages, responses), 1):
            print(f"\n问题 {i}: {messages[0]['content']}")
            print(f"回答: {response}")
            print("-" * 60)

    else:
        # 单次测试
        print("\n单次推理测试")
        print("-" * 60)

        test_messages = [
            [{"role": "user", "content": "你好，请介绍一下你自己"}]
        ]

        responses = inference.chat(test_messages)
        print(f"\n问题: {test_messages[0][0]['content']}")
        print(f"回答: {responses[0]}")


if __name__ == "__main__":
    main()
