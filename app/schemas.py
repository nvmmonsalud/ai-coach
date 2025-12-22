from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ScreeningSettingsIn(BaseModel):
    knockout_rules: List[str] = Field(default_factory=list)
    desired_industries: List[str] = Field(default_factory=list)
    work_authorization: Optional[str] = None


class JobRequirementIn(BaseModel):
    description: str
    mandatory: bool
    min_years_experience: Optional[float] = None


class JobSubmission(BaseModel):
    title: str
    function: str
    industry: str
    location: str
    seniority: str
    compensation: Optional[str] = None
    job_description: str
    screening_settings: ScreeningSettingsIn


class RubricItemOut(BaseModel):
    label: str
    weight: float
    requirement_type: str

    class Config:
        orm_mode = True


class JobRequirementOut(BaseModel):
    id: int
    description: str
    mandatory: bool
    min_years_experience: Optional[float] = None

    class Config:
        orm_mode = True


class ScreeningSettingsOut(BaseModel):
    knockout_rules: List[str]
    desired_industries: List[str]
    work_authorization: Optional[str]


class JobPostingOut(BaseModel):
    id: int
    title: str
    function: str
    industry: str
    location: str
    seniority: str
    compensation: Optional[str]
    job_description: str
    created_at: datetime
    requirements: List[JobRequirementOut]
    screening_settings: ScreeningSettingsOut
    rubric: List[RubricItemOut]


class AuditLogOut(BaseModel):
    action: str
    details: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class JobListingOut(BaseModel):
    id: int
    title: str
    industry: str
    location: str
    seniority: str
    created_at: datetime

    class Config:
        orm_mode = True
