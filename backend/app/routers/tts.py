import io
import re
import logging
import edge_tts
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice Neural TTS"])

VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "bn": "bn-IN-TanishaaNeural",
    "te": "te-IN-ShrutiNeural",
    "ta": "ta-IN-PallaviNeural",
    "or": "bn-IN-TanishaaNeural",  # High-fidelity Magadhan phonetic mapping for Odia
}


def map_odia_to_bengali(text: str) -> str:
    """
    Maps Odia Unicode characters (0x0B00–0x0B7F) to their Bengali equivalents (0x0980–0x09FF).
    Since both belong to the Eastern Indo-Aryan language subfamily with corresponding
    phonetic structures, this allows Microsoft Edge's neural engine to pronounce Odia
    with a natural native Eastern Indian accent rather than an English foreigner cadence.
    """
    res = []
    for ch in text:
        code = ord(ch)
        if 0x0B00 <= code <= 0x0B7F:
            b_code = code - 0x0B00 + 0x0980
            res.append(chr(b_code))
        else:
            res.append(ch)
    return "".join(res)


def sanitize_text(text: str) -> str:
    """Strips markdown formatting, headers, tables, asterisks, and bullets."""
    clean = re.sub(r"\|[\s:\-]+\|[\s:\-|]+", " ", text)
    clean = clean.replace("|", " ")
    clean = re.sub(r"#{1,6}\s+", "", clean)
    clean = re.sub(r"[-*_]{3,}", " ", clean)
    clean = re.sub(r"[*_]{1,2}(.*?)[*_]{1,2}", r"\1", clean)
    clean = re.sub(r"^[ \t]*[•\-*+][ \t]+", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"https?://\S+", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


@router.post("/tts")
async def generate_speech(req: TTSRequest):
    """
    Generates high-fidelity neural speech audio (MP3) using Microsoft Edge Neural TTS.
    Zero API keys required. Supports native accents for Indian languages.
    """
    clean_text = sanitize_text(req.text)
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty."
        )

    lang_code = (req.language or "en").lower()[:2]
    voice = VOICE_MAP.get(lang_code, "en-IN-NeerjaNeural")

    synth_text = clean_text
    if lang_code == "or" or any(0x0B00 <= ord(c) <= 0x0B7F for c in clean_text):
        synth_text = map_odia_to_bengali(clean_text)
        voice = "bn-IN-TanishaaNeural"

    try:
        communicate = edge_tts.Communicate(synth_text, voice)
        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        audio_bytes = audio_buffer.getvalue()
        if not audio_bytes:
            raise RuntimeError("Edge-TTS returned 0 audio bytes.")

        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Error in edge_tts neural audio generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Neural TTS generation error: {str(e)}"
        )
