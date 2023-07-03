from __future__ import annotations

import abc
import enum
import typing

from pydantic import BaseModel


class MessageScope(str, enum.Enum):
    """The scope of message sender or receiver."""

    USER = 'user'
    GROUP = 'group'
    CUSTOMIZED_1 = 'customized_1'
    CUSTOMIZED_2 = 'customized_2'
    CUSTOMIZED_3 = 'customized_3'
    CUSTOMIZED_4 = 'customized_4'
    CUSTOMIZED_5 = 'customized_5'


class RequestMessage(BaseModel, abc.ABC):
    """Base class of request messages."""

    uuid: str = ''
    sender_id: str = ''
    scope: typing.Optional[MessageScope] = None
    meta: dict = {}
    echo: dict = {}


class TextRequestMessage(RequestMessage):
    """Plain text request message."""

    text: str = ''


class FileRequestMessage(RequestMessage):
    """File request message."""

    content: bytes
    file_type: str
    file_name: str


class ResponseMessage(BaseModel, abc.ABC):
    """Base class of response messages."""

    uuid: str = ''
    ack_uuid: str = ''
    receiver_id: typing.Union[str, list[str]] = ''
    scope: typing.Optional[MessageScope] = None
    meta: dict = {}
    echo: dict = {}

    def _downgrade(self) -> str:
        """Default downgrade method: use the JSON representation."""
        return self.json(ensure_ascii=False)

    def downgrade_to_text_message(self) -> TextResponseMessage:
        """When the channel does not support rendering this type of message, how to downgrade it to a text message."""
        return TextResponseMessage(
            uuid=self.uuid,
            ack_uuid=self.ack_uuid,
            receiver_id=self.receiver_id,
            scope=self.scope,
            meta=self.meta,
            echo=self.echo,
            text=self._downgrade(),
        )


class SilenceResponseMessage(ResponseMessage):
    """Response message that outputs nothing."""

    def _downgrade(self) -> str:
        return ''


class TextResponseMessage(ResponseMessage):
    """Plain text response message."""

    text: str = ''

    def _downgrade(self) -> str:
        return self.text


class FallbackResponseMessage(ResponseMessage):
    """Fallback response message.

    Send this message when error occurred.
    """

    reason: str = ''
    suggestion: str = ''

    def _downgrade(self) -> str:
        return f"""{self.reason}
{self.suggestion}"""
