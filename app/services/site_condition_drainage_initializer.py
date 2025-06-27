from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import DRAINAGE_TYPE_DATA, SITE_CONDITION_DATA
from app.models.zoning import SiteCondition, DrainageType  # Adjust paths if needed
from app.core.config import Settings
import logging

logger = logging.getLogger(__name__)


class SiteConditionAndDrainageInitializer:
    @staticmethod
    async def needs_seeding(db: AsyncSession) -> bool:
        site_count = await db.scalar(select(func.count(SiteCondition.id)))
        drainage_count = await db.scalar(select(func.count(DrainageType.id)))
        return site_count == 0 or drainage_count == 0 or Settings.FORCE_SEED

    @staticmethod
    async def initialize(db: AsyncSession) -> bool:
        try:
            if not await SiteConditionAndDrainageInitializer.needs_seeding(db):
                logger.info("⏩ Site conditions and drainage types already seeded, skipping.")
                return False

            logger.info("🌱 Seeding site conditions and drainage types...")

            # Seed Site Conditions
            for condition in SITE_CONDITION_DATA:
                exists = await db.scalar(
                    select(SiteCondition).where(SiteCondition.name == condition["name"])
                )
                if not exists:
                    db.add(SiteCondition(**condition))

            # Seed Drainage Types
            for drainage in DRAINAGE_TYPE_DATA:
                exists = await db.scalar(
                    select(DrainageType).where(DrainageType.name == drainage["name"])
                )
                if not exists:
                    db.add(DrainageType(**drainage))

            await db.commit()
            logger.info("✅ Seeded site conditions and drainage types.")
            return True

        except Exception as e:
            logger.exception("🔥 Seeding site conditions or drainage types failed")
            raise
