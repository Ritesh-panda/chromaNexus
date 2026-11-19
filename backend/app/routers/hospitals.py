from typing import List, Optional
from fastapi import APIRouter, Query
from backend.app.services.hospital_service import find_nearby_hospitals, get_ip_location, geocode_location

router = APIRouter(prefix="/hospitals", tags=["Emergency & Hospital Discovery"])


@router.get("/ip-location")
async def detect_ip_location():
    """
    Detects user's geographic location from public IP.
    Completely free fallback when browser GPS is blocked or timed out.
    """
    loc = await get_ip_location()
    return {"status": "success", "location": loc}


@router.get("/search-location")
async def search_location(query: str = Query(..., min_length=2, description="City, district, or locality name")):
    """
    Geocodes a search string using OpenStreetMap Nominatim.
    Free, no API key needed.
    """
    results = await geocode_location(query)
    return {"status": "success", "results": results}


@router.get("/nearby")
async def get_nearby_hospitals(
    lat: float = Query(..., description="Latitude of user"),
    lng: float = Query(..., description="Longitude of user"),
    radius_km: float = Query(10.0, description="Search radius in kilometers")
):
    """
    Returns nearby verified hospitals, emergency casualty wards, and trauma centers
    queried from OpenStreetMap. Zero API keys, completely free.
    """
    hospitals = await find_nearby_hospitals(lat=lat, lng=lng, radius_km=radius_km)
    return {
        "status": "success",
        "count": len(hospitals),
        "userCoordinates": {"lat": lat, "lng": lng},
        "hospitals": hospitals
    }
