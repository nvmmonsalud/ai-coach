from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from . import models
from .database import get_db


class CurrentUser:
    def __init__(self, user: models.Recruiter):
        self.user = user

    def ensure_can_access_job(self, job: models.JobPosting):
        if self.user.role == "admin":
            return
        if job.recruiter_id != self.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job",
            )


async def get_current_user(
    db: Session = Depends(get_db), x_user_id: int = Header(..., alias="X-User-Id")
) -> CurrentUser:
    user = db.query(models.Recruiter).filter(models.Recruiter.id == x_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Recruiter not found. Use a valid X-User-Id header.",
        )
    return CurrentUser(user=user)
