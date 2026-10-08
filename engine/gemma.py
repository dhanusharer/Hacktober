"""Ollama and Gemma Model Wrapper for CodeWalk.

Provides clean, robust functions to interact with a local Gemma model
hosted on an Ollama server.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Type, TypeVar
import requests
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
DEFAULT_GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma2:2b")
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("GEMMA_TIMEOUT", "90"))

T = TypeVar("T", bound=BaseModel)


class OllamaConnectionError(RuntimeError):
    """Raised when Ollama cannot be reached."""


class OllamaModelError(RuntimeError):
    """Raised when the specified model is missing or fails."""


class StructuredParsingError(ValueError):
    """Raised when model response cannot be parsed into the expected schema."""


def get_configured_host(host: Optional[str] = None) -> str:
    """Return the configured Ollama host URL without trailing slash."""
    return (host or DEFAULT_OLLAMA_HOST).rstrip("/")


def get_configured_model(model: Optional[str] = None) -> str:
    """Return the configured Gemma model name."""
    return model or DEFAULT_GEMMA_MODEL


def check_ollama_status(
    host: Optional[str] = None, model: Optional[str] = None
) -> Dict[str, Any]:
    """Check whether the Ollama server is running and the desired model is pulled.

    Returns a status dict:
    {
        "connected": bool,
        "host": str,
        "available_models": list[str],
        "target_model": str,
        "model_available": bool,
        "error": Optional[str]
    }
    """
    target_host = get_configured_host(host)
    target_model = get_configured_model(model)
    url = f"{target_host}/api/tags"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return {
                "connected": False,
                "host": target_host,
                "available_models": [],
                "target_model": target_model,
                "model_available": False,
                "error": f"Ollama returned HTTP status {response.status_code}",
            }

        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        # Match base name or exact name (e.g. 'gemma2:2b' or 'gemma2:2b-instruct-q4_0')
        target_base = target_model.split(":")[0]
        model_available = any(
            m == target_model or m.startswith(f"{target_model}:") or m.startswith(f"{target_base}:")
            for m in models
        )

        return {
            "connected": True,
            "host": target_host,
            "available_models": models,
            "target_model": target_model,
            "model_available": model_available,
            "error": None,
        }
    except requests.exceptions.ConnectionError:
        return {
            "connected": False,
            "host": target_host,
            "available_models": [],
            "target_model": target_model,
            "model_available": False,
            "error": f"Cannot connect to Ollama at {target_host}. Ensure Ollama is running (`ollama serve`).",
        }
    except Exception as exc:
        return {
            "connected": False,
            "host": target_host,
            "available_models": [],
            "target_model": target_model,
            "model_available": False,
            "error": str(exc),
        }


def generate_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    host: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    format_json: bool = False,
    temperature: float = 0.7,
) -> str:
    """Generate a text completion from the local Gemma model.

    Args:
        prompt: User/instruction prompt
        system_prompt: Optional system instruction
        model: Model name (defaults to configured model)
        host: Ollama host URL
        timeout: Network timeout in seconds
        format_json: If True, instructs Ollama to enforce valid JSON
        temperature: Sampling temperature

    Returns:
        The generated text response.
    """
    target_host = get_configured_host(host)
    target_model = get_configured_model(model)
    url = f"{target_host}/api/generate"

    payload: Dict[str, Any] = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    if system_prompt:
        payload["system"] = system_prompt

    if format_json:
        payload["format"] = "json"

    try:
        response = requests.post(url, json=payload, timeout=timeout)
    except requests.exceptions.ConnectionError as exc:
        raise OllamaConnectionError(
            f"Failed to connect to Ollama at {target_host}. "
            "Please ensure Ollama is installed and running (`ollama serve`)."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise TimeoutError(
            f"Gemma model generation timed out after {timeout} seconds on host {target_host}."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Error querying Ollama API: {exc}") from exc

    if response.status_code == 404:
        raise OllamaModelError(
            f"Model '{target_model}' not found in Ollama. Run: ollama pull {target_model}"
        )
    elif response.status_code != 200:
        raise RuntimeError(
            f"Ollama returned HTTP {response.status_code}: {response.text}"
        )

    data = response.json()
    return data.get("response", "").strip()


def extract_json_from_text(raw_text: str) -> str:
    """Clean model output to extract the first balanced JSON substring if needed."""
    text = raw_text.strip()
    # Remove markdown fences like ```json ... ```
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # If it directly looks like JSON object or list, return it
    if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
        return text

    # Try finding the first {...} block
    match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()

    return text


def generate_structured_response(
    prompt: str,
    response_model: Type[T],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    host: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = 1,
    temperature: float = 0.5,
) -> T:
    """Generate and validate a response conforming to a Pydantic model.

    Retries once on malformed JSON or validation failure.
    """
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            current_prompt = prompt
            if attempt > 0:
                # Add extra emphasis on JSON correctness for retry
                current_prompt = (
                    f"{prompt}\n\nIMPORTANT: Your previous response was invalid. "
                    f"Return ONLY raw valid JSON conforming to the requested schema. Do not add markdown."
                )

            raw_text = generate_response(
                prompt=current_prompt,
                system_prompt=system_prompt,
                model=model,
                host=host,
                timeout=timeout,
                format_json=True,
                temperature=temperature,
            )

            cleaned_json = extract_json_from_text(raw_text)
            parsed_dict = json.loads(cleaned_json)
            validated = response_model.model_validate(parsed_dict)
            return validated

        except (json.JSONDecodeError, ValidationError) as err:
            last_error = err
            logger.warning(
                "Attempt %d/%d to parse structured response failed: %s",
                attempt + 1,
                max_retries + 1,
                err,
            )
            if attempt == max_retries:
                raise StructuredParsingError(
                    f"Failed to generate valid structured response for {response_model.__name__}: {err}"
                ) from err
        except (OllamaConnectionError, OllamaModelError, TimeoutError):
            # Network/service errors should propagate directly without retrying malformed parsing
            raise

    raise StructuredParsingError(f"Generation failed: {last_error}")
