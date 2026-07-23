# 这是一个示例 Python 脚本。
import os

from openai_chat.DeepseekV4Pro import DeepseekV4Pro


# 按 ⌃R 执行或将其替换为您的代码。
# 按 双击 ⇧ 在所有地方搜索类、文件、工具窗口、操作和设置。


def print_hi(name):
    # 在下面的代码行中使用断点来调试脚本。
    print(f'Hi, {name}')  # 按 ⌘F8 切换断点。


# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    question = input("天气助手已启动,请输入您的问题: ")
    print("\n正在思考，请稍候...\n")
    dk = DeepseekV4Pro()

    
    response = dk.task(question)
    print(response)


# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
