"""Prompt guard (HF) — mixed into ``Settings``."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PromptGuardSettings(BaseModel):
    """``HF_TOKEN``, ``PROMPT_GUARD_MODEL_ID``, ``PROMPT_GUARD_DEVICE``."""

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
