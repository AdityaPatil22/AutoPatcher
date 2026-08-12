"""LLM integration layer: call providers, parse responses, and sanitize code output."""

import json
import re
from collections.abc import Callable

import app.config as config


def _scrub_key(text: str) -> str:
    """Remove the API key from any string to prevent accidental leakage."""
    if config.API_KEY and config.API_KEY in text:
        text = text.replace(config.API_KEY, "[REDACTED]")
    return re.sub(r"AIza[0-9A-Za-z_-]{35}", "[REDACTED]", text)


_PROVIDER_DISPATCH: dict[str, Callable] = {}


def call_llm(messages: list[dict]) -> dict:
    """Call the configured LLM provider and return parsed JSON response."""
    provider = config.LLM_PROVIDER
    handler = _PROVIDER_DISPATCH.get(provider)
    if handler is None:
        raise RuntimeError(f"Unknown LLM provider: {provider}")

    try:
        raw = handler(messages)
    except Exception as exc:
        raise RuntimeError(_scrub_key(str(exc))) from None

    return _parse_response(raw)


# ---------------------------------------------------------------------------
# Provider: Gemini (Google genai SDK)
# ---------------------------------------------------------------------------

def _call_gemini(messages: list[dict]) -> str:
    """Send messages to the Google Gemini API using the google-genai SDK with thinking and search."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.API_KEY)
    model = config.LLM_MODEL

    system_parts = []
    contents = []
    for msg in messages:
        if msg["role"] == "system":
            system_parts.append(msg["content"])
        else:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

    THINKING_MODELS = {"gemini-3-flash-preview", "gemini-2.5-pro-preview-05-06"}

    config_kwargs = {
        "system_instruction": "\n\n".join(system_parts) if system_parts else None,
        "temperature": 0.2,
        "tools": [types.Tool(google_search=types.GoogleSearch())],
    }
    if model in THINKING_MODELS:
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH")

    generate_config = types.GenerateContentConfig(**config_kwargs)

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_config,
    )
    return response.text


# ---------------------------------------------------------------------------
# Provider: OpenAI (standard OpenAI API)
# ---------------------------------------------------------------------------

def _call_openai(messages: list[dict]) -> str:
    """Send messages to the OpenAI API."""
    from openai import OpenAI

    client = OpenAI(api_key=config.API_KEY)
    return _openai_chat(client, messages)


# ---------------------------------------------------------------------------
# Provider: NVIDIA NIM (OpenAI-compatible with thinking extras)
# ---------------------------------------------------------------------------

def _call_nvidia(messages: list[dict]) -> str:
    """Send messages to the NVIDIA NIM API via the OpenAI-compatible endpoint."""
    from openai import OpenAI

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=config.API_KEY,
    )
    return _openai_chat(client, messages, extra_body={
        "chat_template_kwargs": {"enable_thinking": True},
        "reasoning_budget": 16384,
    })


# ---------------------------------------------------------------------------
# Shared helper for OpenAI-compatible providers
# ---------------------------------------------------------------------------

def _openai_chat(client, messages: list[dict], *, extra_body: dict | None = None) -> str:
    """Shared chat completion call for any OpenAI-compatible client."""
    oai_messages = []
    for msg in messages:
        role = msg["role"] if msg["role"] in ("system", "assistant", "user") else "user"
        oai_messages.append({"role": role, "content": msg["content"]})

    kwargs = {
        "model": config.LLM_MODEL,
        "messages": oai_messages,
        "temperature": 1,
        "top_p": 0.95,
        "max_tokens": 16384,
    }
    if extra_body:
        kwargs["extra_body"] = extra_body

    completion = client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content or ""


_PROVIDER_DISPATCH.update({
    "gemini": _call_gemini,
    "openai": _call_openai,
    "nvidia": _call_nvidia,
})


def _sanitize_code(code) -> str:
    """Fix common LLM output issues in code strings."""
    if isinstance(code, list):
        code = "\n".join(str(item) for item in code)

    if not code or not isinstance(code, str):
        return code or ""

    real_newlines = code.count("\n")
    escaped_newlines = code.count("\\n")
    if escaped_newlines > real_newlines and escaped_newlines > 3:
        code = code.replace("\\n", "\n").replace("\\t", "\t")

    code = re.sub(r"^(jsx|tsx|javascript|typescript|python|go|java|ruby|rust|cpp?|csharp|swift|kotlin)\n",
                  "", code, count=1)

    if code.count('\\"') > 2 and code.count('"') < code.count('\\"'):
        code = code.replace('\\"', '"')

    # Strip line number prefixes the LLM may have copied from the prompt
    lines = code.split("\n")
    stripped = [re.sub(r"^\s*\d+\s*\|\s?", "", line) for line in lines]
    if stripped != lines:
        code = "\n".join(stripped)

    return code


def _sanitize_result(result: dict) -> dict:
    """Recursively sanitize all code strings in the parsed LLM result."""
    if "fixed_code" in result:
        result["fixed_code"] = _sanitize_code(result["fixed_code"])

    if "fixes" in result and isinstance(result["fixes"], list):
        for fix in result["fixes"]:
            if not isinstance(fix, dict):
                continue
            if "fixed_code" in fix:
                fix["fixed_code"] = _sanitize_code(fix["fixed_code"])
            for change in fix.get("changes", []):
                if isinstance(change, dict):
                    if "original" in change:
                        change["original"] = _sanitize_code(change["original"])
                    if "modified" in change:
                        change["modified"] = _sanitize_code(change["modified"])

    return result


def _parse_response(raw) -> dict:
    """Parse raw LLM text into a dict, handling JSON fences, partial extraction, and fallbacks."""
    if raw is None:
        raw = ""
    if isinstance(raw, list):
        raw = "\n".join(
            part.get("text", str(part)) if isinstance(part, dict) else str(part)
            for part in raw
        )
    if not isinstance(raw, str):
        raw = str(raw)

    cleaned = raw.strip()

    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        return _sanitize_result(json.loads(cleaned))
    except json.JSONDecodeError:
        pass

    brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if brace_match:
        try:
            return _sanitize_result(json.loads(brace_match.group()))
        except json.JSONDecodeError:
            pass

    for key in ("fixed_code", "explanation"):
        pattern = rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"'
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            extracted = {key: match.group(1).encode().decode("unicode_escape")}
            for other_key in ("fixed_code", "explanation"):
                if other_key != key:
                    other = re.search(
                        rf'"{other_key}"\s*:\s*"((?:[^"\\]|\\.)*)"',
                        cleaned,
                        re.DOTALL,
                    )
                    if other:
                        extracted[other_key] = other.group(1).encode().decode("unicode_escape")
            if "fixed_code" in extracted:
                return _sanitize_result(extracted)

    return {
        "fixed_code": cleaned,
        "explanation": "Warning: could not parse LLM JSON response. Returning raw text.",
    }
