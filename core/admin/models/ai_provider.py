# core/admin/models/ai_provider.py

from wtforms import validators

from .base import BaseAdminModel
from core.models.ai_provider import AIProvider

class AIProviderAdmin(BaseAdminModel, model=AIProvider):
    column_list = ["name", "api_url", "model", "priority", "is_active", "created_at", "updated_at", "id"]
    column_details_list = ["name", "api_url", "api_key", "model", "priority", "is_active", "created_at", "updated_at", "id"]
    column_sortable_list = ["name", "api_url", "model", "priority", "is_active", "created_at", "updated_at"]
    column_searchable_list = ["name", "api_url", "model", "priority"]
    column_filters = ["api_url", "model", "priority", "is_active"]
    
    form_columns = ["name", "api_url", "api_key", "model", "priority", "is_active"]
    
    form_args = {
        'name': {
            'validators': [validators.DataRequired()]
        },
        'api_url': {
            'validators': [validators.DataRequired()]
        },
        'api_key': {
            'validators': [validators.DataRequired()]
        },
        'model': {
            'validators': [validators.DataRequired()]
        },
        'priority': {
            'validators': [validators.DataRequired(), validators.NumberRange(min=0)]
        }
    }

    column_labels = {
        "name": "Name",
        "api_url": "API URL",
        "api_key": "API Key",
        "model": "Model",
        "priority": "Priority",
        "is_active": "Is Active",
        "created_at": "Created At",
        "updated_at": "Updated At"
    }

    name = "AI Provider"
    name_plural = "AI Providers"
    icon = "fa-solid fa-network-wired"  # fa-solid fa-microchip, fa-solid fa-robot, fa-solid fa-brain, fa-solid fa-server
    category = "AI"
