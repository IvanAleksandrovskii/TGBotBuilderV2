# api/get_tests.py

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from core import log
from core.models.db_helper import db_helper
from core.models.quiz import Test


router = APIRouter(tags=["tests"])

class TestOut(BaseModel):
    id: UUID
    name: str
    description: str
    
    class Config:
        orm_mode = True


@router.get('/')
async def get_tests(db: AsyncSession = Depends(db_helper.session_getter)):
    try:
        query = await db.execute(Test.active().where(Test.is_psychological))
        tests = query.scalars().all()
    except Exception as e:
        log.exception(f"Error loading tests: {e}")
        raise HTTPException(status_code=500, detail="Error loading tests")
    
    return [TestOut(id=test.id, name=test.name, description=test.description) for test in tests]
