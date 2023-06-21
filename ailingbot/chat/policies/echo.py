import json
import uuid

from ailingbot.chat.messages import (
    RequestMessage,
    ResponseMessage,
    TextRequestMessage,
    FallbackResponseMessage,
    TabularResponseMessage,
)
from ailingbot.chat.policy import ChatPolicy


class EchoChatPolicy(ChatPolicy):
    """Return message to the user with context, for testing purposes only."""

    def __init__(
        self,
        *,
        debug: bool = False,
        **kwargs,
    ):
        super(EchoChatPolicy, self).__init__(debug=debug)

    async def respond(
        self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        if not isinstance(message, TextRequestMessage):
            response = FallbackResponseMessage()
            response.reason = 'EchoChatPolicy can only handle messages of type TextRequestMessage.'
        else:
            response = TabularResponseMessage()
            response.uuid = str(uuid.uuid4())
            response.title = response.uuid
            response.headers = ['Field', 'Value']
            response.data = [
                ['UUID', message.uuid],
                ['Sender', message.sender_id],
                ['Scope', message.scope.name],
                ['Meta', json.dumps(message.meta)],
                ['Echo', json.dumps(message.echo)],
                ['Text', message.text],
            ]
            response.ack_uuid = message.uuid
            response.receiver_id = message.sender_id
            response.scope = message.scope
            response.echo = message.echo

        return response
