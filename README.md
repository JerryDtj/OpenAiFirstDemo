# OpenAiFirstDemo

基于 DeepSeek V4 Pro 的穿衣助手 Demo，通过 Function Calling 自动获取 IP 定位与实时天气，并给出穿搭建议。

## 环境准备

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，并填入以下环境变量（或在 shell 中 export）：

| 变量名 | 说明 |
|--------|------|
| `agicto_api_key` | Agicto 平台 API Key |
| `WEATHER_API_KEY` | 和风天气 API Key |
| `IPINFO_TOKEN` | ipinfo.io Access Token |

## 运行

```bash
python main.py
```

示例问题：`今天穿什么合适？`
