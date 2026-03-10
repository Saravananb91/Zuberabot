"""OpenAI provider implementation for multi-provider support."""

import json
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageToolCall

from zuberabot.providers.base import LLMProvider, LLMResponse, ToolCallRequest


class OpenAIProvider(LLMProvider):
    """
    LLM provider using the native OpenAI client.

    Supports OpenAI natively, as well as OpenAI-compatible endpoints like 
    Ollama, Groq, OpenRouter, Anthropic (via OpenRouter), Gemini (via OpenRouter),
    and Zhipu through a unified interface.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        default_model: str = "ollama/qwen2.5:3b",
    ):
        super().__init__(api_key, api_base)
        self.default_model = default_model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send a chat completion request via the OpenAI client.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions in OpenAI format.
            model: Model identifier (e.g., 'groq/llama-3.1-8b-instant').
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            LLMResponse with content and/or tool calls.
        """
        model = model or self.default_model

        # Determine routing logic based on the *actual* model prefix
        is_ollama = model.startswith("ollama/")
        is_groq = model.startswith("groq/")
        is_openrouter = (
            (self.api_key and self.api_key.startswith("sk-or-")) or
            (self.api_base and "openrouter" in self.api_base) or
            model.startswith("openrouter/")
        ) and not is_groq and not is_ollama

        # 1. Strip prefixes and set URL/API keys per provider
        req_model = model
        req_base_url = self.api_base
        req_api_key = self.api_key

        if is_ollama:
            req_model = model.removeprefix("ollama/")
            req_base_url = f"{(self.api_base or 'http://localhost:11434').rstrip('/')}/v1"
            req_api_key = "ollama"  # placeholder key required by client validation
        elif is_groq:
            # Note: Groq natively supports the OpenAI python client with a custom base URL
            req_model = model.removeprefix("groq/")
            req_base_url = "https://api.groq.com/openai/v1"
            # api_key should be set by user config
        elif is_openrouter:
            # Note: OpenRouter natively supports the OpenAI python client with a custom base URL
            req_model = model.removeprefix("openrouter/")
            req_base_url = "https://openrouter.ai/api/v1"
            # api_key should be set by user config

        # Instantiate a fresh, isolated client for this specific request
        # This guarantees zero cross-contamination of globals/envs between calls
        client = AsyncOpenAI(
            base_url=req_base_url,
            api_key=req_api_key or "sk-no-key-required",
            timeout=180.0,
            max_retries=0,
        )

        kwargs: dict[str, Any] = {
            "model": req_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await client.chat.completions.create(**kwargs)
            return self._parse_response(response)
        except Exception as e:
            provider_name = "Ollama" if is_ollama else ("Groq" if is_groq else ("OpenRouter" if is_openrouter else "LLM"))
            return LLMResponse(
                content=f"Error calling {provider_name}: {str(e)}",
                finish_reason="error",
            )
        finally:
            await client.close()

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse OpenAI response into our standard format."""
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                # OpenAI returns tool call models, not objects with raw string dicts
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}

                tool_calls.append(ToolCallRequest(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                ))

        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
        )

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.default_model
