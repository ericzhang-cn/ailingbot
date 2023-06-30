from __future__ import annotations

import aiohttp

from ailingbot.channels.channel import ChannelAgent
from ailingbot.chat.messages import ResponseMessage, MessageScope
from ailingbot.config import settings
from ailingbot.shared.errors import ExternalHTTPAPIError


class SlackAgent(ChannelAgent):
    """Slack channel agent class."""

    def __init__(self):
        """Initializes class."""
        super(SlackAgent, self).__init__()

        self.oauth_token = settings.channel.oauth_token

    async def _send(
        self,
        *,
        channel: str,
        thread_ts: str = '',
        text: str,
    ) -> None:
        """Sends message using Slack API."""
        async with aiohttp.ClientSession() as session:
            body = {
                'channel': channel,
                'text': text,
            }
            if thread_ts:
                body['thread_ts'] = thread_ts
            async with session.post(
                'https://slack.com/api/chat.postMessage',
                json=body,
                headers={
                    'Authorization': f'Bearer {self.oauth_token}',
                    'Content-Type': 'application/json; charset=utf-8',
                },
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                body = await response.json()
        if not body.get('ok', False):
            raise ExternalHTTPAPIError(body.get('error', ''))

    async def send_message(self, message: ResponseMessage) -> None:
        """Using Slack agent to send message."""
        text = message.downgrade_to_text_message().text
        channel = message.echo['channel']
        thread_ts = message.ack_uuid
        if message.scope == MessageScope.USER:
            await self._send(channel=channel, text=text)
        elif message.scope == MessageScope.GROUP:
            # await self._send(channel=channel, text=text, thread_ts=thread_ts)
            await self._send(channel=channel, text=text)

    async def download_file(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={
                    'Authorization': f'Bearer {self.oauth_token}',
                },
            ) as response:
                if not response.ok:
                    response.raise_for_status()
                return await response.content.read()
