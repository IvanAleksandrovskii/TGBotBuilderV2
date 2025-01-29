# core/models/test_pack_completion.py

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CompletionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    # TODO: Implement later:
    # ABANDONED = "abandoned"
    # ARCHIVED = "archived"  # USE active=False instead
    # ORIGIN_DELETED = "origin_deleted"
    # USER_DECLINED = "user_declined"


class TestPackCompletion(Base):
    """
    Tracks user's progress through a test pack including both standard and custom tests.
    """

    __tablename__ = "test_pack_completions"

    # User information
    user_id: Mapped[int] = mapped_column(nullable=False)  # Telegram user ID
    user_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )  # User contact info

    # Test pack reference
    test_pack_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    test_pack_creator_id: Mapped[int] = mapped_column(nullable=False)

    # Progress tracking
    status: Mapped[CompletionStatus] = mapped_column(
        SQLEnum(CompletionStatus), default=CompletionStatus.IN_PROGRESS, nullable=False
    )

    # Tests to complete (JSON structure)
    tests_to_complete: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Detailed progress data (JSON structure)
    progress_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, default=dict, nullable=True
    )

    """
    # Структура user_data должна содержать:
    user_data: dict = {
        "phone": "",
        "first_name": "",
        "last_name": "",
        "username": ""
    }

    # Структура tests_to_complete должна содержать:
    tests_to_complete = {
        "tests_to_complete": {
            "tests": [{
                "test_name": "Test name",
                "test_id": "test_id",
            },],
        "custom_tests": [{
                "test_name": "Test name",
                "test_id": "test_id",
            },],
        }
    }

    # Структура progress_data должна содержать:
    progress_data = {
        "progress_data": {
            "completed_tests": {
                "test_<UUID>": {
                    "test_name": "Test name",
                    "completed_at": "ISO datetime",
                    "result_text": "текст результата"
                }
            },
            "completed_custom_tests": {
                "custom_<UUID>": {
                    "test_name": "Test name",
                    "completed_at": "ISO datetime",
                    "total_score": 0,
                    "score": 0,
                    "free_answers": [
                        {
                            "question_text": "Text of the question",
                            "answer_text": "пользовательский ввод",
                            "timestamp": "ISO datetime"
                        },
                    ],
                    "test_answers": [
                        {
                            "question_text": "Text of the question",
                            "answer_text": "Answer text",
                            "score": 0,
                            "timestamp": "ISO datetime"
                        },
                    ]
                }
            }
        }
    }
    """

    @classmethod
    async def create_test_pack_completion(
        cls,
        *,
        session: AsyncSession,
        user_id: int,
        user_data: Dict[str, Any],
        test_pack_id: uuid.UUID,
        test_pack_creator_id: int,
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
            tests_to_complete={
                "tests_to_complete": {
                    "tests": tests,
                    "custom_tests": custom_tests,
                }
            },
        )
        session.add(new_completion)
        await session.commit()
        await session.refresh(new_completion)
        return new_completion

    @property
    def completion_percentage(self) -> float:
        """
        Рассчитывает процент завершения тест-пака на основе завершённых тестов.
        """
        total_tests = len(
            self.tests_to_complete.get("tests_to_complete", {}).get("tests", [])
        )
        total_custom_tests = len(
            self.tests_to_complete.get("tests_to_complete", {}).get("custom_tests", [])
        )
        total_tests_count = total_tests + total_custom_tests

        completed_tests = len(
            self.progress_data.get("progress_data", {}).get("completed_tests", {})
        )
        completed_custom_tests = len(
            self.progress_data.get("progress_data", {}).get(
                "completed_custom_tests", {}
            )
        )
        completed_total = completed_tests + completed_custom_tests

        if (total_tests_count == 0) and (completed_total == 0):
            return 0.0
        if (total_tests_count == 0) and (completed_total > 0):
            return 100.0

        return round((completed_total / total_tests_count) * 100, 2)

    async def add_test_result(
        self,
        *,
        session: AsyncSession,
        test_id: str,
        test_name: str,
        test_type: str,
        result_text: Optional[str] = None,
        free_answers: Optional[list[Dict[str, Any]]] = None,
        test_answers: Optional[list[Dict[str, Any]]] = None,
    ):
        """
        Добавляет результат теста в progress_data.

        :param session: Асинхронная сессия SQLAlchemy.
        :param test_id: ID теста.
        :param test_name: Название теста.
        :param test_type: "tests" (психологические) или "custom_tests" (кастомные).
        :param result_text: Только для психологических тестов - текстовый результат.
        :param free_answers: Только для кастомных тестов - пользовательские ответы.
        :param test_answers: Только для кастомных тестов - оценки за тест.
        """
        if test_type not in {"tests", "custom_tests"}:
            raise ValueError("test_type должен быть 'tests' или 'custom_tests'")

        if not self.progress_data:
            self.progress_data = {
                "progress_data": {"completed_tests": {}, "completed_custom_tests": {}}
            }

        completed_section = (
            self.progress_data["progress_data"]["completed_custom_tests"]
            if test_type == "custom_tests"
            else self.progress_data["progress_data"]["completed_tests"]
        )

        test_entry = {
            "test_name": test_name,
            "completed_at": datetime.utcnow().isoformat(),
        }

        if test_type == "tests":
            if result_text is None:
                raise ValueError("result_text обязателен для психологических тестов")
            test_entry["result_text"] = result_text
        else:
            if free_answers is None or test_answers is None:
                raise ValueError(
                    "free_answers и test_answers обязательны для кастомных тестов"
                )
            test_entry["free_answers"] = free_answers
            test_entry["test_answers"] = test_answers

        completed_section[test_id] = test_entry

        await session.commit()

    async def remove_test_by_id(
        self, *, session: AsyncSession, test_id: str, test_type: str
    ):
        """
        Удаляет тест по UUID из tests_to_complete и сохраняет изменения в БД.

        :param session: Асинхронная сессия SQLAlchemy.
        :param test_id: ID теста (UUID).
        :param test_type: Тип теста ("tests" или "custom_tests").
        """
        if test_type not in {"tests", "custom_tests"}:
            raise ValueError("test_type должен быть 'tests' или 'custom_tests'")

        tests_list = self.tests_to_complete.get("tests_to_complete", {}).get(
            test_type, []
        )

        # Фильтруем список, исключая тест с переданным ID
        updated_tests = [t for t in tests_list if t["test_id"] != test_id]

        # Обновляем JSON-структуру
        self.tests_to_complete["tests_to_complete"][test_type] = updated_tests

        # Фиксируем изменения в БД
        await session.commit()

    def __repr__(self):
        return f"<TestPackCompletion(id={self.id}, user={self.user_id}, status={self.status})>"
