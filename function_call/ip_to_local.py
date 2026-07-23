import ipinfo


def get_location_by_ip() -> dict:
    # --- 1. 通过IP获取经纬度 ---
    access_token = '57558f447afee4'  # 替换成你的真实Token
    handler = ipinfo.getHandler(access_token)

    # 不传IP参数，默认查询本机
    details = handler.getDetails()

    latitude, longitude = details.loc.split(',')  # details.loc 格式是 "纬度,经度"
    city = details.city
    print(f"IP定位: {city}, 坐标: {latitude}, {longitude}")
    return {"city": city, "latitude": latitude, "longitude": longitude}