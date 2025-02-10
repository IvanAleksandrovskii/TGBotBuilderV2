import datetime
from sqlalchemy import select
import asyncio
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties
from core import log, settings
from core.models import (
    db_helper,
    TestPackCompletion,
)
from core.models.test_pack_completion import CompletionStatus


async def send_notification(
    bot: Bot,
    abandoned_completion: TestPackCompletion,
    text: str,
    notify_creator: bool = False,
):
    creator_id = abandoned_completion.test_pack_creator_id
    user_id = abandoned_completion.user_id
    if notify_creator:
        await bot.send_message(creator_id, text)
    else:
        await bot.send_message(user_id, text)


async def get_abandoned_tests(session):
    current_time = datetime.datetime.now(datetime.UTC)
    timedelta = current_time - datetime.timedelta(hours=5)  # TODO: Make it configurable (( ! ))

    query = select(TestPackCompletion).where(
        TestPackCompletion.status == CompletionStatus.IN_PROGRESS,
        TestPackCompletion.updated_at < timedelta,
    )
    results = await session.execute(query)
    abandoned_completions = results.scalars().all()
    return abandoned_completions


async def main():
    # Создаем собственный экземпляр бота для скрипта
    session = AiohttpSession(timeout=60)
    bot = Bot(
        token=settings.bot.token,
        session=session,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    try:
        bot_username = (await bot.get_me()).username
        async with db_helper.db_session() as session:
            abandoned_completions = await get_abandoned_tests(session)
            log.info(f"Found {len(abandoned_completions)} abandoned test completions")

            current_time = datetime.datetime.now(datetime.UTC)
            modified_completions = []

            for completion in abandoned_completions:
                # Anti flood
                await asyncio.sleep(0.05)

                if completion.updated_at < current_time - datetime.timedelta(hours=6):  # TODO: Make it configurable (( ! ))
                    log.info(f"Marking completion {completion.id} as abandoned")
                    await send_notification(
                        bot,
                        completion,
                        "Одно из прохождений набора тестов было заброшено.",
                        notify_creator=True,
                    )
                    completion.status = CompletionStatus.ABANDONED
                    modified_completions.append(completion)
                else:
                    log.info(f"Sending reminder for completion {completion.id}")
                    await send_notification(
                        bot,
                        completion,
                        f"Вы не завершили прохождение набора тестов. Пожалуйста, продолжите (перейти по ссылке) -> https://t.me/{bot_username}?start={completion.test_pack_id}",
                    )

            # Batch update all modified completions
            if modified_completions:
                session.add_all(modified_completions)
                await session.commit()
                log.info(
                    f"Updated {len(modified_completions)} completions to ABANDONED status"
                )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
