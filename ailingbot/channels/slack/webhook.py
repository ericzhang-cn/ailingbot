from __future__ import annotations

import re
import typing

from asgiref.typing import ASGIApplication
from fastapi import FastAPI, status, Request, Response, HTTPException
from starlette.background import BackgroundTasks

from ailingbot.channels.channel import ChannelWebhookFactory
from ailingbot.channels.slack.agent import SlackAgent
from ailingbot.chat.chatbot import ChatBot
from ailingbot.chat.messages import (
    TextRequestMessage,
    MessageScope,
    FileRequestMessage,
)
from ailingbot.config import settings


class SlackWebhookFactory(ChannelWebhookFactory):
    """Factory that creates Slack webhook ASGI application."""

    def __init__(self, *, debug: bool = False):
        super(SlackWebhookFactory, self).__init__(debug=debug)

        self.verification_token = settings.channel.verification_token

        self.app: typing.Optional[ASGIApplication | typing.Callable] = None
        self.agent: typing.Optional[SlackAgent] = None
        self.bot: typing.Optional[ChatBot] = None

    async def create_webhook_app(self) -> ASGIApplication | typing.Callable:
        self.app = FastAPI()
        self.agent = SlackAgent()
        self.bot = ChatBot(debug=self.debug)

        async def _chat_task(conversation_id: str, event: dict) -> None:
            """Send a request message to the bot, receive a response message, and send it back to the user."""
            if 'files' in event:
                file_name = event['files'][0]['name']
                file_type = event['files'][0]['filetype'].lower()
                url = event['files'][0]['url_private_download']
                content = await self.agent.download_file(url)
                req_msg = FileRequestMessage(
                    file_name=file_name,
                    file_type=file_type,
                    content=content,
                )
            elif 'text' in event:
                text = re.sub(r'<@\w+>', '', event['text'])
                req_msg = TextRequestMessage(
                    text=text,
                )
            else:
                return

            req_msg.uuid = event['event_ts']
            req_msg.sender_id = event['user']
            req_msg.echo['channel'] = event['channel']
            if event.get('channel_type', '') == 'im':
                req_msg.scope = MessageScope.USER
            else:
                req_msg.scope = MessageScope.GROUP

            response = await self.bot.chat(
                conversation_id=conversation_id, message=req_msg
            )
            await self.agent.send_message(response)

        @self.app.on_event('startup')
        async def startup() -> None:
            await self.agent.initialize()
            await self.bot.initialize()

        @self.app.on_event('shutdown')
        async def shutdown() -> None:
            await self.agent.finalize()
            await self.bot.finalize()

        @self.app.post('/webhook/slack/event/', status_code=status.HTTP_200_OK)
        async def handle_event(
            request: Request,
            background_tasks: BackgroundTasks,
        ) -> dict | Response:
            """Handle the event request from Slack.

            :return: Empty dict.
            :rtype: dict
            """
            message = await request.json()
            if message.get('token', '') != self.verification_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid verification token.',
                )

            if 'challenge' in message:
                return Response(
                    content=message.get('challenge'), media_type='text/plain'
                )

            if message.get('event', {}).get('type') not in [
                'message',
                'app_mention',
            ]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='Event type is not supported.',
                )

            background_tasks.add_task(
                _chat_task,
                message.get('event', {}).get('channel', ''),
                message.get('event', {}),
            )

            return {}

        return self.app
