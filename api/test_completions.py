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
    status: Optional[CompletionStatus] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
    page_size: int = Query(
        20, ge=1, le=100, description="Количество записей на страницу"
    ),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    """
    Возвращает список тестов пользователя с полной информацией и пагинацией.

    - **user_id**: ID пользователя (из Telegram).
    - **status**: (необязательно) Фильтр по статусу: `IN_PROGRESS`, `COMPLETED`, `ABANDONED`.
    - **page**: Номер страницы (по умолчанию 1).
    - **page_size**: Количество записей на страницу (по умолчанию 20, максимум 100).
    - **Сортировка**: тесты сортируются по `updated_at` (самые новые сверху).
    """

    # Базовый запрос
    query = select(TestPackCompletion).where(TestPackCompletion.test_pack_creator_id == user_id)

    if status:
        query = query.where(TestPackCompletion.status == status)

    query = query.order_by(desc(TestPackCompletion.updated_at))

    # Подсчет общего количества записей
    total_query = select(func.count()).select_from(query.subquery())
    total_count = await session.execute(total_query)
    total_count = total_count.scalar()

    if total_count == 0:
        raise HTTPException(status_code=404, detail="Тесты не найдены")

    # Пагинация
    query = query.limit(page_size).offset((page - 1) * page_size)
    results = await session.execute(query)
    test_completions = results.scalars().all()

    # Рассчитываем количество страниц
    total_pages = (total_count + page_size - 1) // page_size  # округление вверх

    return {
        "total_count": total_count,
        "total_pages": total_pages,
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
