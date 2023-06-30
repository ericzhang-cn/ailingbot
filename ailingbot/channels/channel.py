from __future__ import annotations

import abc
import typing

from asgiref.typing import ASGIApplication

from ailingbot.shared.abc import AbstractAsyncComponent
from ailingbot.shared.misc import get_class_dynamically


class ChannelAgent(AbstractAsyncComponent, abc.ABC):
    """Base class of channel agents."""

    def __init__(self):
        super(ChannelAgent, self).__init__()

    @staticmethod
    def get_agent(
        name: str, full_class_path: typing.Optional[str] = None
    ) -> ChannelAgent:
        """Gets channel agent instance.

        :param name: Built-in channel name or full path of agent class.
        :type name: str
        :param full_class_path:
        :type full_class_path:
        :return: Agent instance.
        :rtype: ChannelAgent
        """
        if name.lower() == 'wechatwork':
            from ailingbot.channels.wechatwork.agent import WechatworkAgent

            instance = WechatworkAgent()
        elif name.lower() == 'feishu':
            from ailingbot.channels.feishu.agent import FeishuAgent

            instance = FeishuAgent()
        elif name.lower() == 'dingtalk':
            from ailingbot.channels.dingtalk.agent import DingtalkAgent

            instance = DingtalkAgent()
        else:
            instance = get_class_dynamically(full_class_path)()

        return instance


class ChannelWebhookFactory(abc.ABC):
    """Base class of channel webhook factories."""

    def __init__(self, *, debug: bool = False):
        self.debug = debug

    async def create_webhook_app(self) -> ASGIApplication | typing.Callable:
        """Creates a ASGI application.

        :return: ASGI application.
        :rtype: typing.Union[ASGIApplication, typing.Callable]
        """
        raise NotImplementedError

    @staticmethod
    async def get_webhook(
        name: str,
        full_class_path: typing.Optional[str] = None,
        debug: bool = False,
    ) -> ASGIApplication | typing.Callable:
        """Gets channel webhook ASGI application instance.

        :param name: Built-in channel name or full path of webhook factory class.
        :type name: str
        :param full_class_path:
        :type full_class_path:
        :param debug:
        :type debug:
        :return: Webhook ASGI application.
        :rtype: typing.Union[ASGIApplication, typing.Callable]
        """
        if name.lower() == 'wechatwork':
            from ailingbot.channels.wechatwork.webhook import (
                WechatworkWebhookFactory,
            )

            factory = WechatworkWebhookFactory(debug=debug)
        elif name.lower() == 'feishu':
            from ailingbot.channels.feishu.webhook import (
                FeishuWebhookFactory,
            )

            factory = FeishuWebhookFactory(debug=debug)

        elif name.lower() == 'dingtalk':
            from ailingbot.channels.dingtalk.webhook import (
                DingtalkWebhookFactory,
            )

            factory = DingtalkWebhookFactory(debug=debug)
        elif name.lower() == 'slack':
            from ailingbot.channels.slack.webhook import (
                SlackWebhookFactory,
            )

            factory = SlackWebhookFactory(debug=debug)
        else:
            factory = get_class_dynamically(full_class_path)(debug=debug)

        return await factory.create_webhook_app()
