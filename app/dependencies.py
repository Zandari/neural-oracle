import typing
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import Config
from .repository import SQLiteRepository, Repository
from .models import User
from .llm import OpenRouterLLMApiClient, LLMApiClient


_security = HTTPBearer()


async def repository_dependency() -> typing.AsyncGenerator[Repository]:
    async with SQLiteRepository.from_uri(Config.SQLITE_URI) as repository:
        yield repository


async def user_dependency(
    auth_credentials: HTTPAuthorizationCredentials = Depends(_security),
    repository: Repository = Depends(repository_dependency),
) -> User:
    user = await repository.get_user_by_access_key(auth_credentials.credentials)

    if user is None:
        raise HTTPException(status_code=403, detail="Incorrect access key")

    return user


async def llm_client_dependency() -> LLMApiClient:
    return OpenRouterLLMApiClient(
        api_key=Config.OPENROUTER_API_KEY,
        model=Config.OPENROUTER_MODEL,
        max_chars=Config.CONTEXT_WINDOW_MAX_CHARS,
        system_prompt=Config.SYSTEM_PROMPT,
    )
