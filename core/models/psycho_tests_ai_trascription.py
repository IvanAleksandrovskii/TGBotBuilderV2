# core/models/psycho_tests_ai_trascription.py

from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PsycoTestsAITranscription(Base):
    
    sender_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reciver_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    tests_ids: Mapped[str] = mapped_column(String, nullable=False)  # tests_ids splitted with & symbol
    
    transcription: Mapped[str] = mapped_column(String, nullable=False)
