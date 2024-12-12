# core/admin/models/sent_test.py

from .base import BaseAdminModel
from core.models.sent_test import SentTest


class SentTestAdmin(BaseAdminModel, model=SentTest):
    column_list = [SentTest.sender_id, SentTest.sender_username, SentTest.receiver_id, SentTest.receiver_username, SentTest.status, SentTest.test_id, SentTest.test_name, SentTest.created_at]
    column_searchable_list = [SentTest.sender_username, SentTest.receiver_username, SentTest.test_name]
    column_sortable_list = [SentTest.sender_id, SentTest.sender_username, SentTest.receiver_id, SentTest.receiver_username, SentTest.status, SentTest.test_id, SentTest.test_name, SentTest.created_at]
    column_filters = [SentTest.sender_id, SentTest.sender_username, SentTest.receiver_id, SentTest.receiver_username, SentTest.status, SentTest.test_id, SentTest.test_name, SentTest.created_at]
    column_details_list = '__all__'
    
    can_create = False
    can_edit = False
    can_delete = True
    name = "Sent Test"
    name_plural = "Sent Tests"
    category = "Do NOT touch Data"
    icon = "fas fa-envelope"
