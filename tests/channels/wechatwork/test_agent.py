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


@pytest.mark.asyncio
async def test_get_access_token(agent):
    token1 = await agent.get_access_token()
    assert token1 is not None
    assert isinstance(token1, str)

    token2 = await agent.get_access_token()
    assert token2 is not None
    assert isinstance(token2, str)

    assert token1 == token2


@pytest.mark.asyncio
async def test_clean_access_token(agent):
    await agent.get_access_token()
    assert agent.access_token is not None
    assert agent.expire_in is not None

    agent.clean_access_token()
    assert agent.access_token is None
    assert agent.expire_in is None
