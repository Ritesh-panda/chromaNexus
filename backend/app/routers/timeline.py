from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.timeline import TimelineEventResponse, TimelineEventCreate
from backend.app.services.auth_service import get_current_patient
from backend.app.models.patient import Patient
from backend.app.models.timeline import TimelineEvent

router = APIRouter(prefix="/timeline", tags=["Timeline"])


def format_timeline_response(event: TimelineEvent) -> TimelineEventResponse:
    return TimelineEventResponse(
        id=event.id,
        date=event.date,
        year=event.year,
        title=event.title,
        description=event.description,
        type=event.event_type,
        severity=event.severity or "medium",
        doctorName=event.doctor_name,
        facility=event.facility,
        sourceReportId=event.source_report_id,
        sourceReportTitle=event.source_report_title,
        connectedEntities=event.connected_entities or {}
    )


@router.get("", response_model=List[TimelineEventResponse])
def get_timeline(
    year: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    query = db.query(TimelineEvent).filter(TimelineEvent.patient_id == current_patient.id)
    if year:
        query = query.filter(TimelineEvent.year == year)
    if event_type and event_type != "all":
        if event_type == "medication_start":
            query = query.filter(TimelineEvent.event_type.in_(["medication_start", "medication_stop"]))
        else:
            query = query.filter(TimelineEvent.event_type == event_type)

    events = query.order_by(TimelineEvent.date.desc()).all()
    return [format_timeline_response(e) for e in events]


@router.get("/{event_id}", response_model=TimelineEventResponse)
def get_timeline_event(
    event_id: str,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    event = db.query(TimelineEvent).filter(
        TimelineEvent.id == event_id,
        TimelineEvent.patient_id == current_patient.id
    ).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timeline event not found")
    return format_timeline_response(event)


@router.post("", response_model=TimelineEventResponse, status_code=status.HTTP_201_CREATED)
def create_timeline_event(
    event_in: TimelineEventCreate,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    event = TimelineEvent(
        patient_id=current_patient.id,
        date=event_in.date,
        year=event_in.year,
        title=event_in.title,
        description=event_in.description,
        event_type=event_in.type,
        severity=event_in.severity or "medium",
        doctor_name=event_in.doctorName,
        facility=event_in.facility,
        source_report_id=event_in.sourceReportId,
        source_report_title=event_in.sourceReportTitle,
        connected_entities=event_in.connectedEntities or {}
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return format_timeline_response(event)
