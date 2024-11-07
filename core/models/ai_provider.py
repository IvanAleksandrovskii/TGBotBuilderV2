# core/models/ai_provider.py

from typing import Dict, Any, Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer

from .base import Base
from core import log


class AIProvider(Base):
    name: Mapped[str] = mapped_column(String, nullable=False)
    api_url: Mapped[str] = mapped_column(String, nullable=False)
    api_key: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)

    # Working only with OpenAI-like services
    def get_request_payload(self, message: str) -> Dict[str, Any]:
        """
        Get request payload for the specified AI provider

        :param message: The message to send to the AI provider.
        :return: The request payload as a dictionary.
        :raises ValueError: If the AI provider is not supported.
        """
        # if self.name == "OpenAI" or self.name == "AIMLapi":
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": message}]
        }
        # else:
        #     raise ValueError(f"Unsupported AI provider: {self.name}")

    def get_headers(self) -> Dict[str, str]:
        """
        Construct the headers for the AI provider's API request.

        :return: A dictionary containing the authorization header.
        """
        return {"Authorization": f"Bearer {self.api_key}"}

    # For both OpenAI and AIMLapi is the same
    async def parse_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        Parse the response from the AI provider.

        :param response_data: The response data as a dictionary.
        :return: The parsed response content as a string, or None if parsing fails.
        """
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            log.error(f"Error parsing response from {self.name}: {response_data}")
            return None


    def __repr__(self) -> str:
        return f"<AIProvider(name='{self.name}', priority={self.priority})>"
    
    def __str__(self) -> str:
        return f"{self.name}, priority: {self.priority}, model: {self.model}, last updated: {self.updated_at}"
