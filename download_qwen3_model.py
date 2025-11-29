#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen3 14B 模型下载脚本
支持 Windows 和 Linux 系统
支持多个镜像源：ModelScope（推荐国内用户）、HF-Mirror、Hugging Face
"""

import os
import sys
import platform
from pathlib import Path


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


def download_from_modelscope(model_id, local_dir):
    """
    从 ModelScope 下载模型（国内推荐）

    Args:
        model_id: ModelScope 模型 ID
        local_dir: 本地保存路径
    """
    try:
        from modelscope import snapshot_download as ms_snapshot_download

        print("使用 ModelScope 下载（阿里云，国内高速）")

        # ModelScope 下载
        ms_snapshot_download(
            model_id=model_id,
            cache_dir=str(local_dir.parent),
            local_dir=str(local_dir),
        )

        return True

    except ImportError:
        print("✗ 未安装 modelscope 库")
        print("安装命令: pip install modelscope")
        return False
    except Exception as e:
        print(f"✗ ModelScope 下载失败: {e}")
        return False


def download_from_huggingface(model_name, local_dir, use_mirror=False):
    """
    从 Hugging Face 下载模型

    Args:
        model_name: Hugging Face 模型名称
        local_dir: 本地保存路径
        use_mirror: 是否使用 HF-Mirror 镜像
    """
    try:
        from huggingface_hub import snapshot_download

        if use_mirror:
            print("使用 HF-Mirror 镜像站点")
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        else:
            print("使用 Hugging Face 官方源")

        # 下载模型
        snapshot_download(
            repo_id=model_name,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
        )

        return True

    except ImportError:
        print("✗ 未安装 huggingface_hub 库")
        print("安装命令: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"✗ Hugging Face 下载失败: {e}")
        return False


def download_model(
    model_name="Qwen/Qwen2.5-14B-Instruct",
    local_dir=None,
    source="auto"
):
    """
    下载 Qwen3 14B 模型

    Args:
        model_name: 模型名称
        local_dir: 本地保存路径
        source: 下载源 ("auto", "modelscope", "hf-mirror", "huggingface")
    """
    if local_dir is None:
        local_dir = get_model_path()

    # 创建目录
    local_dir.mkdir(parents=True, exist_ok=True)

    print(f"=" * 60)
    print(f"开始下载 Qwen3 14B 模型")
    print(f"模型名称: {model_name}")
    print(f"保存路径: {local_dir}")
    print(f"下载源: {source}")
    print(f"=" * 60)
    print()

    # ModelScope 模型 ID 映射
    modelscope_models = {
        "Qwen/Qwen2.5-14B-Instruct": "Qwen/Qwen2.5-14B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct": "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-72B-Instruct": "Qwen/Qwen2.5-72B-Instruct",
    }

    success = False

    try:
        if source == "modelscope":
            # 使用 ModelScope
            model_id = modelscope_models.get(model_name, model_name)
            success = download_from_modelscope(model_id, local_dir)

        elif source == "hf-mirror":
            # 使用 HF-Mirror
            success = download_from_huggingface(model_name, local_dir, use_mirror=True)

        elif source == "huggingface":
            # 使用 Hugging Face 官方
            success = download_from_huggingface(model_name, local_dir, use_mirror=False)

        elif source == "auto":
            # 自动选择：优先 ModelScope（国内快）
            print("自动模式: 优先尝试 ModelScope（国内高速）")
            print()

            model_id = modelscope_models.get(model_name, model_name)
            success = download_from_modelscope(model_id, local_dir)

            if not success:
                print("\n" + "=" * 60)
                print("ModelScope 失败，尝试 HF-Mirror...")
                print("=" * 60)
                print()
                success = download_from_huggingface(model_name, local_dir, use_mirror=True)

            if not success:
                print("\n" + "=" * 60)
                print("HF-Mirror 失败，尝试 Hugging Face 官方...")
                print("=" * 60)
                print()
                success = download_from_huggingface(model_name, local_dir, use_mirror=False)

        if success:
            print(f"\n✓ 模型下载完成！")
            print(f"模型位置: {local_dir}")

            # 验证下载的文件
            print("\n下载的文件列表:")
            files = sorted(local_dir.rglob("*"))
            file_count = 0
            for file in files:
                if file.is_file():
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"  {file.relative_to(local_dir)} ({size_mb:.2f} MB)")
                    file_count += 1
                    if file_count >= 20:  # 只显示前 20 个文件
                        remaining = len([f for f in files if f.is_file()]) - file_count
                        if remaining > 0:
                            print(f"  ... 还有 {remaining} 个文件")
                        break

            return str(local_dir)
        else:
            print(f"\n✗ 所有下载源都失败了")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(
        description="下载 Qwen3 14B 模型（支持多个镜像源）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自动选择最快源（推荐）
  python download_qwen3_model.py

  # 使用 ModelScope（国内推荐，阿里云）
  python download_qwen3_model.py --source modelscope

  # 使用 HF-Mirror 镜像
  python download_qwen3_model.py --source hf-mirror

  # 使用 Hugging Face 官方
  python download_qwen3_model.py --source huggingface

  # 自定义保存路径
  python download_qwen3_model.py --output-dir E:/models/qwen3

下载源说明:
  - auto:        自动选择（优先 ModelScope > HF-Mirror > Hugging Face）
  - modelscope:  ModelScope（魔搭社区，阿里云，国内最快）
  - hf-mirror:   HF-Mirror 镜像站点
  - huggingface: Hugging Face 官方（国外快）
        """
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="Qwen/Qwen2.5-14B-Instruct",
        help="模型名称（默认: Qwen/Qwen2.5-14B-Instruct）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="自定义模型保存路径（默认: Windows D:/models/qwen3-14b, Linux ~/models/qwen3-14b）"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="auto",
        choices=["auto", "modelscope", "hf-mirror", "huggingface"],
        help="下载源（默认: auto，自动选择最快的）"
    )
    # 保留旧的 --mirror 参数以兼容旧脚本
    parser.add_argument(
        "--mirror",
        action="store_true",
        help="使用 HF-Mirror（等同于 --source hf-mirror）"
    )

    args = parser.parse_args()

    # 兼容旧的 --mirror 参数
    if args.mirror and args.source == "auto":
        args.source = "hf-mirror"

    # 确定输出路径
    if args.output_dir:
        output_path = Path(args.output_dir)
    else:
        output_path = get_model_path()

    # 下载模型
    download_model(
        model_name=args.model_name,
        local_dir=output_path,
        source=args.source
    )


if __name__ == "__main__":
    main()
