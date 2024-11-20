# core/models/sent_test.py

from sqlalchemy import Column, DateTime, String, BigInteger, Enum
from sqlalchemy.dialects.postgresql import UUID
import enum

from .base import Base


class TestStatus(enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    REJECTED = "rejected"

class SentTest(Base):
    __tablename__ = "sent_tests"

    sender_id = Column(BigInteger, nullable=False)
    sender_username = Column(String, nullable=False)

    test_id = Column(UUID(as_uuid=True), nullable=False)

    test_name = Column(String, nullable=False)

    receiver_id = Column(BigInteger, nullable=True)
    receiver_username = Column(String, nullable=False)

    status = Column(Enum(TestStatus), default=TestStatus.SENT)

    delivered_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    result_score = Column(String, nullable=True)  # May contain a score or a dict of scores with category keys
    result_text = Column(String, nullable=True)
