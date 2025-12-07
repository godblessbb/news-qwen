#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 客户端调用示例
展示如何从其他Python项目调用 Qwen API
"""

import requests
import json


class QwenAPIClient:
    """Qwen API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化客户端

        Args:
            base_url: API服务地址
        """
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> dict:
        """健康检查"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.8
    ) -> dict:
        """
        文本生成

        Args:
            prompt: 输入提示
            max_tokens: 最大生成令牌数
            temperature: 温度参数
            top_p: Top-p采样参数

        Returns:
            生成结果字典
        """
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }

        response = requests.post(
            f"{self.base_url}/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def chat(
        self,
        messages: list,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.8
    ) -> dict:
        """
        对话生成

        Args:
            messages: 对话历史，格式: [{"role": "user", "content": "..."}]
            max_tokens: 最大生成令牌数
            temperature: 温度参数
            top_p: Top-p采样参数

        Returns:
            对话结果字典
        """
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }

        response = requests.post(
            f"{self.base_url}/chat",
            json=payload
        )
        response.raise_for_status()
        return response.json()


def example_generate():
    """示例：文本生成"""
    print("=" * 60)
    print("示例 1: 文本生成")
    print("=" * 60)

    client = QwenAPIClient()

    # 检查服务状态
    health = client.health_check()
    print(f"服务状态: {health}")

    # 生成文本
    prompt = "请用一句话介绍人工智能："
    print(f"\n输入: {prompt}")

    result = client.generate(
        prompt=prompt,
        max_tokens=256,
        temperature=0.7
    )

    print(f"输出: {result['generated_text']}")
    print(f"令牌统计: prompt={result['prompt_tokens']}, "
          f"generated={result['generated_tokens']}, "
          f"total={result['total_tokens']}")


def example_chat():
    """示例：对话"""
    print("\n" + "=" * 60)
    print("示例 2: 对话")
    print("=" * 60)

    client = QwenAPIClient()

    messages = [
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ]

    print(f"\n用户: {messages[0]['content']}")

    result = client.chat(
        messages=messages,
        max_tokens=256
    )

    print(f"助手: {result['reply']}")
    print(f"令牌统计: prompt={result['prompt_tokens']}, "
          f"generated={result['generated_tokens']}, "
          f"total={result['total_tokens']}")

    # 继续对话
    messages.append({"role": "assistant", "content": result['reply']})
    messages.append({"role": "user", "content": "你能做什么？"})

    print(f"\n用户: {messages[-1]['content']}")

    result = client.chat(messages=messages, max_tokens=256)

    print(f"助手: {result['reply']}")


def example_news_analysis():
    """示例：新闻分析"""
    print("\n" + "=" * 60)
    print("示例 3: 新闻分析（实际应用场景）")
    print("=" * 60)

    client = QwenAPIClient()

    # 模拟新闻数据
    news_list = [
        "美国航空Q3财报超预期，营收增长12%",
        "燃油价格上涨对航空业构成压力",
        "多家机构维持AAL买入评级"
    ]

    prompt = f"""请分析以下新闻事件并给出简洁总结：

{chr(10).join([f"{i+1}. {news}" for i, news in enumerate(news_list)])}

要求：
1. 使用过去时态
2. 包含情感属性
3. 控制在100字以内
"""

    print(f"输入新闻数量: {len(news_list)}")

    result = client.generate(
        prompt=prompt,
        max_tokens=256,
        temperature=0.7
    )

    print(f"\n分析结果:\n{result['generated_text']}")


def example_curl():
    """生成 curl 命令示例"""
    print("\n" + "=" * 60)
    print("示例 4: 使用 curl 调用（非Python项目）")
    print("=" * 60)

    print("\n文本生成:")
    print("""
curl -X POST "http://localhost:8000/generate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "请介绍人工智能",
    "max_tokens": 256,
    "temperature": 0.7
  }'
""")

    print("\n对话:")
    print("""
curl -X POST "http://localhost:8000/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "max_tokens": 256
  }'
""")


def main():
    """主函数"""
    print("Qwen API 客户端示例\n")

    try:
        # 示例 1: 文本生成
        example_generate()

        # 示例 2: 对话
        example_chat()

        # 示例 3: 实际应用（新闻分析）
        example_news_analysis()

        # 示例 4: curl 命令
        example_curl()

    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到 API 服务")
        print("请确保 API 服务已启动:")
        print("  python api_server.py")
    except Exception as e:
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
