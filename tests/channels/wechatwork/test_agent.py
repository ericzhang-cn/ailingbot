import pytest

from ailingbot.channels.wechatwork.agent import WechatworkAgent
from ailingbot.config import settings


@pytest.fixture(scope='function')
def agent():
    return WechatworkAgent(
        broker_name=settings.broker.name,
        broker_args=settings.broker.args,
        corpid=settings.channel.agent.args.corpid,
        corpsecret=settings.channel.agent.args.corpsecret,
        agentid=settings.channel.agent.args.agentid,
    )
