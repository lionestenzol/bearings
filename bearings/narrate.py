"""OPTIONAL, provider-agnostic narration.

The digest is complete without this. If you want prose on top, point bearings at
ANY OpenAI-compatible /chat/completions endpoint — OpenAI, an Anthropic-compatible
gateway, Ollama, vLLM, LM Studio, llamafile, OpenRouter, … Configure via flags or
env; uses only stdlib urllib, so even narration adds no dependency.

  BEARINGS_LLM_BASE_URL   e.g. https://api.openai.com/v1  or  http://localhost:11434/v1
  BEARINGS_LLM_MODEL      e.g. gpt-4o-mini  or  llama3.1  or  claude-3-5-sonnet
  BEARINGS_LLM_API_KEY    bearer token (omit for local servers that don't need one)
"""
import json
import os
import urllib.request

_SYSTEM = (
    "You summarize an engineering day from a deterministic git+session digest. "
    "Be terse and factual. No flattery, no filler. Lead with what shipped, then "
    "open threads. 4-6 bullets maximum. Do not invent anything not in the digest."
)


def available(base_url=None, model=None):
    base_url = base_url or os.environ.get("BEARINGS_LLM_BASE_URL")
    model = model or os.environ.get("BEARINGS_LLM_MODEL")
    return bool(base_url and model)


def narrate(digest_md, base_url=None, model=None, api_key=None, timeout=60):
    # type: (str, str, str, str, int) -> str
    base_url = base_url or os.environ.get("BEARINGS_LLM_BASE_URL")
    model = model or os.environ.get("BEARINGS_LLM_MODEL")
    api_key = api_key if api_key is not None else os.environ.get("BEARINGS_LLM_API_KEY", "")
    if not base_url or not model:
        raise RuntimeError(
            "narration needs --llm-base-url and --llm-model "
            "(or BEARINGS_LLM_BASE_URL / BEARINGS_LLM_MODEL)"
        )
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": digest_md},
        ],
        "temperature": 0.2,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    return data["choices"][0]["message"]["content"]
