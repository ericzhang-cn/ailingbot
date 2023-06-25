from __future__ import annotations

import abc

from ailingbot.chat.messages import RequestMessage, ResponseMessage
from ailingbot.shared.abc import AbstractAsyncComponent
from ailingbot.shared.misc import get_class_dynamically


class ChatPolicy(AbstractAsyncComponent, abc.ABC):
    """Base class of chat policies."""

    def __init__(self, *, debug: bool = False):
        super(ChatPolicy, self).__init__()

        self.debug = debug

    @abc.abstractmethod
    async def respond(
        self, *, conversation_id: str, message: RequestMessage
    ) -> ResponseMessage:
        """Responding to user inputs.

        :param conversation_id:
        :type conversation_id:
        :param message: Request message.
        :type message: RequestMessage
        """
        raise NotImplementedError

    @staticmethod
    def get_policy(name: str, *, debug: bool = False) -> ChatPolicy:
        """Gets policy instance.

        :param name: Built-in policy name or full path of policy class.
        :type name: str
        :param debug:
        :type debug:
        :return: Policy instance.
        :rtype: ChatPolicy
        """
        if name.lower() == 'lc_conversation':
            from ailingbot.chat.policies.langchain import (
                LCConversationChatPolicy,
            )

            instance = LCConversationChatPolicy(debug=debug)
        elif name.lower() == 'lc_document_qa':
            from ailingbot.chat.policies.langchain import (
                LCDocumentQAPolicy,
            )

            instance = LCDocumentQAPolicy(debug=debug)
        else:
            instance = get_class_dynamically(name)(debug=debug)

        return instance
