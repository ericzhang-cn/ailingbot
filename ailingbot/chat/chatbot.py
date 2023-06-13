from __future__ import annotations

import asyncio
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
from ailingbot.shared.abc import AbstractAsyncRunnable


class ChatBot(AbstractAsyncRunnable):
    """ChatBot is core component that responsible for retrieve request and make response."""

    def __init__(
        self,
        *,
        num_of_tasks: int = 1,
        debug: bool = False,
        broker_name: typing.Optional[str] = None,
        broker_args: typing.Optional[dict] = None,
        policy_name: typing.Optional[str] = None,
        policy_args: typing.Optional[dict] = None,
    ):
        super(ChatBot, self).__init__(num_of_tasks=num_of_tasks)

        self.debug = debug
        self.locks: dict[str, asyncio.Lock] = {}

        self.broker_name = broker_name
        self.broker_args = broker_args or {}
        self.policy_name = policy_name
        self.policy_args = policy_args or {}

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
        if self.broker_name is not None:
            self.broker = MessageBroker.get_broker(
                self.broker_name, **self.broker_args
            )
            await self.broker.initialize()

        if self.policy_name is not None:
            self.policy = ChatPolicy.get_policy(
                self.policy_name, debug=self.debug, **self.policy_args
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
