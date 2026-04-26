from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "IT-Change-CAB-Platform", "version": "1.0.0"}
