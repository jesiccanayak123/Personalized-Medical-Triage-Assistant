"""OpenAI client wrapper with retry logic and structured outputs."""

import json
from typing import Any, Dict, List, Optional, Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config.settings import settings
from config.logging import logger


T = TypeVar("T", bound=BaseModel)


class OpenAIClient:
    """OpenAI API client wrapper with retry logic and structured outputs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (default from settings)
            model: Chat model name (default from settings)
            embedding_model: Embedding model name (default from settings)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.embedding_model = embedding_model or settings.openai_embedding_model
        self.timeout = timeout or settings.openai_timeout
        self.max_retries = max_retries or settings.openai_max_retries

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=self.timeout,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embedding vectors for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: Optional[str] = None,
    ) -> str:
        """Get chat completion.
        
        Args:
            messages: List of message dicts with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            model: Override model name
            
        Returns:
            Assistant message content
        """
        response = await self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        model: Optional[str] = None,
    ) -> T:
        """Get structured output validated against Pydantic model.
        
        Uses OpenAI's JSON mode with function calling for strict validation.
        
        Args:
            messages: List of message dicts
            response_model: Pydantic model class for response
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            model: Override model name
            
        Returns:
            Validated Pydantic model instance
        """
        # Build JSON schema from Pydantic model
        schema = response_model.model_json_schema()
        
        # Use function calling for structured output
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "structured_response",
                    "description": "Return structured response",
                    "parameters": schema,
                },
            }
        ]

        response = await self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "structured_response"}},
        )

        # Extract and validate the response
        tool_call = response.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        
        return response_model.model_validate(arguments)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    async def json_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get JSON completion using response_format.
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            model: Override model name
            
        Returns:
            Parsed JSON dict
        """
        response = await self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        return json.loads(content)

