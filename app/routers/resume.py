from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.database import get_db
from app.schemas import resume as schemas
from app.services import resume_service as service
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(
    prefix="/resumes",
    tags=["Резюме"]
)

# Создание резюме
@router.post("/", response_model=schemas.ResumeOut, status_code=201)
async def submit_resume(resume: schemas.ResumeCreate, db: AsyncSession = Depends(get_db)) -> Resume:
    return await service.submit_resume(resume, db)

# Ответ на резюме
@router.put("/{resume_id}/response", response_model=schemas.ResumeOut)
async def respond_to_resume(resume_id: int,
                      response: schemas.ResumeUpdateResponse, 
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)) -> Resume:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут отвечать на резюме")
    return await service.respond_to_resume(resume_id, response.response, db)

# Изменение статуса резюме
@router.put("/{resume_id}/status", response_model=schemas.ResumeOut)
async def update_resume_status(resume_id: int,
                         status: schemas.ResumeUpdateStatus, 
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)) -> Resume:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут менять статус резюме")
    return await service.change_resume_status(resume_id, status.status, db)

# Удаление резюме
@router.delete("/{resume_id}")
async def delete_resume(resume_id: int,
                  db: AsyncSession = Depends(get_db),
                  current_user: User = Depends(get_current_user)) -> dict[str, str]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут удалять резюме")
    return await service.delete_resume(resume_id, db)

# Получение всех резюме
@router.get("/", response_model=list[schemas.ResumeOut])
async def get_resumes(db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)) -> List[Resume]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут просматривать резюме")

    return await service.get_all_resumes(db)