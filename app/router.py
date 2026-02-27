import datetime
from fastapi import APIRouter, Depends
from .dependencies import (
    user_dependency,
    repository_dependency,
    llm_client_dependency,
)
from .models import (
    Message,
    MessageCollection,
    User,
)
from .repository import Repository
from .llm import LLMApiClient


router = APIRouter()


@router.get("/me", response_model=User)
async def get_current_user(
    user: User = Depends(user_dependency),
) -> User:
    user.hashed_access_token = None

    return user


@router.post("/chat", response_model=Message)
async def answer_message(
    message: Message,
    user: User = Depends(user_dependency),
    repository: "Repository" = Depends(repository_dependency),
    llm_client: "LLMApiClient" = Depends(llm_client_dependency)
) -> Message:

    message.created_at = datetime.datetime.now(datetime.timezone.utc)
    message.user_id = user.id

    is_added = await repository.put_message(message)
    assert is_added, "Incoming message wasn't added to database"

    message_history: list[Message] = await repository.get_messages_by_user_id(user_id=user.id)
    llm_response: Message = await llm_client.send_message(message_history)
    llm_response.user_id = user.id  # terrible
    if llm_response.created_at is None:
        llm_response.created_at = datetime.datetime.now(datetime.timezone.utc)

    is_added = await repository.put_message(llm_response)
    assert is_added, "LLM response message wasn't added to database"

    return llm_response

@router.get("/chat", response_model=MessageCollection)
async def get_chat_history(
    user: User = Depends(user_dependency),
    repository: "Repository" = Depends(repository_dependency),
) -> MessageCollection:
    message_history: list[Message] = await repository.get_messages_by_user_id(user_id=user.id)

    return MessageCollection(content=message_history)
