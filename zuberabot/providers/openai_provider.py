"""OpenAI provider implementation for multi-provider support."""

import json
import time
import asyncio
from typing import Any

from loguru import logger
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, APIConnectionError
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
        Send a chat completion request via the OpenAI client with robust retries
        and duration logging.
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
            req_model = model.removeprefix("groq/")
            req_base_url = "https://api.groq.com/openai/v1"
        elif is_openrouter:
            req_model = model.removeprefix("openrouter/")
            req_base_url = "https://openrouter.ai/api/v1"

        provider_name = "Ollama" if is_ollama else ("Groq" if is_groq else ("OpenRouter" if is_openrouter else "OpenAI"))

        kwargs: dict[str, Any] = {
            "model": req_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries):
            # Instantiate a fresh, isolated client for this specific request
            client = AsyncOpenAI(
                base_url=req_base_url,
                api_key=req_api_key or "sk-no-key-required",
                timeout=180.0,
                max_retries=0, # We handle retries manually to log them
            )

            start_time = time.time()
            try:
                logger.debug(f"Calling {provider_name} (model: {req_model}) - Attempt {attempt + 1}/{max_retries}")
                response = await client.chat.completions.create(**kwargs)
                
                duration = time.time() - start_time
                parsed_resp = self._parse_response(response)
                
                # Log metrics
                tokens = parsed_resp.usage.get("total_tokens", 0) if getattr(parsed_resp, "usage", None) else 0
                logger.info(f"✅ {provider_name} request completed in {duration:.2f}s | Tokens used: {tokens}")
                
                return parsed_resp

            except (RateLimitError, APITimeoutError, APIConnectionError) as e:
                duration = time.time() - start_time
                logger.warning(f"⚠️ Transient error calling {provider_name} after {duration:.2f}s (Attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Max retries reached for {provider_name}. Last error: {str(e)}")
                    return LLMResponse(
                        content=f"Error calling {provider_name} (Retries exhausted): {str(e)}",
                        finish_reason="error",
                    )
            except APIError as e:
                # Other API errors (e.g., Auth, Invalid Request) aren't typically retryable
                duration = time.time() - start_time
                logger.error(f"❌ API Error calling {provider_name} after {duration:.2f}s: {str(e)}")
                return LLMResponse(
                    content=f"API Error calling {provider_name}: {str(e)}",
                    finish_reason="error",
                )
            except Exception as e:
                duration = time.time() - start_time
                logger.exception(f"❌ Unexpected error calling {provider_name} after {duration:.2f}s: {str(e)}")
                return LLMResponse(
                    content=f"Error calling {provider_name}: {str(e)}",
                    finish_reason="error",
                )
            finally:
                await client.close()
                
        # Fallback (should mathematically not be reached unless max_retries=0)
        return LLMResponse(
            content=f"Error calling {provider_name}: Unhandled exception in retry loop",
            finish_reason="error",
        )

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse OpenAI response into our standard format with fallback robustness."""
        if not response.choices:
            logger.error("No choices found in OpenAI response")
            return LLMResponse(content="", finish_reason="error")
            
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if getattr(message, "tool_calls", None):
            for tc in message.tool_calls:
                try:
                    args = tc.function.arguments
                    if isinstance(args, str):
                        try:
                            # Handle providers that may return poorly formatted JSON or markdown blocks
                            cleaned_args = args.strip()
                            if cleaned_args.startswith("```json"):
                                cleaned_args = cleaned_args[7:]
                            if cleaned_args.endswith("```"):
                                cleaned_args = cleaned_args[:-3]
                            
                            args = json.loads(cleaned_args.strip())
                        except json.JSONDecodeError as decode_error:
                            logger.warning(f"Failed to parse tool call arguments as JSON. Raw string: {args}. Error: {decode_error}")
                            args = {"raw": args}
                    elif not isinstance(args, dict):
                        logger.warning(f"Unexpected tool call argument type: {type(args)}")
                        args = {"raw": str(args)}

                    tool_calls.append(ToolCallRequest(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    ))
                except Exception as e:
                    logger.error(f"Error parsing tool call {tc}: {e}")
                    # Skip parsing this specific broken tool call but process the rest

        usage = {}
        if getattr(response, "usage", None):
            usage = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
        )

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.default_model
