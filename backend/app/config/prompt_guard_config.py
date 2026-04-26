"""Prompt guard (HF) — mixed into ``Settings``."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PromptGuardSettings(BaseModel):
    """``HF_TOKEN``, ``PROMPT_GUARD_MODEL_ID``, ``PROMPT_GUARD_DEVICE``, optional score threshold."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    hf_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_TOKEN"),
    )
    model_id: str = Field(
        default="meta-llama/Llama-Prompt-Guard-2-86M",
        validation_alias=AliasChoices("PROMPT_GUARD_MODEL_ID"),
    )
    device: int = Field(default=-1, validation_alias=AliasChoices("PROMPT_GUARD_DEVICE"))
    malicious_probability_threshold: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices("PROMPT_GUARD_MALICIOUS_THRESHOLD"),
        description=(
            "Block when softmax P(malicious) ≥ this value (see Meta llama-cookbook prompt_guard inference.py). "
            "Lower = stricter (more false positives). Default 0.15 catches many borderline injections."
        ),
    )
    classify_user_feedback: bool = Field(
        default=False,
        validation_alias=AliasChoices("PROMPT_GUARD_CLASSIFY_USER_FEEDBACK"),
        description=(
            "When false (default), ``user_feedback`` is only size-checked — not run through the HF prompt guard. "
            "Feedback often looks like instructions to the classifier (e.g. thumbs-down marker, 'be more concise'). "
            "Set true to apply the same jailbreak scan as normal chat (stricter)."
        ),
    )
