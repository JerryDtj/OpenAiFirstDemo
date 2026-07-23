import os

import ipinfo


def get_location_by_ip() -> dict:
    token = os.environ.get("IPINFO_TOKEN")
    if not token:
        raise ValueError("环境变量 IPINFO_TOKEN 未配置")

    handler = ipinfo.getHandler(token)
    details = handler.getDetails()

    latitude, longitude = details.loc.split(",")
    return {
        "city": details.city,
        "latitude": latitude,
        "longitude": longitude,
    }
