# core/schemas/test_packs.py

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TestPackCreate(BaseModel):
    """
    Схема для создания нового TestPack.
    Передаем:
        - name: название пака
        - tests: список идентификаторов обычных тестов
        - custom_tests: список идентификаторов кастомных тестов
        - creator_id: идентификатор создателя пака
        - creator_username: имя пользователя создателя пака (опционально)
    """

    name: str = Field(..., min_length=1, max_length=100)
    tests: Optional[List[UUID]] = []
    custom_tests: Optional[List[UUID]] = []
    creator_id: int
    creator_username: Optional[str] = None


class TestPackUpdate(BaseModel):
    """
    Схема для обновления TestPack.
    По необходимости можно сделать все поля Optional,
    чтобы поддерживать частичное обновление (PATCH).
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    tests: Optional[List[UUID]] = []
    custom_tests: Optional[List[UUID]] = []


class TestPackOut(BaseModel):
    """
    Схема «ответа» при выдаче данных о паках.
    """
    id: UUID
    name: str
    creator_id: int
    tests: List[str]  # Названия тестов
    custom_tests: List[str]  # Названия кастомных тестов

    class Config:
        from_attributes = True
        # json_schema_extra = {
        #     "example": {
        #         "id": "123e4567-e89b-12d3-a456-426614174000",
        #         "name": "Название тест-пака",
        #         "creator_id": 123456,
        #         "tests": ["Тест 1", "Тест 2"],
        #         "custom_tests": ["Кастомный тест 1"],
        #     }
        # }


from .custom_test import CustomTestBase
from .test_response import TestOut


class CustomTestOut(CustomTestBase):
    id: UUID
    
    class Config:
        from_attributes = True


class TestPackOutExtended(TestPackOut):
    
    tests: List[TestOut]
    custom_tests: List[CustomTestOut]
