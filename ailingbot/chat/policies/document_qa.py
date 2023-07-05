import copy
import tempfile

from langchain.chains import RetrievalQA
from langchain.chains.base import Chain
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms.loading import load_llm_from_config
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.vectorstores.base import VectorStoreRetriever

from ailingbot.chat.messages import (
    RequestMessage,
    ResponseMessage,
    TextRequestMessage,
    FallbackResponseMessage,
    TextResponseMessage,
    FileRequestMessage,
)
from ailingbot.chat.policy import ChatPolicy
from ailingbot.config import settings
from ailingbot.shared.errors import ChatPolicyError


class DocumentQAPolicy(ChatPolicy):
    """Question-Answering based on documents."""

    def __init__(
        self,
        *,
        debug: bool = False,
    ):
        super().__init__(
            debug=debug,
        )

        llm_config = copy.deepcopy(settings.policy.llm)
        self.llm = load_llm_from_config(llm_config)
        self.chains: dict[str, Chain] = {}
        self.chunk_size = settings.policy.get('chunk_size', 1000)
        self.chunk_overlap = settings.policy.get('chunk_overlap', 0)

    def _build_documents_index(
        self, *, content: bytes, file_type: str
    ) -> VectorStoreRetriever:
        """Load document and build index."""
        if file_type.lower() != 'pdf':
            raise ChatPolicyError(
                reason='目前只支持PDF文档',
                suggestion='请上传PDF文档',
            )

        with tempfile.NamedTemporaryFile(delete=True) as tf:
            tf.write(content)
            loader = PyPDFLoader(file_path=tf.name)
            documents = loader.load()

        text_splitter = CharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )
        texts = text_splitter.split_documents(documents)

        embeddings = OpenAIEmbeddings(
            openai_api_key=settings.policy.llm.openai_api_key,
        )
        docsearch = Chroma.from_documents(texts, embeddings)

        return docsearch.as_retriever()

    async def respond(
        self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        if isinstance(message, TextRequestMessage):
            if conversation_id not in self.chains:
                response = FallbackResponseMessage()
                response.reason = '还没有上传文档'
                response.suggestion = '请先上传文档'
            else:
                response = TextResponseMessage()
                response.text = await self.chains[conversation_id].arun(
                    message.text
                )
        elif isinstance(message, FileRequestMessage):
            self.chains[conversation_id] = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type='stuff',
                retriever=self._build_documents_index(
                    content=message.content, file_type=message.file_type
                ),
                return_source_documents=False,
                verbose=self.debug,
            )
            response = TextResponseMessage()
            response.text = f'我已完成学习，现在可以针对 {message.file_name} 进行提问了'
        else:
            response = FallbackResponseMessage()
            response.reason = '不支持的消息类型'

        return response
