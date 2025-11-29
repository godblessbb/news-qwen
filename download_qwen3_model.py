#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen3 14B 模型下载脚本
支持 Windows 和 Linux 系统
"""

import os
import sys
import platform
from pathlib import Path
from huggingface_hub import snapshot_download


def get_model_path():
    """根据操作系统获取模型保存路径"""
    system = platform.system()

    if system == "Windows":
        # Windows 系统使用 D 盘
        model_dir = Path("D:/models/qwen3-14b")
    else:
        # Linux/Mac 系统使用用户主目录
        model_dir = Path.home() / "models" / "qwen3-14b"

    return model_dir


def download_model(model_name="Qwen/Qwen2.5-14B-Instruct", local_dir=None):
    """
    下载 Qwen3 14B 模型

    Args:
        model_name: Hugging Face 模型名称
        local_dir: 本地保存路径
    """
    if local_dir is None:
        local_dir = get_model_path()

    # 创建目录
    local_dir.mkdir(parents=True, exist_ok=True)

    print(f"=" * 60)
    print(f"开始下载 Qwen3 14B 模型")
    print(f"模型名称: {model_name}")
    print(f"保存路径: {local_dir}")
    print(f"=" * 60)

    try:
        # 下载模型
        snapshot_download(
            repo_id=model_name,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
            # 如果需要使用镜像站点，可以添加 endpoint 参数
            # endpoint="https://hf-mirror.com"
        )

        print(f"\n✓ 模型下载完成！")
        print(f"模型位置: {local_dir}")

        # 验证下载的文件
        print("\n下载的文件列表:")
        for file in sorted(local_dir.rglob("*")):
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  {file.relative_to(local_dir)} ({size_mb:.2f} MB)")

        return str(local_dir)

    except Exception as e:
        print(f"\n✗ 下载失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    # 可选：指定自定义路径
    import argparse
    parser = argparse.ArgumentParser(description="下载 Qwen3 14B 模型")
    parser.add_argument(
        "--model-name",
        type=str,
        default="Qwen/Qwen2.5-14B-Instruct",
        help="Hugging Face 模型名称"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="自定义模型保存路径（默认: Windows D:/models/qwen3-14b, Linux ~/models/qwen3-14b）"
    )
    parser.add_argument(
        "--mirror",
        action="store_true",
        help="使用 Hugging Face 镜像站点（中国大陆推荐）"
    )

    args = parser.parse_args()

    # 如果使用镜像，设置环境变量
    if args.mirror:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print("使用 Hugging Face 镜像站点")

    # 确定输出路径
    if args.output_dir:
        output_path = Path(args.output_dir)
    else:
        output_path = get_model_path()

    # 下载模型
    download_model(model_name=args.model_name, local_dir=output_path)


if __name__ == "__main__":
    main()
