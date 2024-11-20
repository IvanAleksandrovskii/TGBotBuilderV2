# core/admin/models/quiz.py

# core/admin/models/quiz.py

from typing import Any, Type
from fastapi import UploadFile, Request
from sqlalchemy import select
from wtforms import Form, TextAreaField
from wtforms.validators import Optional, DataRequired

from core import log
from core.admin.models.base import BaseAdminModel
from core.models import Test, Question, Result
from services import quiz_storage


class TestAdmin(BaseAdminModel, model=Test):
    column_list = [
        Test.id,
        Test.name, 
        Test.is_psycological, 
        Test.multi_graph_results,
        Test.allow_back, 
        Test.allow_play_again, 
        Test.is_active, 
        Test.created_at, 
        Test.updated_at, 
        Test.picture
        ]
    column_details_list = [
        Test.id, 
        Test.name, 
        Test.is_psycological, 
        Test.multi_graph_results,
        Test.category_names,
        Test.description, 
        Test.picture, 
        Test.allow_back, 
        Test.allow_play_again, 
        Test.is_active, 
        Test.created_at, 
        Test.updated_at
        ]
    column_sortable_list = [
        Test.id, 
        Test.name, 
        Test.is_psycological, 
        Test.multi_graph_results,
        Test.category_names,
        Test.allow_back, 
        Test.allow_play_again, 
        Test.is_active, 
        Test.created_at, 
        Test.updated_at
        ]
    column_searchable_list = [Test.id, Test.name]
    column_filters = [Test.name, Test.is_psycological, Test.allow_back, Test.allow_play_again, Test.is_active, Test.multi_graph_results]
    form_columns = [Test.name, Test.description, Test.is_psycological, Test.multi_graph_results, Test.category_names, Test.allow_back, Test.allow_play_again, Test.is_active, Test.picture]
    
    name = "Test"
    name_plural = "Tests"
    icon = "fa-solid fa-clipboard-question"
    category = "Quiz Management"
    
    async def scaffold_form(self) -> Type[Form]:
        form_class = await super().scaffold_form()
        
        form_class.category_names = TextAreaField(
            'Category Names',
            validators=[Optional()],
            description='Введите имена категорий в формате JSON. Пример: {"1": "Интроверсия", "2": "Экстраверсия"}',
            render_kw={
                "rows": 10,
                "style": "width: 50% !important; min-height: 200px !important; resize: vertical !important;"
            }
        )
        
        return form_class

    
    async def scaffold_list_query(self):
        query = select(self.model).order_by(self.model.created_at.desc())
        return query
    
    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        try:
            action = "Created" if is_created else "Updated"
            log.info(f"{action} test: {model.name}")
        except Exception as e:
            log.error(f"Error in after_model_change for test: {e}")

        # Process logo upload
        picture = data.get('picture')
        if picture and isinstance(picture, UploadFile):
            try:
                contents = await picture.read()
                file_path = await quiz_storage.save(picture.filename, contents)
                model.picture = file_path
                log.info(f"Picture uploaded for Test: {model.name}")
            except Exception as e:
                log.error(f"Error uploading picture for Test {model.name}: {str(e)}")

    async def after_model_delete(self, model, session):
        try:
            await quiz_storage.delete(model.picture)
        except Exception as e:
            log.error(f"Error deleting file: {e}")



class QuestionAdmin(BaseAdminModel, model=Question):
    column_list = [Question.id, Question.question_text, Question.order, Question.test_id, Question.is_active, Question.created_at, Question.updated_at, Question.picture]
    column_details_list = "__all__"
    column_sortable_list = [Question.id, Question.order, Question.question_text, Question.test_id, Question.is_active, Question.created_at, Question.updated_at]
    column_searchable_list = [Question.id, Question.question_text, Question.test_id]
    column_filters = [Question.test_id, Question.is_active]
    form_excluded_columns = ["created_at", "updated_at"]
    
    name = "Question"
    name_plural = "Questions"
    icon = "fa-solid fa-question"
    category = "Quiz Management"

    async def scaffold_list_query(self):
        query = select(self.model).order_by(self.model.created_at.desc())
        return query

    async def scaffold_form(self) -> Type[Form]:
        form_class = await super().scaffold_form()
        return form_class
    
    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        try:
            action = "Created" if is_created else "Updated"
            log.info(f"{action} Question: {model.name}")
        except Exception as e:
            log.error(f"Error in after_model_change for Question: {e}")

        # Process logo upload
        picture = data.get('picture')
        if picture and isinstance(picture, UploadFile):
            try:
                contents = await picture.read()
                file_path = await quiz_storage.save(picture.filename, contents)
                model.picture = file_path
                log.info(f"Picture uploaded for Question: {model.name}")
            except Exception as e:
                log.error(f"Error uploading picture for Question {model.name}: {str(e)}")


    async def after_model_delete(self, model, session):
        try:
            await quiz_storage.delete(model.picture)
        except Exception as e:
            log.error(f"Error deleting file: {e}")


class ResultAdmin(BaseAdminModel, model=Result):
    column_list = [Result.id, Result.test_id, Result.category_id, Result.min_score, Result.max_score, Result.is_active, Result.created_at, Result.updated_at, Result.picture]
    column_details_list = "__all__"
    column_sortable_list = [Result.id, Result.test_id, Result.min_score, Result.max_score, Result.is_active, Result.created_at, Result.updated_at]
    column_searchable_list = [Result.id, Result.test_id]
    column_filters = [Result.test_id, Result.is_active]
    form_excluded_columns = ["created_at", "updated_at"]
    
    name = "Result"
    name_plural = "Results"
    icon = "fa-solid fa-star"
    category = "Quiz Management"

    async def scaffold_list_query(self):
        query = select(self.model).order_by(self.model.created_at.desc())
        return query

    async def scaffold_form(self) -> Type[Form]:
        form_class = await super().scaffold_form()
        form_class.text = TextAreaField(
            'Text',
            validators=[DataRequired(message="Text is required")],
            render_kw={
                "rows": 20,
                "style": "width: 70% !important; min-height: 300px !important; resize: vertical !important;"
            }
        )
        return form_class

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        try:
            action = "Created" if is_created else "Updated"
            log.info(f"{action} Result: {model.name}")
        except Exception as e:
            log.error(f"Error in after_model_change for Result: {e}")

        # Process logo upload
        picture = data.get('picture')
        if picture and isinstance(picture, UploadFile):
            try:
                contents = await picture.read()
                file_path = await quiz_storage.save(picture.filename, contents)
                model.picture = file_path
                log.info(f"Picture uploaded for Result: {model.name}")
            except Exception as e:
                log.error(f"Error uploading picture for Result {model.name}: {str(e)}")


    async def after_model_delete(self, model, session):
        try:
            await quiz_storage.delete(model.picture)
        except Exception as e:
            log.error(f"Error deleting file: {e}")

