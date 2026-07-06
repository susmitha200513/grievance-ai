from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/officers", tags=["officers"])


@router.get("", response_model=list[schemas.UserOut])
def list_officers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role("admin")),
):
    return db.query(models.User).filter(models.User.role == "officer").all()


@router.get("/{officer_id}/performance")
def officer_performance(
    officer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role("admin", "officer")),
):
    complaints = db.query(models.Complaint).filter(models.Complaint.assigned_officer_id == officer_id).all()
    completed = [c for c in complaints if c.status == "completed"]

    resolution_days = [
        (c.updated_at - c.created_at).total_seconds() / 86400 for c in completed
    ]
    ratings = [c.feedback.rating for c in completed if c.feedback]

    return {
        "officer_id": officer_id,
        "total_assigned": len(complaints),
        "total_completed": len(completed),
        "avg_resolution_days": round(sum(resolution_days) / len(resolution_days), 1) if resolution_days else None,
        "avg_citizen_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
    }
