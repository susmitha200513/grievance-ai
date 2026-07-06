from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models, auth

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role("admin", "officer")),
):
    total = db.query(models.Complaint).count()
    resolved = db.query(models.Complaint).filter(models.Complaint.status == "completed").count()
    pending = db.query(models.Complaint).filter(models.Complaint.status.in_(
        ["registered", "assigned", "accepted", "in_progress"]
    )).count()
    high_priority = db.query(models.Complaint).filter(
        models.Complaint.ai_priority.in_(["critical", "high"])
    ).count()

    by_area = dict(
        db.query(models.Complaint.area, func.count(models.Complaint.id))
        .group_by(models.Complaint.area).all()
    )
    by_department = dict(
        db.query(models.Complaint.ai_department, func.count(models.Complaint.id))
        .group_by(models.Complaint.ai_department).all()
    )
    by_type = dict(
        db.query(models.Complaint.complaint_type, func.count(models.Complaint.id))
        .group_by(models.Complaint.complaint_type).all()
    )

    return {
        "total_complaints": total,
        "resolved_complaints": resolved,
        "pending_complaints": pending,
        "high_priority_complaints": high_priority,
        "complaints_by_area": by_area,
        "complaints_by_department": by_department,
        "complaints_by_type": by_type,
    }


@router.get("/constituency-health-score")
def constituency_health_score(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role("admin", "officer")),
):
    """
    The standout differentiator: instead of just listing complaints, calculate
    a 0-100 health score per area/ward based on unresolved complaints, safety
    issues, resolution speed, and citizen satisfaction.
    """
    complaints = db.query(models.Complaint).filter(models.Complaint.area.isnot(None)).all()

    by_area = defaultdict(list)
    for c in complaints:
        by_area[c.area].append(c)

    results = []
    for area, items in by_area.items():
        total = len(items)
        unresolved = sum(1 for c in items if c.status != "completed")
        safety_issues = sum(
            1 for c in items if c.complaint_type in ("road", "street_light") and c.ai_priority in ("critical", "high")
        )
        dumping_issues = sum(1 for c in items if c.complaint_type == "illegal_dumping")

        # average resolution time in days (only for completed complaints)
        resolution_days = []
        for c in items:
            if c.status == "completed":
                delta = (c.updated_at - c.created_at).total_seconds() / 86400
                resolution_days.append(delta)
        avg_resolution = sum(resolution_days) / len(resolution_days) if resolution_days else None

        # average citizen rating
        ratings = [c.feedback.rating for c in items if c.feedback]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        # scoring: start at 100, subtract penalties
        score = 100.0
        score -= (unresolved / total) * 35 if total else 0
        score -= min(safety_issues * 5, 25)
        score -= min(dumping_issues * 3, 15)
        if avg_resolution is not None:
            score -= min(max(avg_resolution - 7, 0) * 1.5, 15)  # penalty beyond 7-day target
        if avg_rating is not None:
            score -= (5 - avg_rating) * 5  # lower rating -> bigger penalty
        score = max(0, min(100, round(score, 1)))

        if score >= 85:
            status_label = "Excellent"
        elif score >= 70:
            status_label = "Good"
        elif score >= 50:
            status_label = "Needs Attention"
        else:
            status_label = "Critical"

        results.append({
            "area": area,
            "health_score": score,
            "status": status_label,
            "total_complaints": total,
            "unresolved_complaints": unresolved,
            "avg_resolution_days": round(avg_resolution, 1) if avg_resolution else None,
            "avg_citizen_rating": round(avg_rating, 1) if avg_rating else None,
        })

    results.sort(key=lambda r: r["health_score"])
    return results
