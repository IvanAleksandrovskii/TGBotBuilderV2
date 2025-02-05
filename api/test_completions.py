# api/test_completions.py

from typing import Optional  # List

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func  # , or_

from core.models import db_helper
from core.models.test_pack_completion import TestPackCompletion, CompletionStatus

router = APIRouter()


@router.get(
    "/test-completions/",
    summary="Получить тесты пользователя с пагинацией и список тестпаков",
)
async def get_user_test_completions(
    user_id: int,
    status: Optional[str] = Query(
        None, description="Фильтр по статусу (IN_PROGRESS, COMPLETED, ABANDONED)"
    ),
    test_pack: Optional[str] = Query(
        None, description="UUID (или название) тест-пака для фильтрации прохождений"
    ),
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
    page_size: int = Query(
        20, ge=1, le=100, description="Количество записей на страницу"
    ),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    # 🔹 Конвертация строки статуса в Enum (обработка регистра)
    status_enum = None
    if status:
        try:
            status_enum = CompletionStatus[status.upper()]
        except KeyError:
            valid_values = ", ".join([s.name for s in CompletionStatus])
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status value. Must be one of: {valid_values}",
            )

    # Формируем базовый запрос для прохождений пользователя
    query = select(TestPackCompletion).where(
        TestPackCompletion.test_pack_creator_id == user_id
    )
    if status_enum:
        query = query.where(TestPackCompletion.status == status_enum)
    # Фильтр по тест-паку (здесь фильтруем по test_pack_id, можно добавить или по названию)
    if test_pack:
        query = query.where(TestPackCompletion.test_pack_id == test_pack)
        # Если требуется фильтрация и по названию, можно использовать:
        # query = query.where(
        #     or_(
        #         TestPackCompletion.test_pack_id == test_pack,
        #         TestPackCompletion.test_pack_name.ilike(f"%{test_pack}%")
        #     )
        # )

    query = query.order_by(desc(TestPackCompletion.updated_at))

    # Получаем общее количество записей (без пагинации)
    total_query = select(func.count()).select_from(query.subquery())
    total_count_result = await session.execute(total_query)
    total_count = total_count_result.scalar()

    # Если записей нет – возвращаем пустой ответ с пустым списком тестпаков
    if total_count == 0:
        return {
            "total_count": 0,
            "total_pages": 0,
            "current_page": 1,
            "page_size": page_size,
            "data": [],
            "test_pack_list": [],
            "test_pack_list": [],
        }

    # Запрос для получения списка уникальных тестпаков (UUID и название) с учётом фильтров
    test_pack_query = select(
        TestPackCompletion.test_pack_id, TestPackCompletion.test_pack_name
    ).where(TestPackCompletion.test_pack_creator_id == user_id)
    if status_enum:
        test_pack_query = test_pack_query.where(
            TestPackCompletion.status == status_enum
        )
    # В данном запросе фильтр по test_pack не применяется, чтобы вернуть все тестпаки для пользователя
    test_pack_query = test_pack_query.distinct()
    distinct_result = await session.execute(test_pack_query)
    # Формируем список объектов с uuid и названием
    test_pack_list = [
        {"test_pack_id": str(row[0]), "test_pack_name": row[1]}
        for row in distinct_result.all()
    ]

    # Пагинация – ограничиваем и смещаем выборку
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
                "id": str(tc.id),
                "test_pack_id": str(tc.test_pack_id),
                "test_pack_name": tc.test_pack_name,
                "status": tc.status.value.upper(),
                "created_at": tc.created_at,  # TODO: new
                "updated_at": tc.updated_at,
                "pending_tests": tc.pending_tests,
                "completed_tests": tc.completed_tests,
                "completion_percentage": tc.completion_percentage,  # TODO: new
                "user_data": tc.user_data,
                "ai_transcription": tc.ai_transcription,  # TODO: new, nullable
            }
            for tc in test_completions
        ],
        "test_pack_list": test_pack_list,
    }
