[🇨🇳简体中文](https://github.com/ericzhang-cn/ailingbot/blob/main/README_Chinese.md)

<img src="./img/logo.png" alt="logo" width="50"/>

AilingBot - An all-in-one solution to empower your IM bot with AI.

# Highlights

- 📦**Out of the box**: No development is required, with pre-built capabilities to integrate with mainstream IM and LLM
  models.
- 🧩**Modular**: The project is organized in a modular way, with modules depending on abstract protocols, and similar modules
  implementing the protocols for plug-and-play functionality.
- 💻**Extensible**: Thanks to the modular organization, AilingBot can be extended to new usage scenarios and capabilities by
  implementing custom modules based on the module protocols, such as integrating with new IMs, large models, or
  developing custom dialog strategies.
- 🚀**High Performance**: AilingBot uses coroutine-based asynchronous mode to improve the system's high-concurrency
  performance. Meanwhile, the core process can start multiple processes to further improve the system's high-concurrency
  processing capabilities.
- 🔌**API**: AilingBot provides a clear set of endpoints as its API interface, facilitating integration and coordination with
  other systems and processes.

# Quickstart Guide

## Launch an AI Chatbot in 5 Minutes

### Prerequisites

Please make sure you have the following environments installed on your machine:

- Python (>=3.9): https://www.python.org/
- Poetry: https://python-poetry.org/
- You also need an OpenAI API key. If you don't have one, please apply for it
  here: https://platform.openai.com/account/api-keys

### Set Environment Variables (Optional)

AilingBot's development philosophy encourages configurations to be placed in environment variables. However, you can
skip this step and pass in the required information dynamically when running the start command.

Set environment variable commands:

```shell
export AILINGBOT_POLICY__NAME="input_output"
export AILINGBOT_POLICY__ARGS="{llm_name='openai',llm_args={model_name='gpt-3.5-turbo',openai_api_key='这里填入你的OpenAI API key',temperature=0}}"
```

### Start the Bot

In the AilingBot root directory, first install dependencies:

```shell
poetry install
```

Then enter the virtualenv environment:

```shell
poetry shell
```

Run the following command:

```shell
ailingbot --help
```

If you see the following output, it means AilingBot is installed successfully:

```text
Usage: ailingbot [OPTIONS] COMMAND [ARGS]...

  AilingBot command line tools.

Options:
  --help  Show this message and exit.

Commands:
  bot      Bot commands.
  channel  Channel commands.
```

If you have set environment variables earlier, you can start the bot with the following command:

```shell
ailingbot bot chat
```

If you have not set environment variables, you need to pass in the required information through start parameters:

```shell
ailingbot bot chat --policy input_output --policy-args "{llm_name='openai',llm_args={model_name='gpt-3.5-turbo',openai_api_key='这里填入你的OpenAI API key',temperature=0}}"
```

You can now start an interactive conversation with the bot, as shown in the following screenshot:
![command-line-screenshot](img/command-line-screenshot.png)

## Connect to Instant Messaging Tools

Below we take WeChat Work as an example to demonstrate how AilingBot can be quickly connected to instant messaging
tools.

### Prerequisites

To connect to WeChat Work, in addition to the prerequisites above, you also need to install the following environment:

- RabbitMQ: https://www.rabbitmq.com/

- Assumes you already have a usable WeChat Work app and are familiar with the WeChat Work app development process. If
  you're not familiar with this, please refer to the WeChat Work official developer
  documentation: https://developer.work.weixin.qq.com/

### Configure Environment Variables

Since connecting to instant messaging tools requires configuring many environment variables, AilingBot provides a
template file: .env.example, which can be copied and renamed to .env. Its contents are as follows:

```shell
AILINGBOT_LANG="zh_CN"
AILINGBOT_TZ="Asia/Shanghai"

AILINGBOT_BROKER__NAME="pika"
AILINGBOT_BROKER__ARGS="{'host'='localhost'}"

AILINGBOT_POLICY__NAME="input_output"
AILINGBOT_POLICY__ARGS="{llm_name='openai',llm_args={model_name='gpt-3.5-turbo',openai_api_key='Your OpenAI API key
here',temperature=0}}"

AILINGBOT_CHANNEL__AGENT__NAME="wechatwork"
AILINGBOT_CHANNEL__AGENT__ARGS="{corpid='Your WechatWork corp id here',corpsecret='Your WechatWork corp secret here'
,agentid=0}"
AILINGBOT_CHANNEL__WEBHOOK__NAME="wechatwork"
AILINGBOT_CHANNEL__WEBHOOK__ARGS="{token='Your WechatWork webhook token here',aes_key='Your WechatWork webhook AES key
here'}"
AILINGBOT_CHANNEL__UVICORN__ARGS="{host='0.0.0.0',port='8080'}"
```

The following information needs to be filled in as needed:

- Fill in your OpenAI API key in the openai_api_key field of llm_args in AILINGBOT_POLICY__ARGS
- Fill in the corresponding information of your WeChat Work app in corpid, corpsecret, and agentid in
  AILINGBOT_CHANNEL__AGENT__ARGS
- Fill in the Token and AES key in the configuration of the WeChat Work app's message receiving API in token and aes_key
  in AILINGBOT_CHANNEL__WEBHOOK__ARGS.

After completing the above modifications, run the following command to load the environment variables:

```shell
export $(grep -v '^#' .env | xargs)
```

### Start the Bot

To connect to instant messaging tools, three commands need to be executed to start the corresponding processes
separately:

Start the Channel Webhook process. The purpose of this process is to receive messages sent by users to the WeChat Work
app as a webhook:

```shell
ailingbot channel serve_webhook
```

Start the Bot Serve process. The purpose of this process is to listen for user messages received via the webhook and
generate reply messages based on the corresponding session strategy:

```shell
ailingbot channel serve_webhook
```

Start the Channel Agent process. The purpose of this process is to send the reply messages generated by the Bot Serve
process to the user:

```shell
ailingbot channel serve_agent
```

### Configure Webhook

Finally, we need to go to the WeChat Work management console to configure the webhook address so that WeChat Work knows
to forward the received user messages to our webhook.
The webhook URL is: http(s)://your_public_IP:8080/webhook/wechatwork/event/

After completing the above configuration, you can find the bot in WeChat Work and start a conversation:

<img src="./img/wechatwork-screenshot.png" alt="WeChat Work Bot" width="400"/>

# Roadmap

- [ ] Provide comprehensive user and developer documentation.
- [ ] Support more IM platforms, such as DingTalk, Feishu, and Slack.
- [ ] Support more commonly used LLM prompting paradigms and out-of-the-box dialog strategies.
- [ ] Provide support for commonly used capabilities in LLM Chain, such as Vector Embedding&Query and Grounding.
- [ ] Provide a WebUI.
- [ ] Provide one-click deployment capability based on Docker containers.
- [ ] Enhance the system's observability and manageability.
