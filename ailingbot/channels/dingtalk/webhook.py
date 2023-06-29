from __future__ import annotations

import typing

from asgiref.typing import ASGIApplication
from fastapi import FastAPI, status
from pydantic import BaseModel
from starlette.background import BackgroundTasks

from ailingbot.channels.channel import ChannelWebhookFactory
from ailingbot.channels.dingtalk.agent import DingtalkAgent
from ailingbot.chat.chatbot import ChatBot
from ailingbot.chat.messages import (
    TextRequestMessage,
    MessageScope,
    FileRequestMessage,
)


class DingtalkMessage(BaseModel):
    conversationId: typing.Optional[str]
    msgId: typing.Optional[str]
    conversationType: typing.Optional[str]
    senderId: typing.Optional[str]
    senderStaffId: typing.Optional[str]
    senderNick: typing.Optional[str]
    msgtype: typing.Optional[str]
    text: typing.Optional[dict]
    content: typing.Optional[dict]


class DingtalkWebhookFactory(ChannelWebhookFactory):
    """Factory that creates Dingtalk webhook ASGI application."""

    def __init__(self, *, debug: bool = False):
        super(DingtalkWebhookFactory, self).__init__(debug=debug)

        self.app: typing.Optional[ASGIApplication | typing.Callable] = None
        self.agent: typing.Optional[DingtalkAgent] = None
        self.bot: typing.Optional[ChatBot] = None

    async def create_webhook_app(self) -> ASGIApplication | typing.Callable:
        self.app = FastAPI()
        self.agent = DingtalkAgent()
        self.bot = ChatBot(debug=self.debug)

        async def _download_file() -> bytes:
            return b''

        async def _chat_task(
            conversation_id: str, dingtalk_message: DingtalkMessage
        ) -> None:
            """Send a request message to the bot, receive a response message, and send it back to the user."""

            if dingtalk_message.msgtype == 'text':
                req_msg = TextRequestMessage(
                    text=dingtalk_message.text.get('content', ''),
                )
            elif dingtalk_message.msgtype == 'file':
                dingtalk = DingtalkAgent()
                file_name = dingtalk_message.content.get('fileName', '')
                if len(file_name.split('.')) >= 2:
                    file_type = file_name.split('.')[-1].strip().lower()
                else:
                    file_type = ''
                file_content = await dingtalk.download_file(
                    download_code=dingtalk_message.content.get(
                        'downloadCode', ''
                    )
                )
                req_msg = FileRequestMessage(
                    file_name=file_name,
                    file_type=file_type,
                    content=file_content,
                )
            else:
                return

            req_msg.uuid = dingtalk_message.msgId
            req_msg.sender_id = dingtalk_message.senderId
            if dingtalk_message.conversationType == '1':
                req_msg.scope = MessageScope.USER
                req_msg.echo['staff_ids'] = [dingtalk_message.senderStaffId]
            elif dingtalk_message.conversationType == '2':
                req_msg.scope = MessageScope.GROUP
                req_msg.echo[
                    'conversation_id'
                ] = dingtalk_message.conversationId

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

        @self.app.post(
            '/webhook/dingtalk/event/', status_code=status.HTTP_200_OK
        )
        async def handle_event(
            message: DingtalkMessage,
            background_tasks: BackgroundTasks,
        ) -> dict:
            """Handle the message request from Dingtalk.

            :return: Empty dict.
            :rtype: dict
            """

            background_tasks.add_task(
                _chat_task, message.conversationId, message
            )

            return {}

        return self.app
