import datetime

import aiohttp

from ..models import Message, MessageCollection
from .base import LLMApiClient, LLMApiClientException


class OpenRouterLLMApiClient(LLMApiClient):
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o",
        max_chars: int | None = None,
        system_prompt: str | None = None,
    ) -> None:
        super().__init__(max_chars=max_chars, system_prompt=system_prompt)
        self._api_key = api_key
        self._model = model

    async def send_message(
        self,
        messages: list[Message] | MessageCollection,
        **kwargs,
    ) -> Message:
        msg_list = messages if not isinstance(messages, MessageCollection) else messages.content
        payload = {
            "model": self._model,
            "messages": self._construct_payload(self._trim_to_char_limit(msg_list)),
        }

        async with aiohttp.ClientSession(**kwargs) as session:
            async with session.post(
                self.BASE_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
                json=payload,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMApiClientException(error_text)

                result = await response.json()

                try:
                    model_text = result["choices"][0]["message"]["content"]
                except (KeyError, IndexError) as e:
                    raise LLMApiClientException(f"Unexpected response format: {result}") from e

                return Message(
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                    is_response=True,
                    content=model_text,
                    user_id=None,
                )

    def _construct_payload(self, messages: list[Message]) -> list[dict]:
        result = list()
        if self._system_prompt:
            result.append({
                "role": "system",
                "content": self._system_prompt,
            })
        for message in messages:
            result.append({
                "role": "assistant" if message.is_response else "user",
                "content": message.content,
            })

        return result