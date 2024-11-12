# core/models/quiz_result.py

from sqlalchemy import ForeignKey, Integer, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User
    from .quiz import Test

class QuizResult(Base):
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), type_=UUID(as_uuid=True))
    test_id: Mapped[UUID] = mapped_column(ForeignKey("tests.id"), type_=UUID(as_uuid=True))
    
    is_psychological: Mapped[bool] = mapped_column(Boolean, default=False)
    
    category_id: Mapped[Integer] = mapped_column(Integer, nullable=True)  # TODO: NEW FIELD Number of category (1-4 for example) to summ all answers with the same category
    
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    result_text: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped["User"] = relationship(back_populates="quiz_results")
    test: Mapped["Test"] = relationship(back_populates="quiz_results")

    def __repr__(self):
        return f"QuizResult(id={self.id}, user_id={self.user_id}, test_id={self.test_id}, score={self.score})"
    
    def __str__(self):
        return f"QuizResult(id={self.id}, user_id={self.user_id}, test_id={self.test_id}, score={self.score})"
