[🇬🇧English](https://github.com/ericzhang-cn/ailingbot/blob/main/README.md)

<img src="./img/logo.png" alt="logo" width="50"/>

AilingBot - 一站式解决方案，为你的IM机器人接入AI强大能力。

# 特点

- 📦**开箱即用**：无需开发，预置接入现有主流IM及LLM模型的能力
- 🧩**模块化**：项目采用模块化组织，模块之间通过抽象协议依赖，同类模块实现协议即可即插即用
- 💻**可扩展**：得益于模块化的组织方式，可以基于模块协议实现自己的模块
  扩展AilingBot的使用场景和能力。例如接入到新的IM，新的大模型，或者开发自己的对话策略
- 🚀**高性能**：AilingBot采用基于协程的异步模式，提高系统的高并发性能。同时核心进程
  可以启动多进程，进一步提升系统的高并发处理能力
- 🔌**API**：AilingBot提供一组清晰的Endpoint作为其API接口，方便与其他系统及
  流程集成协同

# 快速使用指南

## 5分钟启动一个AI聊天机器人

### 前置条件

请确保你的机器上装有如下环境：

- Python（>=3.9）：https://www.python.org/
- Poetry：https://python-poetry.org/

同时你需要有一个OpenAI API key。如果没有请到这里申请：https://platform.openai.com/account/api-keys

### 设置环境变量（可选）

AilingBot的开发哲学鼓励将配置放在环境变量中，当然你也可以跳过这一步，在后续启动命令时动态传入。

设置环境变量命令：

```shell
export AILINGBOT_POLICY__NAME="input_output"
export AILINGBOT_POLICY__ARGS="{llm_name='openai',llm_args={model_name='gpt-3.5-turbo',openai_api_key='这里填入你的OpenAI API key',temperature=0}}"
```

### 启动机器人

在AilingBot根目录下，首先安装依赖：

```shell
poetry install
```

然后进入virtualenv环境：

```shell
poetry shell
```

执行以下命令：

```shell
ailingbot --help
```

如果能看到以下输出，则说明AilingBot安装成功：

```text
Usage: ailingbot [OPTIONS] COMMAND [ARGS]...

  AilingBot command line tools.

Options:
  --help  Show this message and exit.

Commands:
  bot      Bot commands.
  channel  Channel commands.
```

如果前面已经设置了环境变量，则可以通过如下命令启动机器人：

```shell
ailingbot bot chat
```

如果没有设置环境变量，则需要通过启动参数传入必要信息：

```shell
ailingbot bot chat --policy input_output --policy-args "{llm_name='openai',llm_args={model_name='gpt-3.5-turbo',openai_api_key='这里填入你的OpenAI API key',temperature=0}}"
```

此时你可以通过一个交互式对话环境与机器人进行对话，如下图所示：
![命令行机器人](img/command-line-screenshot.png)

## 接入即时通讯工具

下面以企业微信为例，演示AilingBot如何快速接入即时通讯工具。

### 前置条件

要接入企业微信，除了上面的前置条件外，还需要安装以下环境：

- RabbitMQ：https://www.rabbitmq.com/
- 同时假设你已经有了一个可用的企业微信应用，并熟悉企业微信应用开发流程。如果对这块不熟悉，请参考企业微信官方开发者文档：
  https://developer.work.weixin.qq.com/

### 配置环境变量

由于接入即时通讯工具需要配置的环境变量较多，AilingBot提供了一个模板文件：.env.example，可以将其复制并重命名为.env。其内容如下：

```text
AILINGBOT_LANG="zh_CN"
AILINGBOT_TZ="Asia/Shanghai"

AILINGBOT_BROKER__NAME="pika"
AILINGBOT_BROKER__ARGS="{'host'='localhost'}"

AILINGBOT_POLICY__NAME="input_output"
AILINGBOT_POLICY__ARGS="{llm_name='openai',llm_args={model_name='gpt-3.5-turbo',openai_api_key='Your OpenAI API key here',temperature=0}}"

AILINGBOT_CHANNEL__AGENT__NAME="wechatwork"
AILINGBOT_CHANNEL__AGENT__ARGS="{corpid='Your WechatWork corp id here',corpsecret='Your WechatWork corp secret here',agentid=0}"
AILINGBOT_CHANNEL__WEBHOOK__NAME="wechatwork"
AILINGBOT_CHANNEL__WEBHOOK__ARGS="{token='Your WechatWork webhook token here',aes_key='Your WechatWork webhook AES key here'}"
AILINGBOT_CHANNEL__UVICORN__ARGS="{host='0.0.0.0',port='8080'}"
```

这里有如下地方需要按需填入：

- AILINGBOT_POLICY__ARGS的llm_args的openai_api_key中填入你的OpenAI API key
- AILINGBOT_CHANNEL__AGENT__ARGS的corpid、corpsecret和agentid需要填入你的企业微信应用的对应信息
- AILINGBOT_CHANNEL__WEBHOOK__ARGS的token和aes_key需要填入你的企业微信应用接收消息API配置中的Token和AES key

完成以上修改后，执行下述命令加载环境变量：

```shell
export $(grep -v '^#' .env | xargs)
```

### 启动机器人

为了实现接入即时通讯工具，需要分别执行一下三个命令启动对应进程：

启动Channel Webhook进程，这个进程的作用是作为Webhook接收用户发送给企业微信应用的消息：

```shell
ailingbot channel serve_webhook
```

启动Bot Serve进程，这个进程的作用是监听通过Webhook接收到的用户消息，并按对应会话策略生成回复消息：

```shell
ailingbot channel serve_webhook
```

启动Channel Agent进程，这个进程的作用是将Bot Serve进程回复的消息发送给用户：

```shell
ailingbot channel serve_agent
```

### 配置Webhook

最后我们需要去企业微信的管理后台，将webhook地址配置好，以便企业微信知道将接收到的用户消息转发到我们的webhook。
Webhook的URL为：http(s)://你的公网IP:8080/webhook/wechatwork/event/

完成以上配置后，就可以在企业微信中找到机器人，进行对话了：

<img src="./img/wechatwork-screenshot.png" alt="企业微信机器人" width="400"/>

# 发展计划

- [ ] 提供完善的使用文档和开发者文档
- [ ] 支持更多的IM端，如钉钉、飞书、Slack等
- [ ] 支持更多常用LLM prompting范式和开箱即用的对话策略
- [ ] 对LLM Chain中的常用能力，如对Vector Embedding&Query和Grounding提供支持
- [ ] 提供WebUI
- [ ] 提供基于Docker容器的一键部署能力
- [ ] 增强系统的可观测性和可治理性