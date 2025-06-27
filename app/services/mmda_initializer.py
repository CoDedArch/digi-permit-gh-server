from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.models.user import MMDA, Department, Committee  # Import your models
from app.core.constants import (
    MMDAS_DATA,
    DEPARTMENTS_DATA,
    COMMITTEES_DATA,
)
import logging

logger = logging.getLogger(__name__)

class MMDAInitializer:
    @staticmethod
    async def initialize_mmdas(db: AsyncSession):
        """Initialize MMDAs, Departments, and Committees in the database."""
        try:
            # Check if seeding is needed
            if not await MMDAInitializer.needs_seeding(db):
                logger.info("⏩ MMDAs already seeded, skipping")
                return False

            logger.info("🏛️ Seeding MMDAs, Departments, and Committees...")
            
            # Seed MMDAs
            for mmda_data in MMDAS_DATA:
                existing_mmda = await db.execute(
                    select(MMDA).where(MMDA.name == mmda_data["name"])
                )
                if existing_mmda.scalar_one_or_none() is None:
                    mmda = MMDA(**mmda_data)
                    db.add(mmda)
                    logger.debug(f"Added MMDA: {mmda_data['name']}")
            await db.flush()  # Ensure MMDAs are committed before adding Departments and Committees
            # Seed Departments for each MMDA
            mmdas = (await db.execute(select(MMDA))).scalars().all()
            for mmda in mmdas:
                for dept_data in DEPARTMENTS_DATA:
                    existing_dept = await db.execute(
                        select(Department).where(
                            (Department.mmda_id == mmda.id) &
                            (Department.code == dept_data["code"])
                        )
                    )
                    if existing_dept.scalar_one_or_none() is None:
                        department = Department(
                            mmda_id=mmda.id,
                            **dept_data
                        )
                        db.add(department)
                        logger.debug(f"Added Department: {dept_data['name']} for {mmda.name}")

            # Seed Committees for each MMDA
            for mmda in mmdas:
                for committee_data in COMMITTEES_DATA:
                    existing_committee = await db.execute(
                        select(Committee).where(
                            (Committee.mmda_id == mmda.id) &
                            (Committee.name == committee_data["name"])
                        )
                    )
                    if existing_committee.scalar_one_or_none() is None:
                        committee = Committee(
                            mmda_id=mmda.id,
                            **committee_data
                        )
                        db.add(committee)
                        logger.debug(f"Added Committee: {committee_data['name']} for {mmda.name}")

            logger.info("✅ MMDAs, Departments, and Committees seeded (commit pending)")

            await db.commit()
            return True

        except Exception as e:
            logger.error(f"🔥 MMDA seeding failed: {e}")
            raise

    @staticmethod
    async def needs_seeding(db: AsyncSession) -> bool:
        """Check if MMDA seeding is required."""
        result = await db.execute(select(func.count(MMDA.id)))
        count = result.scalar()
        return count == 0 or Settings.FORCE_SEED