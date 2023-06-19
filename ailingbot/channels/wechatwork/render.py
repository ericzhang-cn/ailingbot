from __future__ import annotations

import functools

from ailingbot.chat.messages import (
    ResponseMessage,
    TextResponseMessage,
    FallbackResponseMessage,
    InputResponseMessage,
    OptionsResponseMessage,
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


@render.register
async def _render(response: InputResponseMessage) -> tuple[dict, str]:
    """Renders input prompt response message."""
    content = {
        'text': {
            'content': response.title,
        }
    }
    message_type = 'text'
    return content, message_type


@render.register
async def _render(response: OptionsResponseMessage) -> tuple[dict, str]:
    """Renders input prompt response message."""
    content = {
        'template_card': {
            'card_type': 'vote_interaction',
            'main_title': {
                'title': response.title,
            },
            'task_id': response.uuid,
            'checkbox': {
                'question_key': response.uuid,
                'option_list': [
                    {
                        'id': x.value,
                        'text': x.text,
                        'is_checked': False,
                    }
                    for x in response.options
                ],
                'mode': 0,
            },
        }
    }
    message_type = 'template_card'
    return content, message_type
