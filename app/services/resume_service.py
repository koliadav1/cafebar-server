from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.resume import Resume, ResumeStatus
from app.schemas import resume as schemas

# Отправить резюме
async def submit_resume(resume_data: schemas.ResumeCreate, db: AsyncSession) -> Resume:
    resume = Resume(**resume_data.model_dump())
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume

# Ответить на резюме
async def respond_to_resume(resume_id: int, response_text: str, db: AsyncSession) -> Resume:
    result = await db.execute(select(Resume).where(Resume.resume_id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Резюме не найдено")
    resume.response = response_text
    await db.commit()
    await db.refresh(resume)
    return resume

# Изменить статус резюме
async def change_resume_status(resume_id: int, status: ResumeStatus, db: AsyncSession) -> Resume:
    result = await db.execute(select(Resume).where(Resume.resume_id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Резюме не найдено")
    resume.status = status
    await db.commit()
    await db.refresh(resume)
    return resume

# Удалить резюме
async def delete_resume(resume_id: int, db: AsyncSession):
    result = await db.execute(select(Resume).where(Resume.resume_id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Резюме не найдено")
    await db.delete(resume)
    await db.commit()
    return {"detail": "Резюме удалено"}

# Получить все резюме
async def get_all_resumes(db: AsyncSession) -> List[Resume]:
    result = await db.execute(select(Resume))
    return result.scalars().all()