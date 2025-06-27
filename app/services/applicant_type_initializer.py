from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import APPLICANT_TYPE_DATA
from app.models.user import ApplicantType
from app.core.config import Settings
import logging

logger = logging.getLogger(__name__)

class ApplicantTypeInitializer:
    @staticmethod
    async def needs_seeding(db: AsyncSession) -> bool:
        count = await db.scalar(select(func.count(ApplicantType.id)))
        return count == 0 or Settings.FORCE_SEED

    @staticmethod
    async def initialize(db: AsyncSession) -> bool:
        try:
            if not await ApplicantTypeInitializer.needs_seeding(db):
                logger.info("⏩ Applicant types already seeded, skipping.")
                return False

            logger.info("👤 Seeding applicant types...")

            for item in APPLICANT_TYPE_DATA:
                exists = await db.scalar(
                    select(ApplicantType).where(ApplicantType.code == item["code"])
                )
                if not exists:
                    db.add(ApplicantType(**item))

            await db.commit()
            logger.info("✅ Applicant types seeded.")
            return True

        except Exception as e:
            logger.exception("🔥 Failed to seed applicant types.")
            raise
