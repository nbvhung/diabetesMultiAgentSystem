from typing import Literal
from uuid import UUID
from pydantic import Field
from backend.app.schemas.contracts import PredictionResult as PredictionV1

class PredictionResult(PredictionV1):
    schema_version: Literal["1.1"] = "1.1"
    preprocessing_version: str
    inference_latency_ms: float = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    persisted_record_id: UUID | None = None
