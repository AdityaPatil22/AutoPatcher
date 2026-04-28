import json
import re

from app.config import GEMINI_API_KEY, LLM_MODEL, LLM_PROVIDER, OPENAI_API_KEY


def call_llm(messages: list[dict]) -> dict:
    """
    Call the configured LLM provider and return parsed JSON response.
    Supports OpenAI and Google Gemini.
    """
    if LLM_PROVIDER == "gemini":
        raw = _call_gemini(messages)
    else:
        raw = _call_openai(messages)

    return _parse_response(raw)


def _call_openai(messages: list[dict]) -> str:
    from openai import OpenAI

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def _call_gemini(messages: list[dict]) -> str:
    import google.generativeai as genai

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(LLM_MODEL or "gemini-1.5-flash")

    prompt_parts = []
    for msg in messages:
        prefix = "System: " if msg["role"] == "system" else "User: "
        prompt_parts.append(prefix + msg["content"])

    response = model.generate_content(
        "\n\n".join(prompt_parts),
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )
    return response.text


def _parse_response(raw: str) -> dict:
    """Parse the LLM response, handling common formatting issues."""
    cleaned = raw.strip()

    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "fixed_code": cleaned,
            "explanation": f"Warning: could not parse LLM JSON response ({e}). Returning raw text.",
        }
