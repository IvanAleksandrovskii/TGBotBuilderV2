# core/models/quiz.py

from typing import List, Optional, Dict
import uuid
import json

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Boolean, CheckConstraint, JSON
from fastapi_storages.integrations.sqlalchemy import FileType

from .base import Base
from .quiz_result import QuizResult
from services import quiz_storage


"""
The system should support two distinct types of results:

Single-graph results for basic assessments
Single-graph and Multi-graph results for comprehensive psychological tests, allowing the display of multiple visualizations in one report

Also random question ordering and a strict question ordering system should be supported.
"""
class Test(Base):
    """
    Represents a quiz test.
    """
    __tablename__ = "tests"
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    
    # Ordering for tests priority in tests db selection and execution
    position: Mapped[int] = mapped_column(Integer, nullable=True)
    
    is_psychological: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # If many graphs in test result
    multi_graph_results: Mapped[bool] = mapped_column(Boolean, default=False)
    # New field to store category names dictionary
    category_names: Mapped[Dict] = mapped_column(JSON, nullable=True, default=dict)
    
    
    description: Mapped[str] = mapped_column(String, nullable=False)
    picture = mapped_column(FileType(storage=quiz_storage))
    
    allow_back: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_play_again: Mapped[bool] = mapped_column(Boolean, default=True)
    
    questions: Mapped[List["Question"]] = relationship(back_populates="test", cascade="all, delete-orphan")
    results: Mapped[List["Result"]] = relationship(back_populates="test", cascade="all, delete-orphan")
    quiz_results: Mapped[list["QuizResult"]] = relationship(back_populates="test")
    
    def __repr__(self):
        return f"<Test(id={self.id}, name={self.name})>"
    
    def __str__(self):
        return f"{self.name}"
    
    def get_category_name(self, category_id: int) -> str:
        """Get category name by ID, return default if not found"""
        try:
            names = self.category_names or {}
            if isinstance(names, str):
                names = json.loads(names)
            return names.get(str(category_id), f"Category {category_id}")
        except (json.JSONDecodeError, AttributeError):
            return f"Category {category_id}"
    
    
    # TODO: Unimplemented
    def set_category_name(self, category_id: int, name: str) -> None:
        """Set name for a category ID"""
        try:
            names = self.category_names
            if names is None:
                names = {}
            if isinstance(names, str):
                names = json.loads(names)
            names[str(category_id)] = name
            self.category_names = names
        except (json.JSONDecodeError, AttributeError):
            # In case of an error, create a new dictionary only with the new value
            self.category_names = {str(category_id): name}


class Question(Base):
    """
    Represents a question in a quiz test with up to 6 inline answers.
    """
    __tablename__ = "questions"
    
    # Could be same to mix up questions or not to follow the order
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    question_text: Mapped[str] = mapped_column(String, nullable=False)
    picture = mapped_column(FileType(storage=quiz_storage))

    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tests.id"))
    test: Mapped[Test] = relationship(back_populates="questions")

    intro_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
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
        return f"<Question(id={self.id}, question_text={self.question_text})>"

    def __str__(self):
        return f"{self.question_text}"


class Result(Base):
    """
    Represents a result group for a quiz test.
    """
    __tablename__ = "results"
    
    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tests.id"))
    picture = mapped_column(FileType(storage=quiz_storage))
    
    category_id: Mapped[Integer] = mapped_column(Integer, nullable=True)  # Number of category (1-4 for example) to summ all answers with the same category
    
    min_score: Mapped[int] = mapped_column(Integer, nullable=False)
    
    max_score: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    
    test: Mapped[Test] = relationship(back_populates="results")
    
    def __repr__(self):
        return f"<Result(id={self.id}, test_id={self.test_id}, min_score={self.min_score}, max_score={self.max_score})>"
    
    def __str__(self):
        return f"{self.test_id} - {self.min_score} - {self.max_score}"
