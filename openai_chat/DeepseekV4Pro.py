import os

import json
from openai import OpenAI
from openai.types.responses import tool

from function_call.ip_to_local import get_location_by_ip
from function_call.local_weather import local_weather


class DeepseekV4Pro:


    def __new__(cls):
        if not os.environ.get("openai_api_key"):
            raise ValueError("openai_api_key为空,请检查环境变量是否配置")
        return super().__new__(cls)


    def __init__(self):
        client = OpenAI(api_key = os.environ.get("openai_api_key"),base_url="https://api.deepseek.com")
        self.client = client

    def task(self,question:str):
        prompt = """
            你是一个穿衣助手，根据用户所在城市的实时天气，推荐一套简约、实用的穿搭方案。
            输出要求：
            - 直接给出穿衣建议，200字以内
            - 推荐1~2套方案，若天气特殊（如暴雨、高温）需特别提醒
            - 回答清晰、口语化，不需要多余解释
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"{question}"},
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "ip_to_local",
                    "description": "根据当前用户的IP地址获取其经纬度坐标和城市信息。无需任何参数。",
                    "parameters": {
                        "type": "object",
                        "properties": {},  # 无入参
                        "required": []
                    }
                }
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
                                "description": "纬度，范围 -90 到 90，例如 39.9042"
                            },
                            "longitude": {
                                "type": "string",
                                "description": "经度，范围 -180 到 180，例如 116.4074"
                            }
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
            }
        ]

        # 循环处理，直到模型不再要求调用工具
        while True:
            response = self.client.chat.completions.create(
                model="DeepSeek-V4-Flash",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                stream=False,
                reasoning_effort="high",
                timeout=10,  # 缩短超时，提升用户体验
                extra_body={"thinking": {"type": "enabled"}}
            )

            message = response.choices[0].message

            # 如果没有工具调用，说明模型已生成最终答案
            if not message.tool_calls:
                return message.content

            # 有工具调用 -> 将模型的工具请求追加到消息历史
            messages.append(message.model_dump())

            # 执行所有工具调用（通常只有一个，但循环支持多个）
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                if function_name == "ip_to_local":
                    result = get_location_by_ip()  # 返回字典
                elif function_name == "local_weather":
                    latitude = arguments.get("latitude")
                    longitude = arguments.get("longitude")
                    result = local_weather(latitude, longitude)  # 返回字符串
                else:
                    result = "未知工具"

                # 将工具执行结果以 'tool' 角色追加到消息列表
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

            # 继续循环，将工具结果提交给模型，模型可能继续请求工具或直接给出最终答案




