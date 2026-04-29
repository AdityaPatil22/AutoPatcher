import json
import re

from app.config import (
    GEMINI_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    LOCAL_LLM_BASE_URL,
    OPENAI_API_KEY,
)


def call_llm(messages: list[dict]) -> dict:
    """
    Call the configured LLM provider and return parsed JSON response.
    Supports OpenAI, Google Gemini, and local models (Ollama, LM Studio, etc.).
    """
    if LLM_PROVIDER == "gemini":
        raw = _call_gemini(messages)
    elif LLM_PROVIDER == "local":
        raw = _call_local(messages)
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


def _call_local(messages: list[dict]) -> str:
    from openai import OpenAI

    client = OpenAI(base_url=LOCAL_LLM_BASE_URL, api_key="not-needed")

    kwargs: dict = dict(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=4096,
    )
    try:
        kwargs["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(**kwargs)
    except Exception:
        del kwargs["response_format"]
        response = client.chat.completions.create(**kwargs)

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

    return code


def _sanitize_result(result: dict) -> dict:
    """Sanitize all code strings in the parsed LLM result."""
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
    """Parse the LLM response, handling common formatting issues."""
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
