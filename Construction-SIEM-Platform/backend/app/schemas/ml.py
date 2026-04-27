import json
from datetime import datetime

from pydantic import BaseModel, field_validator


class MLModelCreate(BaseModel):
    model_name: str
    model_type: str
    algorithm: str
    target: str
    version: int = 1
    is_active: bool = True
    parameters: dict | None = None


class MLModelUpdate(BaseModel):
    model_name: str | None = None
    is_active: bool | None = None
    parameters: dict | None = None
    metrics: dict | None = None
    version: int | None = None


class MLModelRead(BaseModel):
    id: str
    model_name: str
    model_type: str
    algorithm: str
    target: str
    version: int
    is_active: bool
    parameters: dict | None
    metrics: dict | None
    trained_at: datetime | None
    training_data_range_start: datetime | None
    training_data_range_end: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("parameters", "metrics", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v


class AnomalyScoreRead(BaseModel):
    id: str
    model_id: str
    event_id: str | None
    entity_type: str
    entity_id: str
    anomaly_score: float
    is_anomaly: bool
    features_used: dict | None
    explanation: str | None
    detected_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("features_used", mode="before")
    @classmethod
    def parse_features_json(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v


class PredictRequest(BaseModel):
    event_id: str | None = None
    entity_type: str
    entity_id: str
    features: dict


class PredictResponse(BaseModel):
    anomaly_score: float
    is_anomaly: bool
    explanation: str | None


class TrainResponse(BaseModel):
    success: bool
    metrics: dict | None
    training_time_seconds: float


class AnomalyStatsResponse(BaseModel):
    total_scores: int
    total_anomalies: int
    anomaly_rate: float
    by_entity_type: dict[str, int]
    average_score: float
    max_score: float
