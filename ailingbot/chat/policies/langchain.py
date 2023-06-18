import uuid

from langchain import ConversationChain
from langchain.chains.base import Chain
from langchain.chains.loading import load_chain_from_config
from langchain.llms.loading import load_llm_from_config
from langchain.memory import ConversationBufferMemory

from ailingbot.chat.messages import (
    RequestMessage,
    ResponseMessage,
    TextRequestMessage,
    TextResponseMessage,
    FallbackResponseMessage,
)
from ailingbot.chat.policy import ChatPolicy


class LCChainChatPolicy(ChatPolicy):
    """Load LangChain chain and use the chain as chat policy"""

    def __init__(
        self,
        *,
        debug: bool = False,
        lc_chain_config: dict,
    ):
        super(LCChainChatPolicy, self).__init__(debug=debug)

        self.lc_chain_config = lc_chain_config

        self.chain: dict[str, Chain] = {}

    async def _load_chain(self) -> Chain:
        if self.debug:
            self.lc_chain_config['verbose'] = True
        return load_chain_from_config(self.lc_chain_config)

    async def respond(
        self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        if not isinstance(message, TextRequestMessage):
            response = FallbackResponseMessage()
            response.reason = 'LCChainChatPolicy can only handle messages of type TextRequestMessage.'
        else:
            if conversation_id not in self.chain:
                self.chain[conversation_id] = await self._load_chain()
            r = await self.chain[conversation_id].arun(message.text)
            response = TextResponseMessage()
            response.text = r
        response.uuid = str(uuid.uuid4())
        response.ack_uuid = message.uuid
        response.receiver_id = message.sender_id
        response.scope = message.scope
        response.echo = message.echo

        return response


class LCConversationChain(LCChainChatPolicy):
    def __init__(
        self,
        *,
        debug: bool = False,
        lc_chain_config: dict,
    ):
        super(LCConversationChain, self).__init__(
            debug=debug, lc_chain_config=lc_chain_config
        )

    async def _load_chain(self) -> Chain:
        if self.debug:
            self.lc_chain_config['verbose'] = True
        llm = load_llm_from_config(self.lc_chain_config.get('llm', {}))
        return ConversationChain(llm=llm, memory=ConversationBufferMemory())
