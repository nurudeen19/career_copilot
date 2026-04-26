"""Llama Prompt Guard 2 (HF). Loaded once at app startup — not on first chat request.

Classification follows Meta's reference implementation (``get_jailbreak_score`` / softmax on logits)
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.config.settings import Settings, get_settings

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

_log = logging.getLogger(__name__)

_pipeline: Any | None = None

# HF / DeBERTa: max 512 tokens; long user text is truncated (default: tail may be under-scanned).
_APPROX_CHARS_PER_TOKEN = 4
_MAX_GUARD_MODEL_TOKENS = 512


def is_prompt_guard_loaded() -> bool:
    """True after ``setup_prompt_guard`` has completed successfully."""
    return _pipeline is not None


def setup_prompt_guard(settings: Settings) -> None:
    """Download/load the classifier and keep it in memory. Call from ``init_app``."""
    global _pipeline
    if _pipeline is not None:
        return

    token = settings.hf_token
    if not token:
        raise RuntimeError(
            "Prompt guard needs a Hugging Face token: set HF_TOKEN (or HUGGING_FACE_HUB_TOKEN) "
            f"to access {settings.prompt_guard.model_id}."
        )

    try:
        from transformers import pipeline
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "transformers is required for the prompt guard. Install an optional extra, e.g. "
            "``pip install '.[transformers-cpu]'`` (use PyTorch's CPU wheel index in Docker) or "
            "``pip install '.[transformers-gpu]'`` for GPU hosts, then reinstall."
        ) from exc

    kwargs: dict[str, Any] = {
        "task": "text-classification",
        "model": settings.prompt_guard.model_id,
        "truncation": True,
        "max_length": 512,
        "device": settings.prompt_guard.device,
        "token": token,
    }
    _pipeline = pipeline(**kwargs)
    # Warm a trivial forward pass so the first user message does not pay one-time costs alone.
    _pipeline("ok", truncation=True, max_length=512)
    _log.info(
        "Prompt guard model loaded",
        extra={
            "event": "prompt_guard_loaded",
            "model_id": settings.prompt_guard.model_id,
            "device": settings.prompt_guard.device,
        },
    )


def teardown_prompt_guard() -> None:
    global _pipeline
    _pipeline = None


def _malicious_class_index(model: Any) -> int:
    """Index of the MALICIOUS logit (Meta cookbook: ``probabilities[0, 1]`` for Prompt Guard 2)."""
    cfg = getattr(model, "config", None)
    id2label = getattr(cfg, "id2label", None) if cfg is not None else None
    if isinstance(id2label, dict):
        for k, v in id2label.items():
            if "MALICIOUS" in str(v).upper():
                try:
                    return int(k)
                except (TypeError, ValueError):
                    if str(k).isdigit():
                        return int(str(k))
    return 1


def _softmax_malicious_probability(text: str) -> float:
    """P(malicious) after softmax — same construction as Meta ``get_jailbreak_score``."""
    import torch
    from torch.nn.functional import softmax

    pipe = _pipeline
    if pipe is None:
        raise RuntimeError("prompt_guard pipeline is not loaded")

    model = pipe.model
    tokenizer = pipe.tokenizer
    device = next(model.parameters()).device
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=_MAX_GUARD_MODEL_TOKENS,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = softmax(logits, dim=-1)
    idx = _malicious_class_index(model)
    if idx < 0 or idx >= probs.shape[-1]:
        _log.error(
            "Prompt guard malicious class index out of range",
            extra={
                "event": "prompt_guard_bad_malicious_index",
                "malicious_index": idx,
                "num_labels": int(probs.shape[-1]),
            },
        )
        return 1.0
    return float(probs[0, idx].item())


def classify_prompt(
    text: str,
    settings: Settings | None = None,
    *,
    malicious_threshold: float | None = None,
) -> tuple[bool, str | None]:
    """(safe, denial_message). Uses softmax P(malicious) vs threshold (Meta cookbook), not top-1 only.

    ``malicious_threshold`` overrides ``settings.prompt_guard.malicious_probability_threshold`` when set.
    """
    if _pipeline is None:
        _log.error(
            "Prompt guard classify called with no pipeline loaded",
            extra={"event": "prompt_guard_not_loaded"},
        )
        return False, "Prompt guard is not initialized."

    s = settings or get_settings()
    threshold = (
        float(malicious_threshold)
        if malicious_threshold is not None
        else float(s.prompt_guard.malicious_probability_threshold)
    )

    est_tokens = max(len(text) // _APPROX_CHARS_PER_TOKEN, 1)
    if est_tokens > _MAX_GUARD_MODEL_TOKENS:
        _log.info(
            "Prompt guard input exceeds model window; text truncated for scan",
            extra={
                "event": "prompt_guard_input_truncated",
                "estimated_tokens": est_tokens,
                "char_count": len(text),
                "max_model_tokens": _MAX_GUARD_MODEL_TOKENS,
            },
        )

    try:
        p_mal = _softmax_malicious_probability(text)
    except Exception as exc:  # noqa: BLE001
        _log.exception(
            "Prompt guard inference failed",
            extra={"event": "prompt_guard_inference_failed"},
        )
        return False, f"Prompt guard failed: {exc}"

    _log.debug(
        "Prompt guard scores",
        extra={
            "event": "prompt_guard_scores",
            "p_malicious": round(p_mal, 6),
            "threshold": threshold,
        },
    )

    if p_mal >= threshold:
        _log.warning(
            "Prompt guard blocked message",
            extra={
                "event": "prompt_guard_blocked",
                "p_malicious": round(p_mal, 6),
                "threshold": threshold,
                "char_count": len(text),
            },
        )
        return (
            False,
            "This message was blocked by automated prompt safety checks. "
            "Please ask a normal career question without instructions aimed at overriding the assistant.",
        )

    _log.info(
        "Prompt guard allowed message",
        extra={
            "event": "prompt_guard_allowed",
            "p_malicious": round(p_mal, 6),
            "threshold": threshold,
            "char_count": len(text),
        },
    )
    return True, None
