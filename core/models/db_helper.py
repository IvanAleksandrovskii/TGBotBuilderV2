# core/models/db_helper.py

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncEngine,
    async_sessionmaker, AsyncSession
)
from core import log, settings


class DataBaseHelper:
    def __init__(self, url: str, echo: bool, pool_size: int, max_overflow: int):
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session_getter(self) -> AsyncSession:  # type: ignore 
        async with self.session_factory() as session:
            yield session

    @asynccontextmanager
    async def db_session(self) -> AsyncSession: # type: ignore
        async with self.session_factory() as session:
            try:
                yield session

            except Exception as e:
                log.exception(e)
                await session.rollback()

            finally:
                await session.close()


db_helper = DataBaseHelper(
    url=settings.db.url,
    echo=settings.db.echo,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
)
