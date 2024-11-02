# core/admin/models/promocode.py

# from sqlalchemy import select, func
# from sqlalchemy.orm import selectinload
# from datetime import datetime
from .base import BaseAdminModel
from core.models import Promocode, PromoRegistration   # , User


class PromocodeAdmin(BaseAdminModel, model=Promocode):
    # Отображаемые колонки в списке
    column_list = [
        Promocode.id,
        Promocode.code,
        'user.username',  # Имя создателя промокода
        Promocode.is_active,
        Promocode.created_at
    ]
    
    # Поля для поиска
    column_searchable_list = [
        Promocode.id,
        Promocode.code,
        'user.username',
        'user.chat_id'
    ]
    
    # Сортируемые колонки
    column_sortable_list = [
        Promocode.id,
        Promocode.code,
        Promocode.is_active,
        Promocode.created_at
    ]
    
    # Фильтры
    column_filters = [
        Promocode.code,
        Promocode.is_active,
        Promocode.created_at
    ]
    
    # Детальное представление
    column_details_list = [
        Promocode.id,
        Promocode.code,
        'user.username',
        'user.chat_id',
        # 'registrations_count',
        Promocode.is_active,
        Promocode.created_at,
        Promocode.updated_at
    ]
    
    form_excluded_columns = [
        "created_at",
        "updated_at",
        "registrations"
    ]
    
    can_create = True
    can_edit = False
    can_delete = True
    name = "Promocode"
    name_plural = "Promocodes"
    category = "Referral"
    icon = "fas fa-barcode"


class PromoRegistrationAdmin(BaseAdminModel, model=PromoRegistration):
    column_list = [
        PromoRegistration.id,
        'promocode.code',
        'promocode.user.username',
        'registered_user.username',
        'registered_user.chat_id',
        PromoRegistration.created_at
    ]
    
    column_searchable_list = [
        PromoRegistration.id,
        'promocode.code',
        'promocode.user.username',
        'registered_user.username',
        'registered_user.chat_id'
    ]
    
    column_sortable_list = [
        PromoRegistration.id,
        PromoRegistration.created_at
    ]
    
    column_filters = [
        'promocode.code',
        'promocode.user.username',
        'registered_user.username',
        PromoRegistration.created_at
    ]
    
    column_details_list = [
        PromoRegistration.id,
        'promocode.code',
        'promocode.user.username',
        'registered_user.username',
        'registered_user.chat_id',
        PromoRegistration.created_at,
        PromoRegistration.updated_at
    ]
    
    form_excluded_columns = [
        "created_at",
        "updated_at"
    ]
    
    can_create = False
    can_edit = False
    can_delete = True
    name = "Promo Registration"
    name_plural = "Promo Registrations"
    category = "Referral"
    icon = "fas fa-users"
