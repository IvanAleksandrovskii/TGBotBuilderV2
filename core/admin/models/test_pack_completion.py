# core/admin/models/test_pack_completion.py

from core.admin.models.base import BaseAdminModel
from core.models.test_pack_completion import TestPackCompletion


class TestPackCompletionAdmin(BaseAdminModel, model=TestPackCompletion):
    column_list = "__all__"
    coloumn_details_list = "__all__"
    # column_searchable_list = []
    # column_sortable_list = []
    # column_filters = []
    # column_details_list = []
    # form_excluded_columns = []
    can_create = False 
    can_edit = False  # TODO: Make it False
    can_delete = True
    name = "Test Pack Completion"
    name_plural = "Test Pack Completions"
    category = "Do NOT touch Data"
    # icon = "fas fa-user-alt"
