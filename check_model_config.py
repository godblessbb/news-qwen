#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看模型配置信息
"""

import sys
from pathlib import Path
from transformers import AutoConfig

def check_model_config(model_path):
    """查看模型配置"""
    try:
        config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)

        print("=" * 60)
        print(f"模型配置信息: {model_path}")
        print("=" * 60)
        print()

        # 关键配置信息
        print("📊 关键参数:")
        print(f"  模型架构: {config.model_type}")
        print(f"  隐藏层大小: {config.hidden_size}")
        print(f"  注意力头数: {config.num_attention_heads}")
        print(f"  层数: {config.num_hidden_layers}")

        print()
        print("📏 上下文长度配置:")

        # 最大位置编码
        if hasattr(config, 'max_position_embeddings'):
            print(f"  最大位置编码: {config.max_position_embeddings:,} tokens")

        # 最大窗口大小
        if hasattr(config, 'max_window_layers'):
            print(f"  最大窗口层: {config.max_window_layers}")

        # RoPE 相关
        if hasattr(config, 'rope_theta'):
            print(f"  RoPE Theta: {config.rope_theta:,}")

        if hasattr(config, 'rope_scaling'):
            print(f"  RoPE 缩放: {config.rope_scaling}")

        # 词汇表大小
        if hasattr(config, 'vocab_size'):
            print()
            print("📖 词汇表:")
            print(f"  词汇表大小: {config.vocab_size:,}")

        print()
        print("=" * 60)
        print("💡 实际使用建议:")
        print("=" * 60)

        max_len = config.max_position_embeddings if hasattr(config, 'max_position_embeddings') else 32768

        print(f"""
  ✅ 理论最大输入长度: {max_len:,} tokens

  📝 实际使用建议:
     - 对话/问答: 2,000 - 8,000 tokens
     - 长文档处理: 8,000 - 16,000 tokens
     - 极限长文本: 最高 {max_len:,} tokens

  ⚠️  注意事项:
     - 输入越长,推理速度越慢
     - 输入越长,显存占用越大
     - 建议根据任务需求控制输入长度

  📊 Token 估算:
     - 中文: 1个字 ≈ 1-2 tokens
     - 英文: 1个单词 ≈ 1-2 tokens
     - 例如: 1000个汉字 ≈ 1000-2000 tokens
        """)

    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1

    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        # 默认路径
        import platform
        if platform.system() == "Windows":
            model_path = "D:/models/qwen2.5-7b"
        else:
            model_path = str(Path.home() / "models" / "qwen2.5-7b")

    exit(check_model_config(model_path))
