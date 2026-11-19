from fastapi import APIRouter
from backend.app.services.health_alerts_service import fetch_health_alerts

router = APIRouter(prefix="/alerts", tags=["Health Alerts & Epidemiological News"])


@router.get("")
async def get_alerts():
    """
    Returns public health alerts and advisories from WHO and MoHFW India.
    Zero commercial cost, 100% free open RSS/API feeds.
    """
    alerts = await fetch_health_alerts()
    return {
        "status": "success",
        "count": len(alerts),
        "alerts": alerts
    }
