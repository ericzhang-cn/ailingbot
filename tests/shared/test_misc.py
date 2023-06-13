import pytest

from ailingbot.shared.errors import AilingBotError
from ailingbot.shared.misc import get_class_dynamically


def test_get_class_dynamically():
    klass = get_class_dynamically(
        'ailingbot.brokers.pika_broker.PikaMessageBroker'
    )
    assert klass.__name__ == 'PikaMessageBroker'

    with pytest.raises(AilingBotError):
        get_class_dynamically('ailingbot.not.exists.ClassName')
