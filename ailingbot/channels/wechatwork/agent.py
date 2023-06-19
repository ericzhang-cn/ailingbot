from __future__ import annotations

import typing

import aiohttp
import arrow

from ailingbot.channels.channel import ChannelAgent
from ailingbot.channels.wechatwork.render import render
from ailingbot.chat.messages import ResponseMessage, MessageScope
from ailingbot.config import settings
from ailingbot.shared.errors import ExternalHTTPAPIError


class WechatworkAgent(ChannelAgent):
    """Wechatwork channel agent class."""

    def __init__(
        self,
        *,
        num_of_tasks: int = 1,
    ):
        """Initializes class."""
        super(WechatworkAgent, self).__init__(
            num_of_tasks=num_of_tasks,
        )

        self.corpid = settings.channel.agent.args.corpid
        self.corpsecret = settings.channel.agent.args.corpsecret
        self.agentid = settings.channel.agent.args.agentid
        self.access_token: typing.Optional[str] = None
        self.expire_in: typing.Optional[arrow.Arrow] = None

    async def get_access_token(self) -> str:
        """Gets Wechatwork API access token.

        Returns cached token if not expired, otherwise, refreshes token.

        :return: Access token.
        :rtype: str
        """
        # Returns cached token if not expired.
        if self.expire_in is not None and arrow.now() < self.expire_in:
            return self.access_token

        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://qyapi.weixin.qq.com/cgi-bin/gettoken',
                params={
                    'corpid': self.corpid,
                    'corpsecret': self.corpsecret,
                },
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                body = await response.json()

        if body.get('errcode', -1) != 0:
            raise ExternalHTTPAPIError(body.get('errmsg', ''))
        access_token, expires_in = body.get('access_token', ''), body.get(
            'expires_in', 0
        )
        self.access_token = access_token
        self.expire_in = arrow.now().shift(seconds=(expires_in - 120))
        return access_token

    def clean_access_token(self) -> None:
        """Cleans up access token to force refreshing token."""
        self.access_token = None
        self.expire_in = None

    async def send(self, *, body: dict[str, typing.Any]) -> None:
        """Sends message using Wechatwork API.

        :param body: Request body parameters.
        :type body: typing.Dict[str, typing.Any]
        """
        req_body = {
            'agentid': self.agentid,
            **body,
        }
        access_token = await self.get_access_token()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://qyapi.weixin.qq.com/cgi-bin/message/send',
                params={'access_token': access_token},
                json=req_body,
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                body = await response.json()
        if body.get('errcode', -1) != 0:
            raise ExternalHTTPAPIError(body.get('errmsg', ''))

    async def send_message(self, message: ResponseMessage) -> None:
        """Using Wechatwork agent to send message."""
        try:
            content, message_type = await render(message)
        except NotImplementedError:
            content, message_type = await render(
                message.downgrade_to_text_message()
            )
        body = {
            'msgtype': message_type,
            **content,
        }
        if message.scope == MessageScope.USER:
            body['touser'] = (
                message.receiver_id
                if isinstance(message.receiver_id, str)
                else '|'.join(message.receiver_id)
            )
        elif message.scope == MessageScope.CUSTOMIZED_1:
            body['toparty'] = (
                message.receiver_id
                if isinstance(message.receiver_id, str) is str
                else '|'.join(message.receiver_id)
            )
        elif message.scope == MessageScope.CUSTOMIZED_2:
            body['totag'] = (
                message.receiver_id
                if isinstance(message.receiver_id, str) is str
                else '|'.join(message.receiver_id)
            )

        await self.send(body=body)
