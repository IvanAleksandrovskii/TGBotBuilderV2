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


@router.put("/custom_tests/{test_id}", response_model=CustomTestResponse)
async def update_custom_test(
    test_id: UUID,
    test_data: CustomTestUpdate,
    db: AsyncSession = Depends(db_helper.session_getter)
):
    # Get existing test
    query = await db.execute(
    select(CustomTest).where(CustomTest.id == test_id).options(selectinload(CustomTest.custom_questions))
    )
    test = query.scalar_one_or_none()
    
    if not test:
        raise HTTPException(status_code=404, detail="Custom test not found")

    # Update basic test fields if provided
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
        
        # Create new questions
        for question_data in test_data.questions:
            if question_data.is_quiz_type and not question_data.answers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Quiz question '{question_data.question_text}' must have answers"
                )

            if not question_data.is_quiz_type and question_data.answers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Free-form question '{question_data.question_text}' should not have answers"
                )

            new_question = CustomQuestion(
                question_text=question_data.question_text,
                is_quiz_type=question_data.is_quiz_type,
                answer1_text=(question_data.answers[0].text if question_data.answers and len(question_data.answers) > 0 else None),
                answer1_score=(question_data.answers[0].score if question_data.answers and len(question_data.answers) > 0 else None),
                answer2_text=(question_data.answers[1].text if question_data.answers and len(question_data.answers) > 1 else None),
                answer2_score=(question_data.answers[1].score if question_data.answers and len(question_data.answers) > 1 else None),
                answer3_text=(question_data.answers[2].text if question_data.answers and len(question_data.answers) > 2 else None),
                answer3_score=(question_data.answers[2].score if question_data.answers and len(question_data.answers) > 2 else None),
                answer4_text=(question_data.answers[3].text if question_data.answers and len(question_data.answers) > 3 else None),
                answer4_score=(question_data.answers[3].score if question_data.answers and len(question_data.answers) > 3 else None),
                answer5_text=(question_data.answers[4].text if question_data.answers and len(question_data.answers) > 4 else None),
                answer5_score=(question_data.answers[4].score if question_data.answers and len(question_data.answers) > 4 else None),
                answer6_text=(question_data.answers[5].text if question_data.answers and len(question_data.answers) > 5 else None),
                answer6_score=(question_data.answers[5].score if question_data.answers and len(question_data.answers) > 5 else None),
            )
            test.custom_questions.append(new_question)

    # Save changes
    await db.commit()
    await db.refresh(test)

    # Prepare response
    questions = test.custom_questions
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
                } for i in range(1, 7)
                if getattr(question, f"answer{i}_text") is not None
            ]
        } for question in questions]
    )
