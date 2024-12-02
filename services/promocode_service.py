# services/promocode_service.py

import random
import string
from uuid import UUID
from sqlalchemy import select, and_, func

from async_lru import alru_cache

from core.models import Promocode, PromoRegistration, db_helper
from core import log


class PromoCodeService:
    @staticmethod
    def generate_code(length: int = 8) -> str:
        """Generates a random promocode of specified length"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    @alru_cache(maxsize=100, ttl=300)  # TODO: Move to config
    async def create_promocode(user_id: UUID) -> Promocode:
        """Creates a new promocode for a user"""
        async for session in db_helper.session_getter():
            try:
                # Check if user already has a promocode
                existing = await session.execute(
                    select(Promocode)
                    .where(and_(Promocode.user_id == user_id, Promocode.is_active == True))
                )
                existing_promo = existing.scalar_one_or_none()
                if existing_promo:
                    return existing_promo

                code = PromoCodeService.generate_code()
                promocode = Promocode(
                    code=code,
                    user_id=user_id,
                )
                session.add(promocode)
                await session.commit()
                await session.refresh(promocode)
                return promocode
            except Exception as e:
                log.exception(f"Error in create_promocode: {e}")
                await session.rollback()
                return None
            finally:
                await session.close()

    @staticmethod
    async def register_promo_usage(promocode: str, registered_user_id: UUID) -> bool:
        """Records when a user registers using a promocode"""
        async with db_helper.db_session() as session:
            try:
                # Find the promocode
                result = await session.execute(
                    select(Promocode).where(
                        and_(Promocode.code == promocode, Promocode.is_active == True)
                    )
                )
                promo = result.scalar_one_or_none()
                if not promo:
                    return False
                
                # TODO: Doublecheck for case of one or none violating situations
                result = await session.execute(
                    select(PromoRegistration)
                    .where(PromoRegistration.registered_user_id == registered_user_id)
                    )
                
                is_already_registered = result.scalar_one_or_none()
                
                if is_already_registered:
                    return False
                    
                # Record the usage
                registration = PromoRegistration(
                    promocode_id=promo.id,
                    registered_user_id=registered_user_id
                )
                session.add(registration)
                await session.commit()
                return True
            except Exception as e:
                log.exception(f"Error in register_promo_usage: {e}")
                await session.rollback()
                return False


    # TODO: Not implemented
    @staticmethod
    async def get_registrations_count(promocode: str) -> int:
        """Gets the number of registrations for a specific promocode"""
        async for session in db_helper.session_getter():
            try:
                result = await session.execute(
                    select(Promocode)
                    .where(and_(Promocode.code == promocode, Promocode.is_active == True))
                )
                promo = result.scalar_one_or_none()
                if not promo:
                    return 0

                count = await session.execute(
                    select(func.count())
                    .select_from(PromoRegistration)
                    .where(PromoRegistration.promocode_id == promo.id)
                )
                return count.scalar_one()
            except Exception as e:
                log.exception(f"Error in get_registrations_count: {e}")
                return 0
            finally:
                await session.close()
