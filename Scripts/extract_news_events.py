#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件驱动型新闻分析脚本
从新闻数据中提取对股价有重大影响的事件

周期定义: 上周六 00:00 - 下周五 23:59
"""

import os
import sys
import argparse
import pandas as pd
import torch
from datetime import datetime, timedelta
from pathlib import Path
import platform
import json
import re

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformers import AutoModelForCausalLM, AutoTokenizer

# 尝试导入 BitsAndBytesConfig，如果失败则使用8-bit量化
try:
    from transformers import BitsAndBytesConfig
    BITSANDBYTES_AVAILABLE = True
except ImportError:
    BITSANDBYTES_AVAILABLE = False
    print("⚠️  警告: BitsAndBytes 不可用，将使用 8-bit 量化")

# ==================== 模型配置 ====================

# Qwen2.5-3B 模型上下文长度：32K tokens
# 约等于：
# - 中文：24,000-28,000 字
# - 英文：约 24,000 词
# 为安全起见，我们限制单批次输入为 20,000 tokens (约 15,000 中文字或 18,000 英文词)
MAX_INPUT_TOKENS = 20000  # 模型输入token上限
MAX_INPUT_CHARS = 15000   # 单批次最大字符数（保守估计）

# 事件分析 Prompt 模板
EVENT_ANALYSIS_PROMPT = """你是一位专业的事件驱动型股票交易策略分析师。你的任务是从新闻数据中提取对股价有**重大影响**的事件。

**分析对象**: {symbol} ({name})
**分析周期**: {period_start} 至 {period_end}
{batch_info}

**新闻数据**:
{news_data}

**分析要求**:

1. **事实优先**: 只关注已发生的事实性事件，忽略预测、观点、分析师评级变化

2. **重大影响**: 只提取对股价有实质性影响的事件。分为以下类型：

   **A. 常规重大事件**:
   - 财报发布（业绩超预期/不及预期）
   - 重大合同、订单、合作
   - 产品发布、技术突破
   - 并购、重组、分拆
   - 监管行动、诉讼裁决
   - 高管变动、战略调整
   - 重大投资、融资

   **B. 黑天鹅/突发事件** (⚠️ 重点关注):
   - 安全事故（工厂爆炸、火灾、重大伤亡、数据泄露）
   - 产品质量危机（大规模召回、严重安全漏洞、致命缺陷）
   - 供应链中断（关键供应商倒闭/停产、原材料断供）
   - 网络安全事件（黑客攻击、系统瘫痪、勒索软件）
   - 自然灾害影响（地震、洪水、疫情导致的停产/关闭）
   - 竞争对手的颠覆性举动（可能改变市场格局）

   **C. 舆情/声誉危机** (⚠️ 重点关注):
   - 公关危机（CEO/高管丑闻、企业不当行为曝光）
   - 大规模消费者抵制运动
   - 病毒式传播的负面舆论（社交媒体风暴）
   - 重大劳工纠纷（大规模罢工、工会冲突）
   - 环境污染事故或ESG重大争议
   - 虚假广告、欺诈指控

   **D. 政治/地缘/监管风险** (⚠️ 重点关注):
   - 贸易政策突变（关税加征、贸易禁令）
   - 政府制裁、出口管制
   - 地缘政治冲突直接影响（战争、外交危机）
   - 行业监管政策突然收紧/放松
   - 反垄断调查、政府介入
   - 国家安全审查、强制剥离资产
   - 重大政策变化（税收、补贴、行业准入）

   **判断标准**:
   - 事件是否会导致股价**单日波动 > 5%**？
   - 事件是否会影响公司**未来 1-2 个季度的业绩**？
   - 事件是否会改变市场对公司的**长期预期**？

   如果答案是"是"，则提取；否则忽略。

3. **事件归类**: 将相关新闻归为同一事件，例如：
   - 多条新闻报道同一财报 → 归为一个"Q3财报"事件
   - 多条新闻提到同一产品发布 → 归为一个"产品发布"事件

4. **排除内容**:
   - 单纯的分析师评级调整（如"XX维持买入评级"）
   - 预测性内容（"预计将..."、"可能会..."）
   - 市场情绪、技术分析
   - 无实质内容的消息

5. **情感色彩**: 判断事件对股价的影响（正面/中性/负面）

**输出格式** (JSON数组，每个事件一个对象):

```json
[
  {{
    "event_start": "2024-11-08 10:55:00",
    "event_end": "2024-11-09 15:30:00",
    "event_description": "苹果公布2024财年Q4财报，营收949亿美元同比增长6%，iPhone营收463亿美元超预期，净利润147亿美元。财报显示服务业务持续增长，但大中华区营收下降。整体业绩超华尔街预期，股价影响偏正面。",
    "earliest_news_title": "Apple Reports Fourth Quarter Results",
    "earliest_news_date": "2024-11-08 10:55:00",
    "related_count": 5,
    "chg_in_5": 2.5,
    "chg_in_10": 5.3,
    "source": "Apple Newsroom"
  }},
  {{
    "event_start": "2024-11-10 09:00:00",
    "event_end": "2024-11-10 09:00:00",
    "event_description": "苹果与OpenAI达成战略合作，将ChatGPT集成到iOS 18中。合作将使Siri能够调用ChatGPT功能，提升AI能力。此举标志苹果加速AI布局，对股价影响偏正面。",
    "earliest_news_title": "Apple and OpenAI Announce Partnership",
    "earliest_news_date": "2024-11-10 09:00:00",
    "related_count": 3,
    "chg_in_5": 1.8,
    "chg_in_10": 4.2,
    "source": "Bloomberg"
  }},
  {{
    "event_start": "2024-11-12 14:20:00",
    "event_end": "2024-11-13 18:45:00",
    "event_description": "美国政府宣布对中国出口iPhone所需芯片实施新的限制措施，禁止使用特定制程芯片。此举可能严重影响苹果供应链和对华销售。多家分析师下调苹果目标价，预计将影响Q1出货量。股价影响明显负面。",
    "earliest_news_title": "US Imposes New Chip Export Restrictions",
    "earliest_news_date": "2024-11-12 14:20:00",
    "related_count": 8,
    "chg_in_5": -4.2,
    "chg_in_10": -6.8,
    "source": "Reuters"
  }}
]
```

**重要**:
- 如果本批次新闻中没有符合条件的重大事件，返回空数组: []
- 只返回JSON数组，不要任何其他文字
- event_description 需要高度概括，包含关键数据和情感倾向
- earliest_news_title、earliest_news_date、chg_in_5、chg_in_10、source 必须来自实际新闻数据
- related_count 是被归类到该事件的新闻条数

请开始分析:"""

# 批次合并 Prompt
MERGE_EVENTS_PROMPT = """你是一位专业的事件驱动型股票交易策略分析师。现在需要合并多个批次分析得到的事件。

**分析对象**: {symbol} ({name})
**分析周期**: {period_start} 至 {period_end}

**各批次提取的事件**:
{events_json}

**任务**:
1. 检查是否有重复或相关的事件需要合并
2. 如果多个事件实际上是同一事件，合并它们：
   - 使用最早的 event_start
   - 使用最晚的 event_end
   - 合并 event_description（保持简洁，150字内）
   - 使用最早的新闻作为 earliest_news
   - related_count 为所有相关事件的 related_count 之和
   - chg_in_5, chg_in_10, source 使用 earliest_news 对应的值

3. 如果事件确实是不同的事件，保持分离

**输出格式**:
返回合并后的JSON数组，格式同输入。只返回JSON，不要其他文字。

合并后的事件:"""


def get_model_path():
    """获取默认模型路径"""
    system = platform.system()
    if system == "Windows":
        return "D:/models/qwen2.5-3b"
    else:
        return str(Path.home() / "models" / "qwen2.5-3b")


def load_model(model_path: str, device: str = "auto", use_quantization: bool = True):
    """
    加载 Qwen 模型和 tokenizer (默认 4-bit 量化，如果不可用则降级)

    Args:
        model_path: 模型路径
        device: 设备 (auto/cuda/cpu)
        use_quantization: 是否使用 4-bit 量化 (Windows 上可能需要禁用)

    Returns:
        model, tokenizer
    """
    import traceback

    # 强制刷新输出
    def log(msg):
        print(msg, flush=True)

    log(f"正在加载模型: {model_path}")

    # 检查模型路径是否存在
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型路径不存在: {model_path}")

    # CUDA 诊断信息
    log(f"\n--- CUDA 诊断 ---")
    log(f"PyTorch 版本: {torch.__version__}")
    log(f"CUDA 可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        log(f"CUDA 版本: {torch.version.cuda}")
        log(f"GPU 数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            log(f"GPU {i}: {props.name}")
            log(f"  显存: {props.total_memory / 1024**3:.1f} GB")
            log(f"  当前显存使用: {torch.cuda.memory_allocated(i) / 1024**3:.2f} GB")
    log(f"-----------------\n")

    # 加载 tokenizer
    log(f"加载 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True
    )
    log(f"✅ Tokenizer 加载完成")

    log(f"开始加载模型文件...")

    # 根据 BitsAndBytes 可用性选择量化方式
    quantization_successful = False

    if not use_quantization:
        log(f"⚠️  已禁用 4-bit 量化 (--no-quantize)")
    elif BITSANDBYTES_AVAILABLE:
        try:
            log(f"尝试使用 4-bit 量化 (NF4)...")

            # Windows 上 BitsAndBytes 支持有限，先检测
            if platform.system() == "Windows":
                log(f"⚠️  检测到 Windows 系统，BitsAndBytes 可能不兼容...")
                log(f"⚠️  如果加载卡住或崩溃，请尝试: --no-quantize")

            # 配置 4-bit 量化
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )

            log(f"开始加载模型到 GPU (4-bit)...")
            # 加载模型
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=quantization_config,
                device_map=device,
                trust_remote_code=True,
            )

            log(f"✅ 模型加载完成 (4-bit 量化)!")
            quantization_successful = True

        except Exception as e:
            log(f"⚠️  4-bit 量化失败!")
            log(f"⚠️  错误类型: {type(e).__name__}")
            log(f"⚠️  错误信息: {str(e)[:200]}...")
            log(f"⚠️  详细堆栈:")
            traceback.print_exc()
            log(f"\n⚠️  降级使用 float16...")

    # 如果量化失败或 BitsAndBytes 不可用，使用 float16
    if not quantization_successful:
        if device == "cuda" or (device == "auto" and torch.cuda.is_available()):
            log(f"使用 float16 (GPU)")
            log(f"开始加载模型到 GPU...")

            # 方案1: 先加载到 CPU，再移动到 GPU（更稳定）
            try:
                log(f"尝试方案: 先加载到 CPU，再移动到 GPU...")
                model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    device_map=None,  # 不使用 device_map
                    low_cpu_mem_usage=True,
                )
                log(f"模型加载到 CPU 完成，正在移动到 GPU...")
                model = model.cuda()
                log(f"✅ 模型加载完成 (float16 on GPU)!")
            except Exception as e:
                log(f"❌ 方案1失败: {e}")
                traceback.print_exc()

                # 方案2: 直接使用 device_map="cuda:0"
                log(f"\n尝试方案2: 直接加载到 cuda:0...")
                try:
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        torch_dtype=torch.float16,
                        trust_remote_code=True,
                        device_map="cuda:0",
                    )
                    log(f"✅ 模型加载完成 (float16 on cuda:0)!")
                except Exception as e2:
                    log(f"❌ 方案2也失败: {e2}")
                    traceback.print_exc()
                    raise
        else:
            log(f"使用 CPU 模式 (float32)")
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="cpu",
                trust_remote_code=True,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            log(f"✅ 模型加载完成 (CPU float32)!")

    log(f"模型上下文长度: 32K tokens")
    log(f"建议单批次输入上限: {MAX_INPUT_CHARS} 字符 (约 {MAX_INPUT_TOKENS} tokens)")

    return model, tokenizer


def calculate_week_period(date: pd.Timestamp) -> tuple:
    """
    计算周期: 上周六 00:00 - 下周五 23:59

    Args:
        date: 输入日期

    Returns:
        (period_start, period_end)

    示例:
        输入: 2024-11-13 (周三)
        输出: (2024-11-09 周六, 2024-11-15 周五)
    """
    weekday = date.weekday()  # 0=周一, 6=周日

    # 找到上周六 (本周期开始)
    if weekday == 6:  # 周日
        # 上周六是昨天
        days_to_last_saturday = 1
    else:  # 周一到周六
        # 周一: weekday=0, 需要回退 2 天到上周六
        # 周二: weekday=1, 需要回退 3 天到上周六
        # ...
        # 周六: weekday=5, 需要回退 7 天到上周六
        days_to_last_saturday = (weekday + 2) % 7
        if days_to_last_saturday == 0:
            days_to_last_saturday = 7

    period_start = date - pd.Timedelta(days=days_to_last_saturday)
    period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # 找到下周五 (本周期结束)
    days_to_next_friday = (4 - weekday) % 7
    if days_to_next_friday == 0 and weekday != 4:  # 不是周五
        days_to_next_friday = 7
    elif weekday == 4:  # 如果是周五
        days_to_next_friday = 0

    period_end = date + pd.Timedelta(days=days_to_next_friday)
    period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return period_start, period_end


def format_news_for_prompt(news_df: pd.DataFrame) -> str:
    """
    将新闻数据格式化为 prompt 输入

    Args:
        news_df: 新闻数据 DataFrame (包含 date, title, source, chg_in_5, chg_in_10 列)

    Returns:
        格式化的新闻文本
    """
    lines = []
    for idx, row in news_df.iterrows():
        line = f"[{row['date']}] {row['title']}"
        if pd.notna(row.get('chg_in_5')):
            line += f" | 5日涨跌: {row['chg_in_5']:.2f}%"
        if pd.notna(row.get('chg_in_10')):
            line += f" | 10日涨跌: {row['chg_in_10']:.2f}%"
        if pd.notna(row.get('source')):
            line += f" | 来源: {row['source']}"
        lines.append(line)

    return "\n".join(lines)


def generate_response(model, tokenizer, prompt: str, max_tokens: int = 2048) -> str:
    """
    生成响应

    Args:
        model: 模型
        tokenizer: tokenizer
        prompt: 输入 prompt
        max_tokens: 最大生成 tokens

    Returns:
        生成的文本
    """
    # Tokenize
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS)
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.3,  # 降低温度以获得更稳定的输出
            top_p=0.8,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Decode
    generated_text = tokenizer.decode(
        outputs[0][len(inputs["input_ids"][0]):],
        skip_special_tokens=True
    )

    # 清理显存
    del inputs, outputs
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return generated_text.strip()


def parse_events_json(response_text: str) -> list:
    """
    从 LLM 响应中解析 JSON 事件数组

    Args:
        response_text: LLM 生成的文本

    Returns:
        事件列表 (list of dict)
    """
    # 尝试提取 JSON 数组
    # 方法1: 直接解析
    try:
        events = json.loads(response_text)
        if isinstance(events, list):
            return events
    except json.JSONDecodeError:
        pass

    # 方法2: 提取代码块中的 JSON
    json_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
    matches = re.findall(json_pattern, response_text, re.DOTALL)
    if matches:
        try:
            events = json.loads(matches[0])
            if isinstance(events, list):
                return events
        except json.JSONDecodeError:
            pass

    # 方法3: 查找 [ ... ] 结构
    start_idx = response_text.find('[')
    end_idx = response_text.rfind(']')
    if start_idx != -1 and end_idx != -1:
        try:
            events = json.loads(response_text[start_idx:end_idx+1])
            if isinstance(events, list):
                return events
        except json.JSONDecodeError:
            pass

    # 解析失败
    print(f"警告: 无法解析 JSON 响应:\n{response_text[:500]}")
    return []


def analyze_period_events(
    model,
    tokenizer,
    symbol: str,
    name: str,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
    news_df: pd.DataFrame,
    max_tokens: int = 2048
) -> list:
    """
    分析单个周期的新闻，提取事件

    Args:
        model: 模型
        tokenizer: tokenizer
        symbol: 股票代码
        name: 公司名称
        period_start: 周期开始时间
        period_end: 周期结束时间
        news_df: 新闻数据
        max_tokens: 最大生成 tokens

    Returns:
        事件列表
    """
    # 格式化新闻数据
    news_text = format_news_for_prompt(news_df)

    # 检查是否需要分批
    if len(news_text) <= MAX_INPUT_CHARS:
        # 单批次处理
        prompt = EVENT_ANALYSIS_PROMPT.format(
            symbol=symbol,
            name=name,
            period_start=period_start.strftime('%Y-%m-%d'),
            period_end=period_end.strftime('%Y-%m-%d'),
            batch_info="",
            news_data=news_text
        )

        print(f"  单批次处理 {len(news_df)} 条新闻...")
        response = generate_response(model, tokenizer, prompt, max_tokens)
        events = parse_events_json(response)

        return events

    else:
        # 分批处理
        print(f"  新闻数据较大，采用分批处理...")

        # 计算批次大小
        num_news = len(news_df)
        batch_size = max(1, int(MAX_INPUT_CHARS / (len(news_text) / num_news)))
        batch_size = min(batch_size, num_news)

        all_events = []
        num_batches = (num_news + batch_size - 1) // batch_size

        for i in range(0, num_news, batch_size):
            batch_news = news_df.iloc[i:i+batch_size]
            batch_text = format_news_for_prompt(batch_news)

            batch_info = f"\n**注意**: 这是第 {i//batch_size + 1}/{num_batches} 批次，本批次包含 {len(batch_news)} 条新闻。"

            prompt = EVENT_ANALYSIS_PROMPT.format(
                symbol=symbol,
                name=name,
                period_start=period_start.strftime('%Y-%m-%d'),
                period_end=period_end.strftime('%Y-%m-%d'),
                batch_info=batch_info,
                news_data=batch_text
            )

            print(f"    批次 {i//batch_size + 1}/{num_batches}: {len(batch_news)} 条新闻...")
            response = generate_response(model, tokenizer, prompt, max_tokens)
            batch_events = parse_events_json(response)

            if batch_events:
                all_events.extend(batch_events)
                print(f"      提取了 {len(batch_events)} 个事件")

        # 合并事件
        if len(all_events) > 0:
            print(f"  正在合并 {len(all_events)} 个事件...")
            merged_events = merge_events(
                model, tokenizer, symbol, name,
                period_start, period_end, all_events, max_tokens
            )
            return merged_events
        else:
            return []


def merge_events(
    model,
    tokenizer,
    symbol: str,
    name: str,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
    events: list,
    max_tokens: int = 2048
) -> list:
    """
    合并多个批次提取的事件

    Args:
        model: 模型
        tokenizer: tokenizer
        symbol: 股票代码
        name: 公司名称
        period_start: 周期开始
        period_end: 周期结束
        events: 事件列表
        max_tokens: 最大生成 tokens

    Returns:
        合并后的事件列表
    """
    events_json = json.dumps(events, ensure_ascii=False, indent=2)

    prompt = MERGE_EVENTS_PROMPT.format(
        symbol=symbol,
        name=name,
        period_start=period_start.strftime('%Y-%m-%d'),
        period_end=period_end.strftime('%Y-%m-%d'),
        events_json=events_json
    )

    response = generate_response(model, tokenizer, prompt, max_tokens)
    merged_events = parse_events_json(response)

    if merged_events:
        print(f"  合并后得到 {len(merged_events)} 个事件")
        return merged_events
    else:
        print(f"  合并失败，返回原始事件")
        return events


def process_stock_news(
    input_csv: str,
    output_dir: str,
    model_path: str,
    device: str = "auto",
    max_tokens: int = 2048,
    use_quantization: bool = True
):
    """
    处理股票新闻数据，提取事件

    Args:
        input_csv: 输入 CSV 路径
        output_dir: 输出目录
        model_path: 模型路径
        device: 设备
        max_tokens: 最大生成 tokens
        use_quantization: 是否使用 4-bit 量化
    """
    # 加载模型
    model, tokenizer = load_model(model_path, device, use_quantization)

    # 读取数据
    print(f"\n正在读取数据: {input_csv}")
    df = pd.read_csv(input_csv)

    # 检查必需列
    required_cols = ['symbol', 'name', 'date', 'title', 'source']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"缺少必需列: {missing_cols}")

    # 转换日期
    df['date'] = pd.to_datetime(df['date'])

    # 获取股票信息
    symbol = df['symbol'].iloc[0]
    name = df['name'].iloc[0]

    print(f"股票代码: {symbol}")
    print(f"公司名称: {name}")
    print(f"新闻总数: {len(df)}")
    print(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")

    # 计算周期
    df['period_start'] = df['date'].apply(lambda x: calculate_week_period(x)[0])
    df['period_end'] = df['date'].apply(lambda x: calculate_week_period(x)[1])

    # 按周期分组
    periods = df.groupby(['period_start', 'period_end'])
    print(f"\n共有 {len(periods)} 个周期")

    # 分析每个周期
    all_events = []

    for (period_start, period_end), period_df in periods:
        print(f"\n{'='*60}")
        print(f"周期: {period_start.strftime('%Y-%m-%d')} ({period_start.day_name()}) 至 {period_end.strftime('%Y-%m-%d')} ({period_end.day_name()})")
        print(f"新闻数量: {len(period_df)}")

        # 提取事件
        events = analyze_period_events(
            model, tokenizer, symbol, name,
            period_start, period_end, period_df, max_tokens
        )

        if events:
            print(f"提取了 {len(events)} 个重大事件")

            # 转换为 DataFrame 行
            for event in events:
                event_row = {
                    'symbol': symbol,
                    'name': name,
                    'period_start': period_start.strftime('%Y-%m-%d'),
                    'period_end': period_end.strftime('%Y-%m-%d'),
                    'event_start': event.get('event_start', ''),
                    'event_end': event.get('event_end', ''),
                    'event_description': event.get('event_description', ''),
                    'earliest_news': event.get('earliest_news_title', ''),
                    'related_count': event.get('related_count', 1),
                    'chg_in_5': event.get('chg_in_5', None),
                    'chg_in_10': event.get('chg_in_10', None),
                    'source': event.get('source', '')
                }
                all_events.append(event_row)
        else:
            print("未提取到重大事件")

    # 保存结果
    if all_events:
        output_df = pd.DataFrame(all_events)

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"{symbol}.csv")

        output_df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"\n{'='*60}")
        print(f"✅ 处理完成!")
        print(f"总共提取了 {len(all_events)} 个事件")
        print(f"输出文件: {output_file}")
    else:
        print(f"\n{'='*60}")
        print(f"⚠️ 未提取到任何事件")


def main():
    parser = argparse.ArgumentParser(
        description="事件驱动型新闻分析 - 从新闻中提取对股价有重大影响的事件"
    )

    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='输入 CSV 文件路径 (例如: D:\\GitHub\\LocalFinData\\data\\news\\AAPL.csv)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='D:\\GitHub\\LocalFinData\\data\\events',
        help='输出目录 (默认: D:\\GitHub\\LocalFinData\\data\\events)'
    )

    parser.add_argument(
        '--model-path',
        type=str,
        default=None,
        help=f'模型路径 (默认: {get_model_path()})'
    )

    parser.add_argument(
        '--device',
        type=str,
        default='auto',
        choices=['auto', 'cuda', 'cpu'],
        help='设备选择 (默认: auto)'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=2048,
        help='最大生成 tokens (默认: 2048)'
    )

    parser.add_argument(
        '--no-quantize',
        action='store_true',
        help='禁用 4-bit 量化，直接使用 float16 (Windows 上如果 BitsAndBytes 有问题可以尝试此选项)'
    )

    args = parser.parse_args()

    # 获取模型路径
    model_path = args.model_path if args.model_path else get_model_path()

    # 打印配置
    quantization_mode = "float16 (无量化)" if args.no_quantize else "4-bit 量化"
    print("="*60)
    print("事件驱动型新闻分析脚本")
    print("="*60)
    print(f"模型: Qwen2.5-3B ({quantization_mode})")
    print(f"模型路径: {model_path}")
    print(f"输入文件: {args.input}")
    print(f"输出目录: {args.output_dir}")
    print(f"设备: {args.device}")
    print(f"模型上下文: 32K tokens (约 15,000-28,000 字)")
    print("="*60)

    # 早期验证模型路径
    if not os.path.exists(model_path):
        print(f"\n❌ 错误: 模型路径不存在: {model_path}")
        print(f"\n请确认:")
        print(f"1. 模型已下载到该路径")
        print(f"2. 路径格式正确 (Windows: D:/models/qwen2.5-3b)")
        print(f"3. 或使用 --model-path 参数指定正确路径")
        return

    # 验证输入文件
    if not os.path.exists(args.input):
        print(f"\n❌ 错误: 输入文件不存在: {args.input}")
        return

    # 处理数据
    process_stock_news(
        input_csv=args.input,
        output_dir=args.output_dir,
        model_path=model_path,
        device=args.device,
        max_tokens=args.max_tokens,
        use_quantization=not args.no_quantize
    )


if __name__ == "__main__":
    main()
