import datetime

import aiohttp

from ..models import Message, MessageCollection
from .base import LLMApiClient, LLMApiClientException


class GeminiLLMApiClient(LLMApiClient):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-pro",
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
        endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"

        msg_list = messages if not isinstance(messages, MessageCollection) else messages.content
        payload = self._construct_payload(self._trim_to_char_limit(msg_list))

        async with aiohttp.ClientSession(**kwargs) as session:
            async with session.post(endpoint_url, headers={"Content-Type": "application/json"}, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMApiClientException(error_text)

                result = await response.json()

                try:
                    model_text = result["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError) as e:
                    raise LLMApiClientException(f"Unexpected response format: {result}") from e

                return Message(
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                    is_response=True,
                    content=model_text,
                )

    def _construct_payload(self, messages: list[Message]) -> list[dict]:
        result = list()
        if self._system_prompt:
            result.append({
                "role": "user",
                "parts": [{"text": self._system_prompt}],
            })
        for message in messages:
            result.append({
                "role": "model" if message.is_response else "user",
                "parts": [{"text": message.content}],
            })

        return result