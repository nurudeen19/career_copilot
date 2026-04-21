"""Prompt guard (HF). Env: ``PROMPT_GUARD__*``. Root ``HF_TOKEN`` is merged in ``Settings`` validator."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PromptGuardSettings(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    huggingface_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_TOKEN"),
    )
    model_id: str = Field(default="meta-llama/Llama-Prompt-Guard-2-86M")
    device: int = Field(default=-1)
