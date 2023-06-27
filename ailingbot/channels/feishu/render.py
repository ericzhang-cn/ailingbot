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
        'text': response.text,
    }
    message_type = 'text'
    return content, message_type


@render.register
async def _render(response: FallbackResponseMessage) -> tuple[dict, str]:
    """Renders text response message."""
    content = {
        'config': {'wide_screen_mode': True},
        'elements': [
            {
                'tag': 'markdown',
                'content': f'**原因**：{response.reason}\n**建议**：{response.suggestion}',
            }
        ],
        'header': {
            'template': 'orange',
            'title': {'content': '🤔出了一些问题', 'tag': 'plain_text'},
        },
    }
    message_type = 'interactive'
    return content, message_type
