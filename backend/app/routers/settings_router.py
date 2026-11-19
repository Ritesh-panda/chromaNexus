import logging
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.app.core.config import settings
from backend.app.ai.llm.groq import GroqProvider
from backend.app.ai.llm.ollama import OllamaProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["System & AI Settings"])


class AIModeUpdateRequest(BaseModel):
    mode: str  # 'online' or 'offline'


class AIModeResponse(BaseModel):
    mode: str
    active_provider: str
    online_model: str
    offline_model: str
    groq_configured: bool
    status: str


@router.get("/ai-mode", response_model=AIModeResponse)
def get_ai_mode():
    """Returns the current active AI inference configuration and health."""
    mode = getattr(settings, "AI_INFERENCE_MODE", "online").lower()
    has_groq = bool(getattr(settings, "GROQ_API_KEY", ""))

    active_provider = "Groq LPU (Cloud)" if mode == "online" else "Ollama (Local Offline)"
    
    return AIModeResponse(
        mode=mode,
        active_provider=active_provider,
        online_model=getattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b"),
        offline_model=getattr(settings, "OLLAMA_MODEL", "llama3.2:3b"),
        groq_configured=has_groq,
        status="Operational"
    )


@router.post("/ai-mode", response_model=AIModeResponse)
def set_ai_mode(req: AIModeUpdateRequest):
    """Switches the active inference engine between 'online' (Groq) and 'offline' (Ollama)."""
    target_mode = req.mode.lower().strip()
    if target_mode not in ["online", "offline"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid mode. Supported modes are 'online' (Groq) and 'offline' (Ollama)."
        )

    settings.AI_INFERENCE_MODE = target_mode
    logger.info(f"Switched ChronaNexus AI Inference Mode to: {target_mode.upper()}")

    return get_ai_mode()
