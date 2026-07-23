import os

import requests

QWEATHER_API_URL = os.environ.get(
    "QWEATHER_API_URL",
    "https://ng6yw3a6wn.re.qweatherapi.com/v7/weather/now",
)


def local_weather(latitude: str, longitude: str) -> str:
    api_key = os.environ.get("QWEATHER_API_KEY")
    if not api_key:
        raise ValueError("环境变量 QWEATHER_API_KEY 未配置")

    try:
        resp = requests.get(
            QWEATHER_API_URL,
            params={
                "location": f"{longitude},{latitude}",
                "key": api_key,
            },
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return f"天气服务请求失败: {exc}"

    if data.get("code") != "200":
        return f"天气查询失败，错误码: {data.get('code', '未知')}"

    now = data["now"]
    return f"当前天气: {now['temp']}°C, 风速: {now['windSpeed']} km/h, 天气: {now.get('text', '未知')}"
