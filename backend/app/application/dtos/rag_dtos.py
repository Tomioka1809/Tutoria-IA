from pydantic import BaseModel, Field, model_validator
from typing import Literal


class RetrievedChunkDTO(BaseModel):
    text: str
    source: str | None = None
    cosine_distance: float | None = None
    retrieval_method: Literal["vector", "keyword"] = "vector"


class RAGRetrievalPolicy(BaseModel):
    limit: int = Field(default=6, gt=0)
    max_cosine_distance: float = Field(default=0.45, ge=0.0, le=2.0)
    keyword_fallback_limit: int = Field(default=2, ge=0)

    @model_validator(mode="after")
    def validate_limits(self) -> "RAGRetrievalPolicy":
        if self.keyword_fallback_limit > self.limit:
            raise ValueError("keyword_fallback_limit must not exceed limit")
        return self
