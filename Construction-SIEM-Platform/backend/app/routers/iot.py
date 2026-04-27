from fastapi import APIRouter

from app.schemas.iot import (
    IoTBatchEventRequest,
    IoTBatchEventResponse,
    IoTBufferStatsResponse,
    IoTDeviceStatusResponse,
    IoTEventCreate,
    IoTEventResponse,
    IoTFlushResponse,
)
from app.services.iot_agent import get_iot_agent

router = APIRouter(prefix="/api/v1/iot", tags=["iot"])


@router.post("/events", response_model=IoTEventResponse, status_code=201)
async def ingest_iot_event(payload: IoTEventCreate):
    agent = get_iot_agent()
    result = agent.collect_event(
        device_id=payload.device_id,
        event_type=payload.event_type,
        payload=payload.payload,
    )
    return IoTEventResponse(
        status="success",
        event_id=result["event_id"],
        device_id=result["device_id"],
        event_type=result["event_type"],
        timestamp=result["timestamp"],
        buffered=result["buffered"],
    )


@router.post("/events/batch", response_model=IoTBatchEventResponse)
async def ingest_iot_events_batch(payload: IoTBatchEventRequest):
    agent = get_iot_agent()
    errors = []
    accepted = 0
    for event in payload.events:
        try:
            agent.collect_event(
                device_id=event.device_id,
                event_type=event.event_type,
                payload=event.payload,
            )
            accepted += 1
        except Exception as e:
            errors.append({"device_id": event.device_id, "error": str(e)})
    return IoTBatchEventResponse(
        status="success",
        accepted=accepted,
        failed=len(errors),
        errors=errors,
    )


@router.post("/events/flush", response_model=IoTFlushResponse)
async def flush_iot_buffer():
    agent = get_iot_agent()
    events = agent.flush_buffer()
    return IoTFlushResponse(
        status="success",
        flushed=len(events),
        events=events,
    )


@router.get("/status/{device_id}", response_model=IoTDeviceStatusResponse)
async def get_device_status(device_id: str):
    agent = get_iot_agent()
    status = agent.get_device_status(device_id)
    return IoTDeviceStatusResponse(**status)


@router.get("/buffer/stats", response_model=IoTBufferStatsResponse)
async def get_buffer_stats():
    agent = get_iot_agent()
    stats = agent.get_buffer_stats()
    return IoTBufferStatsResponse(**stats)
