import asyncio

import pytest

from ailingbot.brokers.pika_broker import PikaMessageBroker
from ailingbot.chat.messages import TextRequestMessage, MessageScope


@pytest.fixture(scope='function')
def pika_broker():
    return PikaMessageBroker(host='localhost')


@pytest.mark.asyncio
async def test_produce_and_consume_request_message(pika_broker):
    await pika_broker.initialize()

    await pika_broker.produce_request(
        TextRequestMessage(
            text='Message 1',
            uuid='1',
            sender_id='sender',
            scope=MessageScope.USER,
        )
    )
    await pika_broker.produce_request(
        TextRequestMessage(
            text='Message 2',
            uuid='2',
            sender_id='sender',
            scope=MessageScope.USER,
        )
    )
    await pika_broker.produce_request(
        TextRequestMessage(
            text='Message 3',
            uuid='3',
            sender_id='sender',
            scope=MessageScope.USER,
        )
    )

    message1 = await pika_broker.consume_request()
    assert (
        isinstance(message1, TextRequestMessage)
        and message1.text == 'Message 1'
    )
    message2 = await pika_broker.consume_request()
    assert (
        isinstance(message2, TextRequestMessage)
        and message2.text == 'Message 2'
    )
    message3 = await pika_broker.consume_request()
    assert (
        isinstance(message3, TextRequestMessage)
        and message3.text == 'Message 3'
    )

    await pika_broker.finalize()


@pytest.mark.asyncio
async def test_concurrence_safety(pika_broker):
    await pika_broker.initialize()

    await asyncio.gather(
        *[
            pika_broker.produce_request(
                TextRequestMessage(
                    text=f'Message {x + 1}',
                    uuid=f'{x + 1}',
                    sender_id='sender',
                    scope=MessageScope.USER,
                )
            )
            for x in range(3)
        ]
    )
    tasks = await asyncio.gather(
        *[pika_broker.consume_request() for _ in range(3)]
    )
    assert [x.uuid for x in tasks] == ['1', '2', '3']

    await pika_broker.finalize()
