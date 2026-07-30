import os
from functools import wraps
import time

from langchain_core.tools import tool
import requests
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv()
api_key = os.getenv('agicto_api_key')
joke_api_key = os.getenv('apihz_api_key')
if not joke_api_key or joke_api_key.strip() == "":
    raise ValueError("key is not set")


class get_local_by_ip:
    def run(self):
        start_time = time.perf_counter()
        default_language = ["普通话"]
        response = requests.get('https://ip9.com.cn/get')
        data = response.json()
        if data and data['ret'] == 200:
            area = data.get('data', {}).get('prov', '')
            city_language_map = {
                "北京市": ["北京官话"],
                "天津市": ["北京官话", "冀鲁官话"],
                "上海市": ["吴语 (上海话)"],
                "重庆市": ["西南官话"],
                "河北省": ["冀鲁官话", "北京官话"],
                "山西省": ["晋语", "中原官话"],
                "辽宁省": ["东北官话", "胶辽官话"],
                "吉林省": ["东北官话"],
                "黑龙江省": ["东北官话"],
                "江苏省": ["江淮官话", "吴语"],
                "浙江省": ["吴语"],
                "安徽省": ["江淮官话", "中原官话", "徽语", "赣语", "吴语"],
                "福建省": ["闽语 (闽东/闽南/闽北/闽中/莆仙)", "客家话"],
                "江西省": ["赣语", "客家话"],
                "山东省": ["冀鲁官话", "胶辽官话", "中原官话"],
                "河南省": ["中原官话"],
                "湖北省": ["西南官话", "江淮官话", "赣语"],
                "湖南省": ["湘语", "西南官话", "赣语", "客家话"],
                "广东省": ["粤语", "客家话", "闽语 (潮汕话/雷州话)"],
                "海南省": ["闽语 (海南话)", "粤语 (儋州话)", "黎语"],
                "四川省": ["西南官话"],
                "贵州省": ["西南官话"],
                "云南省": ["西南官话"],
                "陕西省": ["中原官话", "西南官话", "晋语"],
                "甘肃省": ["兰银官话", "中原官话"],
                "青海省": ["中原官话", "藏语"],
                "台湾省": ["闽南语", "客家话"],
                "内蒙古自治区": ["东北官话", "北京官话", "晋语", "蒙古语"],
                "广西壮族自治区": ["西南官话", "粤语", "壮语"],
                "西藏自治区": ["藏语", "西南官话"],
                "宁夏回族自治区": ["兰银官话", "中原官话"],
                "新疆维吾尔自治区": ["中原官话", "兰银官话", "维吾尔语"],
                "香港特别行政区": ["粤语 (广府片)"],
                "澳门特别行政区": ["粤语 (广府片)"]
            }
            # API 返回 "上海", 字典 key 是 "上海市", 用模糊匹配去掉后缀差异
            default_language = ["普通话"]
            for key, value in city_language_map.items():
                if key.startswith(area) or area.startswith(key):
                    default_language = value
                    break
        print(f"get_local_by_ip.run 执行时间: {(time.perf_counter() - start_time)*1000:.1f} 毫秒")
        return default_language


@tool
def get_joke() -> str:
    """ 获取一个笑话"""
    start_time = time.perf_counter()
    url = "https://cn.apihz.cn/api/zici/xiaohua.php"
    params = {
        "id": "10019601",
        "key": joke_api_key
    }

    response = requests.get(url, params=params, timeout=10).json()
    print(f"get_joke 执行时间: {(time.perf_counter() - start_time)*1000:.1f} 毫秒")
    if response and response.get('code') == 200:
        return response.get('content', '')
    else:
        return "获取笑话失败"


tools = [get_joke]

address_tool =  RunnableLambda(lambda x: get_local_by_ip().run())
language = address_tool.invoke(None)



openai_model = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=api_key,
    base_url="https://api.agicto.cn/v1",
    streaming=True,
)

# openai_model = ChatDeepseek(
#     model = "deepseek-v4-pro",
#     api_key=api_key,
#     streaming=True,
# )

start_time = time.perf_counter()
openai_model.invoke("你好")
print(f"openai_model.invoke 执行时间: {(time.perf_counter() - start_time)*1000:.1f} 毫秒")

# InMemorySaver 内部自带 defaultdict 存储, 不需要传 factory
checkpointer = InMemorySaver()

# 读取提示词, 用 ChatPromptTemplate.from_template() 替换 {language} 变量
with open("小奴才系统提示词.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()

# ChatPromptTemplate 会自动扫描 {language} 变量, 不需要手动声明 input_variables
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
])
system_prompt = prompt_template.format(language=str(language))

agent = create_agent(
    model=openai_model,
    checkpointer=checkpointer,
    system_prompt=system_prompt,
    tools=tools,
)


if __name__ == "__main__":
    print("欢迎进入奴才小助手,在这里你就是大王,输入朕累了关闭助手")
    config = {"configurable": {"thread_id": "1"}}
    while True:
        question = input("请输入您的问题：")
        if  question.strip() == "":
            continue
        if question.rfind("朕累了") != -1:
            break
        start_time = time.perf_counter()
        for msg, metadata in agent.stream(
            {"messages": [("user", question)]},
            config=config,
            stream_mode="messages",
        ):
            # 只打印 AI 的文本回复, 跳过工具调用/工具结果
            if type(msg).__name__ == "AIMessageChunk" and msg.content:
                print(msg.content, end="", flush=True)
        print()
        print(f"agent.stream 执行时间: {(time.perf_counter() - start_time)*1000:.1f} 毫秒")
        print("-----------------"*10)
        
