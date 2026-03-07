from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    model_name: str = Field(default="gemini-2.5-flash")
    temperature: float = Field(default=0.0)
    top_k: int = Field(default=40)


def get_default_model_config() -> ModelConfig:
    """
    Returns the default model configuration.
    """
    return ModelConfig()
