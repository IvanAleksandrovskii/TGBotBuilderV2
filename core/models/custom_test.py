# core/models/custom_test/py

import uuid
from typing import Optional, List

from sqlalchemy import ForeignKey, Integer, String, Boolean, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, object_session

from sqlalchemy import event

from .base import Base


class CustomTest(Base):
    """
    Represents a custom test.
    """
    __tablename__ = "custom_tests"
    
    __table_args__ = (Index("idx_custom_test_creator_id", "creator_id"),)
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    creator_id: Mapped[int] = mapped_column(nullable=False)  # Telegram user ID
    
    allow_back: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_questions: Mapped[List["CustomQuestion"]] = relationship(back_populates="custom_test", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CustomTest(id={self.id}, name={self.name})>"
    
    def __str__(self):
        return f"{self.name}"


class CustomQuestion(Base):
    """
    Represents a custom question in a custom test with up to 6 inline answers of a free text type.
    """
    __tablename__ = "custom_questions"


    question_text: Mapped[str] = mapped_column(String, nullable=False)
    is_quiz_type: Mapped[bool] = mapped_column(Boolean, default=False)
    
    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("custom_tests.id"))
    custom_test: Mapped[CustomTest] = relationship(back_populates="custom_questions")
    
    # Inline answers (6 sets of answer text and score)
    answer1_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    answer1_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    answer2_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    answer2_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    answer3_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    answer3_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    answer4_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    answer4_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    answer5_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    answer5_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    answer6_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    answer6_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint('(answer1_text IS NOT NULL AND answer1_score IS NOT NULL) OR '
                        '(answer1_text IS NULL AND answer1_score IS NULL)',
                        name='check_answer1_completeness'),
        CheckConstraint('(answer2_text IS NOT NULL AND answer2_score IS NOT NULL) OR '
                        '(answer2_text IS NULL AND answer2_score IS NULL)',
                        name='check_answer2_completeness'),
        CheckConstraint('(answer3_text IS NOT NULL AND answer3_score IS NOT NULL) OR '
                        '(answer3_text IS NULL AND answer3_score IS NULL)',
                        name='check_answer3_completeness'),
        CheckConstraint('(answer4_text IS NOT NULL AND answer4_score IS NOT NULL) OR '
                        '(answer4_text IS NULL AND answer4_score IS NULL)',
                        name='check_answer4_completeness'),
        CheckConstraint('(answer5_text IS NOT NULL AND answer5_score IS NOT NULL) OR '
                        '(answer5_text IS NULL AND answer5_score IS NULL)',
                        name='check_answer5_completeness'),
        CheckConstraint('(answer6_text IS NOT NULL AND answer6_score IS NOT NULL) OR '
                        '(answer6_text IS NULL AND answer6_score IS NULL)',
                        name='check_answer6_completeness'),
    )

    def __repr__(self):
        return f"<CustomQuestion(id={self.id}, question_text={self.question_text[:50]})>"

    def __str__(self):
        return f"{self.question_text[:50]}"


@event.listens_for(CustomTest, 'before_delete')
def delete_empty_test_pack(mapper, connection, target):
    """
    Срабатывает перед удалением CustomTest из БД.
    Удаляем TestPack, если он станет пустым (без обычных и без кастомных тестов).
    """
    from .test_pack import TestPack
    
    # Получаем ту же ORM-сессию, где идёт удаление:
    session = object_session(target)
    if not session:
        return  # бывает, если объект "detached"

    # Находим TestPack, у которых в M2M-таблице есть данный custom_test
    # (так как сейчас связь ещё не удалена).
    test_packs = (
        session.query(TestPack)
        .join(TestPack.custom_tests)
        .filter(CustomTest.id == target.id)
        .all()
    )

    for test_pack in test_packs:
        # Проверяем, есть ли в пакете обычные тесты:
        has_regular_tests = bool(test_pack.tests)
        
        # Проверяем, есть ли в пакете ещё кастомные тесты (кроме удаляемого)
        other_ct = [ct for ct in test_pack.custom_tests if ct.id != target.id]

        # Если нет регулярных тестов и других кастомных не останется,
        # то удаляем сам test_pack
        if not has_regular_tests and not other_ct:
            session.delete(test_pack)

    # НЕ делаем session.commit(), не закрываем сессию!
    # Всё произойдёт автоматически во внешнем коде (эндпоинт, сервис и т.д.)
