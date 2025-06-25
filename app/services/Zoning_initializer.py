import json
from pathlib import Path
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.models.zoning import (
    ZoningDistrict,
    ZoningPermittedUse,
    ZoningProhibitedUse,
    ZoningUseDocumentRequirement
)
from app.models.document import DocumentTypeModel
from app.core.constants import ZONE_DATA, ZONE_USES
import logging

logger = logging.getLogger(__name__)

# Load requirements from JSON file once
USE_REQUIREMENTS_PATH = Path("scripts/zoning_use_requirements.json")
with open(USE_REQUIREMENTS_PATH, "r", encoding="utf-8") as f:
    USE_REQUIREMENTS = json.load(f)

class ZoningInitializer:
    @staticmethod
    async def initialize_zoning_districts(db: AsyncSession):
        try:
            if not await ZoningInitializer.needs_seeding(db):
                logger.info("⏩ Zoning districts already seeded, skipping")
                return False

            logger.info("🌆 Seeding zoning districts...")

            # Load all document types once
            docs_result = await db.execute(select(DocumentTypeModel))
            document_map = {doc.code: doc for doc in docs_result.scalars().all()}

            for zone_data in ZONE_DATA:
                code = zone_data["code"]

                existing = await db.execute(select(ZoningDistrict).where(ZoningDistrict.code == code))
                if existing.scalar_one_or_none():
                    logger.debug(f"Zoning district already exists: {code}")
                    continue

                permitted = ZONE_USES[code]["permitted"]
                prohibited = ZONE_USES[code]["prohibited"]
                zone_kwargs = {k: v for k, v in zone_data.items() if k not in {"permitted_uses", "prohibited_uses"}}

                district = ZoningDistrict(**zone_kwargs)
                db.add(district)
                await db.flush()

                # Add permitted uses and their requirements
                for use_name in permitted:
                    use_flags = {
                        "requires_epa_approval": False,
                        "requires_heritage_review": False,
                        "requires_traffic_study": False
                    }
                    document_reqs = []

                    for doc_req in USE_REQUIREMENTS.get(use_name, []):
                        doc_code = doc_req["code"]
                        document = document_map.get(doc_code)
                        if not document:
                            logger.warning(f"⚠️ Document type {doc_code} not found for use: {use_name}")
                            continue

                        # Check and collect flags
                        for flag in ["requires_epa_approval", "requires_heritage_review", "requires_traffic_study"]:
                            if doc_req.get(flag):
                                use_flags[flag] = True

                        document_reqs.append(ZoningUseDocumentRequirement(
                            document_type_id=document.id,
                            is_mandatory=doc_req.get("is_mandatory", True),
                            phase=doc_req.get("phase", "application"),
                            notes=doc_req.get("notes")
                        ))

                    permitted_use = ZoningPermittedUse(
                        zoning_district_id=district.id,
                        use=use_name,
                        **use_flags,
                        required_documents=document_reqs
                    )
                    db.add(permitted_use)

                # Add prohibited uses
                db.add_all([
                    ZoningProhibitedUse(zoning_district_id=district.id, use=use)
                    for use in prohibited
                ])

                logger.debug(f"✅ Seeded zoning district: {code}")

            logger.info("✅ Zoning districts seeded (commit pending)")
            await db.commit()
            return True

        except Exception as e:
            logger.exception("🔥 Zoning district seeding failed")
            raise

    @staticmethod
    async def needs_seeding(db: AsyncSession) -> bool:
        result = await db.execute(select(func.count(ZoningDistrict.id)))
        count = result.scalar()
        return count == 0 or Settings.FORCE_SEED
