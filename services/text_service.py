# services/text_service.py

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from core import log
from core.models.text import Text
from core.models.media import Media
from core.config import settings


class TextService:
    @staticmethod
    async def get_text_by_marker(context_marker: str, session: AsyncSession) -> Optional[Text]:
        try:
            result = await session.execute(
                select(Text).where(Text.context_marker == context_marker, Text.is_active == True)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            log.exception(f"Error in get_text_by_marker: {e}")
            return None

    @staticmethod
    async def get_media_urls(text: Text, session: AsyncSession) -> List[str]:
        media_urls = []
        await session.refresh(text, ['media_files'])
        for media in text.media_files:
            if media.is_active:
                full_url = f"{settings.media.base_url}/app/{media.file}"
                media_urls.append(full_url)
        return media_urls

    @staticmethod
    async def get_text_with_media(context_marker: str, session: AsyncSession) -> Optional[dict]:
        text = await TextService.get_text_by_marker(context_marker, session)
        if not text:
            return None

        media_urls = await TextService.get_media_urls(text, session)

        log.debug("Text content: %s", text.body)

        return {
            "text": text.body,
            "media_urls": media_urls,
            "chunk_size": text.reading_pagination if text.reading_pagination else None
        }

    @staticmethod
    async def get_default_media(session: AsyncSession) -> Optional[str]:
        try:
            result = await session.execute(
                select(Media)
                .join(Text.media_files)
                .where(Text.is_default_media == True, Media.is_active == True)
                .order_by(func.random())
                .limit(1)
            )
            default_media = result.scalar_one_or_none()
            if default_media:
                return f"{settings.media.base_url}/app/{default_media.file}"
            return None
        except Exception as e:
            log.exception(f"Error in get_default_media: {e}")
            return None
