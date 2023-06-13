from __future__ import annotations

from langchain.chat_models.base import BaseChatModel
from langchain.llms.base import LLM

from ailingbot.shared.misc import get_class_dynamically


def get_llm(name: str, **kwargs) -> LLM:
    """Gets LangChain LLM instance.

    :param name: Built-in LLM name or full path of LLM class.
    :type name: str
    :return: LangChain LLM instance.
    :rtype: BaseChatModel
    """
    if name.lower() == 'openai':
        from langchain.llms import OpenAI

        instance = OpenAI(**kwargs)
    elif name.lower() == 'azure':
        from langchain.llms import AzureOpenAI

        instance = AzureOpenAI(**kwargs)
    else:
        instance = get_class_dynamically(name)(**kwargs)

    return instance
