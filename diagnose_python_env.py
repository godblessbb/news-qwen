#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 环境诊断脚本
用于诊断 PyCharm 无法加载解释器的问题
"""

import sys
import os
import platform
import subprocess
from pathlib import Path


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60 + "\n")


def check_python_info():
    """检查 Python 基本信息"""
    print_section("Python 基本信息")

    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print(f"Python 版本: {sys.version}")
    print(f"Python 实现: {platform.python_implementation()}")
    print(f"Python 可执行文件: {sys.executable}")
    print(f"Python 安装前缀: {sys.prefix}")
    print(f"Python 基础前缀: {sys.base_prefix}")

    # 检查是否在虚拟环境中
    in_venv = sys.prefix != sys.base_prefix
    print(f"是否在虚拟环境: {'是' if in_venv else '否'}")


def check_environment_variables():
    """检查环境变量"""
    print_section("环境变量")

    important_vars = [
        'PATH',
        'PYTHONPATH',
        'VIRTUAL_ENV',
        'CONDA_PREFIX',
        'CONDA_DEFAULT_ENV',
        'CONDA_EXE',
        'HOME',
        'USERPROFILE',
    ]

    for var in important_vars:
        value = os.environ.get(var)
        if value:
            print(f"{var}:")
            if var == 'PATH':
                # PATH 变量特殊处理，每个路径一行
                paths = value.split(os.pathsep)
                for i, path in enumerate(paths[:10], 1):  # 只显示前10个
                    print(f"  {i}. {path}")
                if len(paths) > 10:
                    print(f"  ... 还有 {len(paths) - 10} 个路径")
            else:
                print(f"  {value}")
        else:
            print(f"{var}: (未设置)")
        print()


def check_conda():
    """检查 Conda 环境"""
    print_section("Conda 环境")

    try:
        # 检查 conda 可执行文件
        result = subprocess.run(
            ['conda', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"✓ Conda 已安装: {result.stdout.strip()}")

            # 获取 conda 路径
            conda_exe = subprocess.run(
                ['which', 'conda'] if platform.system() != 'Windows' else ['where', 'conda'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if conda_exe.returncode == 0:
                print(f"Conda 路径: {conda_exe.stdout.strip()}")

            # 列出所有环境
            print("\nConda 环境列表:")
            env_result = subprocess.run(
                ['conda', 'env', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if env_result.returncode == 0:
                print(env_result.stdout)
            else:
                print(f"✗ 无法列出环境: {env_result.stderr}")

        else:
            print(f"✗ Conda 命令执行失败: {result.stderr}")

    except FileNotFoundError:
        print("✗ Conda 未安装或不在 PATH 中")
    except subprocess.TimeoutExpired:
        print("✗ Conda 命令执行超时")
    except Exception as e:
        print(f"✗ 检查 Conda 时出错: {e}")


def find_python_executables():
    """查找系统中的 Python 可执行文件"""
    print_section("查找 Python 可执行文件")

    if platform.system() == "Windows":
        # Windows 系统
        search_paths = [
            Path(os.environ.get('USERPROFILE', 'C:\\Users')) / 'anaconda3',
            Path(os.environ.get('USERPROFILE', 'C:\\Users')) / 'miniconda3',
            Path('C:\\ProgramData\\Anaconda3'),
            Path('C:\\ProgramData\\Miniconda3'),
            Path('C:\\Python*'),
        ]

        python_names = ['python.exe', 'python3.exe']

    else:
        # Linux/Mac 系统
        search_paths = [
            Path.home() / 'anaconda3',
            Path.home() / 'miniconda3',
            Path('/opt/anaconda3'),
            Path('/opt/miniconda3'),
            Path('/usr/bin'),
            Path('/usr/local/bin'),
        ]

        python_names = ['python', 'python3']

    found_pythons = set()

    print("搜索常见位置...")
    for search_path in search_paths:
        if search_path.exists() and search_path.is_dir():
            for python_name in python_names:
                # 搜索主目录
                python_path = search_path / python_name
                if python_path.exists():
                    found_pythons.add(str(python_path.resolve()))

                # 搜索 bin 目录
                bin_path = search_path / 'bin' / python_name
                if bin_path.exists():
                    found_pythons.add(str(bin_path.resolve()))

                # 搜索 Scripts 目录（Windows）
                scripts_path = search_path / 'Scripts' / python_name
                if scripts_path.exists():
                    found_pythons.add(str(scripts_path.resolve()))

                # 搜索 envs 目录
                envs_path = search_path / 'envs'
                if envs_path.exists():
                    for env_dir in envs_path.iterdir():
                        if env_dir.is_dir():
                            env_python = env_dir / 'bin' / python_name
                            if env_python.exists():
                                found_pythons.add(str(env_python.resolve()))

                            env_python = env_dir / 'Scripts' / python_name
                            if env_python.exists():
                                found_pythons.add(str(env_python.resolve()))

    if found_pythons:
        print(f"\n找到 {len(found_pythons)} 个 Python 解释器:\n")
        for i, python_path in enumerate(sorted(found_pythons), 1):
            print(f"{i}. {python_path}")
            # 尝试获取版本
            try:
                version_result = subprocess.run(
                    [python_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                version = version_result.stdout.strip() or version_result.stderr.strip()
                print(f"   版本: {version}")
            except:
                print(f"   版本: (无法获取)")
            print()
    else:
        print("✗ 未找到 Python 解释器")


def check_installed_packages():
    """检查已安装的包"""
    print_section("已安装的重要包")

    important_packages = [
        'torch',
        'vllm',
        'transformers',
        'huggingface-hub',
        'numpy',
    ]

    for package in important_packages:
        try:
            module = __import__(package.replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {package}: {version}")
        except ImportError:
            print(f"✗ {package}: 未安装")


def check_pycharm_config():
    """检查 PyCharm 配置目录"""
    print_section("PyCharm 配置")

    if platform.system() == "Windows":
        base_path = Path(os.environ.get('APPDATA', '')) / 'JetBrains'
        local_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'JetBrains'
    elif platform.system() == "Darwin":
        base_path = Path.home() / 'Library' / 'Application Support' / 'JetBrains'
        local_path = Path.home() / 'Library' / 'Caches' / 'JetBrains'
    else:
        base_path = Path.home() / '.config' / 'JetBrains'
        local_path = Path.home() / '.cache' / 'JetBrains'

    print(f"配置目录: {base_path}")
    print(f"缓存目录: {local_path}\n")

    # 查找 PyCharm 版本
    if base_path.exists():
        pycharm_dirs = list(base_path.glob('PyCharm*'))
        if pycharm_dirs:
            print("找到的 PyCharm 版本:")
            for pycharm_dir in pycharm_dirs:
                print(f"  - {pycharm_dir.name}")
        else:
            print("✗ 未找到 PyCharm 配置")
    else:
        print("✗ 配置目录不存在")


def generate_fix_suggestions():
    """生成修复建议"""
    print_section("修复建议")

    suggestions = []

    # 检查 conda
    try:
        result = subprocess.run(['conda', '--version'], capture_output=True, timeout=2)
        if result.returncode != 0:
            suggestions.append("1. Conda 未正确安装，请重新安装 Anaconda 或 Miniconda")
    except:
        suggestions.append("1. Conda 不在 PATH 中，请添加 conda 到系统环境变量")

    # 检查权限
    if platform.system() != "Windows":
        python_path = Path(sys.executable)
        if not os.access(python_path, os.X_OK):
            suggestions.append(f"2. Python 可执行文件权限不足: {python_path}")

    # 通用建议
    suggestions.extend([
        "\n通用解决方案:",
        "• 在 PyCharm 中: File -> Invalidate Caches / Restart",
        "• 手动添加解释器: Settings -> Project -> Python Interpreter -> Add",
        "• 使用系统终端验证 conda 和 python 命令可用",
        "• 检查防病毒软件是否阻止 PyCharm 访问 Python",
    ])

    for suggestion in suggestions:
        print(suggestion)


def main():
    """主函数"""
    print("=" * 60)
    print(" Python 环境诊断工具")
    print(" 用于诊断 PyCharm 解释器问题")
    print("=" * 60)

    check_python_info()
    check_environment_variables()
    check_conda()
    find_python_executables()
    check_installed_packages()
    check_pycharm_config()
    generate_fix_suggestions()

    print_section("诊断完成")
    print("请将以上信息保存，以便进一步排查问题。")
    print("\n详细的修复指南请查看: fix_pycharm_interpreter.md")


if __name__ == "__main__":
    main()
