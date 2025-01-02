# core/admin/db_helper.py

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker

from core import settings, log


class AsyncDataBaseHelper:
    def __init__(self, url: str, echo: bool):
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )

    async def dispose(self):
        log.info("Disposing SQLAlchemy engine for admin...")
        await self.engine.dispose()

    @asynccontextmanager
    async def session_getter(self) -> AsyncSession: # type: ignore
        async with self.session_factory() as session:
            try:
                yield session
            finally:
                await session.close()


async_sqladmin_db_helper = AsyncDataBaseHelper(
    url=settings.db.url,
    echo=False,
)
