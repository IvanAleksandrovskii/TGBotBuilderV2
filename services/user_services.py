# services/user_service.py

from sqlalchemy import select, update
# from async_lru import alru_cache

from core import log  # , settings
from core.models import User, db_helper


class UserService:

    @staticmethod
    # @alru_cache(ttl=settings.bot.max_users_cached_time_seconds, maxsize=settings.bot.max_users_cached)
    async def create_user(chat_id: int, username: str | None) -> User:
        async for session in db_helper.session_getter():
            try:
                # Check if user exists
                result = await session.execute(select(User).where(User.chat_id == chat_id))
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    log.info("User %s already exists", chat_id)
                    return existing_user

                user = User(chat_id=chat_id, username=username, is_superuser=False)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user

            except Exception as e:
                log.exception(f"Error in create_user: {e}")
                await session.rollback()
            finally:
                await session.close()

    @staticmethod
    async def get_user(chat_id: int) -> User | None:
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(select(User).where(User.chat_id == chat_id))
                return result.scalar_one_or_none()
            except Exception as e:
                log.exception(f"Error in get_user: {e}")
            finally:
                await session.close()

    @staticmethod
    async def get_all_users() -> list[User]:
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(select(User))
                return result.scalars().unique().all()
            except Exception as e:
                log.exception(f"Error in get_all_users: {e}")
            finally:
                await session.close()

    @staticmethod
    async def is_superuser(chat_id: int) -> bool:
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(select(User).where(User.chat_id == chat_id))
                user = result.scalar_one_or_none()
                return user is not None and user.is_superuser
            except Exception as e:
                log.exception(f"Error in is_superuser: {e}")
            finally:
                await session.close()

    @staticmethod
    async def update_username(chat_id: int, new_username: str | None) -> bool:
        async for session in db_helper.session_getter():
            try:
                user = await session.execute(select(User).where(User.chat_id == chat_id))
                user = user.scalar_one_or_none()
                if user:
                    user.username = new_username
                    await session.commit()
                    log.info("Updated username for user %s to %s", chat_id, new_username)
                    
                    # Clear cache for updated user
                    UserService.get_user.cache_clear()
                    # UserService.create_user.cache_clear()

                    return True
                
                else:
                    log.warning(f"User {chat_id} not found for username update")
                    return False
            except Exception as e:
                log.exception(f"Error in update_username: {e}")
                await session.rollback()
                return False
            finally:
                await session.close()

    @staticmethod
    async def mark_user_as_not_new(chat_id: int) -> bool:
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(
                    update(User)
                    .where(User.chat_id == chat_id)
                    .values(is_new_user=False)
                )
                await session.commit()
                if result.rowcount > 0:
                    log.info(f"Marked user {chat_id} as not new")

                    return True
                
                else:
                    log.warning(f"User {chat_id} not found for marking as not new")
                    return False
            except Exception as e:
                log.exception(f"Error in mark_user_as_not_new: {e}")
                await session.rollback()
                return False
            finally:
                await session.close()
