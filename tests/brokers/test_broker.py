import pytest

from ailingbot.brokers.broker import MessageBroker
from ailingbot.shared.errors import AilingBotError


def test_get_broker():
    MessageBroker.get_broker('pika')
    MessageBroker.get_broker('pika')
    MessageBroker.get_broker('ailingbot.brokers.pika_broker.PikaMessageBroker')

    with pytest.raises(AilingBotError):
        MessageBroker.get_broker('ailingbot.brokers.NotExistsBroker')
