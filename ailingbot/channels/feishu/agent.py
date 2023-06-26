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


class FeishuAgent(ChannelAgent):
    """Feishu channel agent class."""

    def __init__(self):
        """Initializes class."""
        super(FeishuAgent, self).__init__()

        self.app_id = settings.channel.app_id
        self.app_secret = settings.channel.app_secret
        self.access_token: typing.Optional[str] = None
        self.expire_in: typing.Optional[arrow.Arrow] = None

    async def _get_access_token(self) -> str:
        """Gets Feishu API access token.

        Returns cached token if not expired, otherwise, refreshes token.

        :return: Access token.
        :rtype: str
        """
        # Returns cached token if not expired.
        if self.expire_in is not None and arrow.now() < self.expire_in:
            return self.access_token

        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
                json={
                    'app_id': self.app_id,
                    'app_secret': self.app_secret,
                },
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                body = await response.json()

        if body.get('code', -1) != 0:
            raise ExternalHTTPAPIError(body.get('msg', ''))
        access_token, expires_in = body.get(
            'tenant_access_token', ''
        ), body.get('expire', 0)
        self.access_token = access_token
        self.expire_in = arrow.now().shift(seconds=(expires_in - 120))
        return access_token

    def _clean_access_token(self) -> None:
        """Cleans up access token to force refreshing token."""
        self.access_token = None
        self.expire_in = None

    async def _send(
        self, *, receive_id_type: str, body: dict[str, typing.Any]
    ) -> None:
        """Sends message using Feishu API.

        :param body: Request body parameters.
        :type body: typing.Dict[str, typing.Any]
        """
        access_token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://open.feishu.cn/open-apis/im/v1/messages',
                json=body,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json; charset=utf-8',
                },
                params={'receive_id_type': receive_id_type},
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                body = await response.json()
        if body.get('code', -1) != 0:
            raise ExternalHTTPAPIError(body.get('msg', ''))

    async def _reply(
        self, *, ack_uuid: str, body: dict[str, typing.Any]
    ) -> None:
        """Replies message using Feishu API.

        :param body: Request body parameters.
        :type body: typing.Dict[str, typing.Any]
        """
        access_token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'https://open.feishu.cn/open-apis/im/v1/messages/{ack_uuid}/reply',
                json=body,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json; charset=utf-8',
                },
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                body = await response.json()
        if body.get('code', -1) != 0:
            raise ExternalHTTPAPIError(body.get('msg', ''))

    async def send_message(self, message: ResponseMessage) -> None:
        """Using Feishu agent to send message."""
        try:
            content, message_type = await render(message)
        except NotImplementedError:
            content, message_type = await render(
                message.downgrade_to_text_message()
            )
        body = {
            'msg_type': message_type,
            'content': json.dumps(content),
            'uuid': message.uuid,
        }
        if message.scope == MessageScope.USER:
            receive_id_type = 'open_id'
        elif message.scope == MessageScope.GROUP:
            receive_id_type = 'chat_id'
        else:
            receive_id_type = 'open_id'

        if message.ack_uuid:
            await self._reply(ack_uuid=message.ack_uuid, body=body)
        else:
            body['receive_id'] = message.receiver_id
            await self._send(receive_id_type=receive_id_type, body=body)

    async def get_resource_from_message(
        self, message_id: str, file_key: str, resource_type: str
    ) -> bytes:
        """Get file or image resource from message."""
        access_token = await self._get_access_token()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/resources/{file_key}',
                headers={
                    'Authorization': f'Bearer {access_token}',
                },
                params={'type': resource_type},
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                return await response.content.read()
