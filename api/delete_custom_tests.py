# api/delete_custom_tests.py

from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.models import db_helper
from core.models.custom_test import CustomTest


router = APIRouter(tags=["custom-tests"])


@router.delete("/custom_test/{test_id}")
async def delete_custom_test(
    test_id: UUID,
    creator_id: int,
    db: AsyncSession = Depends(db_helper.session_getter)
):
    # Получение теста
    query = await db.execute(
        select(CustomTest).where(CustomTest.id == test_id).options(selectinload(CustomTest.custom_questions))
    )
    test = query.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Custom test not found")

    # Проверка на совпадение creator_id
    if test.creator_id != creator_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. You don't have permission to delete this test."
        )

    # Удаление теста
    await db.delete(test)
    await db.commit()

    return {"status_code": 204, "message": "Custom test deleted."}
