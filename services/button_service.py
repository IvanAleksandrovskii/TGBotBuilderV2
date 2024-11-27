# services/button_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.logger import log
from core.models.button import Button


class ButtonService:
    @staticmethod
    async def get_buttons_by_marker(context_marker: str, session: AsyncSession) -> list[Button]:
        try:
            result = await session.execute(
                Button.active()
                .where(Button.context_marker == context_marker)
                .order_by(Button.order)
            )
            return result.scalars().all()
        except Exception as e:
            log.exception(f"Error in get_buttons_by_marker: {e}")
            return []

    @staticmethod
    async def get_button_by_id(button_id: str, session: AsyncSession) -> Button | None:
        try:
            result = await session.execute(
                Button.active().where(Button.id == button_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            log.exception(f"Error in get_button_by_id: {e}")
            return None

    @staticmethod
    async def create_inline_keyboard(context_marker: str, session: AsyncSession) -> InlineKeyboardMarkup:
        buttons = await ButtonService.get_buttons_by_marker(context_marker, session)
        
        keyboard = []
        current_row = []

        for button in buttons:
            log.info(f"Processing button: {button.text}, is_half_width: {button.is_half_width}")
            btn = InlineKeyboardButton(
                text=button.text,
                url=button.url if button.url else None,
                callback_data=button.callback_data if button.callback_data else None
            )

            if button.is_half_width:
                current_row.append(btn)
                if len(current_row) == 2:  # Max 2 buttons in a row
                    keyboard.append(current_row)
                    current_row = []
            else:
                if current_row:
                    keyboard.append(current_row)
                    current_row = []
                keyboard.append([btn])

        if current_row:
            keyboard.append(current_row)

        log.info("Final keyboard structure: %s", keyboard)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
