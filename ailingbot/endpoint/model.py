import enum
import typing

from pydantic import BaseModel


class RequestMessageType(enum.Enum):
    TEXT = 'text'
    FILE = 'file'


class ResponseMessageType(enum.Enum):
    TEXT = 'text'
    FALLBACK = 'fallback'


class ChatRequest(BaseModel):
    type: str = 'text'
    conversation_id: str = ''
    uuid: str = ''
    sender_id: str = ''
    scope: str = 'user'
    meta: dict = {}
    echo: dict = {}
    text: typing.Optional[str] = None
    file_type: typing.Optional[str] = None
    file_name: typing.Optional[str] = None
    file_url: typing.Optional[str] = None


class ChatResponse(BaseModel):
    type: str = 'text'
    conversation_id: str = ''
    uuid: str = ''
    ack_uuid: str = ''
    receiver_id: str = ''
    scope: str = 'user'
    meta: dict = {}
    echo: dict = {}
    text: typing.Optional[str] = None
    reason: typing.Optional[str] = None
    suggestion: typing.Optional[str] = None
