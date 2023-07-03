from __future__ import annotations

import functools

from ailingbot.chat.messages import (
    ResponseMessage,
    TextResponseMessage,
    FallbackResponseMessage,
)


@functools.singledispatch
async def render(response: ResponseMessage) -> tuple[dict, str]:
    """Virtual function of all response message renders.

    Converts response message to Wechatwork content.

    :param response: Response message.
    :type response: ResponseMessage
    :return: Render result and Wechatwork message type.
    :rtype: typing.Tuple[dict, str]:
    """
    raise NotImplementedError


@render.register
async def _render(response: TextResponseMessage) -> tuple[dict, str]:
    """Renders text response message."""
    content = {
        'text': {
            'content': response.text,
        }
    }
    message_type = 'text'
    return content, message_type


@render.register
async def _render(response: FallbackResponseMessage) -> tuple[dict, str]:
    """Renders error fallback response message."""
    content = {
        'markdown': {
            'content': f"""<font color="warning">Error occurred</font>
Cause: {response.reason}
Suggestion: {response.suggestion}"""
        }
    }
    message_type = 'markdown'
    return content, message_type
