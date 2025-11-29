#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen3 14B 推理脚本（不使用 vLLM）
适用于 Windows 系统，使用标准 transformers 库

性能比 vLLM 低，但兼容性更好
"""

import os
import sys
import platform
from pathlib import Path
from typing import List, Dict
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def get_model_path():
    """根据操作系统获取模型路径"""
    system = platform.system()

    if system == "Windows":
        model_dir = Path("D:/models/qwen3-14b")
    else:
        model_dir = Path.home() / "models" / "qwen3-14b"

    return str(model_dir)


class Qwen3Inference:
    """Qwen3 14B 标准推理类（使用 transformers）"""

    def __init__(
        self,
        model_path: str = None,
        device: str = "auto",
        load_in_8bit: bool = False,
        load_in_4bit: bool = False,
    ):
        """
        初始化模型

        Args:
            model_path: 模型路径
            device: 设备（"cuda", "cpu", "auto"）
            load_in_8bit: 是否使用 8-bit 量化（节省显存）
            load_in_4bit: 是否使用 4-bit 量化（节省更多显存）
        """
        if model_path is None:
            model_path = get_model_path()

        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"模型路径不存在: {model_path}\n"
                f"请先运行 download_qwen3_model.py 下载模型"
            )

        print(f"加载模型: {model_path}")
        print(f"设备: {device}")

        # 设置量化配置
        kwargs = {}
        if load_in_8bit:
            print("使用 8-bit 量化")
            kwargs["load_in_8bit"] = True
        elif load_in_4bit:
            print("使用 4-bit 量化")
            kwargs["load_in_4bit"] = True
        else:
            # 自动选择设备
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            kwargs["device_map"] = device

        # 加载 tokenizer
        print("加载 tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )

        # 加载模型
        print("加载模型（可能需要几分钟）...")
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            **kwargs
        )

        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"✓ 模型加载完成，设备: {self.device}")

    def generate(
        self,
        prompts: List[str],
        temperature: float = 0.7,
        top_p: float = 0.8,
        max_tokens: int = 512,
        **kwargs
    ) -> List[str]:
        """
        生成文本

        Args:
            prompts: 输入提示列表
            temperature: 温度参数
            top_p: Top-p 采样
            max_tokens: 最大生成长度

        Returns:
            生成的文本列表
        """
        results = []

        for prompt in prompts:
            # 编码输入
            inputs = self.tokenizer(prompt, return_tensors="pt")

            if self.device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            # 生成
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    **kwargs
                )

            # 解码输出
            generated_text = self.tokenizer.decode(
                outputs[0][len(inputs["input_ids"][0]):],
                skip_special_tokens=True
            )

            results.append(generated_text)

        return results

    def chat(
        self,
        messages_list: List[List[Dict]],
        temperature: float = 0.7,
        top_p: float = 0.8,
        max_tokens: int = 512,
        **kwargs
    ) -> List[str]:
        """
        对话模式生成

        Args:
            messages_list: 消息列表的列表
            temperature: 温度参数
            top_p: Top-p 采样
            max_tokens: 最大生成长度

        Returns:
            生成的回复列表
        """
        results = []

        for messages in messages_list:
            # 使用 tokenizer 的 chat 模板
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # 生成
            response = self.generate(
                [prompt],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                **kwargs
            )[0]

            results.append(response)

        return results


def main():
    """主函数 - 示例用法"""
    import argparse

    parser = argparse.ArgumentParser(description="Qwen3 14B 推理（不使用 vLLM）")
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="模型路径（默认自动检测）"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="设备"
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
    print("Qwen3 14B 推理引擎（transformers）")
    print("=" * 60)
    print()

    inference = Qwen3Inference(
        model_path=args.model_path,
        device=args.device,
        load_in_8bit=args.load_in_8bit,
        load_in_4bit=args.load_in_4bit,
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
        ]

        print(f"开始批量推理，共 {len(test_messages)} 条...")

        import time
        start_time = time.time()

        # 注意：标准 transformers 不支持真正的批量推理
        # 这里是顺序处理
        responses = inference.chat(test_messages, max_tokens=256)

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"\n✓ 批量推理完成")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"平均每条: {elapsed_time / len(test_messages):.2f} 秒")

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
