"""天气穿衣助手 - 基于 DeepSeek V4 Pro 的 Function Calling Demo."""

import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from openai_chat.DeepseekV4Pro import DeepseekV4Pro

load_dotenv(Path(__file__).resolve().parent / ".env")


def main() -> None:
    print("心情小奴才已启动，请输入您的问题,输入空行结束问题,输入 朕累了,退下吧. 退出:")
    question = ""
    try:
        assistant = DeepseekV4Pro()
    except ValueError as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        sys.exit(1)

    while True:
        line = input()
        question += line
        if line == "":
            print("\n正在思考，请稍候...\n")
            try:
                print(assistant.task(question))
                print("\n")
                question = ""
            except RuntimeError as exc:
                print(f"运行出错: {exc}", file=sys.stderr)
                question = ""
        elif line == "朕累了,退下吧.":
            print("遵命,谢主隆恩")
            time.sleep(1)
            break



if __name__ == "__main__":
    main()
