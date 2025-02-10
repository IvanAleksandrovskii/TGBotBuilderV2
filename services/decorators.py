# services/decorators.py

from aiogram import types
from functools import wraps
from typing import Callable, Optional

from .task_manager import TaskManager, TaskPriority


# Task manager assignment
task_manager = TaskManager(
    max_concurrent_tasks=10,  # TODO: Move to config
    max_queue_size=1000,  # TODO: Move to config
    num_workers=3,  # TODO: Move to config
)


def handle_as_task(
    priority: TaskPriority = TaskPriority.NORMAL, skip_states: Optional[list] = None
):
    """
    Decorator for handling handlers as asynchronous tasks.
    Args:
        priority: Task priority
        skip_states: List of states where the task should NOT be queued
    """

    def decorator(handler: Callable):
        @wraps(handler)
        async def wrapper(*args, **kwargs):
            # Determine update type (message or callback_query)
            update = next(
                (
                    arg
                    for arg in args
                    if isinstance(arg, (types.Message, types.CallbackQuery))
                ),
                None,
            )
            if not update:
                return await handler(*args, **kwargs)

            # Get state from arguments
            state = next(
                (arg for arg in args if str(type(arg).__name__) == "FSMContext"), None
            )

            # Check current state if skip_states specified
            if skip_states and state:
                current_state = await state.get_state()
                if current_state in skip_states:
                    return await handler(*args, **kwargs)

            # Determine chat_id based on update type
            chat_id = (
                update.message.chat.id
                if isinstance(update, types.CallbackQuery)
                else update.chat.id
            )

            # Add task to queue
            task_id = await task_manager.add_task(
                callback=handler,
                chat_id=chat_id,
                priority=priority,
                _args=args,
                _kwargs=kwargs,
            )
            return task_id

        return wrapper

    return decorator
