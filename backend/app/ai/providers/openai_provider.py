"""OpenAI Responses API adapter — official SDK only."""

from __future__ import annotations

import json
import time
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)

from app.ai.errors import (
    ProviderConfigurationError,
    ProviderRequestError,
    StructuredOutputError,
)
from app.ai.providers.base import AIProvider, GenerationRequest, GenerationResult

# Models known to reject temperature / prefer reasoning params (extensible via metadata).
_NO_TEMPERATURE_PREFIXES = ("o1", "o3", "o4", "gpt-5")


class OpenAIProvider(AIProvider):
    code = "openai"
    display_name = "OpenAI"

    def validate_credentials(self, api_key: str | None, base_url: str | None) -> None:
        if not api_key or not api_key.strip():
            raise ProviderConfigurationError("OpenAI API key is not configured.")
        if len(api_key.strip()) < 8:
            raise ProviderConfigurationError("OpenAI API key appears invalid.")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.validate_credentials(request.api_key, request.base_url)
        assert request.api_key is not None

        client_kwargs: dict[str, Any] = {"api_key": request.api_key}
        if request.base_url:
            client_kwargs["base_url"] = request.base_url
        client = OpenAI(**client_kwargs)

        params = self._build_request_params(request)
        started = time.perf_counter()
        try:
            response = client.responses.create(**params)
        except AuthenticationError as exc:
            raise ProviderConfigurationError(
                "OpenAI rejected the API credentials.",
                retryable=False,
            ) from exc
        except RateLimitError as exc:
            raise ProviderRequestError(
                "OpenAI rate limit reached. Try again shortly.",
                retryable=True,
            ) from exc
        except APITimeoutError as exc:
            raise ProviderRequestError(
                "OpenAI request timed out.",
                retryable=True,
            ) from exc
        except APIConnectionError as exc:
            raise ProviderRequestError(
                "Unable to reach OpenAI. Check network connectivity.",
                retryable=True,
            ) from exc
        except BadRequestError as exc:
            raise ProviderRequestError(
                self._safe_provider_message(
                    exc, fallback="OpenAI rejected the request."
                ),
                retryable=False,
            ) from exc
        except APIStatusError as exc:
            retryable = exc.status_code in {408, 409, 429, 500, 502, 503, 504}
            raise ProviderRequestError(
                self._safe_provider_message(exc, fallback="OpenAI request failed."),
                retryable=retryable,
            ) from exc
        finally:
            latency_ms = int((time.perf_counter() - started) * 1000)

        return self._normalize_response(
            response, request=request, latency_ms=latency_ms
        )

    def _supports_temperature(self, request: GenerationRequest) -> bool:
        if not request.supports_temperature:
            return False
        code = request.model_code.lower()
        return not any(code.startswith(prefix) for prefix in _NO_TEMPERATURE_PREFIXES)

    def _build_request_params(self, request: GenerationRequest) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": request.model_code,
            "instructions": request.system_prompt,
            "input": request.user_prompt,
        }
        if request.max_tokens is not None:
            params["max_output_tokens"] = request.max_tokens
        if request.temperature is not None and self._supports_temperature(request):
            params["temperature"] = request.temperature
        if request.seed is not None:
            # Seed is best-effort; omit if unsupported by Responses for some models.
            params["seed"] = request.seed
        if request.reasoning_effort:
            params["reasoning"] = {"effort": request.reasoning_effort}

        if request.response_json_schema and request.supports_structured_output:
            params["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": request.response_schema_name
                    or "curionex_structured_output",
                    "strict": True,
                    "schema": request.response_json_schema,
                }
            }
        elif request.response_json_schema:
            # Fallback: ask for JSON object without strict schema enforcement.
            params["text"] = {"format": {"type": "json_object"}}
            params["instructions"] = (
                f"{request.system_prompt}\n\n"
                "Return ONLY valid JSON matching the required schema. "
                "Do not wrap the JSON in markdown."
            )

        return params

    def _normalize_response(
        self,
        response: Any,
        *,
        request: GenerationRequest,
        latency_ms: int,
    ) -> GenerationResult:
        output_text = self._extract_output_text(response)
        structured: dict[str, Any] | None = None
        if request.response_json_schema:
            structured = self._parse_structured(output_text)

        usage = getattr(response, "usage", None)
        tokens_input = getattr(usage, "input_tokens", None) if usage else None
        tokens_output = getattr(usage, "output_tokens", None) if usage else None
        tokens_total = getattr(usage, "total_tokens", None) if usage else None
        if (
            tokens_total is None
            and tokens_input is not None
            and tokens_output is not None
        ):
            tokens_total = tokens_input + tokens_output

        status = getattr(response, "status", None)
        request_id = getattr(response, "id", None)
        model_id = getattr(response, "model", None) or request.model_code

        metadata: dict[str, Any] = {"api": "responses"}
        if status is not None:
            metadata["status"] = str(status)

        return GenerationResult(
            output_text=output_text,
            structured_output=structured,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
            latency_ms=latency_ms,
            provider_request_id=str(request_id) if request_id else None,
            model_identifier=str(model_id) if model_id else request.model_code,
            raw_status=str(status) if status is not None else None,
            retryable=False,
            provider_metadata=metadata,
        )

    def _extract_output_text(self, response: Any) -> str:
        text = getattr(response, "output_text", None)
        if isinstance(text, str) and text.strip():
            return text
        # Walk output items for message content.
        chunks: list[str] = []
        for item in getattr(response, "output", None) or []:
            if getattr(item, "type", None) != "message":
                continue
            for content in getattr(item, "content", None) or []:
                if getattr(content, "type", None) in {"output_text", "text"}:
                    value = getattr(content, "text", None)
                    if value:
                        chunks.append(str(value))
        joined = "".join(chunks).strip()
        if not joined:
            raise StructuredOutputError("OpenAI returned empty output text.")
        return joined

    def _parse_structured(self, output_text: str) -> dict[str, Any]:
        cleaned = output_text.strip()
        if cleaned.startswith("```"):
            # Strip accidental markdown fences from JSON-object fallback.
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise StructuredOutputError(
                "OpenAI returned malformed JSON structured output."
            ) from exc
        if not isinstance(payload, dict):
            raise StructuredOutputError("Structured output must be a JSON object.")
        return payload

    @staticmethod
    def _safe_provider_message(exc: Exception, *, fallback: str) -> str:
        message = str(exc).strip()
        # Avoid leaking request payloads / keys from verbose SDK messages.
        if not message or len(message) > 300 or "sk-" in message.lower():
            return fallback
        return message or fallback
