from __future__ import annotations

import json
import typing

import aiohttp
import arrow

from ailingbot.channels.channel import ChannelAgent
from ailingbot.channels.feishu.render import render
from ailingbot.chat.messages import ResponseMessage, MessageScope
from ailingbot.config import settings
from ailingbot.shared.errors import ExternalHTTPAPIError


class DingtalkAgent(ChannelAgent):
    """Dingtalk channel agent class."""

    def __init__(self):
        """Initializes class."""
        super(DingtalkAgent, self).__init__()

        self.app_key = settings.channel.app_key
        self.app_secret = settings.channel.app_secret
        self.robot_code = settings.channel.robot_code
        self.access_token: typing.Optional[str] = None
        self.expire_in: typing.Optional[arrow.Arrow] = None

    async def _get_access_token(self) -> str:
        """Gets Dingtalk API access token.

        Returns cached token if not expired, otherwise, refreshes token.

        :return: Access token.
        :rtype: str
        """
        # Returns cached token if not expired.
        if self.expire_in is not None and arrow.now() < self.expire_in:
            return self.access_token

        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://oapi.dingtalk.com/gettoken',
                params={
                    'appkey': self.app_key,
                    'appsecret': self.app_secret,
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

    def _clean_access_token(self) -> None:
        """Cleans up access token to force refreshing token."""
        self.access_token = None
        self.expire_in = None

    async def _send_to_users(
        self, *, user_ids: list[str], body: dict[str, typing.Any]
    ) -> None:
        """Sends message to a batch of user using Dingtalk API.

        :param body: Request body parameters.
        :type body: typing.Dict[str, typing.Any]
        """
        access_token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            body['userIds'] = user_ids
            async with session.post(
                'https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend',
                json=body,
                headers={
                    'x-acs-dingtalk-access-token': access_token,
                    'Content-Type': 'application/json; charset=utf-8',
                },
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                body = await response.json()
        if body.get('processQueryKey', None) is None:
            raise ExternalHTTPAPIError(body.get('message', ''))

    async def _send_to_group(
        self, *, open_conversation_id: str, body: dict[str, typing.Any]
    ) -> None:
        """Replies message using Feishu API.

        :param body: Request body parameters.
        :type body: typing.Dict[str, typing.Any]
        """
        access_token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            body['openConversationId'] = open_conversation_id
            async with session.post(
                'https://api.dingtalk.com/v1.0/robot/groupMessages/send',
                json=body,
                headers={
                    'x-acs-dingtalk-access-token': access_token,
                    'Content-Type': 'application/json; charset=utf-8',
                },
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                body = await response.json()
        if body.get('processQueryKey', None) is None:
            raise ExternalHTTPAPIError(body.get('message', ''))

    async def send_message(self, message: ResponseMessage) -> None:
        """Using Dingtalk agent to send message."""
        try:
            content, message_type = await render(message)
        except NotImplementedError:
            content, message_type = await render(
                message.downgrade_to_text_message()
            )
        body = {
            'msgParam': json.dumps(content, ensure_ascii=False),
            'msgKey': message_type,
            'robotCode': self.robot_code,
        }
        if message.scope == MessageScope.USER:
            await self._send_to_users(
                user_ids=message.echo.get('staff_ids', []), body=body
            )
        elif message.scope == MessageScope.GROUP:
            await self._send_to_group(
                open_conversation_id=message.echo.get('conversation_id', ''),
                body=body,
            )
