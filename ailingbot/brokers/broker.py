from __future__ import annotations

import abc

from ailingbot.chat.messages import RequestMessage, ResponseMessage
from ailingbot.shared.abc import AbstractAsyncComponent
from ailingbot.shared.misc import get_class_dynamically


class MessageBroker(AbstractAsyncComponent, abc.ABC):
    """Base class of message brokers."""

    def __init__(self):
        super(MessageBroker, self).__init__()

    @abc.abstractmethod
    async def produce_request(self, message: RequestMessage) -> None:
        """Produces request message to broker.

        :param message: Request message.
        :type message: RequestMessage
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def consume_request(self) -> RequestMessage:
        """Consumes request message from broker.

        :return: Request message.
        :rtype: RequestMessage
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def produce_response(self, message: ResponseMessage) -> None:
        """Produces response message to broker.

        :param message: Response message.
        :type message: ResponseMessage
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def consume_response(self) -> ResponseMessage:
        """Consumes response message from broker.

        :return: Response message.
        :rtype: ResponseMessage
        """
        raise NotImplementedError

    @staticmethod
    def get_broker(name: str, **kwargs) -> MessageBroker:
        """Gets broker instance.

        :param name: Built-in broker name or full path of broker class.
        :type name: str
        :return: Broker instance.
        :rtype: MessageBroker
        """
        if name.lower() == 'pika':
            from ailingbot.brokers.pika_broker import PikaMessageBroker

            instance = PikaMessageBroker(**kwargs)
        else:
            instance = get_class_dynamically(name)(**kwargs)

        return instance
