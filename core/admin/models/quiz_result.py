# core/admin/models/quiz_result.py

from sqlalchemy import select
from wtforms import IntegerField

from core.admin.models.base import BaseAdminModel
from core.models import QuizResult


class QuizResultAdmin(BaseAdminModel, model=QuizResult):
    column_list = [QuizResult.id, QuizResult.user_id, "user", QuizResult.test_id, "test", QuizResult.category_id, QuizResult.score, QuizResult.is_active, QuizResult.created_at]
    column_details_list = [QuizResult.id, QuizResult.user_id, QuizResult.test_id, QuizResult.category_id, QuizResult.score, QuizResult.is_active, QuizResult.created_at, QuizResult.updated_at]
    column_sortable_list = [QuizResult.id, QuizResult.user_id, QuizResult.test_id, QuizResult.category_id, QuizResult.score, QuizResult.is_active, QuizResult.created_at]
    column_searchable_list = [QuizResult.id, QuizResult.user_id, QuizResult.test_id]
    column_filters = [QuizResult.user_id, QuizResult.test_id, QuizResult.score, QuizResult.category_id, QuizResult.is_active]
    form_excluded_columns = ["created_at", "updated_at"]
    
    name = "Quiz Result"
    name_plural = "Quiz Results"
    icon = "fa-solid fa-chart-simple"
    # category = "Quiz Management"
    category = "Users Associated"

    form_overrides = {
        "score": IntegerField,
    }

    async def scaffold_list_query(self):
        query = select(self.model).order_by(self.model.created_at.desc())
        return query
