from __future__ import annotations

import asyncio
import enum
import typing
import uuid

from loguru import logger

import ailingbot.shared.errors
from ailingbot.brokers.broker import MessageBroker
from ailingbot.chat.messages import (
    RequestMessage,
    FallbackResponseMessage,
    ResponseMessage,
)
from ailingbot.chat.policy import ChatPolicy
from ailingbot.config import settings, validators
from ailingbot.shared.abc import AbstractAsyncRunnable


class BotRunMode(enum.Enum):
    """Running mode of the bot."""

    Broker = 'Broker'
    Standalone = 'Standalone'


class ChatBot(AbstractAsyncRunnable):
    """ChatBot is core component that responsible for retrieve request and make response."""

    def __init__(
        self,
        *,
        num_of_tasks: int = 1,
        run_mode: BotRunMode = BotRunMode.Broker,
        debug: bool = False,
    ):
        super(ChatBot, self).__init__(num_of_tasks=num_of_tasks)

        self.run_mode = run_mode
        self.debug = debug

        self.locks: dict[str, asyncio.Lock] = {}
        self.broker: typing.Optional[MessageBroker] = None
        self.policy: typing.Optional[ChatPolicy] = None

    async def respond(
        self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        try:
            return await self.policy.respond(
                conversation_id=conversation_id, message=message
            )
        except Exception as e:
            logger.error(e)
            return FallbackResponseMessage(
                reason=str(e),
            )

    async def chat(
        self, *, conversation_id: str, message: RequestMessage
    ) -> None:
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
            response = await self.respond(
                conversation_id=conversation_id, message=message
            )
            await self.broker.produce_response(response)

    async def _startup(self):
        if self.run_mode == BotRunMode.Broker:
            self.broker = MessageBroker.get_broker(name=settings.broker.name)
            await self.broker.initialize()

        self.policy = ChatPolicy.get_policy(
            name=settings.policy.name,
            debug=self.debug,
        )
        await self.policy.initialize()

    async def _main_task(self, *, number: int):
        try:
            request_message = await self.broker.consume_request()
        except ailingbot.shared.errors.EmptyQueueError:
            logger.info(f'Task{number}: No more request message to process.')
            await asyncio.sleep(1)
            return

        conversation_id = request_message.sender_id
        if request_message.scope is not None:
            conversation_id = (
                f'{conversation_id}-{request_message.scope.value}'
            )
        if request_message.meta and request_message.meta.get(
            'conversation_tag', None
        ):
            conversation_id = (
                f'{conversation_id}-{request_message.meta["conversation_tag"]}'
            )
        conversation_id = conversation_id.casefold()

        try:
            await self.chat(
                conversation_id=conversation_id, message=request_message
            )
        except ailingbot.shared.errors.AilingBotError as e:
            if e.critical:
                logger.critical(str(e))
                self.should_exit = True
            else:
                logger.error(str(e))
                r = FallbackResponseMessage(
                    uuid=str(uuid.uuid4()),
                    ack_uuid=request_message.uuid,
                    receiver_id=request_message.sender_id,
                    scope=request_message.scope,
                    echo=request_message.echo,
                    reason=e.reason,
                    suggestion=e.suggestion,
                )
                await self.broker.produce_response(r)

    async def _shutdown(self):
        await self.broker.finalize()
