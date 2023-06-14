from __future__ import annotations

import typing
from urllib import parse

import xmltodict
from asgiref.typing import ASGIApplication
from fastapi import FastAPI, status, HTTPException
from fastapi.requests import Request
from fastapi.responses import PlainTextResponse

from ailingbot.brokers.broker import MessageBroker
from ailingbot.channels.channel import ChannelWebhookFactory
from ailingbot.channels.wechatwork.encrypt import signature, decrypt
from ailingbot.chat.messages import TextRequestMessage, MessageScope
from ailingbot.config import settings


class WechatworkWebhookFactory(ChannelWebhookFactory):
    """Factory that creates wechatwork webhook ASGI application."""

    def __init__(self):
        super(WechatworkWebhookFactory, self).__init__()

        self.token = settings.channel.webhook.args.token
        self.aes_key = settings.channel.webhook.args.aes_key

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

        @self.app.get(
            '/webhook/wechatwork/event/',
            status_code=status.HTTP_200_OK,
            response_class=PlainTextResponse,
        )
        async def handle_challenge(
            msg_signature: str, timestamp: int, nonce: int, echostr: str
        ) -> str:
            """Handle the challenge request from Wechatwork.

            :param msg_signature: Message signature from challenge request.
            :type msg_signature: str
            :param timestamp: Challenge request timestamp.
            :type timestamp: int
            :param nonce: Challenge request nonce.
            :type nonce: int
            :param echostr: Challenge request echostr, which should be decrypted and respond to challenger.
            :type echostr: str
            :return: Decrypted echostr.
            :rtype: str
            """
            token = self.token
            aes_key = self.aes_key
            encrypt_message = parse.unquote(echostr)

            sig = signature(
                token=token,
                timestamp=timestamp,
                nonce=nonce,
                msg_encrypt=encrypt_message,
            )
            if sig != msg_signature:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid signature.',
                )

            message, _ = decrypt(key=aes_key, msg_encrypt=encrypt_message)
            return message

        @self.app.post(
            '/webhook/wechatwork/event/', status_code=status.HTTP_200_OK
        )
        async def handle_event(
            msg_signature: str, timestamp: int, nonce: int, request: Request
        ) -> dict:
            """Handle the event request from Wechatwork.

            :param msg_signature: Message signature from challenge request.
            :type msg_signature: str
            :param timestamp: Challenge request timestamp.
            :type timestamp: int
            :param nonce: Challenge request nonce.
            :type nonce: int
            :param request: Http request.
            :type request: Request
            :return: Empty dict.
            :rtype: dict
            """
            token = self.token
            aes_key = self.aes_key
            body_xml = await request.body()
            body = xmltodict.parse(body_xml)
            encrypt_message = body.get('xml', {}).get('Encrypt', '')

            sig = signature(
                token=token,
                timestamp=timestamp,
                nonce=nonce,
                msg_encrypt=encrypt_message,
            )
            if sig != msg_signature:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid signature.',
                )

            message_xml, _ = decrypt(key=aes_key, msg_encrypt=encrypt_message)
            message = xmltodict.parse(message_xml)
            from_user_name = message.get('xml', {}).get('FromUserName', '')
            msg_type = message.get('xml', {}).get('MsgType', '')

            req_msg = None
            if msg_type == 'text':
                message_id = message.get('xml', {}).get('MsgId', '')
                content = message.get('xml', {}).get('Content', '')
                req_msg = TextRequestMessage(
                    uuid=message_id,
                    sender_id=from_user_name,
                    scope=MessageScope.USER,
                    text=content,
                )

            if req_msg:
                await self.broker.produce_request(req_msg)

            return {}

        return self.app
