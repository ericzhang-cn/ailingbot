![Python package workflow](https://github.com/ericzhang-cn/ailingbot/actions/workflows/python-package.yml/badge.svg)
![Pylint workflow](https://github.com/ericzhang-cn/ailingbot/actions/workflows/pylint.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

<p align="center">
  <img src="https://raw.githubusercontent.com/ericzhang-cn/ailingbot/main/img/logo.png" alt="AilingBot" width="300">
</p>

<p align="center"><b>AilingBot - 一站式解决方案，为你的IM机器人接入AI强大能力。</b></p>

# 特点

- 💯**开源&免费**：完全开源且免费
- 📦**开箱即用**：无需开发，预置接入现有主流IM及AI模型的能力
- 🔗**LangChain友好**：方便集成LangChain
- 🧩**模块化**：项目采用模块化组织，模块之间通过抽象协议依赖，同类模块实现协议即可即插即用
- 💻**可扩展**：可以扩展AilingBot的使用场景和能力。例如接入到新的IM，新的AI模型，或者定制自己的对话策略
- 🔥**高性能**：AilingBot采用基于协程的异步模式，提高系统的高并发性能。同时可以通过多进程进一步提升系统的高并发处理能力
- 🔌**通过API集成**：AilingBot提供一组清晰的API接口，方便与其他系统及流程集成协同

# 🚀快速开始

## 5分钟启动一个AI聊天机器人

下面将看到如何通过AilingBot快速启动一个基于命令行界面的AI机器人，效果如图：
<p align="center">
    <img src="https://raw.githubusercontent.com/ericzhang-cn/ailingbot/main/img/command-line-screenshot.png" alt="命令行机器人"/>
</p>


> 💡首先你需要有一个OpenAI API key。如果没有请到这里申请：https://platform.openai.com/account/api-keys

### 通过Docker

```shell
git clone https://github.com/ericzhang-cn/ailingbot.git ailingbot
cd ailingbot
docker build -t ailingbot .
docker run -it --rm \
  -e  AILINGBOT_POLICY__LLM__OPENAI_API_KEY={你的OpenAI API key} \
  ailingbot poetry run ailingbot chat
```

### 通过PIP

#### 安装

```shell
pip install ailingbot
```

#### 生成配置文件

```shell
ailingbot init --silence --overwrite
```

此时在当前目录会创建一个叫settings.toml的文件，这个文件就是AilingBot的配置文件。
接下来修改必要配置，启动机器人只需一项配置，找到settings.toml中以下部分：

```toml
[policy.llm]
_type = "openai"
model_name = "gpt-3.5-turbo"
openai_api_key = ""
temperature = 0
```

将其中`openai_api_key`的值改为你的真实OpenAI API key。

#### 启动机器人

通过如下命令启动机器人：

```shell
ailingbot chat
```

## 接入即时通讯工具

下面演示如何快速将上面的机器人接入企业微信。

### 通过Docker

```shell
git clone https://github.com/ericzhang-cn/ailingbot.git ailingbot
cd ailingbot
docker build -t ailingbot .
docker run -d \
  -e AILINGBOT_POLICY__LLM__OPENAI_API_KEY={你的OpenAI API key} \
  -e AILINGBOT_CHANNEL__CORPID={你的企业微信corpid} \
  -e AILINGBOT_CHANNEL__CORPSECRET={你的企业微信corpsecret} \
  -e AILINGBOT_CHANNEL__AGENTID={你的企业微信agentid} \
  -e AILINGBOT_CHANNEL__TOKEN={你的企业微信webhook token} \
  -e AILINGBOT_CHANNEL__AES_KEY={你的企业微信webhook aes_key} \
  -p 8080:8080
  ailingbot poetry run ailingbot serve
```

### 通过PIP

#### 安装

```shell
pip install ailingbot
```

#### 生成配置文件

```shell
ailingbot init --silence --overwrite
```

#### 修改配置文件

打开`settings.toml`，将其中的下面部分填入你的企业微信应用真实信息：

```toml
[channel]
name = "wechatwork"
corpid = ""
corpsecret = ""
agentid = 0
token = ""
aes_key = ""
```

#### 启动服务

```shell
ailingbot serve
```

最后我们需要去企业微信的管理后台，将webhook地址配置好，以便企业微信知道将接收到的用户消息转发到我们的webhook。
Webhook的URL为：`http(s)://你的公网IP:8080/webhook/wechatwork/event/`

完成以上配置后，就可以在企业微信中找到机器人，进行对话了：

<p align="center">
    <img src="https://raw.githubusercontent.com/ericzhang-cn/ailingbot/main/img/wechatwork-screenshot.png" alt="企业微信机器人" width="300"/>
</p>

# 📖使用指南

## 主要流程

AilingBot的主要处理流程如下图：

<p align="center">
    <img src="https://raw.githubusercontent.com/ericzhang-cn/ailingbot/main/img/flow.png" alt="主要流程" width="500"/>
</p>

1. 首先用户将消息发送给IM的机器人
2. 如果配置了webhook，即时通讯工具会将发送给机器人的请求转发到webhook服务地址
3. Webhook服务将IM原始消息经过处理，转为AilingBot内部的消息格式，发送给ChatBot
4. ChatBot会根据所配置的会话策略（Chat Policy），处理请求并形成响应消息。这个过程中，ChatBot
   可能会进行请求大语言模型、访问向量数据库、调用外部API等操作以完成请求处理
5. ChatBot将响应信息发送给IM Agent，IM Agent负责将AilingBot内部响应信息格式转换成
   特定IM的格式，并调用IM开放能力API发送响应消息
6. IM机器人将消息显示给用户，完成整个处理过程

## 主要概念

- **IM机器人**：多数即时通讯工具内置的能力，允许管理员创建一个机器人，并通过程序处理用户的消息
- **Channel**：Channel表示不同终端，可以是一个IM，也可能是一个自定义终端（如Web）
- **Webhook**：一个http(s)服务，用于接收IM机器人转发的用户消息，不同Channel对于webhook有自己的规范，因此需要有自己的webhook实现
- **IM Agent**：用于调用IM开放能力API，不同的IM开放能力API不同，因此每个Channel需要有对应Agent实现
- **ChatBot**：用于接收和响应用户消息的核心组件
- **会话策略**：具体定义如何响应用户，被ChatBot调用。一个会话策略具体定义了机器人的能力，如闲聊、进行知识问答等
- **LLM**：大语言模型，如何OpenAI的ChatGPT，开放的ChatGLM等均属于不同的大语言模型，大语言模型是实现AI能力的关键组件

## 配置

### 配置方式

AilingBot的配置可以通过两种方式：

- **通过配置文件**：AilingBot读取当前目录的`settings.toml`作为配置文件，其文件格式为[TOML](https://toml.io/en/)
  具体配置项见下文
- **通过环境变量**：AilingBot也会读取环境变量中配置项，具体环境变量列表见下文

> 💡配置文件和环境变量可以混合使用，当一个配置项同时存在于两者时，优先使用环境变量

### 配置项

#### 通用

| 配置项       | 说明                                                                  | TOML                 | 环境变量                             |
|-----------|---------------------------------------------------------------------|----------------------|----------------------------------|
| 语言        | 语言码（参考：http://www.lingoes.net/en/translator/langcode.htm）           | lang                 | AILINGBOT__LANG                  |
| 时区        | 时区码（参考：https://en.wikipedia.org/wiki/List_of_tz_database_time_zones | tz                   | AILINGBOT__TZ                    |
| 会话策略名称    | 预置会话策略名称或完整会话策略class路径                                              | policy.name          | AILINGBOT__POLICY__NAME          |
| Channel名称 | 预置Channel名称                                                         | channel.name         | AILINGBOT__CHANNEL__NAME         |
| Webhook路径 | 非预置Channel webhook的完整class路径                                        | channel.webhook_name | AILINGBOT__CHANNEL__WEBHOOK_NAME |
| Agent路径   | 非预置Channel agent的完整class路径                                          | channel.agent_name   | AILINGBOT__CHANNEL__AGENT_NAME   |
| Uvicorn配置 | 所有uvicorn配置（参考：https://www.uvicorn.org/settings/)，这部分配置会透传给uvicorn  | uvicorn.*            | AILINGBOT__CHANNEL__UVICORN__*   |

#### 内置会话策略配置

##### lc_conversation

lc_conversation使用LangChain的Conversation作为会话策略，其效果为直接和LLM对话，且带有对话历史上下文，因此可以进行多轮会话。

| 配置项 | 说明 | TOML | 环境变量 |
|-----|----|------|------|

##### lc_document_qa

lc_document_qa使用LangChain的[Stuff](https://python.langchain.com/docs/modules/chains/document/stuff)作为对话策略。
用户可上传一个文档，然后针对文档内容进行提问。

| 配置项 | 说明 | TOML | 环境变量 |
|-----|----|------|------|

#### 内置Channel配置

##### 企业微信

| 配置项 | 说明 | TOML | 环境变量 |
|-----|----|------|------|

##### 飞书

| 配置项 | 说明 | TOML | 环境变量 |
|-----|----|------|------|

## 命令行工具

TBD

# 💻开发指南

TBD

# 发展计划

- [ ] 提供完善的使用文档和开发者文档
- [ ] 支持更多的IM端，如钉钉、Slack等
- [ ] 支持更多常用LLM prompting范式和开箱即用的对话策略
- [ ] 对LLM Chain中的常用能力，如对Vector Embedding&Query和Grounding提供支持
- [ ] 提供WebUI
- [ ] 提供基于Docker容器的一键部署能力
- [ ] 增强系统的可观测性和可治理性
