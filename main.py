"""天气穿衣助手 - 基于 DeepSeek V4 Pro 的 Function Calling Demo."""

import sys
from pathlib import Path

from dotenv import load_dotenv

from openai_chat.DeepseekV4Pro import DeepseekV4Pro

load_dotenv(Path(__file__).resolve().parent / ".env")


def main() -> None:
    question = input("天气助手已启动，请输入您的问题: ")
    print("\n正在思考，请稍候...\n")

    try:
        assistant = DeepseekV4Pro()
        print(assistant.task(question))
    except ValueError as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"运行出错: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
