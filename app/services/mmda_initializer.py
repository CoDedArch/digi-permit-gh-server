import json
import re
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.models.user import MMDA, Department, Committee
from app.core.constants import DEPARTMENTS_DATA, COMMITTEES_DATA
import logging

logger = logging.getLogger(__name__)


class MMDAInitializer:
    @staticmethod
    def slugify(name: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip("-")

    @staticmethod
    def generate_fake_phone(index: int) -> str:
        base = 500000000 + index * 237
        return f"+233{str(base)[-9:]}"  # Ensure valid format

    @staticmethod
    async def initialize_mmdas(db: AsyncSession):
        """Initialize MMDAs, Departments, and Committees in the database."""
        try:
            if not await MMDAInitializer.needs_seeding(db):
                logger.info("⏩ MMDAs already seeded, skipping")
                return False

            logger.info("🏛️ Seeding MMDAs from GeoJSON...")

            geojson_path = "scripts/Ghana_New_260_District.geojson"  # adjust path as needed
            with open(geojson_path, "r", encoding="utf-8") as f:
                geojson = json.load(f)

            features = geojson["features"]
            for i, feature in enumerate(features):
                props = feature["properties"]
                geometry = feature["geometry"]

                name = props.get("DISTRICT", "").strip().title()
                region = props.get("REGION", "").strip().title()

                if not name or not geometry:
                    logger.warning(f"⚠️ Skipping invalid feature at index {i}")
                    continue

                slug = MMDAInitializer.slugify(name)
                email = f"{slug}@district.gov.gh"
                phone = MMDAInitializer.generate_fake_phone(i)

                existing_mmda = await db.execute(
                    select(MMDA).where(MMDA.name == name)
                )
                if existing_mmda.scalar_one_or_none() is None:
                    mmda = MMDA(
                        name=name,
                        type="municipal" if "municipal" in name.lower() else "district",
                        region=region,
                        contact_email=email,
                        contact_phone=phone,
                        jurisdiction_boundaries=geometry,
                    )
                    db.add(mmda)
                    logger.debug(f"✅ Added MMDA: {name}")

            await db.flush()

            # Seed Departments
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
                        department = Department(mmda_id=mmda.id, **dept_data)
                        db.add(department)
                        logger.debug(f"Added Department: {dept_data['name']} for {mmda.name}")

            # Seed Committees
            for mmda in mmdas:
                for committee_data in COMMITTEES_DATA:
                    existing_committee = await db.execute(
                        select(Committee).where(
                            (Committee.mmda_id == mmda.id) &
                            (Committee.name == committee_data["name"])
                        )
                    )
                    if existing_committee.scalar_one_or_none() is None:
                        committee = Committee(mmda_id=mmda.id, **committee_data)
                        db.add(committee)
                        logger.debug(f"Added Committee: {committee_data['name']} for {mmda.name}")

            await db.commit()
            logger.info("✅ MMDAs, Departments, and Committees seeded successfully.")
            return True

        except Exception as e:
            logger.error(f"🔥 MMDA seeding failed: {e}")
            raise

    @staticmethod
    async def needs_seeding(db: AsyncSession) -> bool:
        result = await db.execute(select(func.count(MMDA.id)))
        count = result.scalar()
        return count == 0 or Settings.FORCE_SEED
