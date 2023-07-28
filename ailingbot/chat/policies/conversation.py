import copy

from langchain import ConversationChain
from langchain.llms.loading import load_llm_from_config
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory.chat_memory import BaseChatMemory

from ailingbot.chat.messages import (
    ResponseMessage,
    TextRequestMessage,
    FallbackResponseMessage,
    TextResponseMessage,
    RequestMessage,
)
from ailingbot.chat.policy import ChatPolicy
from ailingbot.config import settings


class ConversationChatPolicy(ChatPolicy):
    """Having a direct conversation with a large language model."""

    def __init__(
        self,
        *,
        debug: bool = False,
    ):
        super().__init__(
            debug=debug,
        )

        llm_config = copy.deepcopy(settings.policy.llm)
        llm = load_llm_from_config(llm_config)
        self.chain = ConversationChain(llm=llm, verbose=debug)
        self.history_size = settings.policy.get('history_size', 5)
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
            response.reason = '不支持的消息类型'
        else:
            self.chain.memory = await self._load_memory(
                conversation_id=conversation_id
            )
            response = TextResponseMessage()
            response.text = await self.chain.arun(message.text)

        return response
