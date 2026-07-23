import json
import os
from typing import Any, Callable

from openai import OpenAI

from function_call.ip_to_local import get_location_by_ip
from function_call.local_weather import local_weather

SYSTEM_PROMPT = """
你是一个穿衣助手，根据用户所在城市的实时天气，推荐一套简约、实用的穿搭方案。
输出要求：
- 直接给出穿衣建议，200字以内
- 推荐1~2套方案，若天气特殊（如暴雨、高温）需特别提醒
- 回答清晰、口语化，不需要多余解释
""".strip()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ip_to_local",
            "description": "根据当前用户的IP地址获取其经纬度坐标和城市信息。无需任何参数。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "local_weather",
            "description": "根据提供的经纬度坐标获取该位置的实时天气信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "string",
                        "description": "纬度，范围 -90 到 90，例如 39.9042",
                    },
                    "longitude": {
                        "type": "string",
                        "description": "经度，范围 -180 到 180，例如 116.4074",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
]

TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "ip_to_local": lambda _: get_location_by_ip(),
    "local_weather": lambda args: local_weather(
        args["latitude"], args["longitude"]
    ),
}

MAX_TOOL_ROUNDS = 10


class DeepseekV4Pro:
    def __init__(self) -> None:
        api_key = os.environ.get("agicto_api_key")
        if not api_key:
            raise ValueError("agicto_api_key 为空，请检查环境变量是否配置")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.agicto.cn/v1",
        )

    def _execute_tool(self, function_name: str, arguments: dict[str, Any]) -> Any:
        handler = TOOL_HANDLERS.get(function_name)
        if not handler:
            return {"error": f"未知工具: {function_name}"}
        try:
            return handler(arguments)
        except Exception as exc:
            return {"error": str(exc)}

    def task(self, question: str) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        for _ in range(MAX_TOOL_ROUNDS):
            response = self.client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                stream=False,
                reasoning_effort="high",
                timeout=30,
                extra_body={"thinking": {"type": "enabled"}},
            )

            message = response.choices[0].message
            if not message.tool_calls:
                return message.content or ""

            messages.append(message.model_dump())

            for tool_call in message.tool_calls:
                arguments = json.loads(tool_call.function.arguments or "{}")
                result = self._execute_tool(tool_call.function.name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        raise RuntimeError(f"工具调用超过最大轮次 ({MAX_TOOL_ROUNDS})，请重试")
