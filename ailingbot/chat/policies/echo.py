import json
import uuid

from ailingbot.chat.messages import (
    RequestMessage,
    ResponseMessage,
    TextRequestMessage,
    TextResponseMessage,
    FallbackResponseMessage,
)
from ailingbot.chat.policy import ChatPolicy


class EchoChatPolicy(ChatPolicy):
    """Return message to the user with context, for testing purposes only."""

    def __init__(
            self,
            *,
            debug: bool = False,
    ):
        super(EchoChatPolicy, self).__init__(debug=debug)

    async def respond(
            self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        if not isinstance(message, TextRequestMessage):
            response = FallbackResponseMessage()
            response.reason = 'EchoChatPolicy can only handle messages of type TextRequestMessage.'
        else:
            response = TextResponseMessage()
            response.text = f"""Content: {message.text or ''}
UUID: {message.uuid or ''}
Sender ID: {message.sender_id or ''}
Scope: {message.scope or ''}
Meta: {json.dumps(message.meta) or ''}
Echo: {json.dumps(message.echo) or ''}"""
            response.uuid = str(uuid.uuid4())
            response.ack_uuid = message.uuid
            response.receiver_id = message.sender_id
            response.scope = message.scope
            response.echo = message.echo

        return response
