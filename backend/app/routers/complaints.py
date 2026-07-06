import os
import json
import shutil
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.ai import analyzer, duplicate_detection, scoring

router = APIRouter(prefix="/complaints", tags=["complaints"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _generate_complaint_code(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(models.Complaint).filter(
        models.Complaint.complaint_code.like(f"GRV-{year}-%")
    ).count()
    return f"GRV-{year}-{count + 1:04d}"


@router.post("", response_model=schemas.ComplaintOut)
def create_complaint(
    title: str = Form(...),
    description: str = Form(...),
    complaint_type: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    area: Optional[str] = Form(None),
    force_new: bool = Form(False),  # citizen confirmed "yes, still file a new one"
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role("citizen")),
):
    # 1. AI analysis (category, department, priority, summary, sentiment)
    ai_result = analyzer.analyze_complaint(description, complaint_type, area)

    # 2. Duplicate detection against complaints of the same type/area
    new_embedding = duplicate_detection.get_embedding(description)
    candidates = (
        db.query(models.Complaint)
        .filter(
            models.Complaint.complaint_type == complaint_type,
            models.Complaint.status != models.StatusEnum.rejected,
        )
    )
    if area:
        candidates = candidates.filter(models.Complaint.area == area)
    candidates = candidates.all()

    if not force_new:
        match, similarity = duplicate_detection.find_duplicate(description, new_embedding, candidates)
        if match:
            match.support_count += 1
            match.ai_score = scoring.compute_score(
                match.ai_priority.value if match.ai_priority else "medium",
                match.description,
                match.area,
                match.support_count,
                match.ai_sentiment or "neutral",
            )
            db.commit()
            db.refresh(match)
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "This issue has already been reported. It has been linked as additional support for the existing complaint.",
                    "existing_complaint_id": match.id,
                    "existing_complaint_code": match.complaint_code,
                    "similarity": round(similarity, 2),
                },
            )

    # 3. Save image if provided
    image_path = None
    if image is not None:
        ext = os.path.splitext(image.filename)[1]
        fname = f"{current_user.id}_{int(datetime.utcnow().timestamp())}{ext}"
        full_path = os.path.join(UPLOAD_DIR, fname)
        with open(full_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_path = f"/uploads/{fname}"

    # 4. Score
    score = scoring.compute_score(
        ai_result["priority"], description, area, support_count=1, sentiment=ai_result["sentiment"]
    )

    complaint = models.Complaint(
        complaint_code=_generate_complaint_code(db),
        title=title,
        description=description,
        complaint_type=complaint_type,
        image_path=image_path,
        latitude=latitude,
        longitude=longitude,
        area=area,
        ai_category=ai_result["category"],
        ai_department=ai_result["department"],
        ai_priority=ai_result["priority"],
        ai_summary=ai_result["summary"],
        ai_sentiment=ai_result["sentiment"],
        ai_score=score,
        embedding=json.dumps(new_embedding) if new_embedding else None,
        status=models.StatusEnum.registered,
        citizen_id=current_user.id,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    history = models.ComplaintHistory(
        complaint_id=complaint.id, status=models.StatusEnum.registered, changed_by_id=current_user.id
    )
    db.add(history)
    db.commit()

    return complaint


@router.get("", response_model=List[schemas.ComplaintOut])
def list_complaints(
    status: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    complaint_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    q = db.query(models.Complaint)

    if current_user.role == "citizen":
        q = q.filter(models.Complaint.citizen_id == current_user.id)
    elif current_user.role == "officer":
        q = q.filter(models.Complaint.assigned_officer_id == current_user.id)
    # admin sees everything

    if status:
        q = q.filter(models.Complaint.status == status)
    if area:
        q = q.filter(models.Complaint.area == area)
    if complaint_type:
        q = q.filter(models.Complaint.complaint_type == complaint_type)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (models.Complaint.title.ilike(like))
            | (models.Complaint.complaint_code.ilike(like))
            | (models.Complaint.description.ilike(like))
        )

    return q.order_by(models.Complaint.ai_score.desc().nullslast(), models.Complaint.created_at.desc()).all()


@router.get("/{complaint_id}", response_model=schemas.ComplaintOut)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if current_user.role == "citizen" and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this complaint")
    return complaint


@router.post("/{complaint_id}/assign", response_model=schemas.ComplaintOut)
def assign_officer(
    complaint_id: int,
    officer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role("admin")),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    officer = db.query(models.User).filter(models.User.id == officer_id, models.User.role == "officer").first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")

    complaint.assigned_officer_id = officer.id
    complaint.status = models.StatusEnum.assigned
    db.commit()

    history = models.ComplaintHistory(
        complaint_id=complaint.id, status=models.StatusEnum.assigned, changed_by_id=current_user.id
    )
    db.add(history)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.post("/{complaint_id}/status", response_model=schemas.ComplaintOut)
def update_status(
    complaint_id: int,
    payload: schemas.StatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role("officer", "admin")),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if current_user.role == "officer" and complaint.assigned_officer_id != current_user.id:
        raise HTTPException(status_code=403, detail="This complaint is not assigned to you")

    valid_statuses = [s.value for s in models.StatusEnum]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    complaint.status = payload.status
    db.commit()

    history = models.ComplaintHistory(
        complaint_id=complaint.id,
        status=payload.status,
        remarks=payload.remarks,
        changed_by_id=current_user.id,
    )
    db.add(history)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.post("/{complaint_id}/feedback")
def submit_feedback(
    complaint_id: int,
    payload: schemas.FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role("citizen")),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint or complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.status != models.StatusEnum.completed:
        raise HTTPException(status_code=400, detail="Feedback can only be given after completion")

    feedback = models.Feedback(
        complaint_id=complaint.id, rating=payload.rating, comment=payload.comment
    )
    db.add(feedback)
    db.commit()
    return {"message": "Thank you for your feedback"}


@router.get("/{complaint_id}/timeline")
def get_timeline(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if current_user.role == "citizen" and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    history = (
        db.query(models.ComplaintHistory)
        .filter(models.ComplaintHistory.complaint_id == complaint_id)
        .order_by(models.ComplaintHistory.created_at.asc())
        .all()
    )
    return [
        {"status": h.status, "remarks": h.remarks, "created_at": h.created_at}
        for h in history
    ]
