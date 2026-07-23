import requests



def local_weather(latitude: str, longitude: str) -> str:
    url = "https://ng6yw3a6wn.re.qweatherapi.com/v7/weather/now"
    params = {
        "location": f"{longitude},{latitude}",  # 注意顺序
        "key": "a45f067ca38548789a2788b209c78c7f"
    }
    resp = requests.get(url, params=params, timeout=3)
    data = resp.json()
    temp = data['now']['temp']
    wind = data['now']['windSpeed']
    print(f"当前天气: {temp}°C, 风速: {wind} km/h")
    return f"当前天气: {temp}°C, 风速: {wind} km/h"

# local_weather(31.2222, 121.4581)