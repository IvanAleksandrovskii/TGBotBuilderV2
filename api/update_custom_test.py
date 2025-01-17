# api/update_custom_test.py

from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional

from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.models import db_helper
from core.models.custom_test import CustomTest, CustomQuestion
from core.schemas.custom_test import CustomTestUpdate, CustomTestResponse


router = APIRouter()


# Schema definitions
class AnswerUpdate(BaseModel):
    text: str
    score: float

class QuestionUpdate(BaseModel):
    question_text: str
    is_quiz_type: bool = True
    answers: List[AnswerUpdate]

class CustomTestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    allow_back: Optional[bool] = None
    questions: Optional[List[QuestionUpdate]] = None

class CustomTestResponse(BaseModel):
    id: UUID
    name: str
    description: str
    creator_id: int
    allow_back: bool
    questions: List[QuestionUpdate]

router = APIRouter()

@router.put("/custom_test_update/{test_id}", response_model=CustomTestResponse)
async def update_custom_test(
    test_id: UUID,
    test_data: CustomTestUpdate,
    creator_id: int,
    db: AsyncSession = Depends(db_helper.session_getter)
):
    # Fetch existing test with questions
    query = await db.execute(
        select(CustomTest)
        .where(CustomTest.id == test_id)
        .options(selectinload(CustomTest.custom_questions))
    )
    test = query.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Custom test not found")

    if test.creator_id != creator_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. You don't have permission to edit this test."
        )

    # Update basic test information
    if test_data.name is not None:
        test.name = test_data.name
    if test_data.description is not None:
        test.description = test_data.description
    if test_data.allow_back is not None:
        test.allow_back = test_data.allow_back

    # Update questions if provided
    if test_data.questions is not None:
        # Remove existing questions
        for question in test.custom_questions:
            await db.delete(question)
        await db.flush()

        # Add new questions
        for question_data in test_data.questions:
            # Validate number of answers
            # if not 2 <= len(question_data.answers) <= 6:
            #     raise HTTPException(
            #         status_code=422,
            #         detail="Each question must have between 2 and 6 answers"
            #     )

            # Create new question
            new_question = CustomQuestion(
                test_id=test.id,
                question_text=question_data.question_text,
                is_quiz_type=question_data.is_quiz_type
            )

            # Add answers
            for i, answer in enumerate(question_data.answers, start=1):
                setattr(new_question, f"answer{i}_text", answer.text)
                setattr(new_question, f"answer{i}_score", answer.score)

            db.add(new_question)

    await db.commit()
    await db.refresh(test)

    # Prepare response
    return CustomTestResponse(
        id=test.id,
        name=test.name,
        description=test.description,
        creator_id=test.creator_id,
        allow_back=test.allow_back,
        questions=[
            QuestionUpdate(
                question_text=q.question_text,
                is_quiz_type=q.is_quiz_type,
                answers=[
                    AnswerUpdate(
                        text=getattr(q, f"answer{i}_text"),
                        score=getattr(q, f"answer{i}_score")
                    )
                    for i in range(1, 7)
                    if getattr(q, f"answer{i}_text") is not None
                ]
            )
            for q in test.custom_questions
        ]
    )
