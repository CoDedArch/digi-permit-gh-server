from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.document import PermitTypeModel, PermitDocumentRequirement, DocumentTypeModel
from app.core.constants import PERMIT_REQUIREMENTS, PERMIT_TYPE_DATA, DOCUMENT_TYPES_DATA

class PermitSystemInitializer:
    
    @classmethod
    async def initialize_permit_types(cls, db: AsyncSession):
        """Seed PermitTypeModel from PERMIT_TYPE_DATA"""
        for data in PERMIT_TYPE_DATA:
            existing = await db.execute(
                select(PermitTypeModel).where(PermitTypeModel.id == data["id"])
            )
            if not existing.scalar():
                db.add(PermitTypeModel(**data))
        await db.commit()

    @classmethod
    async def initialize_document_types(cls, db: AsyncSession):
        """Seed document types from DOCUMENT_TYPES_DATA"""
        for data in DOCUMENT_TYPES_DATA:
            existing = await db.execute(
                select(DocumentTypeModel).where(DocumentTypeModel.code == data["code"])
            )
            if not existing.scalar():
                db.add(DocumentTypeModel(**data))
        await db.commit()

    @classmethod
    async def initialize_permit_requirements(cls, db: AsyncSession):
        """Seed PermitDocumentRequirement based on PERMIT_REQUIREMENTS"""
        # Load all document types into a dict by code
        documents = {
            doc.code: doc for doc in (await db.execute(select(DocumentTypeModel))).scalars().all()
        }

        # Load all permit types into a dict by id
        permit_types = {
            p.id: p for p in (await db.execute(select(PermitTypeModel))).scalars().all()
        }

        for permit_code, doc_entries in PERMIT_REQUIREMENTS.items():
            permit = permit_types.get(permit_code)
            if not permit:
                continue

            for entry in doc_entries:
                doc = documents.get(entry["code"])
                if not doc:
                    continue

                # Check for existing entry
                existing = await db.execute(
                    select(PermitDocumentRequirement).where(
                        PermitDocumentRequirement.permit_type_id == permit.id,
                        PermitDocumentRequirement.document_type_id == doc.id
                    )
                )
                if not existing.scalar():
                    db.add(PermitDocumentRequirement(
                        permit_type_id=permit.id,
                        document_type_id=doc.id,
                        is_mandatory=entry.get("is_mandatory", True),
                        phase=entry.get("phase", "application"),
                        notes=entry.get("notes")
                    ))
        await db.commit()
