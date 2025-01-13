# core/admin/models/test_pack.py

from core.admin.models.base import BaseAdminModel
from core.models.custom_test import CustomTest, CustomQuestion


class CustomTestAdmin(BaseAdminModel, model=CustomTest):
    column_list = "__all__"
    coloumn_details_list = "__all__"
    column_searchable_list = [CustomTest.name, CustomTest.creator_id]
    # column_sortable_list = []
    # column_filters = []
    # column_details_list = []
    # form_excluded_columns = []
    can_create = False 
    can_edit = False
    can_delete = True
    name = "Custom Test"
    name_plural = "Custom Tests"
    category = "Custom Tests Data"
    # icon = "fas fa-user-alt"


class CustomQuestionAdmin(BaseAdminModel, model=CustomQuestion):
    column_list = "__all__"
    coloumn_details_list = "__all__"
    column_searchable_list = [CustomQuestion.question_text]
    # column_sortable_list = []
    # column_filters = []
    # column_details_list = []
    # form_excluded_columns = []
    can_create = False 
    can_edit = False
    can_delete = True
    name = "Custom Question"
    name_plural = "Custom Questions"
    category = "Custom Tests Data"
    # icon = "fas fa-user-alt"
