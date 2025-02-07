# api/ai_transcript.py

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import log
from core.models import (
    db_helper,
    TestPackCompletion,
)
from core.models.test_pack_completion import CompletionStatus
from services.ai_services import get_ai_response

from prompt import prompt


router = APIRouter()


@router.get(
    "/ai_transcription/",
    summary="Get AI transcription for test pack completion's psychological tests",
)
async def ai_transcription(
    user_id: int = Query(..., description="User ID"),
    test_pack_completion_id: str = Query(..., description="Test pack completion UUID"),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    try:
        query = select(TestPackCompletion).where(
            TestPackCompletion.id == test_pack_completion_id,
        )

        result = await session.execute(query)
        test_pack_completion = result.scalar_one_or_none()

        if test_pack_completion is None:
            raise HTTPException(
                status_code=404, detail="Test pack completion not found."
            )

        if test_pack_completion.test_pack_creator_id != user_id:
            raise HTTPException(
                status_code=403, detail="You are not allowed to access this resource."
            )

        if test_pack_completion.ai_transcription is not None:
            return test_pack_completion.ai_transcription

        if test_pack_completion.status != CompletionStatus.COMPLETED:
            raise HTTPException(
                status_code=400, detail="Test pack completion is not completed."
            )

        test_results = test_pack_completion.completed_tests
        psychological_test_results = [
            test for test in test_results if test["type"] == "test"
        ]

        if len(psychological_test_results) == 0:
            raise HTTPException(
                status_code=404, detail="No psychological test results found."
            )

        ai_request_text = ""

        ai_request_text += prompt
        for test_result in psychological_test_results:
            ai_request_text += f"\n\n{test_result['result']}"

        result = await get_ai_response(session, ai_request_text)

        if result.content == "No successful response from any AI models.":
            raise HTTPException(
                status_code=404, detail="No successful response from any AI models."
            )

        test_pack_completion.ai_transcription = result.content
        await session.commit()

        return result.content

    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating the AI transcription. Please try again.",
        )


@router.get(
    "/ai_transcription_clear/",
    summary="Clear AI transcription for test pack completion's psychological tests",
)
async def ai_transcription_clear(
    user_id: int = Query(..., description="User ID"),
    test_pack_completion_id: str = Query(..., description="Test pack completion UUID"),
    session: AsyncSession = Depends(db_helper.session_getter),
):
    try:
        query = select(TestPackCompletion).where(
            TestPackCompletion.id == test_pack_completion_id,
        )

        result = await session.execute(query)
        test_pack_completion = result.scalar_one_or_none()

        if test_pack_completion is None:
            raise HTTPException(
                status_code=404, detail="Test pack completion not found."
            )

        if test_pack_completion.test_pack_creator_id != user_id:
            raise HTTPException(
                status_code=403, detail="You are not allowed to access this resource."
            )

        if test_pack_completion.ai_transcription is not None:
            test_pack_completion.ai_transcription = None
            await session.commit()

        return Response(status_code=204)

    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while clearing the AI transcription. Please try again.",
        )
