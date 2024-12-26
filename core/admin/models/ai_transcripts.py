# core/admin/models/ai_transcripts.py

from .base import BaseAdminModel

from core.models.psycho_tests_ai_trascription import PsycoTestsAITranscription


class AITranscriptsAdmin(BaseAdminModel, model=PsycoTestsAITranscription):
    name = "AI Transcription"
    name_plural = "AI Transcriptions"
    icon = "fa-solid fa-book-open"
    
    column_list = "__all__"
    form_columns = "__all__"
    
    column_searchable_list = [PsycoTestsAITranscription.sender_chat_id, PsycoTestsAITranscription.reciver_chat_id]
    column_sortable_list = [PsycoTestsAITranscription.sender_chat_id, PsycoTestsAITranscription.reciver_chat_id]
    column_filters = [PsycoTestsAITranscription.sender_chat_id, PsycoTestsAITranscription.reciver_chat_id]
    
    category = "Do NOT touch Data"
    
    can_create = False
    can_edit = False
    can_delete = True
