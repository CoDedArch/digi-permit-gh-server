from app.core.constants import PREVIOUS_LAND_USES
from app.models.zoning import PreviousLandUse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class PreviousLandUseSeeder:
    @staticmethod
    async def seed(db: AsyncSession):
        logger.info("🌱 Seeding Previous Land Uses...")

        for item in PREVIOUS_LAND_USES:
            existing = await db.execute(
                select(PreviousLandUse).where(PreviousLandUse.id == item["id"])
            )
            if existing.scalar_one_or_none():
                logger.debug(f"⏩ Skipping existing land use: {item['id']}")
                continue

            db.add(PreviousLandUse(id=item["id"], name=item["name"]))

        await db.commit()
        logger.info("✅ Previous Land Uses seeded.")
