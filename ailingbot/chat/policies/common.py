import abc
import uuid

from langchain import ConversationChain
from langchain.chains.base import Chain
from langchain.memory import ConversationBufferMemory

from ailingbot.chat.langchain import get_llm
from ailingbot.chat.messages import (
    RequestMessage,
    ResponseMessage,
    TextRequestMessage,
    TextResponseMessage,
    FallbackResponseMessage,
)
from ailingbot.chat.policy import ChatPolicy


class InputOutputChatPolicy(ChatPolicy):
    """Input and output chat policy.

    InputOutputChatPolicy is a simple chat policy that wraps input with task instructions.
    """

    def __init__(
        self,
        *,
        debug: bool = False,
        llm_name: str = 'openai',
        llm_args: dict,
    ):
        super(InputOutputChatPolicy, self).__init__(debug=debug)

        self.llm = get_llm(llm_name, **llm_args)
        self.chain: dict[str, Chain] = {}

    async def respond(
        self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        if not isinstance(message, TextRequestMessage):
            response = FallbackResponseMessage()
            response.reason = 'InputOutputChatPolicy can only handle messages of type TextRequestMessage.'
        else:
            if conversation_id not in self.chain:
                self.chain[conversation_id] = ConversationChain(
                    llm=self.llm,
                    memory=ConversationBufferMemory(),
                    verbose=self.debug,
                )
            r = await self.chain[conversation_id].arun(message.text)
            response = TextResponseMessage()
            response.text = r
        response.uuid = str(uuid.uuid4())
        response.ack_uuid = message.uuid
        response.receiver_id = message.sender_id
        response.scope = message.scope
        response.echo = message.echo

        return response
