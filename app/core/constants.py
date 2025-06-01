import enum

class PermitType(enum.Enum):
    # Core Types from Ghanaian Regulations
    RESIDENTIAL_SINGLE = "residential_single"           # Single-family homes
    RESIDENTIAL_COMPOUND = "residential_compound"       # Multi-family compound houses
    COMMERCIAL_RETAIL = "commercial_retail"             # Shops, markets (e.g., Kejetia stalls)
    COMMERCIAL_OFFICE = "commercial_office"             # Office buildings
    INDUSTRIAL_LIGHT = "industrial_light"               # Small-scale manufacturing
    INDUSTRIAL_HEAVY = "industrial_heavy"               # Factories, mining support
    INSTITUTIONAL = "institutional"                     # Schools, churches, hospitals
    PUBLIC_ASSEMBLY = "public_assembly"                 # Event venues, stadiums
    INFRASTRUCTURE = "infrastructure"                   # Roads, bridges (regulated by MWRWH)
    TEMPORARY_STRUCTURE = "temporary"                   # Construction sheds, event tents
    
    # Special Cases under LI 1630
    HERITAGE_ALTERATION = "heritage_alteration"         # Modifications to listed buildings
    COASTAL_DEVELOPMENT = "coastal_dev"                 # Projects within 100m of shoreline
    HIGH_RISE = "high_rise"                             # Buildings >6 floors (extra scrutiny)
    MINING_SUPPORT = "mining_support"                   # Structures for mining operations
    
    # Sub-Categories from Local Government Act
    MARKET_STALL = "market_stall"                       # Informal sector (kiosks, containers)
    AGRIC_STRUCTURE = "agric_structure"                 # Farm warehouses, processing units
    TELECOMM_TOWER = "telecomm_tower"                   # Cell towers (requires EPA approval)
    BILLBOARD_SIGN = "billboard_sign"                   # Large outdoor advertising

    def get_required_documents(self) -> list[str]:
        """Returns human-readable document names required for this permit type"""
        
        return DOCUMENT_MAP.get(self, [])

class UserRole(enum.Enum):
    APPLICANT = "applicant"
    REVIEW_OFFICER = "review_officer"
    INSPECTION_OFFICER = "inspection_officer"
    ADMIN = "admin"

class ApplicationStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ADDITIONAL_INFO_REQUESTED = "additional_info_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    INSPECTION_PENDING = "inspection_pending"
    COMPLETED = "completed"

class DocumentType(enum.Enum):
    SITE_PLAN = "site_plan"
    BUILDING_PLAN = "building_plan"
    STRUCTURAL_DRAWINGS = "structural_drawings"
    LAND_TITLE = "land_title"
    IDENTIFICATION = "identification"
    ENGINEER_REPORT = "engineer_report"
    OTHER = "other"

class DocumentStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ReviewStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ReviewOutcome(enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MORE_INFO = "needs_more_info"

class InspectionType(enum.Enum):
    SITE = "site"
    FOUNDATION = "foundation"
    FRAMING = "framing"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FINAL = "final"
    SPECIAL = "special"

class InspectionStatus(enum.Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class InspectionOutcome(enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_MONEY = "mobile_money"
    CREDIT_CARD = "credit_card"

class VerificationStage(enum.Enum):
    OTP_PENDING = "otp_pending"           
    OTP_VERIFIED = "otp_verified"
    DOCUMENT_PENDING = "document_pending"
    FULLY_VERIFIED = "fully_verified"

class PaymentPurpose(enum.Enum):
    APPLICATION_FEE = "application_fee"
    PROCESSING_FEE = "processing_fee"
    REVIEW_FEE = "review_fee"
    INSPECTION_FEE = "inspection_fee"
    PERMIT_ISSUANCE = "permit_issuance"
    PENALTY_FEE = "penalty_fee"
    OTHER = "other"

class NotificationType(enum.Enum):
    APPLICATION_SUBMITTED = "application_submitted"
    REVIEW_REQUESTED = "review_requested"
    ADDITIONAL_INFO_REQUESTED = "additional_info_requested"
    APPLICATION_APPROVED = "application_approved"
    APPLICATION_REJECTED = "application_rejected"
    INSPECTION_SCHEDULED = "inspection_scheduled"
    INSPECTION_RESULT = "inspection_result"
    PAYMENT_RECEIVED = "payment_received"
    SYSTEM_ALERT = "system_alert"

DOCUMENT_MAP = {
    # Residential
    PermitType.RESIDENTIAL_SINGLE: [
        "Completed Application Form",
        "Site Plan (approved by Survey Department)",
        "Architectural Drawings",
        "Land Title Certificate",
        "Structural Engineer's Report",
        "Indenture (if applicable)"
    ],
    PermitType.RESIDENTIAL_COMPOUND: [
        "Environmental Impact Assessment (EIA)",
        "Fire Safety Certificate",
        "Waste Management Plan",
        "All documents required for RESIDENTIAL_SINGLE"
    ],
    
    # Commercial
    PermitType.COMMERCIAL_RETAIL: [
        "Business Operating License",
        "Market Operators Association Approval (for market stalls)",
        "Accessibility Compliance Certificate",
        "Sanitary Facility Plans"
    ],
    PermitType.COMMERCIAL_OFFICE: [
        "Parking Space Allocation Plan",
        "Elevator Safety Certificate (for buildings >2 floors)",
        "Electrical Wiring Diagram"
    ],
    
    # Industrial
    PermitType.INDUSTRIAL_LIGHT: [
        "EPA Permit",
        "Noise Mitigation Plan",
        "Worker Safety Plan"
    ],
    PermitType.INDUSTRIAL_HEAVY: [
        "Ministry of Trade Approval",
        "Hazardous Materials Handling Plan",
        "All documents required for INDUSTRIAL_LIGHT"
    ],
    
    # Institutional/Public
    PermitType.INSTITUTIONAL: [
        "Ministry of Education/Health Approval (as applicable)",
        "Disability Access Compliance Certificate",
        "Emergency Evacuation Plan"
    ],
    PermitType.PUBLIC_ASSEMBLY: [
        "Ghana Fire Service Approval",
        "Public Health Certificate",
        "Crowd Control Plan"
    ],
    
    # Infrastructure
    PermitType.INFRASTRUCTURE: [
        "Ministry of Roads and Highways Approval",
        "Traffic Impact Assessment",
        "Geotechnical Survey Report"
    ],
    
    # Special Cases
    PermitType.HERITAGE_ALTERATION: [
        "Ghana Museums & Monuments Board Approval",
        "Historical Impact Assessment",
        "Conservation Method Statement"
    ],
    PermitType.COASTAL_DEVELOPMENT: [
        "EPA Coastal Zone Permit",
        "Erosion Control Plan",
        "Marine Impact Study"
    ],
    PermitType.HIGH_RISE: [
        "Wind Load Analysis Report",
        "Seismic Stability Report",
        "Crane Operation Plan"
    ],
    PermitType.MINING_SUPPORT: [
        "Minerals Commission Permit",
        "Mine Safety Compliance Certificate",
        "Explosives Storage Plan (if applicable)"
    ],
    
    # Local Government Categories
    PermitType.MARKET_STALL: [
        "Assembly Business Permit",
        "Market Allocation Letter",
        "Simple Sketch Plan"
    ],
    PermitType.AGRIC_STRUCTURE: [
        "Ministry of Food & Agriculture Approval",
        "Pest Control Plan",
        "Water Runoff Management Plan"
    ],
    PermitType.TELECOMM_TOWER: [
        "NCA Frequency Authorization",
        "Radiation Safety Certificate",
        "Aviation Light Compliance"
    ],
    PermitType.BILLBOARD_SIGN: [
        "Advertising Standards Authority Permit",
        "Structural Integrity Certificate",
        "Lighting Impact Assessment (for illuminated signs)"
    ],
    
    # Temporary Structures
    PermitType.TEMPORARY_STRUCTURE: [
        "Temporary Occupation Permit",
        "Demolition Bond (if applicable)",
        "Duration of Use Declaration"
    ]
}