# core/models/promocode.py

from sqlalchemy import String, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Promocode(Base):
    """Stores promocodes generated for users"""
    code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # description: Mapped[str] = mapped_column(String, nullable=True)


class PromoRegistration(Base):
    """Stores information about users who registered using promocodes"""
    promocode_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("promocodes.id"), nullable=False)
    registered_user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
