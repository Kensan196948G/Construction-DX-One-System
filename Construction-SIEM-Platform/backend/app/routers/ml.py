import json
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.anomaly_score import AnomalyScore
from app.models.ml_model import MLModel
from app.schemas.ml import (
    AnomalyScoreRead,
    AnomalyStatsResponse,
    MLModelCreate,
    MLModelRead,
    PredictRequest,
    PredictResponse,
    TrainResponse,
)
from app.services.ml_engine import MLDetectionEngine

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/models", response_model=MLModelRead, status_code=201)
async def create_model(payload: MLModelCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(MLModel).where(MLModel.model_name == payload.model_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Model name already exists")
    model = MLModel(
        model_name=payload.model_name,
        model_type=payload.model_type,
        algorithm=payload.algorithm,
        target=payload.target,
        version=payload.version,
        is_active=payload.is_active,
        parameters=json.dumps(payload.parameters) if payload.parameters else None,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return MLModelRead.model_validate(model)


@router.get("/models", response_model=list[MLModelRead])
async def list_models(
    model_type: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(MLModel)
    if model_type:
        query = query.where(MLModel.model_type == model_type)
    if is_active is not None:
        query = query.where(MLModel.is_active == is_active)
    query = query.order_by(MLModel.created_at.desc())
    result = await db.execute(query)
    models = result.scalars().all()
    return [MLModelRead.model_validate(m) for m in models]


@router.get("/models/{model_id}", response_model=MLModelRead)
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return MLModelRead.model_validate(model)


@router.post("/models/{model_id}/train", response_model=TrainResponse)
async def train_model(model_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    params = json.loads(model.parameters) if model.parameters else {}
    engine = MLDetectionEngine(model_type=model.model_type, parameters=params)

    sample_data = _generate_sample_training_data(model.model_type)
    train_start = time.monotonic()
    metrics = engine.train(sample_data)
    elapsed = time.monotonic() - train_start

    model.metrics = json.dumps(metrics, default=str)
    model.trained_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(model)

    return TrainResponse(success=True, metrics=metrics, training_time_seconds=round(elapsed, 4))


@router.post("/models/{model_id}/predict", response_model=PredictResponse)
async def predict(model_id: str, payload: PredictRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MLModel).where(MLModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    params = json.loads(model.parameters) if model.parameters else {}
    engine = MLDetectionEngine(model_type=model.model_type, parameters=params)

    numeric_features = {
        k: v for k, v in payload.features.items() if isinstance(v, int | float)
    }
    if not numeric_features:
        raise HTTPException(status_code=400, detail="No numeric features provided")

    sample_data = _generate_sample_training_data(model.model_type)
    engine.train(sample_data)

    anomaly_score, is_anomaly, explanation = engine.detect(
        numeric_features, payload.entity_id
    )

    score_entry = AnomalyScore(
        model_id=model_id,
        event_id=payload.event_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        anomaly_score=anomaly_score,
        is_anomaly=is_anomaly,
        features_used=json.dumps(numeric_features),
        explanation=explanation,
        detected_at=datetime.now(UTC),
    )
    db.add(score_entry)
    await db.commit()

    return PredictResponse(anomaly_score=anomaly_score, is_anomaly=is_anomaly, explanation=explanation)


@router.get("/anomalies", response_model=list[AnomalyScoreRead])
async def list_anomalies(
    entity_type: str | None = None,
    is_anomaly: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(AnomalyScore)
    if entity_type:
        query = query.where(AnomalyScore.entity_type == entity_type)
    if is_anomaly is not None:
        query = query.where(AnomalyScore.is_anomaly == is_anomaly)
    query = query.order_by(AnomalyScore.detected_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    scores = result.scalars().all()
    return [AnomalyScoreRead.model_validate(s) for s in scores]


@router.get("/anomalies/stats", response_model=AnomalyStatsResponse)
async def anomaly_stats(db: AsyncSession = Depends(get_db)):
    total_result = await db.execute(select(func.count()).select_from(AnomalyScore))
    total_scores = total_result.scalar_one()

    anomaly_result = await db.execute(
        select(func.count()).select_from(AnomalyScore).where(AnomalyScore.is_anomaly)
    )
    total_anomalies = anomaly_result.scalar_one()

    avg_result = await db.execute(select(func.avg(AnomalyScore.anomaly_score)))
    average_score = round(avg_result.scalar_one() or 0.0, 4)

    max_result = await db.execute(select(func.max(AnomalyScore.anomaly_score)))
    max_score = round(max_result.scalar_one() or 0.0, 4)

    by_type_result = await db.execute(
        select(AnomalyScore.entity_type, func.count().label("count"))
        .group_by(AnomalyScore.entity_type)
    )
    by_entity_type = {row[0]: row[1] for row in by_type_result.all()}

    return AnomalyStatsResponse(
        total_scores=total_scores,
        total_anomalies=total_anomalies,
        anomaly_rate=round(total_anomalies / total_scores, 4) if total_scores > 0 else 0.0,
        by_entity_type=by_entity_type,
        average_score=average_score,
        max_score=max_score,
    )


def _generate_sample_training_data(model_type: str) -> list[dict[str, float]]:
    if model_type == "netflow_anomaly":
        return [
            {"bytes_sent": 500 + i * 10, "bytes_received": 1000 + i * 5, "packets": 50 + i}
            for i in range(100)
        ]
    if model_type == "iot_anomaly":
        return [
            {"temperature": 25.0 + (i % 10) * 0.5, "humidity": 60.0 + (i % 5), "signal": -50 + (i % 20)}
            for i in range(100)
        ]
    return [
        {
            "login_count": 5 + (i % 10),
            "file_access_count": 20 + i,
            "network_connections": 10 + (i % 5),
            "failed_logins": 1 + (i % 3),
        }
        for i in range(100)
    ]
