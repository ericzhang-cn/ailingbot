MAIN_SETTINGS = """# This is the AilingBot configuration file template. Please modify it as needed.

lang = \"zh_CN\"
tz = \"Asia/Shanghai\"

[broker]
name = \"{0}\"

[broker.args]
{1}

[policy]
name = \"{2}\"

[policy.args]
{3}

[channel]

[channel.agent]
name = \"{4}\"

[channel.agent.args]
{5}

[channel.webhook]
name = \"{6}\"

[channel.webhook.args]
{7}

[channel.uvicorn.args]
host = \"0.0.0.0\"
port = 8080
"""

PIKA_BROKER_ARGS_SETTINGS = """host = \"localhost\"
port = 5672
user = \"\"
password = \"\"
timeout = 5
queue_name_prefix = \"\""""

LC_CONVERSATION_CHAIN_POLICY_ARGS_SETTINGS = """
[policy.args.lc_chain_config.llm]
_type = \"openai\"
model_name = \"gpt-3.5-turbo\"
openai_api_key = \"Your OpenAI API key\"
temperature = 0"""

LC_LLM_CHAIN_POLICY_ARGS_SETTINGS = """
[policy.args.lc_chain_config]
_type = \"llm_conversation\"

[policy.args.lc_chain_config.prompt]
_type = \"prompt\"
template = \"\"\"Human: {input}

AI:
\"\"\"
input_variables = [\"input\"]

[policy.args.lc_chain_config.llm]
_type = \"openai\"
model_name = \"gpt-3.5-turbo\"
openai_api_key = \"Your OpenAI API key\"
temperature = 0"""

WECHATWORK_CHANNEL_AGENT_ARGS_SETTINGS = """corpid = \"WechatWork corpid\"
corpsecret = \"WechatWork corpsecret\"
agentid = 0"""

WECHATWORK_CHANNEL_WEBHOOK_ARGS_SETTINGS = """token = \"WechatWork webhook token\"
aes_key = \"WechatWork webhook aes_key\""""

FEISHU_CHANNEL_AGENT_ARGS_SETTINGS = """app_id = \"Feishu app_id\"
app_secret = \"Feishu app_secret\""""

FEISHU_CHANNEL_WEBHOOK_ARGS_SETTINGS = (
    """verification_token = \"Feishu webhook verification_token\""""
)
