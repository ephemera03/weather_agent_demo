# 使用建议
```cmd
#设置环境
conda env create -f environment.yml

#运行环境
conda activate langchain

#运行demo
python langchain_demo.py
```

# 示例
```cmd
C:\Users\UserX\project9.17>conda activate langchain        

(langchain) C:\Users\UserX\project9.17>python langchain_demo.py
欢迎与AI助手交流，输入'exit'结束对话
----------------------------------------------

您: 帮我查一下上海静安区的天气

用户:
帮我查一下上海静安区的天气

AI助手: 
上海静安区当前天气情况（2025年9月18日 09:40）：

🌤️ **天气状况**：多云
🌡️ **气温**：27°C（体感温度29°C）
💨 **风力**：东南风2级，风速9km/h
💧 **湿度**：68%
🌫️ **能见度**：23公里
☁️ **云量**：100%
📊 **气压**：1017百帕
💧 **降水量**：0.0mm（过去1小时）

整体天气状况良好，多云天气，温度适宜，风力较小，湿度适中。

您: 这几天有下雨吗 

用户:
这几天有下雨吗

AI助手: 
根据天气预报，上海静安区未来几天确实有降雨：

🌧️ **降雨情况**：
- **今天（9月18日）**：阴天，预计降水量2.1mm
- **明天（9月19日）**：小雨，预计降水量1.0mm
- **后天（9月20日）**：小雨，预计降水量1.2mm
- **9月21日**：阴天，无雨
- **9月22日**：阴天，预计降水量1.0mm
- **9月23日**：小雨，预计降水量3.9mm
- **9月24日**：中雨，预计降水量14.3mm（雨量较大）

⚠️ **特别提醒**：9月24日将有中雨，降水量达到14.3mm，建议提前做好防雨准备。这几天出门记得带伞！

您: exit

用户:
exit

是否保存对话记录? (y/n): y
请输入保存文件名 (默认为 'conversation.txt'):
对话已保存到 conversation.txt
感谢使用，再见!

(langchain) C:\Users\UserX\project9.17>
```

<br>

# 文件解释

~~~
9.17会议.md
会议演示用的md文档

agent_calls.log
日志文件，记录模型，工具的调用过程和token

conversation.txt
对话内容记录

environment.yml
环境配置文件

langchain_demo.py
智能体demo代码
~~~