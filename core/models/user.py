# core/models/user.py

from sqlalchemy import String, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
# from .quiz_result import QuizResult


class User(Base):
    
    username: Mapped[str] = mapped_column(String, nullable=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)

    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_new_user: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # quiz_results: Mapped[list["QuizResult"]] = relationship(back_populates="user")

    # promocode: Mapped[str] = mapped_column(String, nullable=True)  # Gonna use XXXXXXXX format, Ex.:-'AX7K9PQ2'  # TODO: Migrate

    def __str__(self):
        return f"username={self.username}, chat_id={self.chat_id}"

    def __repr__(self) -> str:
        return self.__str__()
