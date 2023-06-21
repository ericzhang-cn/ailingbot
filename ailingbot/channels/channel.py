from __future__ import annotations

import abc
import asyncio
import typing

from asgiref.typing import ASGIApplication
from loguru import logger

import ailingbot.shared.errors
from ailingbot.brokers.broker import MessageBroker
from ailingbot.chat.messages import ResponseMessage
from ailingbot.config import settings
from ailingbot.shared.abc import AbstractAsyncRunnable
from ailingbot.shared.misc import get_class_dynamically


class ChannelAgent(AbstractAsyncRunnable, abc.ABC):
    """Base class of channel agents."""

    def __init__(self, *, num_of_tasks: int = 1):
        super(ChannelAgent, self).__init__(num_of_tasks=num_of_tasks)

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
            settings.broker.name,
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
    def get_agent(name: str, num_of_tasks: int = 1) -> ChannelAgent:
        """Gets channel agent instance.

        :param name: Built-in channel name or full path of agent class.
        :type name: str
        :param num_of_tasks:
        :type num_of_tasks:
        :return: Agent instance.
        :rtype: ChannelAgent
        """
        if name.lower() == 'wechatwork':
            from ailingbot.channels.wechatwork.agent import WechatworkAgent

            instance = WechatworkAgent(num_of_tasks=num_of_tasks)
        elif name.lower() == 'feishu':
            from ailingbot.channels.feishu.agent import FeishuAgent

            instance = FeishuAgent(num_of_tasks=num_of_tasks)
        else:
            instance = get_class_dynamically(name)(num_of_tasks=num_of_tasks)

        return instance


class ChannelWebhookFactory(abc.ABC):
    """Base class of channel webhook factories."""

    def __init__(self):
        pass

    async def create_webhook_app(self) -> ASGIApplication | typing.Callable:
        """Creates a ASGI application.

        :return: ASGI application.
        :rtype: typing.Union[ASGIApplication, typing.Callable]
        """
        raise NotImplementedError

    @staticmethod
    async def get_webhook(name: str) -> ASGIApplication | typing.Callable:
        """Gets channel webhook ASGI application instance.

        :param name: Built-in channel name or full path of webhook factory class.
        :type name: str
        :return: Webhook ASGI application.
        :rtype: typing.Union[ASGIApplication, typing.Callable]
        """
        if name.lower() == 'wechatwork':
            from ailingbot.channels.wechatwork.webhook import (
                WechatworkWebhookFactory,
            )

            factory = WechatworkWebhookFactory()
        elif name.lower() == 'feishu':
            from ailingbot.channels.feishu.webhook import (
                FeishuWebhookFactory,
            )

            factory = FeishuWebhookFactory()
        else:
            factory = get_class_dynamically(name)()

        return await factory.create_webhook_app()
