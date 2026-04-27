from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Construction-SIEM-Platform",
        "version": "0.1.0",
    }
