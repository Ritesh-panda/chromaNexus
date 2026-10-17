from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.chat import (
    ConversationResponse, ConversationCreate, MessageResponse, MessageCreate, CitationSchema
)
from backend.app.services.auth_service import get_current_patient
from backend.app.services.chat_service import process_clinical_chat_query
from backend.app.models.patient import Patient
from backend.app.models.chat import ChatConversation, ChatMessage

router = APIRouter(prefix="/chat", tags=["AI Clinical Assistant"])


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    threads = db.query(ChatConversation).filter(ChatConversation.patient_id == current_patient.id).order_by(ChatConversation.updated_at.desc()).all()
    return [
        ConversationResponse(
            id=t.id,
            title=t.title,
            lastMessageDate="Today",
            messageCount=len(t.messages)
        ) for t in threads
    ]


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: ConversationCreate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    thread = ChatConversation(
        patient_id=current_patient.id,
        title=conv_in.title or "New Clinical Conversation"
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return ConversationResponse(
        id=thread.id,
        title=thread.title,
        lastMessageDate="Just now",
        messageCount=0
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(
    conversation_id: str,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    conv = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.patient_id == current_patient.id
    ).first()
    if not conv:
        # Return empty list for new client thread
        return []

    return [
        MessageResponse(
            id=m.id,
            sender=m.sender,
            text=m.text,
            timestamp=m.timestamp,
            reasoningType=m.reasoning_type or "fact",
            citations=[CitationSchema(**c) for c in (m.citations or [])]
        ) for m in conv.messages
    ]


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
    conversation_id: str,
    msg_in: MessageCreate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    conv = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.patient_id == current_patient.id
    ).first()
    if not conv:
        conv = ChatConversation(
            id=conversation_id,
            patient_id=current_patient.id,
            title=msg_in.text[:30] + "..." if len(msg_in.text) > 30 else msg_in.text
        )
        db.add(conv)
        db.flush()

    # Extract bounded recent conversation history (last 6 messages = 3 turns) for follow-up resolution
    recent_history = [
        {"sender": m.sender, "text": m.text}
        for m in (conv.messages or [])
    ][-6:]

    # Save User message
    user_msg = ChatMessage(
        conversation_id=conv.id,
        sender="user",
        text=msg_in.text,
        timestamp=datetime.now().strftime("%I:%M %p")
    )
    db.add(user_msg)
    db.flush()

    # Process AI reasoning with conversation history and grounded citations
    ai_text, reasoning_type, citations = process_clinical_chat_query(
        db=db,
        patient=current_patient,
        query=msg_in.text,
        conversation_history=recent_history
    )

    ai_msg = ChatMessage(
        conversation_id=conv.id,
        sender="ai",
        text=ai_text,
        timestamp=datetime.now().strftime("%I:%M %p"),
        reasoning_type=reasoning_type,
        citations=citations
    )
    db.add(ai_msg)
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ai_msg)

    raw_citations: list[dict] = ai_msg.citations if isinstance(ai_msg.citations, list) else []
    return MessageResponse(
        id=ai_msg.id,
        sender=ai_msg.sender,
        text=ai_msg.text,
        timestamp=ai_msg.timestamp,
        reasoningType=ai_msg.reasoning_type,
        citations=[CitationSchema(**c) for c in raw_citations if isinstance(c, dict)]
    )
