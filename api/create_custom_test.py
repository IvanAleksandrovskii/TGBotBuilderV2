# api/custom_tests.py

from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import db_helper
from core.models.custom_test import CustomTest, CustomQuestion
from core.schemas.custom_test import CustomTestCreate


router = APIRouter()


@router.post("/custom_test/")
async def create_custom_test(test_data: CustomTestCreate, db: AsyncSession = Depends(db_helper.session_getter)):
    if not test_data.questions:
        raise HTTPException(status_code=400, detail="A test must have at least one question.")

    new_test = CustomTest(
        name=test_data.name,
        description=test_data.description,
        creator_id=test_data.creator_id,
        allow_back=test_data.allow_back,
    )

    for question_data in test_data.questions:
        if question_data.is_quiz_type and not question_data.answers:
            raise HTTPException(
                status_code=400,
                detail=f"Quiz question '{question_data.question_text}' must have answers."
            )

        if not question_data.is_quiz_type and question_data.answers:
            raise HTTPException(
                status_code=400,
                detail=f"Free-form question '{question_data.question_text}' should not have answers."
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
        new_test.custom_questions.append(new_question)

    db.add(new_test)
    await db.commit()
    await db.refresh(new_test)

    return {"id": str(new_test.id), "name": new_test.name, "description": new_test.description}
