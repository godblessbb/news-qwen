import sys
import os

print("="*60)
print("Python 环境测试")
print("="*60)
print(f"Python 版本: {sys.version}")
print(f"Python 路径: {sys.executable}")
print(f"当前工作目录: {os.getcwd^(^)}")
print("="*60)

# 测试导入
packages = ['torch', 'vllm', 'transformers', 'numpy']
for package in packages:
    try:
        module = __import__(package)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {package}: {version}")
    except ImportError:
        print(f"✗ {package}: 未安装")
