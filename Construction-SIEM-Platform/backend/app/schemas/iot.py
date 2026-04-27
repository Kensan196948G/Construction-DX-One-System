
from pydantic import BaseModel


class IoTSensorPayload(BaseModel):
    temperature: float | None = None
    humidity: float | None = None
    vibration: float | None = None
    noise_level: float | None = None
    gps_lat: float | None = None
    gps_lng: float | None = None
    battery_level: float | None = None
    signal_strength: int | None = None
    additional: dict | None = None


class IoTEventCreate(BaseModel):
    device_id: str
    event_type: str
    payload: IoTSensorPayload | dict


class IoTEventResponse(BaseModel):
    status: str = "success"
    event_id: str
    device_id: str
    event_type: str
    timestamp: str
    buffered: bool = False


class IoTBatchEventRequest(BaseModel):
    events: list[IoTEventCreate]


class IoTBatchEventResponse(BaseModel):
    status: str = "success"
    accepted: int
    failed: int
    errors: list[dict] = []


class IoTFlushResponse(BaseModel):
    status: str = "success"
    flushed: int
    events: list[dict]


class IoTDeviceStatusResponse(BaseModel):
    device_id: str
    online: bool
    last_seen: str | None
    buffer_size: int
    total_events_collected: int
    battery_level: float | None = None
    signal_strength: int | None = None


class IoTBufferStatsResponse(BaseModel):
    status: str = "success"
    total_buffered: int
    device_count: int
    oldest_buffer: str | None
    max_buffer_size: int
    retention_seconds: int
