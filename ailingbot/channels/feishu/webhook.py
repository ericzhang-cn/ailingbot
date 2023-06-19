from __future__ import annotations

import json
import typing

from asgiref.typing import ASGIApplication
from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel

from ailingbot.brokers.broker import MessageBroker
from ailingbot.channels.channel import ChannelWebhookFactory
from ailingbot.chat.messages import TextRequestMessage, MessageScope
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

        self.verification_token = (
            settings.channel.webhook.args.verification_token
        )

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

        @self.app.post(
            '/webhook/feishu/event/', status_code=status.HTTP_200_OK
        )
        async def handle_event(
            event: FeishuEventBody,
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
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail='Event type is not supported.',
                )
            if event.event.message.message_type != 'text':
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail='Message type is not supported.',
                )

            req_msg = TextRequestMessage(
                uuid=event.event.message.message_id,
                text=json.loads(event.event.message.content).get('text', ''),
                sender_id=event.event.sender.sender_id.get('open_id', ''),
            )
            if event.event.message.chat_type == 'p2p':
                req_msg.scope = MessageScope.USER
            elif event.event.message.chat_type == 'group':
                req_msg.scope = MessageScope.GROUP
                req_msg.meta['conversation_tag'] = event.event.message.chat_id

            await self.broker.produce_request(req_msg)

            return {}

        return self.app
