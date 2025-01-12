# core/admin/models/test_pack.py

from core.admin.models.base import BaseAdminModel
from core.models.test_pack import TestPack


class TestPackAdmin(BaseAdminModel, model=TestPack):
    column_list = "__all__"
    coloumn_details_list = "__all__"
    column_searchable_list = [TestPack.name, TestPack.test_ids_string]
    # column_sortable_list = []
    # column_filters = []
    # column_details_list = []
    # form_excluded_columns = []
    can_create = False 
    can_edit = False
    can_delete = True
    name = "Test Pack"
    name_plural = "Test Packs"
    category = "Do NOT touch Data"
    # icon = "fas fa-user-alt"
