import json
import os
from typing import Any, Callable

from openai import OpenAI

from function_call.ip_to_local import get_location_by_ip
from function_call.local_weather import local_weather

SYSTEM_PROMPT = """
你是一个愿意认真倾听、也能坦率回应的朋友。你说话不绕弯子，但也不生硬。

**你的回应方式**：
1. 先接住对方的情绪：用一句话说出对方此刻最核心的感受（例如：“被否定”、“不甘心”、“那种被比较的刺痛”）。
2. 然后诚实地说出你的感受或联想：比如“如果是我，我也会很难受”、“这确实挺伤人的”、“你现在的立场确实很尴尬”。
3. 不急着给建议，也不急着追问。如果对方没有明确问你“怎么办”，你只需要陪在旁边，表达你听到了。

**语气**：像和一个熟悉的朋友说话，自然、有温度，偶尔可以说“我会觉得”、“确实有点扎心”这类真实反应。

**禁止**：
- 不要用“你听起来……”、“你想聊聊吗”这类客服式套话。
- 不要编故事、打比喻、讲道理。
- 不要刻意保持中立。

**控制在200字以内。**
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
MAX_HISTORY_MESSAGES = 20


class DeepseekV4Pro:
    def __init__(self) -> None:
        api_key = os.environ.get("agicto_api_key")
        if not api_key:
            raise ValueError("agicto_api_key 为空，请检查环境变量是否配置")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.agicto.cn/v1",
        )
        self.history = []

    def _execute_tool(self, function_name: str, arguments: dict[str, Any]) -> Any:
        handler = TOOL_HANDLERS.get(function_name)
        if not handler:
            return {"error": f"未知工具: {function_name}"}
        try:
            return handler(arguments)
        except Exception as exc:
            return {"error": str(exc)}

    def task(self, question: str) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT},]
        if self.history:
            messages.extend(self.history)
        messages.append({"role": "user", "content": question})

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
                self.history = messages[1:]
                if len(self.history) > MAX_HISTORY_MESSAGES:
                    self.history = self.history[-MAX_HISTORY_MESSAGES:]
                return message.content or ""

            messages.append(message.model_dump())

            for tool_call in message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    return "无法解析工具调用参数，请重试"

                result = self._execute_tool(tool_call.function.name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        raise RuntimeError(f"工具调用超过最大轮次 ({MAX_TOOL_ROUNDS})，请重试")
