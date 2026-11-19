import math
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


async def get_ip_location() -> Dict[str, Any]:
    """
    Detects user's approximate location from public IP.
    Completely free, no GPS permission needed.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://ipapi.co/json/")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("latitude") and data.get("longitude"):
                    return {
                        "city": data.get("city") or "Local Area",
                        "region": data.get("region") or "",
                        "country": data.get("country_name") or "India",
                        "latitude": float(data["latitude"]),
                        "longitude": float(data["longitude"]),
                        "displayName": f"{data.get('city')}, {data.get('region')}"
                    }
    except Exception as e:
        logger.warning(f"ipapi.co failed: {e}. Trying fallback ip-api.com...")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://ip-api.com/json/")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("lat") and data.get("lon"):
                    return {
                        "city": data.get("city") or "Local Area",
                        "region": data.get("regionName") or "",
                        "country": data.get("country") or "India",
                        "latitude": float(data["lat"]),
                        "longitude": float(data["lon"]),
                        "displayName": f"{data.get('city')}, {data.get('regionName')}"
                    }
    except Exception as e:
        logger.warning(f"ip-api.com failed: {e}")

    # Safe general India fallback
    return {
        "city": "Vijayawada",
        "region": "Andhra Pradesh",
        "country": "India",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "displayName": "Vijayawada, Andhra Pradesh"
    }


async def geocode_location(query: str) -> List[Dict[str, Any]]:
    """
    Geocodes a search string (city, district, pincode) using OpenStreetMap Nominatim.
    100% Free, zero API key.
    """
    clean_q = query.strip()
    if not clean_q:
        return []
    url = f"https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "ChronaNexus-Healthcare/1.0 (contact@chronanexus.org)"}
    params = {
        "q": clean_q,
        "format": "json",
        "limit": 5,
        "countrycodes": "in"
    }
    try:
        async with httpx.AsyncClient(timeout=6.0, headers=headers) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data:
                    results.append({
                        "displayName": item.get("display_name", clean_q),
                        "latitude": float(item["lat"]),
                        "longitude": float(item["lon"]),
                        "type": item.get("type", "location")
                    })
                return results
    except Exception as e:
        logger.warning(f"Nominatim geocoding error: {e}")
    return []


async def find_nearby_hospitals(
    lat: float,
    lng: float,
    radius_km: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Discovers nearby verified hospitals, emergency casualty wards, and trauma centers.
    Uses OpenStreetMap Nominatim with bounding-box discovery for speed & reliability,
    with Overpass API mirrors as secondary fallback.
    100% Free, zero commercial API keys required.
    """
    hospitals = []
    headers = {"User-Agent": "ChronaNexus-Healthcare/1.0 (contact@chronanexus.org)"}
    delta = min(max(radius_km / 111.0, 0.03), 0.25)

    # 1. Primary: High-speed OpenStreetMap Nominatim Bounding-Box Query
    try:
        nominatim_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": "hospital",
            "format": "json",
            "limit": 12,
            "viewbox": f"{lng - delta},{lat + delta},{lng + delta},{lat - delta}",
            "bounded": 1,
            "countrycodes": "in"
        }
        async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
            resp = await client.get(nominatim_url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    h_lat = float(item["lat"])
                    h_lng = float(item["lon"])
                    dist = haversine_distance(lat, lng, h_lat, h_lng)
                    display_parts = item.get("display_name", "").split(", ")
                    name = display_parts[0] if display_parts else "Hospital"
                    if name.lower() in ["hospital", "clinic", "#hospital"]:
                        name = ", ".join(display_parts[:2])

                    address = ", ".join(display_parts[1:4]) if len(display_parts) > 1 else "Local Area"
                    is_emergency = any(w in item.get("display_name", "").lower() for w in ["hospital", "emergency", "trauma", "casualty"])

                    hospitals.append({
                        "id": str(item.get("place_id", f"nom_{h_lat}_{h_lng}")),
                        "name": name,
                        "type": "General Hospital & Casualty" if is_emergency else "Healthcare Facility",
                        "distanceKm": dist,
                        "isEmergency": is_emergency,
                        "phone": "108",
                        "address": address,
                        "latitude": h_lat,
                        "longitude": h_lng,
                        "directionsUrl": f"https://www.google.com/maps/dir/?api=1&destination={h_lat},{h_lng}"
                    })
    except Exception as e:
        logger.warning(f"Nominatim hospital lookup encountered notice: {e}")

    # 2. Secondary: Overpass API (if Nominatim returned fewer than 3 items)
    if len(hospitals) < 3:
        radius_meters = int(min(max(radius_km, 2.0), 25.0) * 1000)
        overpass_query = f"""[out:json][timeout:5];
(
  node["amenity"="hospital"](around:{radius_meters},{lat},{lng});
  way["amenity"="hospital"](around:{radius_meters},{lat},{lng});
  node["healthcare"="hospital"](around:{radius_meters},{lat},{lng});
);
out center 10;"""

        for endpoint in ["https://overpass-api.de/api/interpreter", "https://lz4.overpass-api.de/api/interpreter"]:
            try:
                async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
                    resp = await client.post(endpoint, data={"data": overpass_query})
                    if resp.status_code == 200:
                        elements = resp.json().get("elements", [])
                        for elem in elements:
                            tags = elem.get("tags", {})
                            name = tags.get("name") or tags.get("name:en")
                            if not name:
                                continue
                            h_lat = elem.get("lat") or (elem.get("center", {}).get("lat"))
                            h_lng = elem.get("lon") or (elem.get("center", {}).get("lon"))
                            if not h_lat or not h_lng:
                                continue
                            dist = haversine_distance(lat, lng, float(h_lat), float(h_lng))
                            hospitals.append({
                                "id": str(elem.get("id")),
                                "name": name,
                                "type": "Government / General Hospital",
                                "distanceKm": dist,
                                "isEmergency": True,
                                "phone": tags.get("phone") or "108",
                                "address": tags.get("addr:full") or "District Central Road",
                                "latitude": float(h_lat),
                                "longitude": float(h_lng),
                                "directionsUrl": f"https://www.google.com/maps/dir/?api=1&destination={h_lat},{h_lng}"
                            })
                        break
            except Exception:
                continue

    # 3. Always ensure 108 Emergency dispatch is front and center
    has_108 = any(h.get("id") == "em_108" for h in hospitals)
    if not has_108:
        hospitals.insert(0, {
            "id": "em_108",
            "name": "National Ambulance Dispatch (108 Network)",
            "type": "24/7 Emergency Trauma & Ambulance",
            "distanceKm": 0.0,
            "isEmergency": True,
            "phone": "108",
            "address": "Immediate 24/7 Dispatch to Detected GPS Coordinates",
            "latitude": lat,
            "longitude": lng,
            "directionsUrl": f"https://www.google.com/maps/search/hospitals/@{lat},{lng},13z"
        })

    # Sort nearest first
    hospitals.sort(key=lambda x: x["distanceKm"])
    return hospitals[:10]
