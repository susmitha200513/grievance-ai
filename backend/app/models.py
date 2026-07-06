import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base


class RoleEnum(str, enum.Enum):
    citizen = "citizen"
    officer = "officer"
    admin = "admin"


class StatusEnum(str, enum.Enum):
    registered = "registered"
    assigned = "assigned"
    accepted = "accepted"
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"


class PriorityEnum(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(RoleEnum), default=RoleEnum.citizen, nullable=False)
    department = Column(String, nullable=True)  # for officers
    created_at = Column(DateTime, default=datetime.utcnow)

    complaints = relationship("Complaint", back_populates="citizen", foreign_keys="Complaint.citizen_id")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_code = Column(String, unique=True, index=True)  # GRV-2026-0001
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    complaint_type = Column(String, nullable=False)  # road, street_light, garbage, corruption, water
    image_path = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area = Column(String, nullable=True)  # ward / locality name

    # AI-derived fields
    ai_category = Column(String, nullable=True)
    ai_department = Column(String, nullable=True)
    ai_priority = Column(SAEnum(PriorityEnum), nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_sentiment = Column(String, nullable=True)
    ai_score = Column(Float, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON-encoded vector for duplicate detection

    status = Column(SAEnum(StatusEnum), default=StatusEnum.registered)
    duplicate_of_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    support_count = Column(Integer, default=1)  # how many citizens back this issue

    citizen_id = Column(Integer, ForeignKey("users.id"))
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    citizen = relationship("User", back_populates="complaints", foreign_keys=[citizen_id])
    history = relationship("ComplaintHistory", back_populates="complaint", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="complaint", uselist=False, cascade="all, delete-orphan")


class ComplaintHistory(Base):
    __tablename__ = "complaint_history"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    status = Column(SAEnum(StatusEnum), nullable=False)
    remarks = Column(Text, nullable=True)
    completion_image_path = Column(String, nullable=True)
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="history")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), unique=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="feedback")
