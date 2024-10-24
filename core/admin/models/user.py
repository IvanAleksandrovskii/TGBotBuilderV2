# core/admin/models/user.py

from core.admin.models.base import BaseAdminModel
from core.models import User


class UserAdmin(BaseAdminModel, model=User):
    column_list = [User.id, User.chat_id, User.username, User.is_superuser, User.is_new_user, User.is_active, User.created_at, User.updated_at]
    column_searchable_list = [User.id, User.chat_id, User.username]
    column_sortable_list = [User.id, User.chat_id, User.username, User.is_superuser, User.is_new_user, User.is_active, User.created_at, User.updated_at]
    column_filters = [User.chat_id, User.username, User.is_superuser]
    column_details_list = [User.id, User.chat_id, User.username, User.is_superuser, User.is_new_user, User.is_active, User.created_at, User.updated_at]
    form_excluded_columns = ["created_at", "updated_at"]  # , "quiz_results"
    can_create = True  # TODO: It should be False but True to make possible import of users from the old bot
    can_edit = True
    can_delete = True
    name = "User"
    name_plural = "Users"
    category = "Do NOT touch Data"
    icon = "fas fa-user-alt"
