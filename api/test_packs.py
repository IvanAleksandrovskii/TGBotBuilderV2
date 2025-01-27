# api/test_packs.py

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from core.models import db_helper
from core.models.test_pack import TestPack
from core.models.quiz import Test
from core.models.custom_test import CustomTest
from core.schemas.test_packs import (
    TestPackOut, 
    TestPackCreate, 
    TestPackUpdate,
    TestPackOutExtended,
    CustomTestOut,
    TestOut,
)


router = APIRouter(prefix="/test-packs", tags=["test-packs"])


@router.get("/{creator_id}", response_model=List[TestPackOut])
async def list_test_packs(
    creator_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=100),
):
    """
    Получить список своих TestPack с постраничной разбивкой.
    
    page: Номер страницы (>=1)
    limit: Сколько элементов на странице (по умолчанию 10, максимум 100)
    """
    offset = (page - 1) * limit

    async with db_helper.db_session() as session:
        # Допустим, вы храните creator_id для каждого пака.
        # Если нужно выбрать только паки текущего пользователя, фильтруем:
        query = select(TestPack).order_by(TestPack.updated_at.desc()).where(TestPack.creator_id == creator_id)
        # Считаем общее кол-во при желании
        # total = await session.scalar(select(func.count(TestPack.id))) 

        packs_result = await session.execute(query.offset(offset).limit(limit))
        packs = packs_result.scalars().all()

        # Преобразуем в Pydantic-модели
        packs_out = []
        for pack in packs:
            packs_out.append(TestPackOut(
                id=pack.id,
                name=pack.name,
                creator_id=pack.creator_id,
                test_count=pack.test_count,
                tests=[test.name for test in pack.tests],  # предполагаем relationship
                custom_tests=[ct.name for ct in pack.custom_tests]  # предполагаем relationship
            ))
    return packs_out


@router.post("/", response_model=TestPackOut, status_code=201)
async def create_test_pack(
    data: TestPackCreate  # TODO: user id sould be in the request data && creator_username should be too but optional
):
    """
    Создать новый TestPack. 
    """
    async with db_helper.db_session() as session:
        # TODO: Проверим, что у пользователя не превышен лимит в 5 паков
        # packs_count = await session.scalar(
        #     select(func.count(TestPack.id)).where(TestPack.creator_id == current_user.id)
        # )
        # if packs_count >= 5:
        #     raise HTTPException(status_code=400, detail="Maximum of 5 test packs already created.")

        # Забираем объекты Test по списку ID
        selected_tests = []
        if data.tests:
            tests_result = await session.execute(select(Test).where(Test.id.in_(data.tests)))
            selected_tests = tests_result.scalars().all()

        # Забираем объекты CustomTest по списку ID
        selected_custom_tests = []
        if data.custom_tests:
            custom_tests_result = await session.execute(
                select(CustomTest).where(CustomTest.id.in_(data.custom_tests))
            )
            selected_custom_tests = custom_tests_result.scalars().all()

        new_pack = TestPack(
            name=data.name,
            creator_id=data.creator_id,
            creator_username=data.creator_username,
            tests=selected_tests, 
            custom_tests=selected_custom_tests
        )

        session.add(new_pack)
        await session.commit()
        await session.refresh(new_pack)  # чтобы получить id и обновлённые поля

        return TestPackOut(
            id=new_pack.id,
            name=new_pack.name,
            creator_id=new_pack.creator_id,
            test_count=new_pack.test_count,
            tests=[t.name for t in new_pack.tests],
            custom_tests=[ct.name for ct in new_pack.custom_tests]
        )


# @router.get("/test_pack/{pack_id}", response_model=TestPackOut)
# async def get_test_pack(pack_id: UUID):
#     """
#     Получить конкретный TestPack по ID.
#     """
#     async with db_helper.db_session() as session:
#         query = select(TestPack).where(TestPack.id == pack_id)
#         result = await session.execute(query)
#         pack = result.scalar_one_or_none()

#         if not pack:
#             raise HTTPException(status_code=404, detail="Test pack not found")

#         return TestPackOut(
#             id=pack.id,
#             name=pack.name,
#             creator_id=pack.creator_id,
#             test_count=pack.test_count,
#             tests=[t.name for t in pack.tests],
#             custom_tests=[ct.name for ct in pack.custom_tests]
#         )

@router.get("/test_pack/{pack_id}", response_model=TestPackOutExtended)
async def get_test_pack(pack_id: UUID):
    """
    Получить конкретный TestPack по ID и отдать объекты тестов (id, name, description).
    """
    async with db_helper.db_session() as session:
        query = select(TestPack).where(TestPack.id == pack_id)
        result = await session.execute(query)
        pack = result.scalar_one_or_none()

        if not pack:
            raise HTTPException(status_code=404, detail="Test pack not found")

        # Формируем списки обычных и кастомных тестов
        regular_tests_out = [
            TestOut(
                id=test.id,
                name=test.name,
                description=test.description
            )
            for test in pack.tests
        ]
        custom_tests_out = [
            CustomTestOut(
                id=ct.id,
                name=ct.name,
                description=ct.description,
                creator_id=ct.creator_id,
            )
            for ct in pack.custom_tests
        ]

        return TestPackOutExtended(
            id=pack.id,
            name=pack.name,
            creator_id=pack.creator_id,
            test_count=pack.test_count,
            tests=regular_tests_out,
            custom_tests=custom_tests_out,
        )


@router.put("/test_pack/{pack_id}", response_model=TestPackOut)
@router.patch("/test_pack/{pack_id}", response_model=TestPackOut) 
async def update_test_pack(pack_id: UUID, data: TestPackUpdate):
    """
    Обновить TestPack (PUT/PATCH). 
    - PUT может предполагать полное обновление, а 
    - PATCH — частичное.
    Здесь, для упрощения, используем один метод.
    """
    async with db_helper.db_session() as session:
        query = select(TestPack).where(TestPack.id == pack_id)
        result = await session.execute(query)
        pack = result.scalar_one_or_none()
        if not pack:
            raise HTTPException(status_code=404, detail="Test pack not found")

        # Обновляем поля, если они переданы
        if data.name is not None:
            pack.name = data.name

        if data.tests is not None:
            tests_result = await session.execute(select(Test).where(Test.id.in_(data.tests)))
            pack.tests = tests_result.scalars().all()

        if data.custom_tests is not None:
            custom_tests_result = await session.execute(
                select(CustomTest).where(CustomTest.id.in_(data.custom_tests))
            )
            pack.custom_tests = custom_tests_result.scalars().all()

        # Здесь можно проверить права: pack.creator_id == current_user.id

        session.add(pack)
        await session.commit()
        await session.refresh(pack)

        return TestPackOut(
            id=pack.id,
            name=pack.name,
            creator_id=pack.creator_id,
            test_count=pack.test_count,
            tests=[t.name for t in pack.tests],
            custom_tests=[ct.name for ct in pack.custom_tests]
        )


@router.delete("/test_pack/{pack_id}")
async def delete_test_pack(pack_id: UUID):
    """
    Удалить TestPack.
    """
    async with db_helper.db_session() as session:
        query = select(TestPack).where(TestPack.id == pack_id)
        result = await session.execute(query)
        pack = result.scalar_one_or_none()

        if not pack:
            raise HTTPException(status_code=404, detail="Test pack not found")

        # Проверка: pack.creator_id == current_user.id ?
        try:
            await session.delete(pack)
            await session.commit()
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Test pack not found during delete")

    return {"detail": "Test pack deleted successfully"}
