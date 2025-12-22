from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

from .database import Base


class Recruiter(Base):
    __tablename__ = "recruiters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="recruiter")
    jobs = relationship("JobPosting", back_populates="recruiter")
    audit_logs = relationship("AuditLog", back_populates="recruiter")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    function = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    location = Column(String, nullable=False)
    seniority = Column(String, nullable=False)
    compensation = Column(String, nullable=True)
    job_description = Column(Text, nullable=False)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    recruiter = relationship("Recruiter", back_populates="jobs")
    requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete")
    screening_setting = relationship(
        "ScreeningSetting", back_populates="job", uselist=False, cascade="all, delete"
    )
    rubric_items = relationship("RubricItem", back_populates="job", cascade="all, delete")


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    description = Column(Text, nullable=False)
    mandatory = Column(Boolean, nullable=False, default=True)
    min_years_experience = Column(Float, nullable=True)

    job = relationship("JobPosting", back_populates="requirements")


class ScreeningSetting(Base):
    __tablename__ = "screening_settings"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    knockout_rules = Column(Text, nullable=True)
    desired_industries = Column(Text, nullable=True)
    work_authorization = Column(String, nullable=True)

    job = relationship("JobPosting", back_populates="screening_setting")


class RubricItem(Base):
    __tablename__ = "rubric_items"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    label = Column(String, nullable=False)
    weight = Column(Float, nullable=False, default=1.0)
    requirement_type = Column(String, nullable=False)

    job = relationship("JobPosting", back_populates="rubric_items")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id"), nullable=False)
    action = Column(String, nullable=False)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    recruiter = relationship("Recruiter", back_populates="audit_logs")
    job = relationship("JobPosting")
