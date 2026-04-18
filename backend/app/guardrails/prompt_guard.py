"""Llama Prompt Guard 2 (HF). Loaded once at app startup — not on first chat request."""

from __future__ import annotations

import os
from typing import Any

from app.config.settings import Settings

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

_pipeline: Any | None = None


def is_prompt_guard_loaded() -> bool:
    """True after ``setup_prompt_guard`` has completed successfully."""
    return _pipeline is not None


def _hf_token(settings: Settings) -> str | None:
    return (
        settings.huggingface_token
        or os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        or None
    )


def setup_prompt_guard(settings: Settings) -> None:
    """Download/load the classifier and keep it in memory. Call from ``init_app``."""
    global _pipeline
    if _pipeline is not None:
        return

    token = _hf_token(settings)
    if not token:
        raise RuntimeError(
            "Prompt guard requires HF_TOKEN (or HUGGINGFACE_TOKEN / HUGGING_FACE_HUB_TOKEN) "
            "to access meta-llama/Llama-Prompt-Guard-2-86M."
        )

    from transformers import pipeline

    kwargs: dict[str, Any] = {
        "task": "text-classification",
        "model": settings.prompt_guard_model_id,
        "truncation": True,
        "max_length": 512,
        "device": settings.prompt_guard_device,
        "token": token,
    }
    _pipeline = pipeline(**kwargs)
    # Warm a trivial forward pass so the first user message does not pay one-time costs alone.
    _pipeline("ok", truncation=True, max_length=512)


def teardown_prompt_guard() -> None:
    global _pipeline
    _pipeline = None


def _malicious(item: dict[str, Any]) -> bool:
    label_raw = str(item.get("label", "")).strip()
    u = label_raw.upper()
    if "MALICIOUS" in u:
        return True
    if "BENIGN" in u:
        return False

    pipe = _pipeline
    if pipe is None:
        return False

    cfg = getattr(pipe.model, "config", None)
    id2label = getattr(cfg, "id2label", None) if cfg is not None else None
    if isinstance(id2label, dict) and u.startswith("LABEL_"):
        try:
            idx = int(u.split("_")[-1])
        except ValueError:
            idx = -1
        named = id2label.get(idx) or id2label.get(str(idx))
        if named is not None:
            return "MALICIOUS" in str(named).upper()

    if u.startswith("LABEL_"):
        try:
            idx = int(u.split("_")[-1])
        except ValueError:
            return False
        return idx == 1

    return False


def classify_prompt(text: str) -> tuple[bool, str | None]:
    """(safe, denial_message). Requires ``setup_prompt_guard`` already run."""
    if _pipeline is None:
        return False, "Prompt guard is not initialized."

    try:
        batch = _pipeline(text, truncation=True, max_length=512)
    except Exception as exc:  # noqa: BLE001
        return False, f"Prompt guard failed: {exc}"

    item = batch[0] if isinstance(batch, list) else batch
    if not isinstance(item, dict):
        return False, "Prompt guard returned an unexpected response."

    if _malicious(item):
        return (
            False,
            "This message was blocked by automated prompt safety checks. "
            "Please ask a normal career question without instructions aimed at overriding the assistant.",
        )
    return True, None
