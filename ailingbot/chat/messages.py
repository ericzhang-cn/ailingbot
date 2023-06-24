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

    type: str
    content: typing.IO


class InputRequestMessage(RequestMessage):
    """Input request message."""

    value: typing.Any = None


class ResponseMessage(BaseModel, abc.ABC):
    """Base class of response messages."""

    uuid: str = ''
    ack_uuid: str = ''
    receiver_id: typing.Union[str, list[str]] = ''
    scope: typing.Optional[MessageScope] = None
    meta: dict = {}
    echo: dict = {}

    def _downgrade(self) -> str:
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


class ContentResponseMessage(ResponseMessage, abc.ABC):
    """Base class of response message that outputs content."""

    pass


class SilenceResponseMessage(ContentResponseMessage):
    """Response message that outputs nothing."""

    def _downgrade(self) -> str:
        return ''


class TextResponseMessage(ContentResponseMessage):
    """Plain text response message."""

    text: str = ''

    def _downgrade(self) -> str:
        return self.text


class TabularResponseMessage(ContentResponseMessage):
    """Tabular response message."""

    title: str = ''
    headers: list[str] = []
    data: list[list] = []


class FallbackResponseMessage(ContentResponseMessage):
    """Fallback response message.

    Send this message when error occurred.
    """

    reason: str = ''
    suggestion: str = ''

    def _downgrade(self) -> str:
        return f"""{self.reason}
{self.suggestion}"""


class FormResponseMessage(ResponseMessage, abc.ABC):
    """Base class of form response messages."""

    title: str = ''


class InputResponseMessage(FormResponseMessage):
    """Input prompt response message.

    Ask for user input.
    """

    required: bool = True
    visible: bool = True

    def _downgrade(self) -> str:
        return self.title


class Option(BaseModel):
    """Option for OptionsResponseMessage."""

    text: str = ''
    value: typing.Any = None


class OptionsResponseMessage(FormResponseMessage):
    """Options prompt response message.

    Give options for the user to make a choice.
    """

    options: list[Option] = []

    def _downgrade(self) -> str:
        nl = '\n'
        return f"""{self.title}
{nl.join([f'{x.text}[{str(x.value)}]' for x in self.options])}"""
