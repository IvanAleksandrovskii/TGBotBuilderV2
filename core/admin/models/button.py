# core/admin/models/button.py

from wtforms import validators

from core.admin.models.base import BaseAdminModel
from core.models import Button


class ButtonAdmin(BaseAdminModel, model=Button):
    column_list = [Button.id, Button.context_marker, Button.text, Button.callback_data, Button.url, Button.is_inline, Button.is_half_width, Button.order, Button.is_active]
    column_details_list = [Button.id, Button.context_marker, Button.text, Button.callback_data, Button.url, Button.is_inline, Button.order, Button.is_active, Button.created_at, Button.updated_at]
    column_sortable_list = [Button.id, Button.context_marker, Button.text, Button.is_inline, Button.order, Button.is_active, Button.created_at, Button.updated_at]
    column_searchable_list = [Button.id, Button.context_marker, Button.text, Button.callback_data]
    column_filters = [Button.context_marker, Button.is_inline, Button.is_active]
    
    form_columns = ['context_marker', 'text', 'callback_data', 'url', 'is_inline', 'is_half_width', 'order', 'is_active']
    
    form_args = {
        'context_marker': {
            'validators': [validators.DataRequired()]
        },
        'text': {
            'validators': [validators.DataRequired()]
        },
        'order': {
            'validators': [validators.DataRequired(), validators.NumberRange(min=0)]
        }
    }

    name = "Button"
    name_plural = "Buttons"
    icon = "fa-solid fa-rectangle-list"
    category = "Important Data"