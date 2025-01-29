__all__ = [
    "setup_admin",
]

from .user import UserAdmin
from .text import TextAdmin
from .media import MediaAdmin
from .button import ButtonAdmin
from .quiz_result import QuizResultAdmin
from .promocode import PromocodeAdmin, PromoRegistrationAdmin

from .ai_provider import AIProviderAdmin
from .quiz import TestAdmin, QuestionAdmin, ResultAdmin
from .sent_test import SentTestAdmin
from .ai_transcripts import AITranscriptsAdmin

from .test_pack import TestPackAdmin

from .custom_test import CustomTestAdmin, CustomQuestionAdmin

from .test_pack_completion import TestPackCompletionAdmin


# Register admin views
def setup_admin(admin):
    admin.add_view(UserAdmin)
    admin.add_view(TextAdmin)
    admin.add_view(MediaAdmin)
    admin.add_view(ButtonAdmin)
    admin.add_view(QuizResultAdmin)
    admin.add_view(PromocodeAdmin)
    admin.add_view(PromoRegistrationAdmin)
    admin.add_view(AIProviderAdmin)
    
    admin.add_view(TestAdmin)
    admin.add_view(QuestionAdmin)
    admin.add_view(ResultAdmin)
    admin.add_view(SentTestAdmin)
    admin.add_view(AITranscriptsAdmin)
    
    admin.add_view(TestPackAdmin)
    
    admin.add_view(CustomTestAdmin)
    admin.add_view(CustomQuestionAdmin)
    
    admin.add_view(TestPackCompletionAdmin)
