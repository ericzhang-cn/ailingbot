from __future__ import annotations

import json
import typing

from asgiref.typing import ASGIApplication
from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel
from starlette.background import BackgroundTasks

from ailingbot.brokers.broker import MessageBroker
from ailingbot.channels.channel import ChannelWebhookFactory
from ailingbot.channels.feishu.agent import FeishuAgent
from ailingbot.chat.messages import (
    TextRequestMessage,
    MessageScope,
    FileRequestMessage,
)
from ailingbot.config import settings


class FeishuEventBodyHeader(BaseModel):
    event_id: typing.Optional[str]
    event_type: typing.Optional[str]
    create_time: typing.Optional[str]
    token: typing.Optional[str]
    app_id: typing.Optional[str]
    tenant_key: typing.Optional[str]


class FeishuEventBodyEventSender(BaseModel):
    sender_id: typing.Optional[dict[str, str]]
    sender_type: typing.Optional[str]
    tenant_key: typing.Optional[str]


class FeishuEventBodyEventMessage(BaseModel):
    message_id: typing.Optional[str]
    root_id: typing.Optional[str]
    parent_id: typing.Optional[str]
    create_time: typing.Optional[str]
    chat_id: typing.Optional[str]
    chat_type: typing.Optional[str]
    message_type: typing.Optional[str]
    content: typing.Optional[str]


class FeishuEventBodyEvent(BaseModel):
    sender: typing.Optional[FeishuEventBodyEventSender]
    message: typing.Optional[FeishuEventBodyEventMessage]


class FeishuEventBody(BaseModel):
    """The event body of Feishu message."""

    challenge: typing.Optional[str]
    token: typing.Optional[str]
    type: typing.Optional[str]
    header: typing.Optional[FeishuEventBodyHeader]
    event: typing.Optional[FeishuEventBodyEvent]


class FeishuWebhookFactory(ChannelWebhookFactory):
    """Factory that creates Feishu webhook ASGI application."""

    def __init__(self):
        super(FeishuWebhookFactory, self).__init__()

        self.verification_token = settings.channel.verification_token

        self.broker: typing.Optional[MessageBroker] = None
        self.app: typing.Optional[ASGIApplication | typing.Callable] = None

    async def create_webhook_app(self) -> ASGIApplication | typing.Callable:
        self.broker = MessageBroker.get_broker(settings.broker.name)
        self.app = FastAPI()

        @self.app.on_event('startup')
        async def startup() -> None:
            await self.broker.initialize()

        @self.app.on_event('shutdown')
        async def shutdown() -> None:
            await self.broker.finalize()

        def _create_text_request_message(
            event: FeishuEventBody,
        ) -> TextRequestMessage:
            text = json.loads(event.event.message.content).get('text', '')
            text = ' '.join(
                [
                    x
                    for x in text.split(' ')
                    if not x.strip().startswith('@_user_')
                ]
            )
            return TextRequestMessage(
                text=text,
            )

        async def _create_file_request_message(
            event: FeishuEventBody,
        ) -> FileRequestMessage:
            content = json.loads(event.event.message.content)
            file_key = content.get('file_key', '')
            file_name = content.get('file_name', '')

            feishu = FeishuAgent()
            content = await feishu.get_resource_from_message(
                event.event.message.message_id, file_key, 'file'
            )
            if len(file_name.split('.')) >= 2:
                file_type = file_name.split('.')[-1].strip().lower()
            else:
                file_type = ''

            return FileRequestMessage(
                content=content,
                file_type=file_type,
                file_name=file_name,
            )

        async def _create_request_message_task(event: FeishuEventBody) -> None:
            """Background task for creating request message from event."""
            if event.event.message.message_type == 'text':
                req_msg = _create_text_request_message(event)
            elif event.event.message.message_type == 'file':
                req_msg = await _create_file_request_message(event)
            else:
                return

            req_msg.uuid = event.event.message.message_id
            req_msg.sender_id = event.event.sender.sender_id.get('open_id', '')
            if event.event.message.chat_type == 'p2p':
                req_msg.scope = MessageScope.USER
            elif event.event.message.chat_type == 'group':
                req_msg.scope = MessageScope.GROUP
                req_msg.meta['chat_id'] = event.event.message.chat_id

            await self.broker.produce_request(req_msg)

        @self.app.post(
            '/webhook/feishu/event/', status_code=status.HTTP_200_OK
        )
        async def handle_event(
            event: FeishuEventBody,
            background_tasks: BackgroundTasks,
        ) -> dict:
            """Handle the event request from Feishu.

            :return: Empty dict.
            :rtype: dict
            """
            if event.type and event.type == 'url_verification':
                if not event.token or event.token != self.verification_token:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='Invalid verification token.',
                    )
                else:
                    return {
                        'challenge': event.challenge,
                    }

            if event.header.token != self.verification_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid verification token.',
                )
            if event.header.event_type != 'im.message.receive_v1':
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='Event type is not supported.',
                )
            if event.event.message.message_type not in ['text', 'file']:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='Message type is not supported.',
                )

            background_tasks.add_task(_create_request_message_task, event)

            return {}

        return self.app
