# api/get_custom_tests.py

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core import log
from core.models.db_helper import db_helper
from core.models.custom_test import CustomTest
from core.schemas import CustomTestResponse


router = APIRouter(tags=["custom-tests"])


@router.get("/custom_test/{test_id}", response_model=CustomTestResponse)
async def get_custom_test(
    test_id: str, creator_id: int, db: AsyncSession = Depends(db_helper.session_getter)
):
    query = await db.execute(
        select(CustomTest)
        .where(CustomTest.id == test_id)
        .options(selectinload(CustomTest.custom_questions))
    )
    test = query.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Custom test not found.")

    if test.creator_id != creator_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. You don't have permission to view this test.",
        )

    questions = test.custom_questions

    return CustomTestResponse(
        id=test.id,
        name=test.name,
        description=test.description,
        creator_id=test.creator_id,
        allow_back=test.allow_back,
        questions=[
            {
                "question_text": question.question_text,
                "is_quiz_type": question.is_quiz_type,
                "answers": [
                    {
                        "text": getattr(question, f"answer{i}_text"),
                        "score": getattr(question, f"answer{i}_score"),
                    }
                    for i in range(1, 7)
                    if getattr(question, f"answer{i}_text") is not None
                ],
            }
            for question in questions
        ],
    )


@router.get("/custom_tests/{creator_id}", response_model=list[CustomTestResponse])
async def get_custom_tests_by_creator_id(creator_id: int, db: AsyncSession = Depends(db_helper.session_getter)):
    
    # Запрос на выборку тестов, созданных указанным пользователем
    query = select(CustomTest).where(CustomTest.creator_id == creator_id).options(selectinload(CustomTest.custom_questions))
    result = await db.execute(query)
    tests = result.scalars().all()

    log.debug(f"Get custom tests by creator_id: {creator_id}")
    log.debug(f"Found {len(tests)} tests.")
    log.debug(f"Tests: {tests}")

    if not tests:
        return []
    
    return [
        CustomTestResponse(
            id=test.id,
            name=test.name,
            description=test.description,
            creator_id=test.creator_id,
            allow_back=test.allow_back,
            questions=[
                {
                    "question_text": question.question_text,
                    "is_quiz_type": question.is_quiz_type,
                    "answers": [
                        {
                            "text": getattr(question, f"answer{i}_text"),
                            "score": getattr(question, f"answer{i}_score"),
                        }
                        for i in range(1, 7)
                        if getattr(question, f"answer{i}_text") is not None
                    ],
                }
                for question in test.custom_questions
            ],
        )
        for test in tests
    ]
