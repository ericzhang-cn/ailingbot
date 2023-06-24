import copy
import uuid

from langchain import ConversationChain
from langchain.llms.loading import load_llm_from_config
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory.chat_memory import BaseChatMemory

from ailingbot.chat.messages import (
    RequestMessage,
    ResponseMessage,
    TextRequestMessage,
    TextResponseMessage,
    FallbackResponseMessage,
)
from ailingbot.chat.policy import ChatPolicy
from ailingbot.config import settings


class LCConversationChatPolicy(ChatPolicy):
    """Having a direct conversation with a large language model."""

    def __init__(
        self,
        *,
        debug: bool = False,
    ):
        super(LCConversationChatPolicy, self).__init__(
            debug=debug,
        )

        llm_config = copy.deepcopy(settings.policy.llm)
        llm = load_llm_from_config(llm_config)
        self.chain = ConversationChain(llm=llm, verbose=debug)
        self.history_size = settings.policy.history_size or 5
        self.memories: dict[str, BaseChatMemory] = {}

    async def _load_memory(self, *, conversation_id: str) -> BaseChatMemory:
        """Load memory for conversation. Create a new memory if not exists.

        :param conversation_id: Conversation ID.
        :type conversation_id: str
        :return: Chat memory.
        :rtype: BaseChatMemory
        """
        if conversation_id not in self.memories:
            self.memories[conversation_id] = ConversationBufferWindowMemory(
                k=self.history_size
            )
        return self.memories[conversation_id]

    async def respond(
        self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        if not isinstance(message, TextRequestMessage):
            response = FallbackResponseMessage()
            response.reason = 'LCConversationChatPolicy can only handle messages of type TextRequestMessage.'
        else:
            if conversation_id not in self.chain:
                self.chain.memory = await self._load_memory(
                    conversation_id=conversation_id
                )
            response = TextResponseMessage()
            response.text = await self.chain.arun(message.text)
        response.uuid = str(uuid.uuid4())
        response.ack_uuid = message.uuid
        response.receiver_id = message.sender_id
        response.scope = message.scope
        response.echo = message.echo

        return response


class LCDocumentQAPolicy(ChatPolicy):
    """Question-Answering based on documents."""

    async def respond(
        self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        pass
