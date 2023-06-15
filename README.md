[🇨🇳简体中文](https://github.com/ericzhang-cn/ailingbot/blob/main/README_Chinese.md)

---

![Python package workflow](https://github.com/ericzhang-cn/ailingbot/actions/workflows/python-package.yml/badge.svg)

<img src="./img/logo.png" alt="logo" width="50"/>

AilingBot - An all-in-one solution to empower your IM bot with AI.

# Features

- 💯**Open source&Free**: Completely open source and free.
- 📦**Out of the box**: No development is required, with pre-built capabilities to integrate with mainstream IM and LLM
  models.
- 🔗**Integrated LangChain**: The ability to integrate LangChain allows for the direct use of LangChain's pre-existing chains or agents.
- 🧩**Modular**: The project is organized in a modular way, with modules depending on abstract protocols, and similar
  modules
  implementing the protocols for plug-and-play functionality.
- 💻**Extensible**: It can expand the usage scenarios and capabilities of AilingBot. For example, integrating with new instant messaging platforms, new language learning models, or developing their own chains, agents, and chat policy.
- 🚀**High Performance**: AilingBot uses coroutine-based asynchronous mode to improve the system's high-concurrency
  performance. Meanwhile, the core servers can start multiple processes to further improve the system's high-concurrency
  processing capabilities.
- 🔌**API**: AilingBot provides a clear set of endpoints as its API interface, facilitating integration and coordination
  with
  other systems and processes.

# Quickstart Guide

## Launch an AI Chatbot in 5 Minutes

### Prerequisites

Please make sure you have the following environments installed on your machine:

- Python (>=3.9): https://www.python.org/
- Poetry: https://python-poetry.org/
- You also need an OpenAI API key. If you don't have one, please apply for it
  here: https://platform.openai.com/account/api-keys

### Modify configuration file

Copy the configuration file template and rename it:

```shell
cp settings.example.toml settings.toml
```

Modify the necessary configuration and start the bot with only one configuration item. Find the following section in settings.toml:

```toml
[policy.args.lc_chain_config.llm]
_type = "openai"
model_name = "gpt-3.5-turbo"
openai_api_key = "Your OpenAI API key"
temperature = 0
```

Change the value of `openai_api_key` to your actual OpenAI API key.

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

Start the bot with the following command:

```shell
ailingbot bot chat -c settings.toml
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

### Modify the configuration file.

Open settings.toml, the complete content is as follows:

```toml
# This is the AilingBot configuration file template. Please modify it as needed.

lang = "zh_CN"
tz = "Asia/Shanghai"

[broker]
name = "pika"

[broker.args]
host = "localhost"

[policy]
name = "lc_conversation_chain"
# name = "lc_llm_chain"

[policy.args]

[policy.args.lc_chain_config]
_type = "llm_chain"

[policy.args.lc_chain_config.prompt]
_type = "prompt"
template = """Human: {input}

AI:
"""
input_variables = ["input"]

[policy.args.lc_chain_config.llm]
_type = "openai"
model_name = "gpt-3.5-turbo"
openai_api_key = "Your OpenAI API key"
temperature = 0

[channel]

[channel.agent]

name = "wechatwork"

[channel.agent.args]
corpid = "WechatWork corpid"
corpsecret = "WechatWork corpsecret"
agentid = 0

[channel.webhook]
name = "wechatwork"

[channel.webhook.args]
token = "WechatWork webhook token"
aes_key = "WechatWork webhook aes_key"

[channel.uvicorn.args]
host = "0.0.0.0"
port = 8080
```

Here are the places that need to be filled in as needed:

- `openai_api_key = "Your OpenAI API key"`
- `corpid = "WechatWork corpid"`
- `corpsecret = "WechatWork corpsecret"`
- `agentid = 0`
- `token = "WechatWork webhook token"`
- `aes_key = "WechatWork webhook aes_key"`

### Start the Bot

To connect to instant messaging tools, three commands need to be executed to start the corresponding processes
separately:

Start the Channel Webhook process. The purpose of this process is to receive messages sent by users to the WeChat Work
app as a webhook:

```shell
ailingbot channel serve_webhook
```

Start the Bot Serve process. The purpose of this process is to listen for user messages received via the webhook and
generate reply messages based on the corresponding chat policy:

```shell
ailingbot bot serve
```

Start the Channel Agent process. The purpose of this process is to send the reply messages generated by the Bot Serve
process to the user:

```shell
ailingbot channel serve_agent
```

### Configure Webhook

Finally, we need to go to the WeChat Work management console to configure the webhook address so that WeChat Work knows
to forward the received user messages to our webhook.
The webhook URL is: `http(s)://your_public_IP:8080/webhook/wechatwork/event/`

After completing the above configuration, you can find the bot in WeChat Work and start a conversation:

<img src="./img/wechatwork-screenshot.png" alt="WeChat Work Bot" width="400"/>

# Roadmap

- [ ] Provide comprehensive user and developer documentation.
- [ ] Support more IM platforms, such as DingTalk, Feishu, and Slack.
- [ ] Support more commonly used LLM prompting paradigms and out-of-the-box chat policy.
- [ ] Provide support for commonly used capabilities in LLM Chain, such as Vector Embedding&Query and Grounding.
- [ ] Provide a WebUI.
- [ ] Provide one-click deployment capability based on Docker containers.
- [ ] Enhance the system's observability and manageability.

# License

> MIT License
>
>Copyright (c) 2023 AilingBot
>
>Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
>The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.
