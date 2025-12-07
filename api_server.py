#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen 模型 API 服务
提供 HTTP API 接口供其他项目调用
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# ==================== 配置区域 ====================
# 您可以在这里修改默认配置

# 默认模型路径（Windows路径示例，根据实际情况修改）
DEFAULT_MODEL_PATH = "D:/models/qwen2.5-7b"

# 默认量化设置
DEFAULT_LOAD_IN_4BIT = True  # 默认使用4-bit量化
DEFAULT_LOAD_IN_8BIT = False  # 8-bit量化（与4-bit互斥）

# 默认设备
DEFAULT_DEVICE = "auto"  # auto/cuda/cpu

# API服务配置
API_HOST = "0.0.0.0"  # 监听所有网卡，改为 "127.0.0.1" 则只允许本机访问
API_PORT = 8000  # API端口

# 生成参数默认值
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.8

# ==================== 结束配置区域 ====================

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Qwen Model API",
    description="提供文本生成和对话功能的 API 服务",
    version="1.0.0"
)

# 全局模型和tokenizer
model = None
tokenizer = None


class GenerateRequest(BaseModel):
    """文本生成请求"""
    prompt: str = Field(..., description="输入提示文本")
    max_tokens: int = Field(DEFAULT_MAX_TOKENS, description="最大生成令牌数")
    temperature: float = Field(DEFAULT_TEMPERATURE, description="温度参数(0-2)")
    top_p: float = Field(DEFAULT_TOP_P, description="Top-p采样参数(0-1)")


class ChatMessage(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """对话请求"""
    messages: List[ChatMessage] = Field(..., description="对话历史")
    max_tokens: int = Field(DEFAULT_MAX_TOKENS, description="最大生成令牌数")
    temperature: float = Field(DEFAULT_TEMPERATURE, description="温度参数(0-2)")
    top_p: float = Field(DEFAULT_TOP_P, description="Top-p采样参数(0-1)")


class GenerateResponse(BaseModel):
    """生成响应"""
    generated_text: str
    prompt_tokens: int
    generated_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    """对话响应"""
    reply: str
    prompt_tokens: int
    generated_tokens: int
    total_tokens: int


def load_model(
    model_path: str = DEFAULT_MODEL_PATH,
    load_in_4bit: bool = DEFAULT_LOAD_IN_4BIT,
    load_in_8bit: bool = DEFAULT_LOAD_IN_8BIT,
    device: str = DEFAULT_DEVICE
):
    """加载模型"""
    global model, tokenizer

    logger.info(f"正在加载模型: {model_path}")
    logger.info(f"4-bit量化: {load_in_4bit}, 8-bit量化: {load_in_8bit}")

    # 检查本地路径
    is_local_path = (
        os.path.sep in model_path or
        "/" in model_path and not model_path.count("/") == 1 or
        ":" in model_path or
        model_path.startswith(".") or
        model_path.startswith("~")
    )

    if is_local_path:
        model_path_obj = Path(model_path).expanduser().resolve()
        if not model_path_obj.exists():
            raise FileNotFoundError(f"模型路径不存在: {model_path}")
        model_path = str(model_path_obj)
        logger.info(f"本地模型路径: {model_path}")

    load_kwargs = {"trust_remote_code": True}

    # 加载 tokenizer
    logger.info("加载 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, **load_kwargs)

    # 确定设备
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info(f"目标设备: {device}")

    # 加载模型
    logger.info("加载模型...")
    model_kwargs = {**load_kwargs}

    if load_in_4bit:
        logger.info("使用 4-bit 量化")
        model_kwargs["load_in_4bit"] = True
        model_kwargs["device_map"] = "auto"
    elif load_in_8bit:
        logger.info("使用 8-bit 量化")
        model_kwargs["load_in_8bit"] = True
        model_kwargs["device_map"] = "auto"
    else:
        model_kwargs["torch_dtype"] = torch.float16 if device == "cuda" else torch.float32
        model_kwargs["device_map"] = device if device != "cpu" else None

    model = AutoModelForCausalLM.from_pretrained(model_path, **model_kwargs)

    if device == "cpu" and not (load_in_4bit or load_in_8bit):
        model = model.to("cpu")

    logger.info("✓ 模型加载完成")


@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    logger.info("API 服务启动中...")
    load_model()
    logger.info("API 服务已就绪")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Qwen Model API",
        "status": "running",
        "docs": "/docs",
        "model_loaded": model is not None
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": str(next(model.parameters()).device) if model else None
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    文本生成接口

    示例请求:
    ```json
    {
        "prompt": "请介绍一下人工智能",
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.8
    }
    ```
    """
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    try:
        # 编码输入
        inputs = tokenizer(request.prompt, return_tensors="pt")
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        prompt_tokens = len(inputs["input_ids"][0])

        # 生成
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        # 解码
        generated_text = tokenizer.decode(
            outputs[0][len(inputs["input_ids"][0]):],
            skip_special_tokens=True
        )

        generated_tokens = len(outputs[0]) - prompt_tokens

        return GenerateResponse(
            generated_text=generated_text.strip(),
            prompt_tokens=prompt_tokens,
            generated_tokens=generated_tokens,
            total_tokens=prompt_tokens + generated_tokens
        )

    except Exception as e:
        logger.error(f"生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    对话接口

    示例请求:
    ```json
    {
        "messages": [
            {"role": "user", "content": "你好，请介绍一下你自己"}
        ],
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.8
    }
    ```
    """
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="模型未加载")

    try:
        # 转换消息格式
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # 使用 chat 模板
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # 编码
        inputs = tokenizer(prompt, return_tensors="pt")
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        prompt_tokens = len(inputs["input_ids"][0])

        # 生成
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        # 解码
        reply = tokenizer.decode(
            outputs[0][len(inputs["input_ids"][0]):],
            skip_special_tokens=True
        )

        generated_tokens = len(outputs[0]) - prompt_tokens

        return ChatResponse(
            reply=reply.strip(),
            prompt_tokens=prompt_tokens,
            generated_tokens=generated_tokens,
            total_tokens=prompt_tokens + generated_tokens
        )

    except Exception as e:
        logger.error(f"对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Qwen 模型 API 服务")
    parser.add_argument(
        "--model-path",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help=f"模型路径（默认: {DEFAULT_MODEL_PATH}）"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=API_HOST,
        help=f"监听地址（默认: {API_HOST}）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=API_PORT,
        help=f"监听端口（默认: {API_PORT}）"
    )
    parser.add_argument(
        "--no-4bit",
        action="store_true",
        help="禁用4-bit量化（默认启用）"
    )
    parser.add_argument(
        "--load-in-8bit",
        action="store_true",
        help="使用8-bit量化替代4-bit"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=DEFAULT_DEVICE,
        choices=["auto", "cuda", "cpu"],
        help=f"设备选择（默认: {DEFAULT_DEVICE}）"
    )

    args = parser.parse_args()

    # 更新全局配置
    global DEFAULT_MODEL_PATH, DEFAULT_LOAD_IN_4BIT, DEFAULT_LOAD_IN_8BIT, DEFAULT_DEVICE
    DEFAULT_MODEL_PATH = args.model_path
    DEFAULT_LOAD_IN_4BIT = not args.no_4bit and not args.load_in_8bit
    DEFAULT_LOAD_IN_8BIT = args.load_in_8bit
    DEFAULT_DEVICE = args.device

    # 启动服务
    logger.info(f"启动 API 服务: http://{args.host}:{args.port}")
    logger.info(f"API 文档: http://{args.host}:{args.port}/docs")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
