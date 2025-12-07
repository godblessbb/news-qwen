# Qwen 模型 API 使用指南

本指南介绍如何启动 API 服务并从其他项目调用。

## 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn pydantic requests pyyaml
```

### 2. 修改默认配置（可选）

编辑 `config.yaml` 或 `api_server.py` 顶部的配置区域：

```yaml
# config.yaml
model:
  path: "D:/models/qwen2.5-7b"  # 修改为您的模型路径
  load_in_4bit: true             # 默认使用4-bit量化
  device: "auto"

api:
  host: "0.0.0.0"
  port: 8000
```

### 3. 启动 API 服务

#### 方式1：使用默认配置（推荐）

```bash
# Windows (PowerShell)
python api_server.py

# Linux/Mac
python api_server.py
```

**默认启用 4-bit 量化**，无需每次指定参数！

#### 方式2：自定义参数

```bash
# 指定模型路径
python api_server.py --model-path D:/models/qwen2.5-7b

# 禁用4-bit量化
python api_server.py --no-4bit

# 使用8-bit量化
python api_server.py --load-in-8bit

# 使用CPU
python api_server.py --device cpu

# 更改端口
python api_server.py --port 8080
```

### 4. 验证服务状态

启动成功后，访问：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **根路径**: http://localhost:8000/

## API 接口说明

### 1. 文本生成 (`/generate`)

**请求示例**：

```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={
        "prompt": "请介绍人工智能",
        "max_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.8
    }
)

result = response.json()
print(result['generated_text'])
```

**响应格式**：

```json
{
  "generated_text": "生成的文本内容...",
  "prompt_tokens": 10,
  "generated_tokens": 156,
  "total_tokens": 166
}
```

### 2. 对话接口 (`/chat`)

**请求示例**：

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "max_tokens": 256,
        "temperature": 0.7
    }
)

result = response.json()
print(result['reply'])
```

**响应格式**：

```json
{
  "reply": "你好！有什么我可以帮助你的吗？",
  "prompt_tokens": 15,
  "generated_tokens": 20,
  "total_tokens": 35
}
```

## 在其他项目中使用

### Python 项目

使用提供的客户端类：

```python
# 方式1：使用封装好的客户端
from api_client_example import QwenAPIClient

client = QwenAPIClient("http://localhost:8000")

# 文本生成
result = client.generate(
    prompt="请分析这条新闻...",
    max_tokens=256
)
print(result['generated_text'])

# 对话
result = client.chat(
    messages=[
        {"role": "user", "content": "你好"}
    ]
)
print(result['reply'])
```

### 其他语言

使用标准 HTTP 请求：

**JavaScript (Node.js)**:

```javascript
const axios = require('axios');

async function generate(prompt) {
  const response = await axios.post('http://localhost:8000/generate', {
    prompt: prompt,
    max_tokens: 256,
    temperature: 0.7
  });
  return response.data.generated_text;
}

generate("请介绍人工智能").then(console.log);
```

**cURL (命令行)**:

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "请介绍人工智能",
    "max_tokens": 256
  }'
```

## 实际应用示例

### 新闻分析

```python
from api_client_example import QwenAPIClient

client = QwenAPIClient()

news_items = [
    "美国航空Q3财报超预期，营收增长12%",
    "燃油价格上涨对航空业构成压力",
    "多家机构维持AAL买入评级"
]

prompt = f"""请分析以下新闻：

{chr(10).join([f'{i+1}. {item}' for i, item in enumerate(news_items)])}

要求：情感分析+影响评估，控制在100字内
"""

result = client.generate(prompt, max_tokens=256)
print(result['generated_text'])
```

## 性能优化

### 显存需求

- **4-bit 量化**（默认）：~3-4GB 显存
- **8-bit 量化**：~7-8GB 显存
- **无量化**：~14-16GB 显存

### 并发处理

API 服务器默认单进程，如需提高并发性能：

```bash
# 使用 gunicorn 启动多工作进程
pip install gunicorn

gunicorn api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

**注意**：每个worker都会加载一次模型，需要足够的显存。

## 故障排除

### 问题1：模型加载失败

**错误**：`FileNotFoundError: 模型路径不存在`

**解决**：
1. 检查 `api_server.py` 中 `DEFAULT_MODEL_PATH` 配置
2. 或启动时指定：`python api_server.py --model-path D:/models/qwen2.5-7b`

### 问题2：CUDA 内存不足

**错误**：`CUDA out of memory`

**解决**：
1. 使用 4-bit 量化（默认已启用）
2. 或使用 CPU：`python api_server.py --device cpu`

### 问题3：端口已被占用

**错误**：`Address already in use`

**解决**：
```bash
# 更改端口
python api_server.py --port 8001
```

### 问题4：无法从外部访问

**解决**：
1. 确保 `--host 0.0.0.0`（默认已设置）
2. 检查防火墙设置
3. 如果只需本机访问，使用 `--host 127.0.0.1`

## 运行示例代码

```bash
# 确保 API 服务已启动
python api_server.py

# 在另一个终端运行示例
python api_client_example.py
```

## 后台运行（生产环境）

### Linux/Mac

```bash
# 使用 nohup
nohup python api_server.py > api.log 2>&1 &

# 查看日志
tail -f api.log

# 停止服务
ps aux | grep api_server.py
kill <PID>
```

### Windows

```powershell
# 使用 start
start /B python api_server.py

# 或创建 Windows 服务（推荐使用 NSSM）
```

## API 文档

启动服务后访问交互式文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

可以直接在浏览器中测试 API 调用！

## 安全建议

1. **生产环境**：
   - 使用 HTTPS（配置反向代理如 Nginx）
   - 添加身份验证（API Key 或 OAuth）
   - 限制请求频率（Rate Limiting）

2. **本地开发**：
   - 使用 `--host 127.0.0.1` 只允许本机访问
   - 防火墙禁止外部访问端口

## 下一步

- 查看 `api_client_example.py` 了解更多使用示例
- 修改 `config.yaml` 自定义默认配置
- 集成到您的项目中进行实际应用
