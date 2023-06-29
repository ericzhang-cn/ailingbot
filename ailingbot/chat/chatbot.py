from __future__ import annotations

import asyncio
import typing
import uuid

from loguru import logger

from ailingbot.chat.messages import (
    RequestMessage,
    FallbackResponseMessage,
    ResponseMessage,
)
from ailingbot.chat.policy import ChatPolicy
from ailingbot.config import settings
from ailingbot.shared.abc import AbstractAsyncComponent


class ChatBot(AbstractAsyncComponent):
    """ChatBot is core component that responsible for retrieve request and make response."""

    def __init__(
        self,
        *,
        debug: bool = False,
    ):
        super(ChatBot, self).__init__()

        self.debug = debug

        self.locks: dict[str, asyncio.Lock] = {}
        self.policy: typing.Optional[ChatPolicy] = None

    async def chat(
        self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        """Run chat pipeline, and replies messages to sender.

        :param conversation_id: Conversation id.
        :type conversation_id: str
        :param message: Reqeust message.
        :type message: RequestMessage
        """
        if conversation_id not in self.locks:
            self.locks[conversation_id] = asyncio.Lock()
        lock = self.locks[conversation_id]

        async with lock:
            try:
                r = await self.policy.respond(
                    conversation_id=conversation_id, message=message
                )
            except Exception as e:
                logger.error(e)
                r = FallbackResponseMessage(
                    reason=str(e),
                )
            r.uuid = str(uuid.uuid4())
            r.ack_uuid = message.uuid
            r.receiver_id = message.sender_id
            r.scope = message.scope
            r.echo = message.echo

            return r

    async def _initialize(self) -> None:
        self.policy = ChatPolicy.get_policy(
            name=settings.policy.name,
            debug=self.debug,
        )
        await self.policy.initialize()

    async def _finalize(self):
        await self.policy.finalize()
