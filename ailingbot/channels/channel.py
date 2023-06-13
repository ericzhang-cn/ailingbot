from __future__ import annotations

import abc
import asyncio
import typing

from asgiref.typing import ASGIApplication
from loguru import logger

import ailingbot.shared.errors
from ailingbot.brokers.broker import MessageBroker
from ailingbot.chat.messages import ResponseMessage
from ailingbot.shared.abc import AbstractAsyncRunnable
from ailingbot.shared.misc import get_class_dynamically


class ChannelAgent(AbstractAsyncRunnable, abc.ABC):
    """Base class of channel agents."""

    def __init__(
        self, *, num_of_tasks: int = 1, broker_name: str, broker_args: dict
    ):
        super(ChannelAgent, self).__init__(num_of_tasks=num_of_tasks)

        self.broker_name = broker_name
        self.broker_args = broker_args or {}

        self.broker: typing.Optional[MessageBroker] = None

    @abc.abstractmethod
    async def send_message(self, message: ResponseMessage) -> None:
        """Send message from agent to users, groups or other targets.

        :param message: Message body.
        :type message: ResponseMessage
        """
        raise NotImplementedError

    async def _startup(self) -> None:
        self.broker = MessageBroker.get_broker(
            self.broker_name, **self.broker_args
        )
        await self.broker.initialize()

    async def _main_task(self, *, number: int) -> None:
        try:
            response_message = await self.broker.consume_response()
            await self.send_message(response_message)
        except ailingbot.shared.errors.EmptyQueueError:
            logger.info(f'Task{number}: No more response message to process.')
            await asyncio.sleep(1)

    async def _shutdown(self) -> None:
        await self.broker.finalize()

    @staticmethod
    def get_agent(
        name: str, broker_name: str, broker_args: dict, **kwargs
    ) -> ChannelAgent:
        """Gets channel agent instance.

        :param name: Built-in channel name or full path of agent class.
        :type name: str
        :param broker_name:
        :type broker_name:
        :param broker_args:
        :type broker_args:
        :return: Agent instance.
        :rtype: ChannelAgent
        """
        if name.lower() == 'wechatwork':
            from ailingbot.channels.wechatwork.agent import WechatworkAgent

            instance = WechatworkAgent(
                broker_name=broker_name, broker_args=broker_args, **kwargs
            )
        else:
            instance = get_class_dynamically(name)(**kwargs)

        return instance


class ChannelWebhookFactory(abc.ABC):
    """Base class of channel webhook factories."""

    def __init__(self, *, broker_name: str, broker_args: dict):
        self.broker_name = broker_name
        self.broker_args = broker_args or {}

    async def create_webhook_app(self) -> ASGIApplication | typing.Callable:
        """Creates a ASGI application.

        :return: ASGI application.
        :rtype: typing.Union[ASGIApplication, typing.Callable]
        """
        raise NotImplementedError

    @staticmethod
    async def get_webhook(
        name: str, broker_name: str, broker_args: dict, **kwargs
    ) -> ASGIApplication | typing.Callable:
        """Gets channel webhook ASGI application instance.

        :param name: Built-in channel name or full path of webhook factory class.
        :type name: str
        :param broker_name:
        :type broker_name:
        :param broker_args:
        :type broker_args:
        :return: Webhook ASGI application.
        :rtype: typing.Union[ASGIApplication, typing.Callable]
        """
        if name.lower() == 'wechatwork':
            from ailingbot.channels.wechatwork.webhook import (
                WechatworkWebhookFactory,
            )

            factory = WechatworkWebhookFactory(
                broker_name=broker_name, broker_args=broker_args, **kwargs
            )
        else:
            factory = get_class_dynamically(name)(**kwargs)

        return await factory.create_webhook_app()
