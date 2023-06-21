[🇨🇳简体中文](https://github.com/ericzhang-cn/ailingbot/blob/main/README_Chinese.md)

---

![Python package workflow](https://github.com/ericzhang-cn/ailingbot/actions/workflows/python-package.yml/badge.svg)
![Pylint workflow](https://github.com/ericzhang-cn/ailingbot/actions/workflows/pylint.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

<img src="https://github.com/ericzhang-cn/ailingbot/raw/main/img/logo.png" alt="logo" width="50" height="50"/>

AilingBot - An all-in-one solution to empower your IM bot with LLM.

# Features

- 💯**Open source & free**: Completely open source and free
- 📦**Out-of-the-box**: No development required, pre-installed with the ability to integrate with existing mainstream IM
  and LLM models
- 🔗**Integrated with LangChain**: Integrated with LangChain's ability to directly use pre-installed Chains or Agents
- 🧩**Modular**: The project is organized in a modular way, with modules depending on abstract protocols between them.
  Similar modules can implement protocols and be used immediately
- 💻**Scalable**: AilingBot's usage scenarios and capabilities can be expanded. For example, integrating with new IM, new
  LLM, or developing your own Chain, Agent, and chat policy
- 🚀**High performance**: AilingBot uses coroutine-based asynchronous mode to improve system's high concurrency
  performance. At the same time, the core process can start multiple processes to further improve the system's high
  concurrency processing capability
- 🔌**Integrated through API**: AilingBot provides a set of clear API interfaces for easy integration and collaboration
  with other systems and processes

# List of supported IMs

## Supported

- Enterprise WeChat
- Feishu

## Coming soon

- DingTalk
- Slack

# Quick Start Guide

## Start an AI chatbot in 5 minutes

Below you will see how to quickly start a command-line-based AI chatbot through AilingBot, with the effect as shown in
the figure:
![Command-line robot](https://github.com/ericzhang-cn/ailingbot/raw/main/img/command-line-screenshot.png)


> 💡First, you need an OpenAI API key. If you don't have one, apply here: https://platform.openai.com/account/api-keys

### Through Docker

```shell
git clone https://github.com/ericzhang-cn/ailingbot.git ailingbot
cd ailingbot
docker build -t ailingbot .
docker run -it --rm -e AILINGBOT_POLICY__LLM__OPENAI_API_KEY={Your OpenAI API key} ailingbot poetry run ailingbot bot chat
```

### Through PIP

#### Installation

```shell
pip install ailingbot
```

#### Generate configuration file

```shell
ailingbot init --silence --overwrite
```

At this point, a file called settings.toml will be created in the current directory, which is AilingBot's configuration
file.
Next, modify the necessary configurations. To start the robot, only one configuration is required. Find the following
section in settings.toml:

```toml
[policy.llm]
_type = "openai"
model_name = "gpt-3.5-turbo"
openai_api_key = ""
temperature = 0
```

Change the value of `openai_api_key` to your real OpenAI API key.

#### Start the robot

Start the robot with the following command:

```shell
ailingbot bot chat
```

## Integrating Instant Messaging Tools

Here's how to quickly integrate the above robot into Enterprise WeChat.

### Through Docker

```shell
export AILINGBOT_CHANNEL__AGENTID={Your Enterprise WeChat application AgentId}
export AILINGBOT_CHANNEL__CORPSECRET={Your Enterprise WeChat application CorpSecret}
export AILINGBOT_CHANNEL__AES_KEY={Your Enterprise WeChat application Webhook AES Key}
export AILINGBOT_CHANNEL__CORPID={Your Enterprise WeChat application CorpId}
export AILINGBOT_CHANNEL__TOKEN={Your Enterprise WeChat application Webhook Token}
export AILINGBOT_POLICY__LLM__OPENAI_API_KEY={Your OpenAI API key}
docker compose up
```

### Through PIP

#### Modify the configuration file

Open `settings.toml` and fill in the following section with your Enterprise WeChat application's real information:

```toml
[channel]
name = "wechatwork"
corpid = ""
corpsecret = ""
agentid = 0
token = ""
aes_key = ""
```

#### Start the service

```shell
ailingbot bot serve
ailingbot bot channel serve_agent
ailingbot bot channel serve_webhook
```

Finally, we need to go to the Enterprise WeChat management console to configure the webhook address so that Enterprise
WeChat knows to forward the received user messages to our webhook.
The URL of the webhook is: `http(s)://your_public_IP:8080/webhook/wechatwork/event/`

After completing the above configuration, you can find the robot in Enterprise WeChat and start a conversation:

<img src="https://github.com/ericzhang-cn/ailingbot/raw/main/img/wechatwork-screenshot.png" alt="Enterprise WeChat robot" width="400"/>

# Development Plan

- [ ] Provide complete usage and developer documentation
- [ ] Support more IM clients, such as DingTalk, Slack, etc.
- [ ] Support more commonly used LLM prompting paradigms and out-of-the-box chat policy
- [ ] Provide support for common capabilities in LLM Chain, such as Vector Embedding&Query and Grounding
- [ ] Provide a WebUI
- [ ] Provide one-click deployment capability based on Docker containers
- [ ] Enhance system observability and govern

# 许可协议

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
