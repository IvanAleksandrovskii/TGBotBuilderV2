# api/update_custom_test.py

from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.models import db_helper
from core.models.custom_test import CustomTest, CustomQuestion
from core.schemas.custom_test import CustomTestUpdate, CustomTestResponse


router = APIRouter()


@router.put("/custom_test_update/{test_id}", response_model=CustomTestResponse)
async def update_custom_test(
    test_id: UUID,
    test_data: CustomTestUpdate,
    db: AsyncSession = Depends(db_helper.session_getter)
):
    # Получение существующего теста
    query = await db.execute(
        select(CustomTest).where(CustomTest.id == test_id).options(selectinload(CustomTest.custom_questions))
    )
    test = query.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Custom test not found")

    # Проверка на совпадение creator_id
    if test.creator_id != test_data.creator_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. You don't have permission to edit this test."
        )

    # Обновление данных теста
    if test_data.name is not None:
        test.name = test_data.name
    if test_data.description is not None:
        test.description = test_data.description
    if test_data.allow_back is not None:
        test.allow_back = test_data.allow_back

    # Обновление вопросов
    if test_data.questions is not None:
        for question in test.custom_questions:
            await db.delete(question)

        for question_data in test_data.questions:
            new_question = CustomQuestion(
                question_text=question_data.question_text,
                is_quiz_type=question_data.is_quiz_type,
                answer1_text=question_data.answers[0].text if question_data.answers and len(question_data.answers) > 0 else None,
                answer1_score=question_data.answers[0].score if question_data.answers and len(question_data.answers) > 0 else None,
                # Аналогично для других ответов...
            )
            test.custom_questions.append(new_question)

    await db.commit()
    await db.refresh(test)

    return CustomTestResponse(
        id=test.id,
        name=test.name,
        description=test.description,
        creator_id=test.creator_id,
        allow_back=test.allow_back,
        questions=[{
            "question_text": question.question_text,
            "is_quiz_type": question.is_quiz_type,
            "answers": [
                {
                    "text": getattr(question, f"answer{i}_text"),
                    "score": getattr(question, f"answer{i}_score")
                } for i in range(1, 7) if getattr(question, f"answer{i}_text") is not None
            ]
        } for question in test.custom_questions]
    )
