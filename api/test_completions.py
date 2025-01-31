# api/test_completions.py
from typing import Optional  # List

from fastapi import APIRouter, Query, HTTPException, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from core.models import db_helper
from core.models.test_pack_completion import TestPackCompletion, CompletionStatus


router = APIRouter()


@router.get("/test-completions", summary="Получить тесты пользователя с пагинацией")
async def get_user_test_completions(
    user_id: int,
    status: Optional[str] = Query(
        None, description="Фильтр по статусу (IN_PROGRESS, COMPLETED, ABANDONED)"
    ),
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
    page_size: int = Query(
        20, ge=1, le=100, description="Количество записей на страницу"
    ),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    # 🔹 Convert status string to Enum (handling case sensitivity)
    status_enum = None
    if status:
        try:
            status_enum = CompletionStatus[status.upper()]  # Ensure case consistency
        except KeyError:
            valid_values = ", ".join([s.name for s in CompletionStatus])
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status value. Must be one of: {valid_values}",
            )

    # Query DB
    query = select(TestPackCompletion).where(TestPackCompletion.test_pack_creator_id == user_id)
    if status_enum:
        query = query.where(TestPackCompletion.status == status_enum)
    query = query.order_by(desc(TestPackCompletion.updated_at))

    # Fetch data
    total_query = select(func.count()).select_from(query.subquery())
    total_count = await session.execute(total_query)
    total_count = total_count.scalar()

    if total_count == 0:
        # raise HTTPException(status_code=404, detail="Тесты не найдены")
        return {
            "total_count": 0,
            "total_pages": 0,
            "current_page": 1,
            "page_size": page_size,
            "data": [],
        }

    # Pagination
    query = query.limit(page_size).offset((page - 1) * page_size)
    results = await session.execute(query)
    test_completions = results.scalars().all()

    return {
        "total_count": total_count,
        "total_pages": (total_count + page_size - 1) // page_size,
        "current_page": page,
        "page_size": page_size,
        "data": [
            {
                "test_pack_id": str(tc.test_pack_id),
                "status": tc.status.value,
                "updated_at": tc.updated_at,
                "pending_tests": tc.pending_tests,
                "completed_tests": tc.completed_tests,
                "user_data": tc.user_data,
            }
            for tc in test_completions
        ],
    }
