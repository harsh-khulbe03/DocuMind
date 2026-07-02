from app.config import Settings
from app.llm.base import LLMProvider


def get_llm(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "ollama":
        from app.llm.ollama import OllamaProvider
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    if settings.llm_provider == "bedrock":
        from app.llm.bedrock import BedrockProvider
        return BedrockProvider(
            model_id=settings.bedrock_model_id,
            region=settings.aws_region,
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
        )

    raise ValueError(f"Unknown LLM provider: {settings.llm_provider!r}")
