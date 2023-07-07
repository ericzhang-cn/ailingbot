import uuid

import aiohttp
from aiohttp import ClientResponseError, ClientError
from fastapi import FastAPI, HTTPException
from starlette import status

from ailingbot.chat.chatbot import ChatBot
from ailingbot.chat.messages import (
    MessageScope,
    TextRequestMessage,
    TextResponseMessage,
    FileRequestMessage,
    FallbackResponseMessage,
)
from ailingbot.endpoint.model import (
    RequestMessageType,
    ResponseMessageType,
    ChatRequest,
    ChatResponse,
)

bot = ChatBot()
app = FastAPI(title='AilingBot')


@app.on_event('startup')
async def startup() -> None:
    await bot.initialize()


@app.on_event('shutdown')
async def shutdown() -> None:
    await bot.finalize()


@app.post(
    '/chat/',
    status_code=status.HTTP_200_OK,
    response_model=ChatResponse,
    tags=['Chat'],
)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        req_type = RequestMessageType(request.type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Request message type {request.type} is not supported.',
        )

    _uuid = request.uuid or str(uuid.uuid4())
    conversation_id = request.uuid or 'default_conversation'
    sender_id = request.sender_id or 'anonymous'
    try:
        scope = MessageScope(request.scope.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Request message scope {request.scope} is not supported.',
        )
    meta = request.meta or {}
    echo = request.echo or {}

    if req_type == RequestMessageType.TEXT:
        if not request.text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'Field text is required.',
            )
        req = TextRequestMessage(
            uuid=_uuid,
            sender_id=sender_id,
            scope=scope,
            meta=meta,
            echo=echo,
            text=request.text,
        )
    elif req_type == RequestMessageType.FILE:
        if not request.file_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'Field file_type is required.',
            )
        if not request.file_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'Field file_name is required.',
            )
        if not request.file_url:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'Field file_url is required.',
            )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    request.file_url,
                ) as r:
                    if not r.ok:
                        r.raise_for_status()
                    file_content = await r.content.read()
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        req = FileRequestMessage(
            uuid=_uuid,
            sender_id=sender_id,
            scope=scope,
            meta=meta,
            echo=echo,
            file_type=request.file_type,
            file_name=request.file_name,
            content=file_content,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Request message type {request.type} is not supported.',
        )

    res = await bot.chat(conversation_id=conversation_id, message=req)
    response = ChatResponse(
        conversation_id=conversation_id,
        uuid=res.uuid,
        ack_uuid=res.ack_uuid,
        receiver_id=res.receiver_id,
        scope=str(res.scope.value),
        meta=res.meta,
        echo=res.echo,
    )
    if isinstance(res, TextResponseMessage):
        response.type = ResponseMessageType.TEXT.value
        response.text = res.text
    elif isinstance(res, FallbackResponseMessage):
        response.type = ResponseMessageType.FALLBACK.value
        response.reason = res.reason
        response.suggestion = res.suggestion
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Response message type is not supported.',
        )

    return response
