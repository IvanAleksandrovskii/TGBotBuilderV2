__all__ = [
    "setup_admin",
]

from .user import UserAdmin
from .text import TextAdmin
from .media import MediaAdmin
from .button import ButtonAdmin
# from .quiz import TestAdmin, QuestionAdmin, ResultAdmin
# from .quiz_result import QuizResultAdmin
from .promocode import PromocodeAdmin, PromoRegistrationAdmin

# Register admin views
def setup_admin(admin):
    admin.add_view(UserAdmin)
    admin.add_view(TextAdmin)
    admin.add_view(MediaAdmin)
    admin.add_view(ButtonAdmin)
    # admin.add_view(TestAdmin)
    # admin.add_view(QuestionAdmin)
    # admin.add_view(ResultAdmin)
    # admin.add_view(QuizResultAdmin)
    admin.add_view(PromocodeAdmin)
    admin.add_view(PromoRegistrationAdmin)
