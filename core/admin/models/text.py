# core/admin/models/text.py

from sqlalchemy import select

from fastapi import Request
# from fastapi.exceptions import HTTPException
from wtforms import validators, SelectMultipleField, StringField, TextAreaField
from wtforms.widgets import ListWidget, CheckboxInput

from core.admin.models.base import BaseAdminModel
from core.models import Text, Media
from core import log
from core.admin import async_sqladmin_db_helper


class TextAdmin(BaseAdminModel, model=Text):
    column_list = [Text.id, Text.context_marker, Text.is_default_media, Text.is_active, Text.reading_pagination, Text.created_at, Text.updated_at]
    column_details_list = [Text.id, Text.context_marker, Text.body, Text.body_html, Text.is_default_media, Text.is_active, Text.reading_pagination, Text.created_at, Text.updated_at, Text.media_files]
    column_sortable_list = [Text.id, Text.context_marker, Text.is_default_media, Text.is_active, Text.created_at, Text.updated_at]
    column_searchable_list = [Text.id, Text.context_marker]
    column_filters = [Text.context_marker, Text.is_default_media, Text.is_active]
    form_columns = ['context_marker', 'body', 'body_html', 'is_default_media', 'is_active', 'reading_pagination', 'media_files']

    # form_args = {
    #     'body': {
    #         'render_kw': {"rows": 20}
    #     },
    #     'body_html': {
    #         'render_kw': {"rows": 20}
    #     }
    # }

    name = "Text"
    name_plural = "Texts"
    icon = "fa-solid fa-file-lines"
    category = "Important Data"

    async def scaffold_form(self):
        form_class = await super().scaffold_form()
        form_class.context_marker = StringField(
            'Context Marker',
            validators=[validators.DataRequired(message="Context Marker is required")]
        )
        form_class.body = TextAreaField(
            'Body',
            validators=[validators.DataRequired(message="Body is required")]
        )
        form_class.body_html = TextAreaField(
            'Body HTML',
        )
        form_class.media_files = SelectMultipleField(
            'Media Files',
            choices=await self._get_media_choices(),
            widget=ListWidget(prefix_label=False),
            option_widget=CheckboxInput(),
            coerce=self._coerce_media,
            validators=[validators.Length(max=10, message="You can select up to 10 media files.")]
        )
        return form_class

    def _coerce_media(self, value):
        if hasattr(value, 'id'):
            return str(value.id)
        return str(value)

    async def _get_media_choices(self):
        async with async_sqladmin_db_helper.session_getter() as session:
            try:
                result = await session.execute(select(Media).where(Media.is_active == True).order_by(Media.file))
                media_files = result.scalars().all()
                return [(str(media.id), f"{media.file} ({media.file_type}) - {media.description}") for media in media_files]
            except Exception as e:
                log.exception(f"Error in _get_media_choices: {e}")

    # async def on_model_change(self, data: dict, model: Text, is_created: bool, request: Request) -> None:
    #     try:
    #         logger.debug(f"Received data in on_model_change: {data}")
    #         logger.debug(f"Model before changes: {model.__dict__}")

    #         context_marker = data.get('context_marker')
    #         body = data.get('body')
    #         logger.debug(f"context_marker: {context_marker}, body: {body}")

    #         if not context_marker:
    #             raise ValueError("Context Marker is required")
    #         if not body:
    #             raise ValueError("Body is required")

    #         model.context_marker = context_marker
    #         model.body = body
    #         model.is_default_media = data.get('is_default_media', False)
    #         model.is_active = data.get('is_active', True)

    #         action = "Created" if is_created else "Updated"
    #         logger.info(f"{action} Text successfully with id: {model.id}")

    #         media_files = data.get('media_files')
    #         if media_files is not None:
    #             async with async_sqladmin_db_helper.session_getter() as session:
    #                 try:
    #                     # Fetch the Text model within this session
    #                     model = await session.merge(model)
    
    #                     # Fetch Media objects within the same session
    #                     media_objects = await session.execute(select(Media).where(Media.id.in_(media_files)))
    #                     model.media_files = media_objects.scalars().all()
    
    #                     # Commit the changes
    #                     await session.commit()
    #                 except Exception as e:
    #                     await session.rollback()
    #                     logger.exception(f"Error in on_model_change for {self.name}: {str(e)}")
    #                     raise

    #         logger.debug(f"Model after changes: {model.__dict__}")

    #     except ValueError as e:
    #         logger.error(f"Validation error in on_model_change for {self.name}: {str(e)}")
    #         raise
    #     except Exception as e:
    #         logger.error(f"Error in on_model_change for {self.name}: {str(e)}")
    #         raise ValueError(f"An unexpected error occurred while creating/updating {self.name}. Error: {str(e)}")

    async def after_model_change(self, data: dict, model: Text, is_created: bool, request: Request) -> None:
        try:
            media_files = data.get('media_files')
            if media_files is not None:
                async with async_sqladmin_db_helper.session_getter() as session:
                    try:
                        # Fetch the Text model within this session
                        model = await session.merge(model)
                        
                        # Fetch Media objects within the same session
                        media_objects = await session.execute(select(Media).where(Media.id.in_(media_files)))
                        model.media_files = media_objects.scalars().all()
                        
                        # Commit the changes
                        await session.commit()
                        
                        log.info(f"Updated media files for Text with id: {model.id}")
                    except Exception as e:
                        await session.rollback()
                        log.exception(f"Error in after_model_change for {self.name}: {str(e)}")
                        raise

            log.debug(f"Model after changes: {model.__dict__}")

        except Exception as e:
            log.error(f"Error in after_model_change for {self.name}: {str(e)}")
