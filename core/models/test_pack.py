# core/models/test_pack.py

from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Table, Column, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import select

from .base import Base
from .quiz import Test


# Association table for many-to-many relationship between TestPack and Test
test_pack_tests = Table(
    'test_pack_tests',
    Base.metadata,
    Column('test_pack_id', ForeignKey('test_packs.id'), primary_key=True),
    Column('test_id', ForeignKey('tests.id'), primary_key=True)
)


class TestPack(Base):
    """
    Represents a collection of tests that can be sent together.
    """
    __tablename__ = "test_packs"
    
    # Basic information
    name: Mapped[str] = mapped_column(String, nullable=False)
    
    # Creator information
    creator_id: Mapped[int] = mapped_column(nullable=False)  # Telegram user ID
    creator_username: Mapped[str] = mapped_column(String, nullable=True)  # Telegram username
    
    # Relationships
    tests: Mapped[List[Test]] = relationship(
        "Test",
        secondary=test_pack_tests,
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<TestPack(id={self.id}, name={self.name}, creator_id={self.creator_id})>"
    
    def __str__(self):
        return f"{self.name}"
    
    @property
    def test_count(self) -> int:
        """Returns the number of tests in the pack"""
        return len(self.tests)
    
    @hybrid_property
    def test_ids_string(self) -> str:
        """Returns string of test IDs for searching"""
        return ' '.join(str(test.id) for test in self.tests)

    @test_ids_string.expression
    def test_ids_string(cls):
        return (
            select(func.string_agg(Test.id.cast(String), ' '))
            .select_from(test_pack_tests.join(Test, test_pack_tests.c.test_id == Test.id))
            .where(test_pack_tests.c.test_pack_id == cls.id)
            .scalar_subquery()
        )
