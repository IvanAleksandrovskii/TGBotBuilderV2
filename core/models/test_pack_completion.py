# core/models/test_pack_completion.py

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any  # , Optional

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import JSON, ARRAY, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from core import log


class CompletionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# TODO: Add completion date and time ?
class TestPackCompletion(Base):
    """
    Tracks user's progress through a test pack including both standard and custom tests.
    """

    __tablename__ = "test_pack_completions"

    __table_args__ = (Index("idx_test_pack_creator_id", "test_pack_creator_id"),)

    # User information
    user_id: Mapped[int] = mapped_column(nullable=False)  # Telegram user ID
    user_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )  # User contact info

    # Test pack reference
    test_pack_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    test_pack_creator_id: Mapped[int] = mapped_column(nullable=False)
    test_pack_name: Mapped[str] = mapped_column(nullable=False)

    # Progress tracking
    status: Mapped[CompletionStatus] = mapped_column(
        SQLEnum(CompletionStatus), default=CompletionStatus.IN_PROGRESS, nullable=False
    )

    pending_tests: Mapped[List[Dict[str, Any]]] = mapped_column(
        ARRAY(JSON), default=list
    )
    completed_tests: Mapped[List[Dict[str, Any]]] = mapped_column(
        ARRAY(JSON), default=list
    )

    ai_transcription: Mapped[str] = mapped_column(nullable=True)

    # TODO: Use this instead ???
    # pending_tests: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    # completed_tests: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)

    @classmethod
    async def create_test_pack_completion(
        cls,
        *,
        session: AsyncSession,
        user_id: int,
        user_data: Dict[str, Any],
        test_pack_id: uuid.UUID,
        test_pack_creator_id: int,
        test_pack_name: str,
        tests: list[Dict[str, Any]],
        custom_tests: list[Dict[str, Any]],
    ) -> "TestPackCompletion":
        """
        Создаёт новую запись TestPackCompletion в базе данных.

        :param session: SQLAlchemy сессия.
        :param user_id: Telegram ID пользователя.
        :param user_data: Данные пользователя (имя, телефон и т. д.).
        :param test_pack_id: UUID тест-пака.
        :param test_pack_creator_id: ID создателя тест-пака.
        :param tests: Список обычных тестов (словарь с test_name и test_id).
        :param custom_tests: Список кастомных тестов (словарь с test_name и test_id).
        :return: Новый объект TestPackCompletion.
        """
        new_completion = cls(
            user_id=user_id,
            user_data=user_data,
            test_pack_id=test_pack_id,
            test_pack_creator_id=test_pack_creator_id,
            test_pack_name=test_pack_name,
            pending_tests=[
                *[
                    {"type": "test", "id": t["id"], "name": t["test_name"]}
                    for t in tests
                ],
                *[
                    {"type": "custom", "id": ct["id"], "name": ct["test_name"]}
                    for ct in custom_tests
                ],
            ],
            completed_tests=[],
            ai_transcription=None,
        )

        log.debug(f"New test pack completion: {new_completion}")
        log.debug(
            f"New test pack completion: pending_tests={new_completion.pending_tests}, completed_tests={new_completion.completed_tests}"
        )

        session.add(new_completion)
        await session.commit()
        await session.refresh(new_completion)
        return new_completion

    @property
    def completion_percentage(self) -> float:
        total = len(self.pending_tests) + len(self.completed_tests)
        if total == 0:
            return 0.0
        return round(len(self.completed_tests) / total * 100, 2)

    async def remove_test_by_id(self, session, test_id: str):
        self.pending_tests = [t for t in self.pending_tests if t["id"] != test_id]
        await session.commit()

    def __repr__(self):
        return f"<TestPackCompletion(id={self.id}, user={self.user_id}, status={self.status})>"
