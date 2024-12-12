# core/models/media.py

from sqlalchemy import String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_storages.integrations.sqlalchemy import FileType

from .base import Base
from .media_to_text import text_media_association
from services.fastapi_storage import main_storage
from core import log

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .text import Text


class Media(Base):
    __tablename__ = 'media'

    file: Mapped[str] = mapped_column(FileType(storage=main_storage))

    file_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    
    # Many-to-many relationship with Text
    texts: Mapped[list["Text"]] = relationship(
        "Text",
        secondary=text_media_association,
        back_populates="media_files",
        cascade="all, delete",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Media(id={self.id}, file_type={self.file_type})>"


@event.listens_for(Media, 'before_update')
def before_update_media(mapper, connection, target):
    if hasattr(target, '_file_to_delete') and target._file_to_delete:
        try:
            main_storage.delete(target._file_to_delete)
        except Exception as e:
            log.error(f"Error deleting old file {target.file}: {str(e)}")
        delattr(target, '_file_to_delete')


@event.listens_for(Media.file, 'set')
def on_file_set(target, value, oldvalue, initiator):
    if oldvalue and oldvalue != value:
        target._file_to_delete = oldvalue


@event.listens_for(Media, 'after_delete')
def after_delete_media(mapper, connection, target):
    if target.file:
        try:
            main_storage.delete(target.file)
        except Exception as e:
            log.error(f"Error deleting media {target.file}: {str(e)}")
