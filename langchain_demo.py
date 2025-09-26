# %%
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool
import requests
from datetime import datetime
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.messages import HumanMessage
import logging

# 配置日志
logging.basicConfig(
    filename="agent_calls.log",  # 日志文件名
    level=logging.INFO,          # 日志级别
    format="%(asctime)s - %(message)s",  # 时间 + 消息
    encoding="utf-8"
)

class TraceHandler(BaseCallbackHandler):
    def __init__(self):
        super().__init__()
        self.last_user_input = None

    def log(self, message: str):
        logging.info(message)

    def on_chain_start(self, serialized, inputs, **kwargs):
        user_input = None
        if isinstance(inputs, dict) and "messages" in inputs:
            for msg in inputs["messages"]:
                if isinstance(msg, HumanMessage):
                    user_input = msg.content
                    break

        if user_input and user_input != self.last_user_input:
            self.log("\n" + "=" * 50)
            self.log("新查询开始")
            self.log(f"用户输入: {user_input}")
            self.last_user_input = user_input

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.log(f"[LLM开始] Prompt: {prompts}")

    def on_llm_end(self, response, **kwargs):
        self.log(f"[LLM结束] 输出: {response.generations}")

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.log(f"[调用工具开始] {serialized.get('name')} 输入: {input_str}")

    def on_tool_end(self, output, **kwargs):
        self.log(f"[调用工具结束] 输出: {output}")


def geo_query(city):
    '''
    city:搜索到城市名称,str
    city_ids:包含相关城市名称的列表,list
    '''
    url = "https://mx5g7cdjjw.re.qweatherapi.com/geo/v2/city/lookup"
    params = {
        "location": city,
        "key": "e01da349b93d494697b282c61a61c105"
    }

    response = requests.get(url, params=params)
    try:
        city_ids = [(item["id"], item["name"]) for item in response.json()["location"]]
    except:
        return False
    else:
        return city_ids

def weather_query(city_tuple):
    '''
    city_tuple:查询的城市的名称和序号组成的二元元组,str
    output:结果列表,list
    '''
    url = "https://mx5g7cdjjw.re.qweatherapi.com/v7/weather/now"
    params = {
        "location": city_tuple[0],
        "key": "e01da349b93d494697b282c61a61c105"
    }

    response = requests.get(url, params=params)
    weather_result = response.json()["now"]
    result = {"location":city_tuple[1]}
    result.update(weather_result)
    return result

def weather_forecast_query(city_tuple,daytime):
    '''
    city_tuple:查询的城市的名称和序号组成的二元元组,str
    daytime:查询日期，可选且仅可选值3,7,10,15,30，int
    output:结果列表,list
    '''
    if daytime == 3:
        url = "https://mx5g7cdjjw.re.qweatherapi.com/v7/weather/3d"
    elif daytime == 7:
        url = "https://mx5g7cdjjw.re.qweatherapi.com/v7/weather/7d"
    elif daytime == 10:
        url = "https://mx5g7cdjjw.re.qweatherapi.com/v7/weather/10d"
    elif daytime == 15:
        url = "https://mx5g7cdjjw.re.qweatherapi.com/v7/weather/15d"
    elif daytime == 30:
        url = "https://mx5g7cdjjw.re.qweatherapi.com/v7/weather/30d"
    else:
        raise ValueError(f"daytime 参数无效: {daytime}，必须是 3, 7, 10, 15, 30 之一")
    params = {
        "location": city_tuple[0],
        "key": "e01da349b93d494697b282c61a61c105"
    }

    response = requests.get(url, params=params)
    weather_result = {"daily": response.json()["daily"]}
    result = {"location":city_tuple[1]}
    result.update(weather_result)
    return result

def past_weather_query(city_tuple, date):
    '''
    city_tuple:查询的城市的名称和序号组成的二元元组,str
    date:date选择日期,最多可选择最近10天(不包含今天)的数据。日期格式为yyyyMMdd,例如 date="20200531",str
    output:结果列表,list
    '''
    url = "https://mx5g7cdjjw.re.qweatherapi.com/v7/historical/weather"
    params = {
        "location": city_tuple[0],
        "date": date,
        "key": "e01da349b93d494697b282c61a61c105"
    }

    response = requests.get(url, params=params)
    weather_result_daily = response.json()["weatherDaily"]
    weather_result_hourly = {"weatherHourly": response.json()["weatherHourly"]}
    result = {"location":city_tuple[1]}
    result.update(weather_result_daily)
    result.update(weather_result_hourly)
    return result


@tool
def get_weather_now(city: str) -> str:  
    """
    如果查询日期就是当天则使用该工具
    获取输入城市当前的天气
    city:查询的城市名称，使用英文或中文名称查询
    """
    city_ids = geo_query(city)
    data = []
    for id in city_ids:
        temp = weather_query(id)
        data.append(temp)
    description = {
        "location": "观测地点名称，例如城市、区、县或站点名",
        "obsTime": "观测时间，ISO 8601 格式（YYYY-MM-DDTHH:MM+时区），表示数据采集的时间",
        "temp": "实况气温，单位：摄氏度 (°C)",
        "feelsLike": "体感温度，单位：摄氏度 (°C)，综合温度、湿度、风速等因素计算",
        "icon": "天气现象代码，对应天气图标（例如 101 表示多云）",
        "text": "天气现象文字描述，例如 晴、多云、阴、小雨",
        "wind360": "风向角度，单位：度 (°)，0 表示北风，90 表示东风，180 表示南风，270 表示西风",
        "windDir": "风向文字描述，例如 北风、东北风、西南风",
        "windScale": "风力等级，整数或字符串，参考中国气象局风力等级标准（0-12 级）",
        "windSpeed": "风速，单位：公里/小时 (km/h)",
        "humidity": "相对湿度，单位：百分比 (%)",
        "precip": "降水量，单位：毫米 (mm)，表示过去一小时的降水量",
        "pressure": "大气压强，单位：百帕 (hPa)",
        "vis": "能见度，单位：公里 (km)",
        "cloud": "云量，单位：百分比 (%)，表示天空被云覆盖的比例",
        "dew": "露点温度，单位：摄氏度 (°C)，表示空气中水汽达到饱和时的温度"
    }
    output = {"description":description,
              "data":data
              }
    return "和{re1}相关的部分天气数据如下表所示{re2}".format(re1=city, re2=output)

@tool
def get_weather_forecast(city: str, daytime: int) -> str:  
    """
    如果查询时间在当前日期之后则使用该工具
    获取输入城市的天气预报（最多只能到未来30天）
    city:查询的城市名称，使用英文或中文名称查询
    daytime:预报天数,只能从3,7,10,15,30中选择一个值,类型为int,在符合查找要求的前提下,建议优先选择少的天数来节约token
    """
    city_ids = geo_query(city)
    city_id = city_ids[0]
    data = weather_forecast_query(city_id, daytime)
    daily_description = {
        "fxDate": "预报日期，格式为 YYYY-MM-DD",
        "sunrise": "日出时间，格式 HH:MM，在高纬度地区可能为空",
        "sunset": "日落时间，格式 HH:MM，在高纬度地区可能为空",
        "moonrise": "当天月升时间，格式 HH:MM，可能为空",
        "moonset": "当天月落时间，格式 HH:MM，可能为空",
        "moonPhase": "月相名称，例如 新月、满月、上弦月、下弦月",
        "moonPhaseIcon": "月相图标代码，可参考天气图标项目",
        "tempMax": "预报当天最高气温，单位：摄氏度 (°C)",
        "tempMin": "预报当天最低气温，单位：摄氏度 (°C)",
        "iconDay": "预报白天天气状况的图标代码，可参考天气图标项目",
        "textDay": "预报白天天气状况文字描述，例如 晴、多云、小雨",
        "iconNight": "预报夜间天气状况的图标代码，可参考天气图标项目",
        "textNight": "预报夜间天气状况文字描述，例如 晴、多云、小雨",
        "wind360Day": "预报白天风向角度，单位：度 (°)，0 表示北风，90 表示东风",
        "windDirDay": "预报白天风向文字描述，例如 北风、东北风",
        "windScaleDay": "预报白天风力等级，参考中国气象局风力等级标准（0-12 级）",
        "windSpeedDay": "预报白天风速，单位：公里/小时 (km/h)",
        "wind360Night": "预报夜间风向角度，单位：度 (°)，0 表示北风，90 表示东风",
        "windDirNight": "预报夜间风向文字描述，例如 北风、东北风",
        "windScaleNight": "预报夜间风力等级，参考中国气象局风力等级标准（0-12 级）",
        "windSpeedNight": "预报夜间风速，单位：公里/小时 (km/h)",
        "precip": "预报当天总降水量，单位：毫米 (mm)",
        "uvIndex": "紫外线强度指数，数值越大表示紫外线越强",
        "humidity": "相对湿度，单位：百分比 (%)",
        "pressure": "大气压强，单位：百帕 (hPa)",
        "vis": "能见度，单位：公里 (km)",
        "cloud": "云量，单位：百分比 (%)，可能为空"
    }
    output = {"description":daily_description,
              "data":data
              }
    return "{re1}的天气预报数据如下表所示{re2}".format(re1=city, re2=output)

@tool
def get_weather_past(city: str, date: str) -> str:  
    """
    如果查询时间在当前日期之前则使用该工具
    获取输入城市过去10天内(不含今天)指定的某一天的天气
    city:查询的城市名称，使用英文或中文名称查询
    date:date选择日期,最多可选择最近10天(不包含今天)的数据。日期格式为yyyyMMdd,例如 date="20200531"
    """
    city_ids = geo_query(city)
    city_id = city_ids[0]
    data = past_weather_query(city_id, date)
    weather_description = {
        "weatherDaily": {
            "date": "当天日期，格式为 YYYY-MM-DD",
            "sunrise": "当天日出时间，格式 HH:MM，在高纬度地区可能为空",
            "sunset": "当天日落时间，格式 HH:MM，在高纬度地区可能为空",
            "moonrise": "当天月升时间，格式 HH:MM，可能为空",
            "moonset": "当天月落时间，格式 HH:MM，可能为空",
            "moonPhase": "当天月相名称，例如 新月、满月、上弦月、下弦月",
            "tempMax": "当天最高气温，单位：摄氏度 (°C)",
            "tempMin": "当天最低气温，单位：摄氏度 (°C)",
            "precip": "当天总降水量，单位：毫米 (mm)",
            "pressure": "当天平均大气压强，单位：百帕 (hPa)",
            "humidity": "当天平均相对湿度，单位：百分比 (%)"
        },
        "weatherHourly": {
            "time": "当天时间，格式为 YYYY-MM-DD HH:MM",
            "temp": "该小时的气温，单位：摄氏度 (°C)",
            "icon": "该小时天气状况的图标代码，可参考天气图标项目",
            "text": "该小时天气状况的文字描述，例如 晴、多云、小雨",
            "wind360": "该小时风向角度，单位：度 (°)，0 表示北风，90 表示东风",
            "windDir": "该小时风向文字描述，例如 北风、东北风",
            "windScale": "该小时风力等级，参考中国气象局风力等级标准（0-12 级）",
            "windSpeed": "该小时风速，单位：公里/小时 (km/h)",
            "humidity": "该小时相对湿度，单位：百分比 (%)",
            "precip": "该小时累计降水量，单位：毫米 (mm)",
            "pressure": "该小时大气压强，单位：百帕 (hPa)"
        }
    }
    output = {"description":weather_description,
              "data":data
              }
    return "{re1}在{re2}当天的天气数据如下表所示{re3}".format(re1=city, re2 =date, re3=output)

@tool
def get_recent_time() -> str:
    "调用该工具可以获取计算机本地当前时间"
    now = datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    return "当前时间为{r1}".format(r1=now)


# DeepSeek
deepseek = ChatOpenAI(
    api_key="sk-339296d0d272420bbe6c41928c0af3bf",
    base_url="https://api.deepseek.com/v1",
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=1024,
    streaming=False  # 关闭流式
)

handler = TraceHandler()
checkpointer = InMemorySaver()

agent = create_react_agent(
    model=deepseek,  
    tools=[get_weather_now, get_weather_forecast, get_weather_past, get_recent_time],  
    checkpointer=checkpointer,
    prompt="""你是一个专业的天气助手。请遵循以下规则：
    1. 按需求选择合适的一个或几个工具获取天气
    2. 直接给出完整回答，无需解释工具使用过程
    3. 如果用户的指令没有明确给出查询的年份或月份，那就默认是当前时间的年份和月份吧
    """  
)


# %%
# 交互式聊天
config = {"configurable": {"thread_id": "1"}, "callbacks":[TraceHandler()]}

# 保存所有对话历史
conversation_history = []

print("欢迎与AI助手交流，输入'exit'结束对话")
print("----------------------------------------------")

try:
    while True:
        # 获取用户输入
        user_input = input("\n您: ")
        print("\n用户:\n" + user_input)
        # 检查退出条件
        if user_input.lower() in ['退出', 'exit', 'quit']:
            break
        
        # 调用AI助手
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config
        )
        
        # 获取AI回复
        ai_response = result["messages"][-1].content
        
        # 打印AI回复
        print("\nAI助手: \n" + ai_response)
        # 保存对话记录
        conversation_history.append({
            "user": user_input,
            "assistant": ai_response
        })

except KeyboardInterrupt:
    print("\n对话被用户中断")

# 询问是否保存对话
save_option = input("\n是否保存对话记录? (y/n): ")
if save_option.lower() in ['y', 'yes', '是']:
    filename = input("请输入保存文件名 (默认为 'conversation.txt'): ") or "conversation.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("对话记录\n")
        f.write("===================\n\n")
        
        for i, exchange in enumerate(conversation_history, 1):
            f.write(f"--- 对话 {i} ---\n")
            f.write(f"用户: {exchange['user']}\n\n")
            f.write(f"AI助手: {exchange['assistant']}\n\n")
    
    print(f"对话已保存到 {filename}")

print("感谢使用，再见!")


