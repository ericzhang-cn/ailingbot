from __future__ import annotations

import asyncio
import pickle
import typing

import aio_pika
from loguru import logger

import ailingbot.shared.errors
from ailingbot.brokers.broker import MessageBroker
from ailingbot.chat.messages import ResponseMessage, RequestMessage


class PikaMessageBroker(MessageBroker):
    """Pika message broker.

    Using Pika(AMQP protocol) as message broker.
    """

    def __init__(
        self,
        *,
        host: str = 'localhost',
        port: int = 5672,
        user: str = '',
        password: str = '',
        timeout: int = 5,
        queue_name_prefix: str = '',
    ):
        """Creates instance.

        :param host: AMQP host.
        :type host: str
        :param port: AMQP port.
        :type port: int
        :param user: AMQP user.
        :type user: str
        :param password: AMQP password.
        :type password: str
        :param timeout: Timeout for consuming message.
        :type timeout: int
        :param queue_name_prefix: Prefix of queue name.
        :type queue_name_prefix: str
        """
        super(PikaMessageBroker, self).__init__()

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout
        self.connection: typing.Optional[
            aio_pika.abc.AbstractConnection
        ] = None
        self.channel: typing.Optional[aio_pika.abc.AbstractChannel] = None
        self.exchange: typing.Optional[aio_pika.abc.AbstractExchange] = None
        self.req_queue: typing.Optional[aio_pika.abc.AbstractQueue] = None
        self.resp_queue: typing.Optional[aio_pika.abc.AbstractQueue] = None

        self.req_queue_name = 'ailingbot_request_queue'
        self.resp_queue_name = 'ailingbot_response_queue'
        if queue_name_prefix != '':
            self.req_queue_name = f'{queue_name_prefix}_{self.req_queue_name}'
            self.resp_queue_name = (
                f'{queue_name_prefix}_{self.resp_queue_name}'
            )

    async def _initialize(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(
                f'amqp://{self.user}:{self.password}@{self.host}:{self.port}/',
                timeout=5,
            )
        except asyncio.TimeoutError:
            raise ailingbot.shared.errors.BrokerError(
                'Connecting to broker timeout', critical=True
            )
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            'direct', auto_delete=False
        )
        self.req_queue = await self.channel.declare_queue(
            self.req_queue_name, auto_delete=False
        )
        self.resp_queue = await self.channel.declare_queue(
            self.resp_queue_name, auto_delete=False
        )

        await self.req_queue.bind(self.exchange, self.req_queue_name)
        await self.resp_queue.bind(self.exchange, self.resp_queue_name)

    async def _finalize(self) -> None:
        await self.req_queue.unbind(self.exchange, self.req_queue_name)
        await self.resp_queue.unbind(self.exchange, self.resp_queue_name)
        await self.connection.close()

    async def _produce(
        self,
        message: typing.Union[RequestMessage | ResponseMessage],
        *,
        queue_name: str,
        log_format: str,
    ) -> None:
        await self.exchange.publish(
            aio_pika.Message(body=pickle.dumps(message)),
            routing_key=queue_name,
        )
        logger.info(log_format.format(message.uuid))

    async def produce_request(self, message: RequestMessage) -> None:
        await self._produce(
            message,
            queue_name=self.req_queue_name,
            log_format='Produce request message, uuid: {}',
        )

    async def produce_response(self, message: ResponseMessage) -> None:
        await self._produce(
            message,
            queue_name=self.resp_queue_name,
            log_format='Produce response message, uuid: {}',
        )

    async def _consume(
        self,
        *,
        queue: aio_pika.abc.AbstractQueue,
        log_format: str,
    ) -> typing.Union[RequestMessage | ResponseMessage]:
        try:
            incoming_message = await queue.get(timeout=self.timeout)
        except aio_pika.exceptions.QueueEmpty as e:
            raise ailingbot.shared.errors.EmptyQueueError(str(e))

        await incoming_message.ack()
        message = pickle.loads(incoming_message.body)
        logger.info(log_format.format(message.uuid))
        return message

    async def consume_request(self) -> RequestMessage:
        return await self._consume(
            queue=self.req_queue,
            log_format='Consume request message, uuid: {}',
        )

    async def consume_response(self) -> ResponseMessage:
        return await self._consume(
            queue=self.resp_queue,
            log_format='Consume response message, uuid: {}',
        )
