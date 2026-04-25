from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["system"])
settings = get_settings()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }
