from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.resume import Resume, ResumeStatus
from app.schemas import resume as schemas

#Отправить резюме
def submit_resume(resume_data: schemas.ResumeCreate, db: Session) -> Resume:
    resume = Resume(**resume_data.model_dump())
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume

#Ответить на резюме
def respond_to_resume(resume_id: int, response_text: str, db: Session) -> Resume:
    resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Резюме не найдено")
    resume.response = response_text
    db.commit()
    db.refresh(resume)
    return resume

#Изменить статус резюме
def change_resume_status(resume_id: int, status: ResumeStatus, db: Session) -> Resume:
    resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Резюме не найдено")
    resume.status = status
    db.commit()
    db.refresh(resume)
    return resume

#Удалить резюме
def delete_resume(resume_id: int, db: Session):
    resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Резюме не найдено")
    db.delete(resume)
    db.commit()
    return {"detail": "Резюме удалено"}

#Получить все резюме
def get_all_resumes(db: Session) -> List[Resume]:
    return db.query(Resume).all()