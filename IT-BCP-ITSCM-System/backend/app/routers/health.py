from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "IT-BCP-ITSCM-System", "version": "1.0.0"}
