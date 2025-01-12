# core/admin/models/media.py

from .base import BaseAdminModel
from core.models import Media


class MediaAdmin(BaseAdminModel, model=Media):
    column_list = [Media.id, Media.file, Media.file_type, Media.description, Media.is_active, Media.created_at, Media.updated_at]
    column_details_list = [Media.id, Media.file, Media.file_type, Media.description, Media.is_active, Media.created_at, Media.updated_at, Media.texts]
    column_sortable_list = [Media.id, Media.file_type, Media.is_active, Media.created_at, Media.updated_at]
    column_searchable_list = [Media.id, Media.file_type, Media.description]
    column_filters = [Media.file_type, Media.is_active]

    form_columns = [Media.file, Media.file_type, Media.description, Media.is_active]

    name = "Media"
    name_plural = "Media Files"
    icon = "fa-solid fa-image"

    category = "Important Data"
