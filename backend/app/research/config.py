from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT=Path(__file__).resolve().parents[3]


class ResearchSettings(BaseSettings):
    model_config=SettingsConfigDict(env_file='.env',extra='ignore')
    groq_api_key: SecretStr | None=Field(default=None,repr=False)
    groq_model: str='openai/gpt-oss-20b'
    groq_timeout_seconds: float=Field(default=25,ge=1,le=60)
    groq_max_output_tokens: int=Field(default=2000,ge=256,le=4000)
    diabetes_llm_enabled: bool=True
    # Requests never download models or content. Prepare explicitly, then serve offline.
    diabetes_corpus_dir: Path=ROOT/'data/knowledge/diabetes-v2'
    diabetes_semantic_dir: Path=ROOT/'artifacts/embeddings/diabetes-minilm-1.0'
    diabetes_reranker_dir: Path=ROOT/'artifacts/embeddings/diabetes-reranker-1.0'
    diabetes_max_retrieval_rounds: int=Field(default=2,ge=1,le=2)


research_settings=ResearchSettings()
