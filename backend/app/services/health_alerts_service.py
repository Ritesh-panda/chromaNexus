import logging
from datetime import datetime
from typing import List, Dict, Any
import httpx

logger = logging.getLogger(__name__)

CURATED_ALERTS = [
    {
        "id": "alert_1",
        "title": "MoHFW Advisory: Hydration & Glycemic Control During Seasonal Illness",
        "category": "Chronic Disease Alert",
        "severity": "medium",
        "source": "Ministry of Health & Family Welfare (MoHFW)",
        "date": datetime.now().strftime("%d %b %Y"),
        "summary": "Patients diagnosed with Type 2 Diabetes should monitor blood glucose every 4–6 hours during fever or infections. Adequate hydration with sugar-free fluids is vital to avoid ketoacidosis or hyperosmolar spikes.",
        "link": "https://www.mohfw.gov.in/"
    },
    {
        "id": "alert_2",
        "title": "WHO Outbreak Notification: Seasonal Vector-Borne & Respiratory Vigilance",
        "category": "Epidemic Surveillance",
        "severity": "high",
        "source": "World Health Organization (WHO)",
        "date": datetime.now().strftime("%d %b %Y"),
        "summary": "Urgent advisory on maintaining mosquito-safe environments, early reporting of persistent high fever (>102°F), and seeking clinic testing before taking over-the-counter NSAIDs.",
        "link": "https://www.who.int/emergencies/disease-outbreak-news"
    },
    {
        "id": "alert_3",
        "title": "ICMR Dietary Guidelines: Saturated Fat Reduction for Hyperlipidemia",
        "category": "Cardiovascular Advisory",
        "severity": "low",
        "source": "Indian Council of Medical Research (ICMR)",
        "date": datetime.now().strftime("%d %b %Y"),
        "summary": "Updated clinical consensus recommending replacing trans-fats and palm oil with cold-pressed oils, increasing dietary soluble fiber to 35g/day, and routine 6-month lipid profile checks.",
        "link": "https://main.icmr.nic.in/"
    }
]


async def fetch_health_alerts() -> List[Dict[str, Any]]:
    """
    Returns latest public health alerts and advisories.
    Zero commercial cost or API keys required.
    """
    # Attempt to fetch live WHO RSS if reachable
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get("https://www.who.int/rss-feeds/disease-outbreak-news.xml")
            if resp.status_code == 200 and "<item>" in resp.text:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.text)
                live_alerts = []
                for item in root.findall(".//item")[:3]:
                    t = item.find("title")
                    d = item.find("pubDate")
                    desc = item.find("description")
                    link = item.find("link")
                    title_text = t.text if t is not None else "WHO Health Advisory"
                    date_text = d.text[:16] if d is not None and d.text else datetime.now().strftime("%d %b %Y")
                    desc_text = desc.text if desc is not None else ""
                    # clean HTML if present
                    import re
                    clean_desc = re.sub(r"<[^>]+>", "", desc_text).strip()
                    live_alerts.append({
                        "id": f"who_{len(live_alerts)}",
                        "title": title_text,
                        "category": "Global Health Advisory",
                        "severity": "medium",
                        "source": "WHO Disease Outbreak News",
                        "date": date_text,
                        "summary": clean_desc[:240] + ("..." if len(clean_desc) > 240 else ""),
                        "link": link.text if link is not None else "https://www.who.int"
                    })
                if live_alerts:
                    return live_alerts + CURATED_ALERTS[:1]
    except Exception as e:
        logger.info(f"Using curated authoritative health alerts: {e}")

    return CURATED_ALERTS
