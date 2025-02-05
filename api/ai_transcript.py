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


router = APIRouter()


# TODO: Дописать шаблон отвтета
prompt: str = """Отвечай по-русски. Я провожу кинологические психологические тесты для собак, где сами их хозяева проходят за них тесты, 
отвечая на поведенческие вопросы за своих питомцев, главная задача определить подходит ли их собака для работы или 
нет и стоит ли брать ее в рабочий коллектив или это может повредить другим собакам или самой собаке. Какие рекомендации мы можем дать хозяину, 
чтобы поддерживать мотивацию собаки, быстро адаптировать ее в коллектив.
Представь, что ты психолог. 
Чтобы не рушить атмосферу "психологии переноса", отвечай не используя слов собака или что либо другое относящееся к теме животных, 
говори о личности, собаки очень похожи на людей, говори именно не обо мне, а о личности, о результатах которой идет речь. Нельзя использовать
слова хозяин/питомец или другие связанные с этим слова, можно говорить только работодатель и сотрудник.
Тесты разделены на блоки.
1 блок "мышление" в нем тест критического мышления Старки, 
2 блок "эмоциональное состояние" в нем шкала депрессии Бека,  шкала тревожности Бека, шкала безнадежности Бека 
3 блок "поведение" в нем тест Томаса-Килманна, тест на стрессоустойчивость, экспресс диагностика стресса
4 блок "коммуникация"
Отвечай по структуре:
Перечисли только те методики, которые проходил питомец (используй слово сотрудник), возьми их из результатов.
Напиши фразу: "После тестирования были получены результаты:"
Выводы по тестам пиши в предложенном выше порядке обозначая название блока, не пиши слово блок.
После подведи емкий итог, с позиции психодиагностики, сделай общий вывод по результатам тестов, напиши о качестве работы данной личности, подойдет ли она на работу или нет, 
о рисках, которые это за собой влечет для остального коллектива.
Дай отдельно рекомендации для хозяйна.
Далее результаты тестов:
"""


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
