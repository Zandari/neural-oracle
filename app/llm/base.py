from abc import ABC, abstractmethod

from ..models import Message, MessageCollection


class LLMApiClientException(Exception):
    ...


class LLMApiClient(ABC):
    def __init__(self, max_chars: int | None = None, system_prompt: str | None = None) -> None:
        self._max_chars = max_chars
        self._system_prompt = system_prompt

    @abstractmethod
    async def send_message(self, messages: list[Message] | MessageCollection) -> Message:
        ...

    def _trim_to_char_limit(self, messages: list[Message]) -> list[Message]:
        if self._max_chars is None:
            return messages

        result: list[Message] = []
        budget = self._max_chars

        for message in reversed(messages):
            length = len(message.content)
            if budget - length < 0 and result:
                break
            result.append(message)
            budget -= length

        result.reverse()
        return result