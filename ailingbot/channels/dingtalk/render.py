import functools
import json

from ailingbot.chat.messages import (
    ResponseMessage,
    TextResponseMessage,
    FallbackResponseMessage,
)


@functools.singledispatch
async def render(response: ResponseMessage) -> tuple[dict, str]:
    """Virtual function of all response message renders.

    Converts response message to Feishu content.

    :param response: Response message.
    :type response: ResponseMessage
    :return: Render result and Feishu message type.
    :rtype: typing.Tuple[dict, str]:
    """
    raise NotImplementedError


@render.register
async def _render(response: TextResponseMessage) -> tuple[dict, str]:
    """Renders text response message."""
    content = {
        'content': response.text,
    }
    message_type = 'sampleText'
    return content, message_type
