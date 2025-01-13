# core/models/custom_test/py

import uuid
from typing import Optional, List

from sqlalchemy import ForeignKey, Integer, String, Boolean, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import event

from .base import Base


class CustomTest(Base):
    """
    Represents a custom test.
    """
    __tablename__ = "custom_tests"
    
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
    Вызывается до фактического удаления CustomTest из БД.
    """
    from sqlalchemy.orm import Session
    
    from .test_pack import TestPack  # , test_pack_custom_tests
    from .custom_test import CustomTest  # чтобы можно было фильтровать
    session = Session(bind=connection)

    # Находим те TestPack, где присутствует именно этот CustomTest
    # (он ещё есть в M2M-таблице, поэтому join сработает)
    test_packs = session.query(TestPack)\
        .join(TestPack.custom_tests)\
        .filter(CustomTest.id == target.id)\
        .all()

    for test_pack in test_packs:
        # Сейчас test_pack.custom_tests всё ещё содержит target.
        # Но если «удалить target» - значит из test_pack.custom_tests пропадёт target
        # Нужно проверить, не останется ли других.
        # На этот момент ORM-сессия ещё не обновлена, так что
        # len(test_pack.custom_tests) может быть N, где N>=1

        # Поэтому надёжнее проверить «кроме target есть кто-то ещё?»
        other_custom_tests = [ct for ct in test_pack.custom_tests if ct.id != target.id]
        if not test_pack.tests and not other_custom_tests:
            # Удаляем TestPack, т.к. он точно станет пустым
            session.delete(test_pack)

    session.commit()
    session.close()
