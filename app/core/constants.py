import enum
from typing import Dict, List
from sqlalchemy.sql import exists

class PermitType(str, enum.Enum):
    """
    Simplified to focus on the ACTION being requested, not the building type.
    Building types are handled by zoning permitted uses.
    """
    NEW_CONSTRUCTION = "new_construction"
    RENOVATION = "renovation"
    CHANGE_OF_USE = "change_of_use"
    DEMOLITION = "demolition"
    TEMPORARY = "temporary"
    SIGN_PERMIT = "sign_permit"
    SUBDIVISION = "subdivision"
    
    @property
    def display_name(self) -> str:
        names = {
            "new_construction": "New Construction",
            "renovation": "Renovation/Alteration",
            "change_of_use": "Change of Building Use",
            "demolition": "Demolition Permit",
            "temporary": "Temporary Structure",
            "sign_permit": "Signage/Billboard",
            "subdivision": "Land Subdivision"
        }
        return names[self.value]


PERMIT_TYPE_DATA = [
{
    "id": PermitType.NEW_CONSTRUCTION.value,
    "name": PermitType.NEW_CONSTRUCTION.display_name,
    "description": "Permits for constructing new buildings or major structural additions.",
    "base_fee": 500.00,
    "standard_duration_days": 90,
    "is_active": True
},
{
    "id": PermitType.RENOVATION.value,
    "name": PermitType.RENOVATION.display_name,
    "description": "Covers alterations, interior remodels, or improvements to existing structures.",
    "base_fee": 250.00,
    "standard_duration_days": 60,
    "is_active": True
},
{
    "id": PermitType.CHANGE_OF_USE.value,
    "name": PermitType.CHANGE_OF_USE.display_name,
    "description": "Required when the intended use of a building is being changed (e.g. residential to commercial).",
    "base_fee": 200.00,
    "standard_duration_days": 45,
    "is_active": True
},
{
    "id": PermitType.DEMOLITION.value,
    "name": PermitType.DEMOLITION.display_name,
    "description": "Covers full or partial demolition of structures.",
    "base_fee": 150.00,
    "standard_duration_days": 30,
    "is_active": True
},
{
    "id": PermitType.TEMPORARY.value,
    "name": PermitType.TEMPORARY.display_name,
    "description": "For temporary structures such as event tents or kiosks.",
    "base_fee": 100.00,
    "standard_duration_days": 15,
    "is_active": True
},
{
    "id": PermitType.SIGN_PERMIT.value,
    "name": PermitType.SIGN_PERMIT.display_name,
    "description": "Permits for billboards, business signage, and other advertising structures.",
    "base_fee": 75.00,
    "standard_duration_days": 20,
    "is_active": True
},
{
    "id": PermitType.SUBDIVISION.value,
    "name": PermitType.SUBDIVISION.display_name,
    "description": "For dividing land parcels into multiple lots for development or sale.",
    "base_fee": 600.00,
    "standard_duration_days": 120,
    "is_active": True
},
]

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
    ISSUED = "issued"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DocumentType(enum.Enum):
    SITE_PLAN = "site_plan"
    BUILDING_PLAN = "building_plan"
    STRUCTURAL_DRAWINGS = "structural_drawings"
    LAND_TITLE = "land_title"
    IDENTIFICATION = "identification"
    ENGINEER_REPORT = "engineer_report"
    OTHER = "other"

PERMIT_REQUIREMENTS = {
    "new_construction": [
        {"code": "site_plan", "phase": "application"},
        {"code": "architectural_drawings", "phase": "application"},
        {"code": "structural_drawings", "phase": "review"},
        {"code": "zoning_clearance", "phase": "application"},
        {"code": "ownership_documents", "phase": "application"},
        {"code": "building_permit_form", "phase": "application"},
    ],
    "renovation": [
        {"code": "site_plan"},
        {"code": "architectural_drawings"},
        {"code": "ownership_documents"},
    ],
    "change_of_use": [
        {"code": "site_plan"},
        {"code": "zoning_clearance"},
        {"code": "building_permit_form"},
    ],
    "demolition": [
        {"code": "site_plan"},
        {"code": "structural_drawings"},
        {"code": "ownership_documents"},
        {"code": "building_permit_form"},
    ],
    "temporary": [
        {"code": "site_plan"},
        {"code": "building_permit_form"},
        {"code": "fire_safety"},
    ],
    "sign_permit": [
        {"code": "site_plan"},
        {"code": "ownership_documents"},
    ],
    "subdivision": [
        {"code": "survey_plan"},
        {"code": "ownership_documents"},
        {"code": "zoning_clearance"},
    ]
}


DOCUMENT_TYPES_DATA = [
    {
        "name": "Site Plan",
        "code": "site_plan",
        "description": "Detailed layout of the proposed development showing boundaries, building footprints, roads, and setbacks.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Architectural Drawings",
        "code": "architectural_drawings",
        "description": "Blueprints or CAD drawings showing building design, floor plans, elevations, and sections.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Structural Drawings",
        "code": "structural_drawings",
        "description": "Engineering drawings for foundation, framing, and structural integrity.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Zoning Clearance",
        "code": "zoning_clearance",
        "description": "Official documentation confirming that the development conforms to current zoning regulations.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Environmental Impact Assessment (EIA)",
        "code": "eia_report",
        "description": "Report assessing the potential environmental consequences of the proposed development.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Fire Safety Certificate",
        "code": "fire_safety",
        "description": "Certificate verifying fire safety compliance for the proposed structure.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Building Permit Application Form",
        "code": "building_permit_form",
        "description": "Completed application form required for processing building permits.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Survey Plan",
        "code": "survey_plan",
        "description": "Cadastral map showing property boundaries and measurements prepared by a licensed surveyor.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Ownership Documents",
        "code": "ownership_documents",
        "description": "Land title or leasehold agreements verifying legal ownership of the property.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Utility Connection Approvals",
        "code": "utility_approvals",
        "description": "Evidence of approved connections to electricity, water, and waste services.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Traffic Impact Assessment (TIA)",
        "code": "tia_report",
        "description": "Analysis report evaluating the development's impact on traffic flow and safety.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Heritage Impact Statement",
        "code": "heritage_impact",
        "description": "Required if the site or nearby areas have heritage significance.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Drainage Plan",
        "code": "drainage_plan",
        "description": "Details stormwater drainage systems and flood mitigation strategies.",
        "is_custom": False,
        "is_active": True,
    },
    {
        "name": "Geotechnical Report",
        "code": "geotechnical_report",
        "description": "Provides soil analysis and ground stability for construction purposes.",
        "is_custom": False,
        "is_active": True,
    },
]

class DocumentStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"

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

class ZoneType(str, enum.Enum):
    # Rural Zones
    RURAL_A = "Ru A"  # Low-intensity agriculture, fragile lands
    RURAL_B = "Ru B"  # Intensive cultivation, plantations
    
    # Residential Zones
    RESIDENTIAL_A = "Re A"  # Low density (10-15 dwellings/ha)
    RESIDENTIAL_B = "Re B"  # Medium density (16-30 dwellings/ha)
    RESIDENTIAL_C = "Re C"  # High density (>30 dwellings/ha)
    RESIDENTIAL_D = "Re D"  # Multi-storey apartments
    RESIDENTIAL_E = "Re E"  # Community dwellings (hostels, barracks)
    REDEVELOPMENT_ZONE = "Re Z"  # Slum upgrading areas
    
    # Education Zones
    EDUCATION_PRIMARY = "Ed P"  # Nursery, Primary, JHS
    EDUCATION_SECONDARY = "Ed S"  # SHS, Vocational schools
    EDUCATION_TERTIARY = "Ed T"  # Universities, Polytechnics
    
    # Health Zones
    HEALTH_CLINIC = "H CI"  # Clinics
    HEALTH_POST = "H P"  # Health posts
    HEALTH_CENTER = "H C"  # Health centers
    HEALTH_POLYCLINIC = "H Po"  # Urban health centers
    HEALTH_DISTRICT_HOSPITAL = "H G"  # District hospitals
    HEALTH_REGIONAL_HOSPITAL = "H R"  # Regional/Teaching hospitals
    
    # Business/Commercial Zones
    CENTRAL_BUSINESS_DISTRICT = "CBD"
    SUB_REGIONAL_BUSINESS = "SBC"  # Sub-regional business centers
    MIXED_BUSINESS = "BM"  # Mixed business/residential
    INFORMAL_BUSINESS = "BL"  # Local markets, kiosks
    GOVERNMENT_BUSINESS = "BG"  # Government offices
    
    # Industrial Zones
    LIGHT_INDUSTRIAL = "LI"  # Clean, low-pollution industries
    SERVICE_INDUSTRY = "IS"  # Repair workshops, motor traders
    GENERAL_INDUSTRIAL = "IG"  # Manufacturing, food processing
    NOXIOUS_INDUSTRIAL = "IN"  # Hazardous industries (chemicals, slaughterhouses)
    EXTRACTIVE_INDUSTRIAL = "IE"  # Mining, quarrying
    
    # Special Use Zones
    PLACES_OF_WORSHIP = "PW"
    RECREATION_SPORTS = "RS"  # Stadiums, golf courses
    PUBLIC_OPEN_SPACE = "POS"  # Parks, gardens
    PROTECTED_COASTAL = "CZ"  # Coastal/waterfront protection
    CONSERVATION_AREA = "CA"  # Forests, wildlife habitats
    TRANSPORT_WAREHOUSING = "TW"  # Airports, ports, freight terminals
    
    # Tourism Zone
    TOURIST_ZONE = "T"  # Hotels, resorts, cultural sites
    
    # Emergency/Utility Zones
    SPECIAL_EMERGENCY = "SE"  # Fire stations, ambulance depots
    SPECIAL_UTILITY = "SU"  # Power plants, sewage treatment
    SPECIAL_SECURITY = "SM"  # Military, police facilities
    
    # Other
    HERBAL_MEDICINE = "HM"  # Herbal medicine facilities
    FOREST_RESERVE = "FR"  # Protected forest areas
    COMMERCIAL_TIMBER = "FC"  # Timber production areas

class RequirementPhase(str, enum.Enum):
    APPLICATION = "application"
    REVIEW = "review"
    CONSTRUCTION = "construction"
    POST_APPROVAL = "post_approval"


DOCUMENT_REQUIREMENTS = {
    # Core Action-Based Requirements
    PermitType.NEW_CONSTRUCTION: {
        "base_requirements": [
            {"name": "Completed Application Form", "phase": RequirementPhase.APPLICATION},
            {"name": "Site Plan", "phase": RequirementPhase.APPLICATION, 
             "conditional": "not is_temporary"},
            {"name": "Architectural Drawings", "phase": RequirementPhase.APPLICATION},
            {"name": "Land Title Certificate", "phase": RequirementPhase.APPLICATION}
        ],
        "zoning_specific": {
            ZoneType.RESIDENTIAL_A: [
                {"name": "Neighborhood Impact Statement", "phase": RequirementPhase.REVIEW}
            ],
            ZoneType.CENTRAL_BUSINESS_DISTRICT: [
                {"name": "Traffic Management Plan", "phase": RequirementPhase.REVIEW},
                {"name": "Pedestrian Flow Analysis", "phase": RequirementPhase.REVIEW}
            ]
        }
    },
    
    PermitType.CHANGE_OF_USE: {
        "base_requirements": [
            {"name": "Current Floor Plans", "phase": RequirementPhase.APPLICATION},
            {"name": "Proposed Floor Plans", "phase": RequirementPhase.APPLICATION},
            {"name": "Zoning Compliance Letter", "phase": RequirementPhase.REVIEW}
        ],
        "zoning_specific": {
            ZoneType.LIGHT_INDUSTRIAL: [
                {"name": "EPA Preliminary Assessment", "phase": RequirementPhase.APPLICATION}
            ]
        }
    },
    
    # Special Process Requirements
    "special_processes": {
        "heritage_site": [
            {"name": "Heritage Impact Assessment", "phase": RequirementPhase.REVIEW}
        ],
        "coastal_zone": [
            {"name": "Coastal Erosion Study", "phase": RequirementPhase.REVIEW}
        ],
        "high_rise": [
            {"name": "Wind Load Analysis", "phase": RequirementPhase.REVIEW}
        ]
    }
}


ZONE_USES: Dict[ZoneType, Dict[str, List[str]]] = {
    # -------------------------------------------------------------------------
    # RURAL ZONES
    # -------------------------------------------------------------------------
    ZoneType.RURAL_A: {
        "permitted": [
            "Low-intensity agriculture",
            "Forestry/tree crops",
            "Detached/compound houses",
            "Cottage industries",
            "Public open space",
            "Community facilities"
        ],
        "prohibited": [
            "Large-scale industry",
            "Mechanized agriculture",
            "Commercial development",
            "Mass transportation facilities"
        ]
    },
    ZoneType.RURAL_B: {
        "permitted": [
            "Animal husbandry",
            "Intensive crop farming",
            "Plantations",
            "Farm houses",
            "Agro-processing"
        ],
        "prohibited": [
            "Residential subdivisions",
            "Industrial development",
            "Urban infrastructure"
        ]
    },

    # -------------------------------------------------------------------------
    # RESIDENTIAL ZONES
    # -------------------------------------------------------------------------
    ZoneType.RESIDENTIAL_A: {
        "permitted": [
            "Detached houses",
            "Duplexes",
            "Home businesses (max 2 employees)",
            "Clinics (<250m²)",
            "Places of worship (<250m²)",
            "Childcare facilities"
        ],
        "prohibited": [
            "Apartments/flats",
            "Industries",
            "Large commercial",
            "Animal husbandry"
        ]
    },
    ZoneType.RESIDENTIAL_B: {
        "permitted": [
            "Semi-detached houses",
            "Row houses",
            "Corner shops",
            "Basic schools",
            "Community centers"
        ],
        "prohibited": [
            "Heavy commercial",
            "Manufacturing",
            "Transport depots"
        ]
    },
    ZoneType.RESIDENTIAL_C: {
        "permitted": [
            "Compound houses",
            "Mixed-use (residential/commercial)",
            "Local markets",
            "Informal businesses"
        ],
        "prohibited": [
            "Large industries",
            "Hazardous activities",
            "Slaughterhouses"
        ]
    },
    ZoneType.RESIDENTIAL_D: {
        "permitted": [
            "Multi-storey flats/apartments",
            "Shops at ground floor level",
            "Clinics/pharmacies",
            "Public open spaces",
            "Guest houses/small hotels"
        ],
        "prohibited": [
            "Industrial development",
            "Standalone commercial buildings",
            "Animal husbandry"
        ]
    },
    ZoneType.RESIDENTIAL_E: {
        "permitted": [
            "Hostels/boarding houses",
            "Barracks",
            "Institutional housing",
            "Restaurants/eating places"
        ],
        "prohibited": [
            "Large commercial development",
            "Industrial activities",
            "Markets over 1,000m²"
        ]
    },
    ZoneType.REDEVELOPMENT_ZONE: {
        "permitted": [
            "Residential upgrading",
            "Local markets",
            "Mixed uses",
            "Corner shops"
        ],
        "prohibited": [
            "Large-scale relocation",
            "Heavy infrastructure",
            "Hazardous industries"
        ]
    },
        # -------------------------------------------------------------------------
    # MISSING ZONES (Adding TW, HM, FR, FC)
    # -------------------------------------------------------------------------
    ZoneType.TRANSPORT_WAREHOUSING: {
        "permitted": [
            "Airports/ports",
            "Freight terminals",
            "Ancillary offices",
            "Parking facilities"
        ],
        "prohibited": [
            "Residential development",
            "Educational facilities",
            "Hospitals"
        ]
    },
    ZoneType.HERBAL_MEDICINE: {
        "permitted": [
            "Herbal clinics",
            "Medicinal plant cultivation",
            "Research facilities"
        ],
        "prohibited": [
            "Conventional pharmaceuticals",
            "Industrial activities",
            "Large-scale commercial"
        ]
    },
    ZoneType.FOREST_RESERVE: {
        "permitted": [
            "Eco-tourism",
            "Research activities",
            "Limited timber harvesting"
        ],
        "prohibited": [
            "Permanent structures",
            "Agriculture",
            "Industrial activities"
        ]
    },
    ZoneType.COMMERCIAL_TIMBER: {
        "permitted": [
            "Timber production",
            "Nurseries",
            "Processing facilities"
        ],
        "prohibited": [
            "Residential development",
            "Non-forestry industries",
            "Urban infrastructure"
        ]
    },
    # -------------------------------------------------------------------------
    # EDUCATION ZONES (Adding all education zones)
    # -------------------------------------------------------------------------
    ZoneType.EDUCATION_PRIMARY: {
        "permitted": [
            "Nursery/Primary/JHS",
            "Teachers' accommodation",
            "Playgrounds",
            "School clinics"
        ],
        "prohibited": [
            "Transport depots",
            "Animal husbandry",
            "Industrial activities"
        ]
    },
    ZoneType.EDUCATION_SECONDARY: {
        "permitted": [
            "SHS/Vocational schools",
            "Students' hostels",
            "Science labs",
            "Sports facilities"
        ],
        "prohibited": [
            "Large markets",
            "Industrial workshops",
            "Commercial warehouses"
        ]
    },
    ZoneType.EDUCATION_TERTIARY: {
        "permitted": [
            "Universities/Polytechnics",
            "Research facilities",
            "Student housing",
            "Campus retail"
        ],
        "prohibited": [
            "Heavy industries",
            "Large-scale commercial",
            "Transport terminals"
        ]
    },
    # -------------------------------------------------------------------------
    # COMMERCIAL ZONES
    # -------------------------------------------------------------------------
    ZoneType.CENTRAL_BUSINESS_DISTRICT: {
        "permitted": [
            "Offices",
            "Banks",
            "Hotels",
            "High-rise apartments",
            "Government buildings"
        ],
        "prohibited": [
            "Industrial manufacturing",
            "Single-unit housing",
            "Animal husbandry"
        ]
    },
    ZoneType.INFORMAL_BUSINESS: {
        "permitted": [
            "Street vending",
            "Artisan workshops",
            "Micro-retail (<20m²)"
        ],
        "prohibited": [
            "Large warehouses",
            "Heavy manufacturing",
            "Noxious industries"
        ]
    },

    # -------------------------------------------------------------------------
    # INDUSTRIAL ZONES
    # -------------------------------------------------------------------------
    ZoneType.LIGHT_INDUSTRIAL: {
        "permitted": [
            "Electronics assembly",
            "Jewelry making",
            "Medical equipment",
            "Small-scale printing"
        ],
        "prohibited": [
            "Chemical processing",
            "Metal smelting",
            "Waste disposal"
        ]
    },
    ZoneType.NOXIOUS_INDUSTRIAL: {
        "permitted": [
            "Slaughterhouses",
            "Cement production",
            "Chemical plants"
        ],
        "prohibited": [
            "Residential housing",
            "Schools/hospitals",
            "Food markets"
        ]
    },
    # -------------------------------------------------------------------------
    # BUSINESS/COMMERCIAL (Adding missing SBC, BM, BG)
    # -------------------------------------------------------------------------
    ZoneType.SUB_REGIONAL_BUSINESS: {
        "permitted": [
            "Regional markets",
            "Cold storage",
            "Government offices",
            "Service industries"
        ],
        "prohibited": [
            "Heavy industry",
            "Residential development",
            "Hazardous activities"
        ]
    },
    ZoneType.MIXED_BUSINESS: {
        "permitted": [
            "Professional offices",
            "Medical clinics",
            "Motor traders",
            "Residential above commercial"
        ],
        "prohibited": [
            "Heavy manufacturing",
            "Industrial repair",
            "Ground-floor residential"
        ]
    },
    ZoneType.GOVERNMENT_BUSINESS: {
        "permitted": [
            "Government offices",
            "Libraries",
            "Police posts",
            "Ancillary services"
        ],
        "prohibited": [
            "Private commercial",
            "Industrial activities",
            "Residential use"
        ]
    },

    # -------------------------------------------------------------------------
    # INDUSTRIAL (Adding missing IS, IG, IE)
    # -------------------------------------------------------------------------
    ZoneType.SERVICE_INDUSTRY: {
        "permitted": [
            "Motor repairs",
            "Dry cleaning",
            "Tailoring",
            "Small workshops"
        ],
        "prohibited": [
            "Heavy manufacturing",
            "Hazardous materials",
            "Large-scale warehousing"
        ]
    },
    ZoneType.GENERAL_INDUSTRIAL: {
        "permitted": [
            "Food processing",
            "Vehicle assembly",
            "Warehousing (<50% area)"
        ],
        "prohibited": [
            "Hazardous industries",
            "Residential development",
            "Large commercial"
        ]
    },
    ZoneType.EXTRACTIVE_INDUSTRIAL: {
        "permitted": [
            "Quarrying",
            "Mining",
            "Ancillary processing"
        ],
        "prohibited": [
            "Residential within 1km",
            "Permanent structures in operational areas",
            "Sensitive land uses"
        ]
    },
    # -------------------------------------------------------------------------
    # SPECIAL ZONES (Partial examples - add others similarly)
    # -------------------------------------------------------------------------
    ZoneType.PROTECTED_COASTAL: {
        "permitted": [
            "Eco-tourism",
            "Fishing",
            "Boat building"
        ],
        "prohibited": [
            "Sand winning",
            "Heavy industry",
            "Permanent structures <100m from shoreline"
        ]
    },
    ZoneType.PLACES_OF_WORSHIP: {
        "permitted": [
            "Churches/mosques",
            "Pastoral housing",
            "Religious schools",
            "Social centers"
        ],
        "prohibited": [
            "Industrial activities",
            "Large commercial",
            "Animal husbandry"
        ]
    },
    ZoneType.RECREATION_SPORTS: {
        "permitted": [
            "Sports fields",
            "Club houses",
            "Ancillary facilities"
        ],
        "prohibited": [
            "Residential development",
            "Industrial activities",
            "Permanent commercial"
        ]
    },
    ZoneType.PUBLIC_OPEN_SPACE: {
        "permitted": [
            "Parks/gardens",
            "Children's play areas",
            "Incidental structures"
        ],
        "prohibited": [
            "Permanent buildings",
            "Commercial development",
            "Industrial activities"
        ]
    },
    ZoneType.CONSERVATION_AREA: {
        "permitted": [
            "Eco-tourism",
            "Research facilities",
            "Limited recreation"
        ],
        "prohibited": [
            "Urban development",
            "Industrial activities",
            "Intensive cultivation"
        ]
    },
    ZoneType.TOURIST_ZONE: {
        "permitted": [
            "Hotels/resorts",
            "Cultural facilities",
            "Artisan shops"
        ],
        "prohibited": [
            "Heavy industry",
            "Large-scale commercial",
            "Hazardous activities"
        ]
    },
    ZoneType.SPECIAL_EMERGENCY: {
        "permitted": [
            "Fire stations",
            "Ambulance depots",
            "Disaster response"
        ],
        "prohibited": [
            "Commercial development",
            "Residential use",
            "Industrial activities"
        ]
    },
    ZoneType.SPECIAL_UTILITY: {
        "permitted": [
            "Power plants",
            "Water treatment",
            "Waste facilities"
        ],
        "prohibited": [
            "Residential development",
            "Commercial activities",
            "Sensitive land uses"
        ]
    },
    ZoneType.SPECIAL_SECURITY: {
        "permitted": [
            "Military facilities",
            "Police training",
            "Ammunition storage"
        ],
        "prohibited": [
            "Civilian housing",
            "Commercial development",
            "Public access areas"
        ]
    },
    # -------------------------------------------------------------------------
    # HEALTH ZONES (Completing all health sub-zones)
    # -------------------------------------------------------------------------
    ZoneType.HEALTH_CLINIC: {
        "permitted": [
            "OPD services",
            "Maternal/child care",
            "Staff housing"
        ],
        "prohibited": [
            "Industrial activities",
            "Petrol stations",
            "Large commercial"
        ]
    },
    ZoneType.HEALTH_POST: {
        "permitted": [
            "Basic medical care",
            "Immunization",
            "Staff quarters"
        ],
        "prohibited": [
            "In-patient wards",
            "Surgical facilities",
            "Industrial uses"
        ]
    },
    ZoneType.HEALTH_CENTER: {
        "permitted": [
            "Basic hospitalization",
            "Laboratory services",
            "Ambulance services"
        ],
        "prohibited": [
            "Specialist care",
            "Large-scale commercial",
            "Industrial activities"
        ]
    },
    ZoneType.HEALTH_POLYCLINIC: {
        "permitted": [
            "Specialist clinics",
            "Minor surgery",
            "Diagnostic imaging"
        ],
        "prohibited": [
            "Major surgery",
            "Industrial activities",
            "Large markets"
        ]
    },
    ZoneType.HEALTH_REGIONAL_HOSPITAL: {
        "permitted": [
            "Specialist medical blocks",
            "Teaching facilities",
            "Research centers"
        ],
        "prohibited": [
            "Industrial development",
            "Large commercial",
            "Residential (non-staff)"
        ]
    },

    ZoneType.HEALTH_DISTRICT_HOSPITAL: {
        "permitted": [
            "Medical facilities",
            "Staff housing",
            "Ambulance services"
        ],
        "prohibited": [
            "Industrial activities",
            "Entertainment venues",
            "Petrol stations"
        ]
    }
}




ZONE_DATA: List[Dict] = [
    # -------------------------------------------------------------------------
    # RURAL ZONES (2)
    # -------------------------------------------------------------------------
    {
        "code": ZoneType.RURAL_A,
        "name": "Rural Zone A",
        "description": "Low-intensity agricultural use (grazing, shifting cultivation). Protects fragile lands and water catchments.",
        "max_height": 7.5,  # meters (2 storeys max)
        "max_coverage": 0.3,  # 30%
        "min_plot_size": 40000,  # 4ha (from Table 8)
        "color_code": "Light Green"
    },
    {
        "code": ZoneType.RURAL_B,
        "name": "Rural Zone B",
        "description": "Intensive cultivation, plantations, and animal husbandry. High-quality agricultural soils.",
        "max_height": 7.5,
        "max_coverage": 0.3,
        "min_plot_size": 4000,  # m²
        "color_code": "Light Green"
    },

    # -------------------------------------------------------------------------
    # RESIDENTIAL ZONES (6)
    # -------------------------------------------------------------------------
    {
        "code": ZoneType.RESIDENTIAL_A,
        "name": "Residential Low Density",
        "description": "Detached houses (10-15 dwellings/ha). Plot sizes ≥500m². Home businesses allowed with restrictions.",
        "max_height": 12.0,  # (Table 9)
        "max_coverage": 0.45,  # 45%
        "min_plot_size": 500,  # m² (Section 2.4.3)
        "color_code": "Pale Yellow Ochre",
        "density": "10-15 dwellings/ha"
    },
    {
        "code": ZoneType.RESIDENTIAL_B,
        "name": "Residential Medium Density",
        "description": "Mix of detached, semi-detached, and row houses (16-30 dwellings/ha). Local shops permitted.",
        "max_height": 8.5,
        "max_coverage": 0.6,  # 60% for detached
        "min_plot_size": 235,
        "color_code": "Yellow Ochre",
        "density": "16-30 dwellings/ha"
    },
    {
        "code": ZoneType.RESIDENTIAL_C,
        "name": "Residential High Density",
        "description": "High-density urban housing (>30 dwellings/ha). Minimum plot size 110m² with upgrading provisions.",
        "max_height": 7.5,
        "max_coverage": 0.7,  # 70% for detached
        "min_plot_size": 110,
        "color_code": "Dark Yellow Ochre",
        "density": ">30 dwellings/ha"
    },
    {
        "code": ZoneType.RESIDENTIAL_D,
        "name": "Residential Multi-Storey",
        "description": "Flats/apartments (max 300 persons/ha). Ground floor commercial permitted. Parking required.",
        "max_height": 20.0,  # 5 storeys without lift
        "max_coverage": 0.35,
        "min_plot_size": 1000,
        "color_code": "Dark Yellow Ochre",
        "density": "Max 300 persons/ha"
    },
    {
        "code": ZoneType.RESIDENTIAL_E,
        "name": "Residential Institutional",
        "description": "Community dwellings (barracks, hostels, guest houses >6 rooms). Located near transport nodes.",
        "max_height": 25.0,
        "max_coverage": 0.35,
        "min_plot_size": 1000,
        "color_code": "Dark Yellow Ochre",
        "parking_requirement": "2 spaces per 5 units"
    },
    {
        "code": ZoneType.REDEVELOPMENT_ZONE,
        "name": "Redevelopment/Upgrading Zone",
        "description": "High-density informal areas targeted for environmental upgrading with minimal relocation.",
        "max_height": None,  # Case-by-case
        "max_coverage": None,  # Flexible standards
        "min_plot_size": None,
        "color_code": "Broken black line boundary",
        "special_notes": "Upgrading strategy prioritizes minimal relocation"
    },

    # -------------------------------------------------------------------------
    # EDUCATION ZONES (3)
    # -------------------------------------------------------------------------
    {
        "code": ZoneType.EDUCATION_PRIMARY,
        "name": "Education Zone (Primary/JHS)",
        "description": "Nursery, Primary and Junior High Schools. Must be within walking distance of neighborhoods.",
        "max_height": 10.0,  # 2 storeys encouraged
        "max_coverage": 0.4,
        "min_plot_size": 12140,  # 1.214ha (Table 1)
        "color_code": "Citrus Yellow",
    },
    {
        "code": ZoneType.EDUCATION_SECONDARY,
        "name": "Education Zone (SHS/Vocational)",
        "description": "Senior High Schools and Technical/Vocational institutions. 4-8ha sites recommended.",
        "max_height": 12.0,
        "max_coverage": 0.35,
        "min_plot_size": 16200,  # 1.62ha
        "color_code": "Citrus Yellow"
    },
    {
        "code": ZoneType.EDUCATION_TERTIARY,
        "name": "Education Zone (Tertiary)",
        "description": "Universities, Polytechnics, and specialized institutions. Requires serene environments.",
        "max_height": 25.0,
        "max_coverage": 0.3,
        "min_plot_size": 40500,  # 4.05ha
        "color_code": "Citrus Yellow"
    },

    # -------------------------------------------------------------------------
    # HEALTH ZONES (6)
    # -------------------------------------------------------------------------
    {
        "code": ZoneType.HEALTH_CLINIC,
        "name": "Health Zone A (Clinic)",
        "description": "Basic health services (OPD, immunization). Max 10 mins walking distance from homes.",
        "max_height": 8.0,
        "max_coverage": 0.5,
        "min_plot_size": 2000,  # ~0.5ha
        "color_code": "Deep Red",
        "population_served": "Up to 5,000"
    },
    {
        "code": ZoneType.HEALTH_POST,
        "name": "Health Zone B (Health Post)",
        "description": "Serves 200-5,000 people. Provides basic OPD, maternal care, and immunization services.",
        "max_height": 8.0,
        "max_coverage": 0.5,
        "min_plot_size": 5000,  # 0.5ha
        "color_code": "Deep Red"
    },
    {
        "code": ZoneType.HEALTH_CENTER,
        "name": "Health Zone C (Health Centre)",
        "description": "Serves sub-districts (15-20km radius). Includes labs, X-ray, and 5-10 observation beds.",
        "max_height": 10.0,
        "max_coverage": 0.4,
        "min_plot_size": 15000,  # 1.5ha
        "color_code": "Deep Red"
    },
    {
        "code": ZoneType.HEALTH_POLYCLINIC,
        "name": "Health Zone D (Polyclinic)",
        "description": "Urban health centers with minor surgery capabilities. Serves 60,000-100,000 people.",
        "max_height": 12.0,
        "max_coverage": 0.35,
        "min_plot_size": 50000,  # 5ha
        "color_code": "Deep Red"
    },
    {
        "code": ZoneType.HEALTH_DISTRICT_HOSPITAL,
        "name": "Health Zone E (District Hospital)",
        "description": "General hospitals serving districts (60-120 beds). Requires 10ha minimum site.",
        "max_height": 15.0,
        "max_coverage": 0.3,
        "min_plot_size": 100000,  # 10ha
        "color_code": "Deep Red"
    },
    {
        "code": ZoneType.HEALTH_REGIONAL_HOSPITAL,
        "name": "Health Zone F (Regional/Teaching Hospital)",
        "description": "Referral hospitals with specialist services (150-300 beds). 15ha minimum site.",
        "max_height": 20.0,
        "max_coverage": 0.25,
        "min_plot_size": 150000,  # 15ha
        "color_code": "Deep Red"
    },

    # -------------------------------------------------------------------------
    # BUSINESS/COMMERCIAL ZONES (5)
    # -------------------------------------------------------------------------
    {
        "code": ZoneType.CENTRAL_BUSINESS_DISTRICT,
        "name": "Central Business District",
        "description": "High-intensity commercial core with high-rise development. Requires traffic impact studies.",
        "max_height": None,  # Case-by-case
        "max_coverage": 0.8,  # 80%
        "min_plot_size": 250,
        "color_code": "Powder Blue",
        "parking_requirement": "1 space per 200m² floor area"
    },
    {
        "code": ZoneType.SUB_REGIONAL_BUSINESS,
        "name": "Sub-Regional Business Center",
        "description": "Secondary commercial nodes with cold storage, bulk breaking, and major retail.",
        "max_height": 20.0,
        "max_coverage": 0.6,
        "min_plot_size": 300,
        "color_code": "Powder Blue"
    },
    {
        "code": ZoneType.MIXED_BUSINESS,
        "name": "Mixed Business Zone",
        "description": "Lower-intensity commercial with professional offices and ground-floor retail.",
        "max_height": 25.0,
        "max_coverage": 0.75,
        "min_plot_size": 300,
        "color_code": "Diagonal stripes (Blue/Yellow)"
    },
    {
        "code": ZoneType.INFORMAL_BUSINESS,
        "name": "Informal Business Zone",
        "description": "Local markets (<1ha) and micro-enterprises. Maximum floor area 250m² for businesses.",
        "max_height": 8.6,
        "max_coverage": 0.75,
        "min_plot_size": 250,
        "color_code": "Powder Blue"
    },
    {
        "code": ZoneType.GOVERNMENT_BUSINESS,
        "name": "Government Business Zone",
        "description": "Civic centers and government offices. High amenity standards required.",
        "max_height": 15.0,
        "max_coverage": 0.4,
        "min_plot_size": 500,
        "color_code": "Deep Red"
    },

    # -------------------------------------------------------------------------
    # INDUSTRIAL ZONES (5)
    # -------------------------------------------------------------------------
    {
        "code": ZoneType.LIGHT_INDUSTRIAL,
        "name": "Light Industrial Zone",
        "description": "Clean, low-pollution industries (electronics, medical devices). Max 500m² ancillary offices.",
        "max_height": 6.5,
        "max_coverage": 0.6,
        "min_plot_size": 1000,
        "color_code": "Violet-Purple",
        "setbacks": "10m front, 6m sides/rear"
    },
    {
        "code": ZoneType.SERVICE_INDUSTRY,
        "name": "Service Industry Zone",
        "description": "Small workshops, motor repairs, and tradesman depots. Max 250m² floor area.",
        "max_height": 6.5,
        "max_coverage": 0.6,
        "min_plot_size": 250,
        "color_code": "Violet-Purple"
    },
    {
        "code": ZoneType.GENERAL_INDUSTRIAL,
        "name": "General Industrial Zone",
        "description": "Manufacturing, food processing, and assembly plants. Warehousing limited to 50% floor area.",
        "max_height": 8.0,
        "max_coverage": 0.3,
        "min_plot_size": 600,
        "color_code": "Violet-Purple",
        "setbacks": "10m front, 6m sides, 10m rear"
    },
    {
        "code": ZoneType.NOXIOUS_INDUSTRIAL,
        "name": "Noxious/Offensive Industry Zone",
        "description": "Hazardous industries (chemicals, slaughterhouses). Requires EIA and strict EPA monitoring.",
        "max_height": 8.0,
        "max_coverage": 0.25,
        "min_plot_size": 2000,
        "color_code": "Violet-Purple",
        "setbacks": "15m all sides"
    },
    {
        "code": ZoneType.EXTRACTIVE_INDUSTRIAL,
        "name": "Extractive Industry Zone",
        "description": "Quarries, mines, and mineral processing. No residential within 1km of blasting areas.",
        "max_height": 10.0,
        "max_coverage": 0.1,
        "min_plot_size": 10000,  # 1ha
        "color_code": "Violet-Purple",
        "special_notes": "Requires rehabilitation plan post-extraction"
    },

    # -------------------------------------------------------------------------
    # SPECIAL USE ZONES (11)
    # -------------------------------------------------------------------------
    {
        "code": ZoneType.PLACES_OF_WORSHIP,
        "name": "Places of Worship Zone",
        "description": "Churches, mosques, and other religious facilities. 15-30 mins walking distance from homes.",
        "max_height": 15.0,
        "max_coverage": 0.4,
        "min_plot_size": 2000,  # 0.2-1ha
        "color_code": "Deep Red",
        "parking_requirement": "1 space per 20m² assembly area"
    },
    {
        "code": ZoneType.RECREATION_SPORTS,
        "name": "Recreation & Sports Zone",
        "description": "Stadia, golf courses, and organized sports facilities. Requires parking and amenities.",
        "max_height": 15.0,
        "max_coverage": 0.3,
        "min_plot_size": 10000,  # 1ha
        "color_code": "Mid Green"
    },
    {
        "code": ZoneType.PUBLIC_OPEN_SPACE,
        "name": "Public Open Space Zone",
        "description": "Parks, playgrounds, and floodplains. No permanent structures allowed.",
        "max_height": 3.5,  # e.g., gazebos
        "max_coverage": 0.05,  # 5%
        "min_plot_size": 500,
        "color_code": "Mid Green",
        "special_notes": "No construction in 1:10 year floodplains"
    },
    {
        "code": ZoneType.PROTECTED_COASTAL,
        "name": "Protected Coastal Zone",
        "description": "100m buffer from shoreline. Limited to eco-tourism and fishing-related uses.",
        "max_height": None,  # Case-by-case
        "max_coverage": 0.1,
        "min_plot_size": None,
        "color_code": "Blue broken lines",
        "setbacks": "Minimum 100m from high water mark"
    },
    {
        "code": ZoneType.CONSERVATION_AREA,
        "name": "Conservation Zone",
        "description": "Areas of natural/cultural significance. Limited development permitted.",
        "max_height": 3.5,
        "max_coverage": 0.05,
        "min_plot_size": None,
        "color_code": "Dark Green",
        "buffer_zones": "10-60m riparian buffers required"
    },
    {
        "code": ZoneType.TRANSPORT_WAREHOUSING,
        "name": "Transport & Warehousing Zone",
        "description": "Airports, ports, freight terminals, and bulk storage. Excludes residential uses.",
        "max_height": 10.0,
        "max_coverage": 0.5,
        "min_plot_size": 1000,
        "color_code": "Light Grey"
    },
    {
        "code": ZoneType.TOURIST_ZONE,
        "name": "Tourist Zone",
        "description": "Hotels, resorts, and cultural attractions. High design standards required.",
        "max_height": 15.0,
        "max_coverage": 0.3,
        "min_plot_size": 10000,  # 1ha
        "color_code": "Orange",
        "parking_requirement": "1 space per room + 1 per 20m² public area"
    },
    {
        "code": ZoneType.SPECIAL_EMERGENCY,
        "name": "Emergency Services Zone",
        "description": "Fire stations, ambulance depots, and disaster response facilities.",
        "max_height": 10.0,
        "max_coverage": 0.4,
        "min_plot_size": 200,  # m² for local stations
        "color_code": "Deep Red"
    },
    {
        "code": ZoneType.SPECIAL_UTILITY,
        "name": "Utility Zone",
        "description": "Power plants, water treatment, and waste facilities. Requires EIA.",
        "max_height": None,  # Facility-dependent
        "max_coverage": None,
        "min_plot_size": None,
        "color_code": "Deep Red"
    },
    {
        "code": ZoneType.SPECIAL_SECURITY,
        "name": "Security/Military Zone",
        "description": "Police training, military bases, and correctional facilities. Restricted access.",
        "max_height": None,
        "max_coverage": None,
        "min_plot_size": None,
        "color_code": "Broken black line boundary"
    },
    {
        "code": ZoneType.HERBAL_MEDICINE,
        "name": "Herbal Medicine Zone",
        "description": "Facilities for traditional medicine practice and research.",
        "max_height": 8.0,
        "max_coverage": 0.4,
        "min_plot_size": 5000,
        "color_code": "Deep Red"
    },

    # -------------------------------------------------------------------------
    # FORESTRY ZONES (2)
    # -------------------------------------------------------------------------
    {
        "code": ZoneType.FOREST_RESERVE,
        "name": "Forest Reserve",
        "description": "Protected forest areas. Limited to eco-tourism and research activities.",
        "max_height": None,
        "max_coverage": 0.01,  # 1%
        "min_plot_size": None,
        "color_code": "Dark Green"
    },
    {
        "code": ZoneType.COMMERCIAL_TIMBER,
        "name": "Commercial Timber Zone",
        "description": "Timber production areas with controlled harvesting.",
        "max_height": None,
        "max_coverage": 0.05,
        "min_plot_size": None,
        "color_code": "Dark Green"
    }
]


MMDAS_DATA = [
    # METROPOLITAN ASSEMBLIES
{
        "name": "Accra Metropolitan Assembly",
        "type": "metropolitan",
        "region": "Greater Accra",
        "contact_email": "info@ama.gov.gh",
        "contact_phone": "+233302665134",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3100, 5.5500], [-0.2000, 5.5500], 
                [-0.2000, 5.6500], [-0.3100, 5.6500], 
                [-0.3100, 5.5500]
            ]]
        }
    },
    {
        "name": "Kumasi Metropolitan Assembly",
        "type": "metropolitan",
        "region": "Ashanti",
        "contact_email": "info@kma.gov.gh",
        "contact_phone": "+233322022000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.6500, 6.6500], [-1.5500, 6.6500],
                [-1.5500, 6.7500], [-1.6500, 6.7500],
                [-1.6500, 6.6500]
            ]]
        }
    },
    {
        "name": "Tamale Metropolitan Assembly",
        "type": "metropolitan",
        "region": "Northern",
        "contact_email": "info@tma.gov.gh",
        "contact_phone": "+233372022021",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.8500, 9.4000], [-0.7500, 9.4000],
                [-0.7500, 9.5000], [-0.8500, 9.5000],
                [-0.8500, 9.4000]
            ]]
        }
    },
    {
        "name": "Sekondi-Takoradi Metropolitan Assembly",
        "type": "metropolitan",
        "region": "Western",
        "contact_email": "info@stma.gov.gh",
        "contact_phone": "+233312023456",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.8000, 4.9000], [-1.7000, 4.9000],
                [-1.7000, 5.0000], [-1.8000, 5.0000],
                [-1.8000, 4.9000]
            ]]
        }
    },
    {
        "name": "Tema Metropolitan Assembly",
        "type": "metropolitan",
        "region": "Greater Accra",
        "contact_email": "info@tma.gov.gh",
        "contact_phone": "+233303308200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.0500, 5.6500], [0.0500, 5.6500],
                [0.0500, 5.7500], [-0.0500, 5.7500],
                [-0.0500, 5.6500]
            ]]
        }
    },
    {
        "name": "Cape Coast Metropolitan Assembly",
        "type": "metropolitan",
        "region": "Central",
        "contact_email": "info@ccma.gov.gh",
        "contact_phone": "+233332132000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.3000, 5.1000], [-1.2000, 5.1000],
                [-1.2000, 5.2000], [-1.3000, 5.2000],
                [-1.3000, 5.1000]
            ]]
        }
    },
    # MUNICIPAL ASSEMBLIES
    {
        "name": "Adentan Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@adma.gov.gh",
        "contact_phone": "+233302400000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1833, 5.7167], [-0.1667, 5.7167],
                [-0.1667, 5.7333], [-0.1833, 5.7333],
                [-0.1833, 5.7167]
            ]]
        }
    },
    {
        "name": "Ashaiman Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@ashaiman.gov.gh",
        "contact_phone": "+233303308300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.0333, 5.7500], [0.0000, 5.7500],
                [0.0000, 5.7833], [-0.0333, 5.7833],
                [-0.0333, 5.7500]
            ]]
        }
    },
    {
        "name": "Ga Central Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@gcma.gov.gh",
        "contact_phone": "+233302400500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3500, 5.6000], [-0.3000, 5.6000],
                [-0.3000, 5.6500], [-0.3500, 5.6500],
                [-0.3500, 5.6000]
            ]]
        }
    },
    {
        "name": "Ga East Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@gea.gov.gh",
        "contact_phone": "+233302400600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.2500, 5.6500], [-0.2000, 5.6500],
                [-0.2000, 5.7000], [-0.2500, 5.7000],
                [-0.2500, 5.6500]
            ]]
        }
    },
    {
        "name": "Ga West Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@gwma.gov.gh",
        "contact_phone": "+233302400700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.4000, 5.5500], [-0.3500, 5.5500],
                [-0.3500, 5.6000], [-0.4000, 5.6000],
                [-0.4000, 5.5500]
            ]]
        }
    },
    {
        "name": "Korle Klottey Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@kokma.gov.gh",
        "contact_phone": "+233302400800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.2000, 5.5500], [-0.1500, 5.5500],
                [-0.1500, 5.6000], [-0.2000, 5.6000],
                [-0.2000, 5.5500]
            ]]
        }
    },
    {
        "name": "La Dade-Kotopon Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@ladakma.gov.gh",
        "contact_phone": "+233302400900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1500, 5.5500], [-0.1000, 5.5500],
                [-0.1000, 5.6000], [-0.1500, 5.6000],
                [-0.1500, 5.5500]
            ]]
        }
    },
    {
        "name": "Ledzokuku Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@lekmah.gov.gh",
        "contact_phone": "+233302401000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1000, 5.6000], [-0.0500, 5.6000],
                [-0.0500, 5.6500], [-0.1000, 5.6500],
                [-0.1000, 5.6000]
            ]]
        }
    },
    {
        "name": "Okaikwei North Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@oknma.gov.gh",
        "contact_phone": "+233302401100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.2500, 5.6500], [-0.2000, 5.6500],
                [-0.2000, 5.7000], [-0.2500, 5.7000],
                [-0.2500, 5.6500]
            ]]
        }
    },

    # Ashanti Region (6)
    {
        "name": "Asokore Mampong Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@asokore.gov.gh",
        "contact_phone": "+233322022100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.5500, 6.7000], [-1.5000, 6.7000],
                [-1.5000, 6.7500], [-1.5500, 6.7500],
                [-1.5500, 6.7000]
            ]]
        }
    },
    {
        "name": "Ejisu Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@ejisu.gov.gh",
        "contact_phone": "+233322022200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.5000, 6.7000], [-1.4500, 6.7000],
                [-1.4500, 6.7500], [-1.5000, 6.7500],
                [-1.5000, 6.7000]
            ]]
        }
    },
    {
        "name": "Ejura/Sekyedumase Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@ejura.gov.gh",
        "contact_phone": "+233322022300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.3667, 7.3833], [-1.3000, 7.3833],
                [-1.3000, 7.4500], [-1.3667, 7.4500],
                [-1.3667, 7.3833]
            ]]
        }
    },
    {
        "name": "Obuasi Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@obuasi.gov.gh",
        "contact_phone": "+233322022400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.6833, 6.1833], [-1.6167, 6.1833],
                [-1.6167, 6.2500], [-1.6833, 6.2500],
                [-1.6833, 6.1833]
            ]]
        }
    },
    {
        "name": "Offinso Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@offinso.gov.gh",
        "contact_phone": "+233322022500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.9167, 7.3500], [-1.8500, 7.3500],
                [-1.8500, 7.4167], [-1.9167, 7.4167],
                [-1.9167, 7.3500]
            ]]
        }
    },
    {
        "name": "Mampong Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@mampong.gov.gh",
        "contact_phone": "+233322022600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.4000, 7.0500], [-1.3333, 7.0500],
                [-1.3333, 7.1167], [-1.4000, 7.1167],
                [-1.4000, 7.0500]
            ]]
        }
    },

    # Bono Region (2)
    {
        "name": "Sunyani Municipal Assembly",
        "type": "municipal",
        "region": "Bono",
        "contact_email": "info@sunyani.gov.gh",
        "contact_phone": "+233352022000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.3333, 7.3333], [-2.2667, 7.3333],
                [-2.2667, 7.4000], [-2.3333, 7.4000],
                [-2.3333, 7.3333]
            ]]
        }
    },
    {
        "name": "Berekum Municipal Assembly",
        "type": "municipal",
        "region": "Bono",
        "contact_email": "info@berekum.gov.gh",
        "contact_phone": "+233352022100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.5833, 7.4500], [-2.5167, 7.4500],
                [-2.5167, 7.5167], [-2.5833, 7.5167],
                [-2.5833, 7.4500]
            ]]
        }
    },

    # Central Region (4)
    {
        "name": "Agona West Municipal Assembly",
        "type": "municipal",
        "region": "Central",
        "contact_email": "info@agonawest.gov.gh",
        "contact_phone": "+233332022100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.7000, 5.5333], [-0.6333, 5.5333],
                [-0.6333, 5.6000], [-0.7000, 5.6000],
                [-0.7000, 5.5333]
            ]]
        }
    },
    {
        "name": "Awutu Senya East Municipal Assembly",
        "type": "municipal",
        "region": "Central",
        "contact_email": "info@awutusenya.gov.gh",
        "contact_phone": "+233332022200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.4833, 5.5333], [-0.4167, 5.5333],
                [-0.4167, 5.6000], [-0.4833, 5.6000],
                [-0.4833, 5.5333]
            ]]
        }
    },
    {
        "name": "Effutu Municipal Assembly",
        "type": "municipal",
        "region": "Central",
        "contact_email": "info@effutu.gov.gh",
        "contact_phone": "+233332022300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.4000, 5.1333], [-1.3333, 5.1333],
                [-1.3333, 5.2000], [-1.4000, 5.2000],
                [-1.4000, 5.1333]
            ]]
        }
    },
    {
        "name": "Gomoa East Municipal Assembly",
        "type": "municipal",
        "region": "Central",
        "contact_email": "info@gomoaeast.gov.gh",
        "contact_phone": "+233332022400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.7333, 5.3167], [-0.6667, 5.3167],
                [-0.6667, 5.3833], [-0.7333, 5.3833],
                [-0.7333, 5.3167]
            ]]
        }
    },

    # Eastern Region (5)
    {
        "name": "New Juaben South Municipal Assembly",
        "type": "municipal",
        "region": "Eastern",
        "contact_email": "info@njsma.gov.gh",
        "contact_phone": "+233342022000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.2833, 6.0833], [-0.2167, 6.0833],
                [-0.2167, 6.1500], [-0.2833, 6.1500],
                [-0.2833, 6.0833]
            ]]
        }
    },
    {
        "name": "Nsawam Adoagyiri Municipal Assembly",
        "type": "municipal",
        "region": "Eastern",
        "contact_email": "info@nsawam.gov.gh",
        "contact_phone": "+233342022100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3500, 5.8000], [-0.2833, 5.8000],
                [-0.2833, 5.8667], [-0.3500, 5.8667],
                [-0.3500, 5.8000]
            ]]
        }
    },
    {
        "name": "Suhum Municipal Assembly",
        "type": "municipal",
        "region": "Eastern",
        "contact_email": "info@suhum.gov.gh",
        "contact_phone": "+233342022200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.4500, 6.0333], [-0.3833, 6.0333],
                [-0.3833, 6.1000], [-0.4500, 6.1000],
                [-0.4500, 6.0333]
            ]]
        }
    },
    {
        "name": "Akuapim South Municipal Assembly",
        "type": "municipal",
        "region": "Eastern",
        "contact_email": "info@akuapimsouth.gov.gh",
        "contact_phone": "+233342022300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1000, 5.9167], [-0.0333, 5.9167],
                [-0.0333, 5.9833], [-0.1000, 5.9833],
                [-0.1000, 5.9167]
            ]]
        }
    },
    {
        "name": "Kibi Municipal Assembly",
        "type": "municipal",
        "region": "Eastern",
        "contact_email": "info@kibi.gov.gh",
        "contact_phone": "+233342022400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.5500, 6.1667], [-0.4833, 6.1667],
                [-0.4833, 6.2333], [-0.5500, 6.2333],
                [-0.5500, 6.1667]
            ]]
        }
    },

    # Northern Region (3)
    {
        "name": "Sagnarigu Municipal Assembly",
        "type": "municipal",
        "region": "Northern",
        "contact_email": "info@sagnarigu.gov.gh",
        "contact_phone": "+233372022100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.8500, 9.3500], [-0.7833, 9.3500],
                [-0.7833, 9.4167], [-0.8500, 9.4167],
                [-0.8500, 9.3500]
            ]]
        }
    },
    {
        "name": "Yendi Municipal Assembly",
        "type": "municipal",
        "region": "Northern",
        "contact_email": "info@yendi.gov.gh",
        "contact_phone": "+233372022200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.0167, 9.4333], [0.0500, 9.4333],
                [0.0500, 9.5000], [-0.0167, 9.5000],
                [-0.0167, 9.4333]
            ]]
        }
    },
    {
        "name": "Savelugu Municipal Assembly",
        "type": "municipal",
        "region": "Northern",
        "contact_email": "info@savelugu.gov.gh",
        "contact_phone": "+233372022300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.8333, 9.6167], [-0.7667, 9.6167],
                [-0.7667, 9.6833], [-0.8333, 9.6833],
                [-0.8333, 9.6167]
            ]]
        }
    },
    {
        "name": "La Nkwantanang-Madina Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@lanma.gov.gh",
        "contact_phone": "+233302401200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1833, 5.6833], [-0.1167, 5.6833],
                [-0.1167, 5.7500], [-0.1833, 5.7500],
                [-0.1833, 5.6833]
            ]]
        }
    },
    {
        "name": "Ningo-Prampram District Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@nprda.gov.gh",
        "contact_phone": "+233302401300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.1167, 5.7000], [0.1833, 5.7000],
                [0.1833, 5.7667], [0.1167, 5.7667],
                [0.1167, 5.7000]
            ]]
        }
    },
    {
        "name": "Shai-Osudoku District Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@sodma.gov.gh",
        "contact_phone": "+233302401400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.0500, 5.9167], [0.1167, 5.9167],
                [0.1167, 5.9833], [0.0500, 5.9833],
                [0.0500, 5.9167]
            ]]
        }
    },

    # Ashanti Region (additional municipals)
    {
        "name": "Asante Akim Central Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@aacma.gov.gh",
        "contact_phone": "+233322022700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.2500, 6.8000], [-1.1833, 6.8000],
                [-1.1833, 6.8667], [-1.2500, 6.8667],
                [-1.2500, 6.8000]
            ]]
        }
    },
    {
        "name": "Bekwai Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@bekwai.gov.gh",
        "contact_phone": "+233322022800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.5833, 6.4500], [-1.5167, 6.4500],
                [-1.5167, 6.5167], [-1.5833, 6.5167],
                [-1.5833, 6.4500]
            ]]
        }
    },
    {
        "name": "Bosome Freho District Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@bosomfreho.gov.gh",
        "contact_phone": "+233322022900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.2833, 6.6167], [-1.2167, 6.6167],
                [-1.2167, 6.6833], [-1.2833, 6.6833],
                [-1.2833, 6.6167]
            ]]
        }
    },

    # Bono Region (additional municipals)
    {
        "name": "Dormaa Central Municipal Assembly",
        "type": "municipal",
        "region": "Bono",
        "contact_email": "info@dormaa.gov.gh",
        "contact_phone": "+233352022200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.7833, 7.2833], [-2.7167, 7.2833],
                [-2.7167, 7.3500], [-2.7833, 7.3500],
                [-2.7833, 7.2833]
            ]]
        }
    },
    {
        "name": "Wenchi Municipal Assembly",
        "type": "municipal",
        "region": "Bono",
        "contact_email": "info@wenchi.gov.gh",
        "contact_phone": "+233352022300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.1000, 7.7333], [-2.0333, 7.7333],
                [-2.0333, 7.8000], [-2.1000, 7.8000],
                [-2.1000, 7.7333]
            ]]
        }
    },

    # Bono East Region
    {
        "name": "Techiman Municipal Assembly",
        "type": "municipal",
        "region": "Bono East",
        "contact_email": "info@techiman.gov.gh",
        "contact_phone": "+233352022400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.9333, 7.5833], [-1.8667, 7.5833],
                [-1.8667, 7.6500], [-1.9333, 7.6500],
                [-1.9333, 7.5833]
            ]]
        }
    },
    {
        "name": "Kintampo North Municipal Assembly",
        "type": "municipal",
        "region": "Bono East",
        "contact_email": "info@kintamponorth.gov.gh",
        "contact_phone": "+233352022500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.7333, 8.0500], [-1.6667, 8.0500],
                [-1.6667, 8.1167], [-1.7333, 8.1167],
                [-1.7333, 8.0500]
            ]]
        }
    },

    # Central Region (additional municipals)
    {
        "name": "Assin Central Municipal Assembly",
        "type": "municipal",
        "region": "Central",
        "contact_email": "info@assincma.gov.gh",
        "contact_phone": "+233332022500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.2833, 5.7000], [-1.2167, 5.7000],
                [-1.2167, 5.7667], [-1.2833, 5.7667],
                [-1.2833, 5.7000]
            ]]
        }
    },
    {
        "name": "Kasoa Municipal Assembly",
        "type": "municipal",
        "region": "Central",
        "contact_email": "info@kasoa.gov.gh",
        "contact_phone": "+233332022600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.4333, 5.5333], [-0.3667, 5.5333],
                [-0.3667, 5.6000], [-0.4333, 5.6000],
                [-0.4333, 5.5333]
            ]]
        }
    },

    # Eastern Region (additional municipals)
    {
        "name": "Koforidua Municipal Assembly",
        "type": "municipal",
        "region": "Eastern",
        "contact_email": "info@kma.gov.gh",
        "contact_phone": "+233342022500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.2833, 6.0833], [-0.2167, 6.0833],
                [-0.2167, 6.1500], [-0.2833, 6.1500],
                [-0.2833, 6.0833]
            ]]
        }
    },
    {
        "name": "Akuapim North Municipal Assembly",
        "type": "municipal",
        "region": "Eastern",
        "contact_email": "info@akuapim.gov.gh",
        "contact_phone": "+233342022600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1000, 5.9167], [-0.0333, 5.9167],
                [-0.0333, 5.9833], [-0.1000, 5.9833],
                [-0.1000, 5.9167]
            ]]
        }
    },

    # Northern Region (additional municipals)
    {
        "name": "Gushegu Municipal Assembly",
        "type": "municipal",
        "region": "Northern",
        "contact_email": "info@gushegu.gov.gh",
        "contact_phone": "+233372022400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.2167, 9.9167], [-0.1500, 9.9167],
                [-0.1500, 9.9833], [-0.2167, 9.9833],
                [-0.2167, 9.9167]
            ]]
        }
    },
    {
        "name": "Karaga District Assembly",
        "type": "municipal",
        "region": "Northern",
        "contact_email": "info@karaga.gov.gh",
        "contact_phone": "+233372022500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.8500, 9.8500], [-0.7833, 9.8500],
                [-0.7833, 9.9167], [-0.8500, 9.9167],
                [-0.8500, 9.8500]
            ]]
        }
    },

    # Savannah Region
    {
        "name": "Damongo Municipal Assembly",
        "type": "municipal",
        "region": "Savannah",
        "contact_email": "info@damongo.gov.gh",
        "contact_phone": "+233372022600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.8167, 9.0833], [-1.7500, 9.0833],
                [-1.7500, 9.1500], [-1.8167, 9.1500],
                [-1.8167, 9.0833]
            ]]
        }
    },

    # North East Region
    {
        "name": "Nalerigu Municipal Assembly",
        "type": "municipal",
        "region": "North East",
        "contact_email": "info@nalerigu.gov.gh",
        "contact_phone": "+233372022700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3667, 10.5167], [-0.3000, 10.5167],
                [-0.3000, 10.5833], [-0.3667, 10.5833],
                [-0.3667, 10.5167]
            ]]
        }
    },

    # Upper East Region
    {
        "name": "Bolgatanga Municipal Assembly",
        "type": "municipal",
        "region": "Upper East",
        "contact_email": "info@bolga.gov.gh",
        "contact_phone": "+233382022000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.8500, 10.7833], [-0.7833, 10.7833],
                [-0.7833, 10.8500], [-0.8500, 10.8500],
                [-0.8500, 10.7833]
            ]]
        }
    },

    # Upper West Region
    {
        "name": "Wa Municipal Assembly",
        "type": "municipal",
        "region": "Upper West",
        "contact_email": "info@wma.gov.gh",
        "contact_phone": "+233392022000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.5000, 10.0500], [-2.4333, 10.0500],
                [-2.4333, 10.1167], [-2.5000, 10.1167],
                [-2.5000, 10.0500]
            ]]
        }
    },

    # Volta Region
    {
        "name": "Ho Municipal Assembly",
        "type": "municipal",
        "region": "Volta",
        "contact_email": "info@homa.gov.gh",
        "contact_phone": "+233362022000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.4667, 6.6000], [0.5333, 6.6000],
                [0.5333, 6.6667], [0.4667, 6.6667],
                [0.4667, 6.6000]
            ]]
        }
    },

    # Oti Region
    {
        "name": "Dambai Municipal Assembly",
        "type": "municipal",
        "region": "Oti",
        "contact_email": "info@dambai.gov.gh",
        "contact_phone": "+233362022100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.1667, 7.9833], [0.2333, 7.9833],
                [0.2333, 8.0500], [0.1667, 8.0500],
                [0.1667, 7.9833]
            ]]
        }
    },

    # Western Region
    {
        "name": "Takoradi Municipal Assembly",
        "type": "municipal",
        "region": "Western",
        "contact_email": "info@stma.gov.gh",
        "contact_phone": "+233312022100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.7667, 4.8833], [-1.7000, 4.8833],
                [-1.7000, 4.9500], [-1.7667, 4.9500],
                [-1.7667, 4.8833]
            ]]
        }
    },

    # Western North Region
    {
        "name": "Sefwi Wiawso Municipal Assembly",
        "type": "municipal",
        "region": "Western North",
        "contact_email": "info@wiawso.gov.gh",
        "contact_phone": "+233312022200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.5167, 6.2167], [-2.4500, 6.2167],
                [-2.4500, 6.2833], [-2.5167, 6.2833],
                [-2.5167, 6.2167]
            ]]
        }
    },
    {
        "name": "Ayawaso Central Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@ayawasocentral.gov.gh",
        "contact_phone": "+233302401500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.2000, 5.6000], [-0.1500, 5.6000],
                [-0.1500, 5.6500], [-0.2000, 5.6500],
                [-0.2000, 5.6000]
            ]]
        }
    },
    {
        "name": "Ayawaso East Municipal Assembly",
        "type": "municipal",
        "region": "Greater Accra",
        "contact_email": "info@ayawasoeast.gov.gh",
        "contact_phone": "+233302401600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1500, 5.6000], [-0.1000, 5.6000],
                [-0.1000, 5.6500], [-0.1500, 5.6500],
                [-0.1500, 5.6000]
            ]]
        }
    },

    # Ashanti Region (additional)
    {
        "name": "Asante Akim North Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@aaknorth.gov.gh",
        "contact_phone": "+233322023000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.2000, 6.8000], [-1.1333, 6.8000],
                [-1.1333, 6.8667], [-1.2000, 6.8667],
                [-1.2000, 6.8000]
            ]]
        }
    },
    {
        "name": "Atwima Nwabiagya Municipal Assembly",
        "type": "municipal",
        "region": "Ashanti",
        "contact_email": "info@atwimanwabiagya.gov.gh",
        "contact_phone": "+233322023100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.9167, 6.7000], [-1.8500, 6.7000],
                [-1.8500, 6.7667], [-1.9167, 6.7667],
                [-1.9167, 6.7000]
            ]]
        }
    },

    # Bono East Region (additional)
    {
        "name": "Techiman North Municipal Assembly",
        "type": "municipal",
        "region": "Bono East",
        "contact_email": "info@techimannorth.gov.gh",
        "contact_phone": "+233352022600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.8667, 7.6500], [-1.8000, 7.6500],
                [-1.8000, 7.7167], [-1.8667, 7.7167],
                [-1.8667, 7.6500]
            ]]
        }
    },
    {
        "name": "Nkoranza North Municipal Assembly",
        "type": "municipal",
        "region": "Bono East",
        "contact_email": "info@nkoranzanorth.gov.gh",
        "contact_phone": "+233352022700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.7000, 7.5833], [-1.6333, 7.5833],
                [-1.6333, 7.6500], [-1.7000, 7.6500],
                [-1.7000, 7.5833]
            ]]
        }
    },

    # Central Region (additional)
    {
        "name": "Assin North Municipal Assembly",
        "type": "municipal",
        "region": "Central",
        "contact_email": "info@assinnorth.gov.gh",
        "contact_phone": "+233332022700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.2833, 5.7667], [-1.2167, 5.7667],
                [-1.2167, 5.8333], [-1.2833, 5.8333],
                [-1.2833, 5.7667]
            ]]
        }
    },
    {
        "name": "Awutu Senya West Municipal Assembly",
        "type": "municipal",
        "region": "Central",
        "contact_email": "info@awutusenyawest.gov.gh",
        "contact_phone": "+233332022800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.5500, 5.5333], [-0.4833, 5.5333],
                [-0.4833, 5.6000], [-0.5500, 5.6000],
                [-0.5500, 5.5333]
            ]]
        }
    },

    # Eastern Region (additional)
    {
        "name": "Akyemansa Municipal Assembly",
        "type": "municipal",
        "region": "Eastern",
        "contact_email": "info@akyemansa.gov.gh",
        "contact_phone": "+233342022700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.0500, 6.2500], [-0.9833, 6.2500],
                [-0.9833, 6.3167], [-1.0500, 6.3167],
                [-1.0500, 6.2500]
            ]]
        }
    },
    {
        "name": "Asuogyaman Municipal Assembly",
        "type": "municipal",
        "region": "Eastern",
        "contact_email": "info@asuogyaman.gov.gh",
        "contact_phone": "+233342022800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.0833, 6.2500], [0.1500, 6.2500],
                [0.1500, 6.3167], [0.0833, 6.3167],
                [0.0833, 6.2500]
            ]]
        }
    },

    # Northern Region (additional)
    {
        "name": "Kumbungu Municipal Assembly",
        "type": "municipal",
        "region": "Northern",
        "contact_email": "info@kumbungu.gov.gh",
        "contact_phone": "+233372022800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.0167, 9.5833], [-0.9500, 9.5833],
                [-0.9500, 9.6500], [-1.0167, 9.6500],
                [-1.0167, 9.5833]
            ]]
        }
    },
    {
        "name": "Mion Municipal Assembly",
        "type": "municipal",
        "region": "Northern",
        "contact_email": "info@mion.gov.gh",
        "contact_phone": "+233372022900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1500, 9.5000], [-0.0833, 9.5000],
                [-0.0833, 9.5667], [-0.1500, 9.5667],
                [-0.1500, 9.5000]
            ]]
        }
    },

    # Savannah Region (additional)
    {
        "name": "Bole Municipal Assembly",
        "type": "municipal",
        "region": "Savannah",
        "contact_email": "info@bole.gov.gh",
        "contact_phone": "+233372023000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.4833, 9.0333], [-2.4167, 9.0333],
                [-2.4167, 9.1000], [-2.4833, 9.1000],
                [-2.4833, 9.0333]
            ]]
        }
    },
    {
        "name": "West Gonja Municipal Assembly",
        "type": "municipal",
        "region": "Savannah",
        "contact_email": "info@westgonja.gov.gh",
        "contact_phone": "+233372023100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.8167, 9.1500], [-1.7500, 9.1500],
                [-1.7500, 9.2167], [-1.8167, 9.2167],
                [-1.8167, 9.1500]
            ]]
        }
    },

    # North East Region (additional)
    {
        "name": "East Mamprusi Municipal Assembly",
        "type": "municipal",
        "region": "North East",
        "contact_email": "info@eastmamprusi.gov.gh",
        "contact_phone": "+233372023200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3667, 10.5833], [-0.3000, 10.5833],
                [-0.3000, 10.6500], [-0.3667, 10.6500],
                [-0.3667, 10.5833]
            ]]
        }
    },
    {
        "name": "West Mamprusi Municipal Assembly",
        "type": "municipal",
        "region": "North East",
        "contact_email": "info@westmamprusi.gov.gh",
        "contact_phone": "+233372023300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.8333, 10.5167], [-0.7667, 10.5167],
                [-0.7667, 10.5833], [-0.8333, 10.5833],
                [-0.8333, 10.5167]
            ]]
        }
    },

    # Upper East Region (additional)
    {
        "name": "Bawku Municipal Assembly",
        "type": "municipal",
        "region": "Upper East",
        "contact_email": "info@bawku.gov.gh",
        "contact_phone": "+233382022100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3167, 11.0500], [-0.2500, 11.0500],
                [-0.2500, 11.1167], [-0.3167, 11.1167],
                [-0.3167, 11.0500]
            ]]
        }
    },
    {
        "name": "Kassena-Nankana Municipal Assembly",
        "type": "municipal",
        "region": "Upper East",
        "contact_email": "info@knma.gov.gh",
        "contact_phone": "+233382022200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.0833, 10.7833], [-1.0167, 10.7833],
                [-1.0167, 10.8500], [-1.0833, 10.8500],
                [-1.0833, 10.7833]
            ]]
        }
    },

    # Upper West Region (additional)
    {
        "name": "Jirapa Municipal Assembly",
        "type": "municipal",
        "region": "Upper West",
        "contact_email": "info@jirapa.gov.gh",
        "contact_phone": "+233392022100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.8667, 10.5500], [-2.8000, 10.5500],
                [-2.8000, 10.6167], [-2.8667, 10.6167],
                [-2.8667, 10.5500]
            ]]
        }
    },
    {
        "name": "Nadowli-Kaleo Municipal Assembly",
        "type": "municipal",
        "region": "Upper West",
        "contact_email": "info@nadowlikaleo.gov.gh",
        "contact_phone": "+233392022200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.7500, 10.3833], [-2.6833, 10.3833],
                [-2.6833, 10.4500], [-2.7500, 10.4500],
                [-2.7500, 10.3833]
            ]]
        }
    },

    # Volta Region (additional)
    {
        "name": "Keta Municipal Assembly",
        "type": "municipal",
        "region": "Volta",
        "contact_email": "info@keta.gov.gh",
        "contact_phone": "+233362022200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.9833, 5.9167], [1.0500, 5.9167],
                [1.0500, 5.9833], [0.9833, 5.9833],
                [0.9833, 5.9167]
            ]]
        }
    },
    {
        "name": "Ketu South Municipal Assembly",
        "type": "municipal",
        "region": "Volta",
        "contact_email": "info@ketusouth.gov.gh",
        "contact_phone": "+233362022300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [1.0167, 6.0833], [1.0833, 6.0833],
                [1.0833, 6.1500], [1.0167, 6.1500],
                [1.0167, 6.0833]
            ]]
        }
    },

    # Oti Region (additional)
    {
        "name": "Jasikan Municipal Assembly",
        "type": "municipal",
        "region": "Oti",
        "contact_email": "info@jasikan.gov.gh",
        "contact_phone": "+233362022400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.2333, 7.4000], [0.3000, 7.4000],
                [0.3000, 7.4667], [0.2333, 7.4667],
                [0.2333, 7.4000]
            ]]
        }
    },
    {
        "name": "Kadjebi Municipal Assembly",
        "type": "municipal",
        "region": "Oti",
        "contact_email": "info@kadjebi.gov.gh",
        "contact_phone": "+233362022500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.4667, 7.5167], [0.5333, 7.5167],
                [0.5333, 7.5833], [0.4667, 7.5833],
                [0.4667, 7.5167]
            ]]
        }
    },

    # Western Region (additional)
    {
        "name": "Ahanta West Municipal Assembly",
        "type": "municipal",
        "region": "Western",
        "contact_email": "info@ahantawest.gov.gh",
        "contact_phone": "+233312022300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.9333, 4.8833], [-1.8667, 4.8833],
                [-1.8667, 4.9500], [-1.9333, 4.9500],
                [-1.9333, 4.8833]
            ]]
        }
    },
    {
        "name": "Nzema East Municipal Assembly",
        "type": "municipal",
        "region": "Western",
        "contact_email": "info@nzemaeast.gov.gh",
        "contact_phone": "+233312022400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.6167, 4.8667], [-2.5500, 4.8667],
                [-2.5500, 4.9333], [-2.6167, 4.9333],
                [-2.6167, 4.8667]
            ]]
        }
    },

    # Western North Region (additional)
    {
        "name": "Bibiani-Anhwiaso-Bekwai Municipal Assembly",
        "type": "municipal",
        "region": "Western North",
        "contact_email": "info@bibiani.gov.gh",
        "contact_phone": "+233312022500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.3333, 6.4667], [-2.2667, 6.4667],
                [-2.2667, 6.5333], [-2.3333, 6.5333],
                [-2.3333, 6.4667]
            ]]
        }
    },
    {
        "name": "Wassa Amenfi East Municipal Assembly",
        "type": "municipal",
        "region": "Western North",
        "contact_email": "info@wassaamenfieast.gov.gh",
        "contact_phone": "+233312022600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.0833, 5.7833], [-2.0167, 5.7833],
                [-2.0167, 5.8500], [-2.0833, 5.8500],
                [-2.0833, 5.7833]
            ]]
        }
    },
    {
        "name": "Ada West District Assembly",
        "type": "district",
        "region": "Greater Accra",
        "contact_email": "info@adawest.gov.gh",
        "contact_phone": "+233302401700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.3833, 5.7833], [0.4500, 5.7833],
                [0.4500, 5.8500], [0.3833, 5.8500],
                [0.3833, 5.7833]
            ]]
        }
    },
    {
        "name": "Ada East District Assembly",
        "type": "district",
        "region": "Greater Accra",
        "contact_email": "info@adaeast.gov.gh",
        "contact_phone": "+233302401800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.4500, 5.7833], [0.5167, 5.7833],
                [0.5167, 5.8500], [0.4500, 5.8500],
                [0.4500, 5.7833]
            ]]
        }
    },
    {
        "name": "Shai Osudoku District Assembly",
        "type": "district",
        "region": "Greater Accra",
        "contact_email": "info@shaiosudoku.gov.gh",
        "contact_phone": "+233302401900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.1167, 5.9167], [0.1833, 5.9167],
                [0.1833, 5.9833], [0.1167, 5.9833],
                [0.1167, 5.9167]
            ]]
        }
    },
    {
        "name": "Ningo Prampram District Assembly",
        "type": "district",
        "region": "Greater Accra",
        "contact_email": "info@ningoprampram.gov.gh",
        "contact_phone": "+233302402000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.1833, 5.7000], [0.2500, 5.7000],
                [0.2500, 5.7667], [0.1833, 5.7667],
                [0.1833, 5.7000]
            ]]
        }
    },
    {
        "name": "Kpone Katamanso District Assembly",
        "type": "district",
        "region": "Greater Accra",
        "contact_email": "info@kponekatamanso.gov.gh",
        "contact_phone": "+233302402100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.0500, 5.7000], [0.1167, 5.7000],
                [0.1167, 5.7667], [0.0500, 5.7667],
                [0.0500, 5.7000]
            ]]
        }
    },

    # Ashanti Region (5 districts)
    {
        "name": "Adansi North District Assembly",
        "type": "district",
        "region": "Ashanti",
        "contact_email": "info@adansinorth.gov.gh",
        "contact_phone": "+233322023200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.3667, 6.1333], [-1.3000, 6.1333],
                [-1.3000, 6.2000], [-1.3667, 6.2000],
                [-1.3667, 6.1333]
            ]]
        }
    },
    {
        "name": "Adansi South District Assembly",
        "type": "district",
        "region": "Ashanti",
        "contact_email": "info@adansisouth.gov.gh",
        "contact_phone": "+233322023300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.3667, 6.2000], [-1.3000, 6.2000],
                [-1.3000, 6.2667], [-1.3667, 6.2667],
                [-1.3667, 6.2000]
            ]]
        }
    },
    {
        "name": "Ahafo Ano North District Assembly",
        "type": "district",
        "region": "Ashanti",
        "contact_email": "info@ahafoanonorth.gov.gh",
        "contact_phone": "+233322023400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.1667, 6.9500], [-2.1000, 6.9500],
                [-2.1000, 7.0167], [-2.1667, 7.0167],
                [-2.1667, 6.9500]
            ]]
        }
    },
    {
        "name": "Ahafo Ano South District Assembly",
        "type": "district",
        "region": "Ashanti",
        "contact_email": "info@ahafoanosouth.gov.gh",
        "contact_phone": "+233322023500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.1000, 6.9500], [-2.0333, 6.9500],
                [-2.0333, 7.0167], [-2.1000, 7.0167],
                [-2.1000, 6.9500]
            ]]
        }
    },
    {
        "name": "Amansie West District Assembly",
        "type": "district",
        "region": "Ashanti",
        "contact_email": "info@amansiewest.gov.gh",
        "contact_phone": "+233322023600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.9167, 6.3000], [-1.8500, 6.3000],
                [-1.8500, 6.3667], [-1.9167, 6.3667],
                [-1.9167, 6.3000]
            ]]
        }
    },

    # Bono Region (5 districts)
    {
        "name": "Banda District Assembly",
        "type": "district",
        "region": "Bono",
        "contact_email": "info@banda.gov.gh",
        "contact_phone": "+233352022800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.7833, 8.1667], [-2.7167, 8.1667],
                [-2.7167, 8.2333], [-2.7833, 8.2333],
                [-2.7833, 8.1667]
            ]]
        }
    },
    {
        "name": "Jaman North District Assembly",
        "type": "district",
        "region": "Bono",
        "contact_email": "info@jamannorth.gov.gh",
        "contact_phone": "+233352022900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.7833, 7.9000], [-2.7167, 7.9000],
                [-2.7167, 7.9667], [-2.7833, 7.9667],
                [-2.7833, 7.9000]
            ]]
        }
    },
    {
        "name": "Jaman South District Assembly",
        "type": "district",
        "region": "Bono",
        "contact_email": "info@jamansouth.gov.gh",
        "contact_phone": "+233352023000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.7167, 7.9000], [-2.6500, 7.9000],
                [-2.6500, 7.9667], [-2.7167, 7.9667],
                [-2.7167, 7.9000]
            ]]
        }
    },
    {
        "name": "Tain District Assembly",
        "type": "district",
        "region": "Bono",
        "contact_email": "info@tain.gov.gh",
        "contact_phone": "+233352023100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.9333, 7.9167], [-2.8667, 7.9167],
                [-2.8667, 7.9833], [-2.9333, 7.9833],
                [-2.9333, 7.9167]
            ]]
        }
    },
    {
        "name": "Wenchi District Assembly",
        "type": "district",
        "region": "Bono",
        "contact_email": "info@wenchidistrict.gov.gh",
        "contact_phone": "+233352023200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.1000, 7.8000], [-2.0333, 7.8000],
                [-2.0333, 7.8667], [-2.1000, 7.8667],
                [-2.1000, 7.8000]
            ]]
        }
    },

    # Bono East Region (5 districts)
    {
        "name": "Atebubu-Amantin District Assembly",
        "type": "district",
        "region": "Bono East",
        "contact_email": "info@atebubu.gov.gh",
        "contact_phone": "+233352023300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.2500, 7.7500], [-1.1833, 7.7500],
                [-1.1833, 7.8167], [-1.2500, 7.8167],
                [-1.2500, 7.7500]
            ]]
        }
    },
    {
        "name": "Kintampo South District Assembly",
        "type": "district",
        "region": "Bono East",
        "contact_email": "info@kintampo.gov.gh",
        "contact_phone": "+233352023400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.7333, 8.1167], [-1.6667, 8.1167],
                [-1.6667, 8.1833], [-1.7333, 8.1833],
                [-1.7333, 8.1167]
            ]]
        }
    },
    {
        "name": "Nkoranza South District Assembly",
        "type": "district",
        "region": "Bono East",
        "contact_email": "info@nkoranzasouth.gov.gh",
        "contact_phone": "+233352023500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.7000, 7.6500], [-1.6333, 7.6500],
                [-1.6333, 7.7167], [-1.7000, 7.7167],
                [-1.7000, 7.6500]
            ]]
        }
    },
    {
        "name": "Pru East District Assembly",
        "type": "district",
        "region": "Bono East",
        "contact_email": "info@prueast.gov.gh",
        "contact_phone": "+233352023600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.9167, 8.1667], [-0.8500, 8.1667],
                [-0.8500, 8.2333], [-0.9167, 8.2333],
                [-0.9167, 8.1667]
            ]]
        }
    },
    {
        "name": "Sene East District Assembly",
        "type": "district",
        "region": "Bono East",
        "contact_email": "info@sene.gov.gh",
        "contact_phone": "+233352023700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.4833, 7.9167], [-0.4167, 7.9167],
                [-0.4167, 7.9833], [-0.4833, 7.9833],
                [-0.4833, 7.9167]
            ]]
        }
    },

    # Central Region (5 districts)
    {
        "name": "Abura-Asebu-Kwamankese District Assembly",
        "type": "district",
        "region": "Central",
        "contact_email": "info@aakdistrict.gov.gh",
        "contact_phone": "+233332022900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.3333, 5.2000], [-1.2667, 5.2000],
                [-1.2667, 5.2667], [-1.3333, 5.2667],
                [-1.3333, 5.2000]
            ]]
        }
    },
    {
        "name": "Agona East District Assembly",
        "type": "district",
        "region": "Central",
        "contact_email": "info@agona.gov.gh",
        "contact_phone": "+233332023000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.7000, 5.6000], [-0.6333, 5.6000],
                [-0.6333, 5.6667], [-0.7000, 5.6667],
                [-0.7000, 5.6000]
            ]]
        }
    },
    {
        "name": "Ajumako-Enyan-Essiam District Assembly",
        "type": "district",
        "region": "Central",
        "contact_email": "info@ajumako.gov.gh",
        "contact_phone": "+233332023100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.9833, 5.3833], [-0.9167, 5.3833],
                [-0.9167, 5.4500], [-0.9833, 5.4500],
                [-0.9833, 5.3833]
            ]]
        }
    },
    {
        "name": "Asikuma-Odoben-Brakwa District Assembly",
        "type": "district",
        "region": "Central",
        "contact_email": "info@aobdistrict.gov.gh",
        "contact_phone": "+233332023200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.0167, 5.7500], [-0.9500, 5.7500],
                [-0.9500, 5.8167], [-1.0167, 5.8167],
                [-1.0167, 5.7500]
            ]]
        }
    },
    {
        "name": "Assin South District Assembly",
        "type": "district",
        "region": "Central",
        "contact_email": "info@assinsouth.gov.gh",
        "contact_phone": "+233332023300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.2833, 5.8333], [-1.2167, 5.8333],
                [-1.2167, 5.9000], [-1.2833, 5.9000],
                [-1.2833, 5.8333]
            ]]
        }
    },

    # Eastern Region (5 districts)
    {
        "name": "Abuakwa North District Assembly",
        "type": "district",
        "region": "Eastern",
        "contact_email": "info@abuakwanorth.gov.gh",
        "contact_phone": "+233342022900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3667, 6.0500], [-0.3000, 6.0500],
                [-0.3000, 6.1167], [-0.3667, 6.1167],
                [-0.3667, 6.0500]
            ]]
        }
    },
    {
        "name": "Abuakwa South District Assembly",
        "type": "district",
        "region": "Eastern",
        "contact_email": "info@abuakwasouth.gov.gh",
        "contact_phone": "+233342023000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3000, 6.0500], [-0.2333, 6.0500],
                [-0.2333, 6.1167], [-0.3000, 6.1167],
                [-0.3000, 6.0500]
            ]]
        }
    },
    {
        "name": "Achiase District Assembly",
        "type": "district",
        "region": "Eastern",
        "contact_email": "info@achiase.gov.gh",
        "contact_phone": "+233342023100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.0833, 5.9167], [-1.0167, 5.9167],
                [-1.0167, 5.9833], [-1.0833, 5.9833],
                [-1.0833, 5.9167]
            ]]
        }
    },
    {
        "name": "Akwapim North District Assembly",
        "type": "district",
        "region": "Eastern",
        "contact_email": "info@akwapimnorth.gov.gh",
        "contact_phone": "+233342023200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1000, 5.9833], [-0.0333, 5.9833],
                [-0.0333, 6.0500], [-0.1000, 6.0500],
                [-0.1000, 5.9833]
            ]]
        }
    },
    {
        "name": "Akwapim South District Assembly",
        "type": "district",
        "region": "Eastern",
        "contact_email": "info@akwapimsouth.gov.gh",
        "contact_phone": "+233342023300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.0333, 5.9167], [0.0333, 5.9167],
                [0.0333, 5.9833], [-0.0333, 5.9833],
                [-0.0333, 5.9167]
            ]]
        }
    },

    # Northern Region (5 districts)
    {
        "name": "Gushiegu District Assembly",
        "type": "district",
        "region": "Northern",
        "contact_email": "info@gushiegu.gov.gh",
        "contact_phone": "+233372023400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.2167, 9.9167], [-0.1500, 9.9167],
                [-0.1500, 9.9833], [-0.2167, 9.9833],
                [-0.2167, 9.9167]
            ]]
        }
    },
    {
        "name": "Karaga District Assembly",
        "type": "district",
        "region": "Northern",
        "contact_email": "info@karaga.gov.gh",
        "contact_phone": "+233372023500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.8500, 9.8500], [-0.7833, 9.8500],
                [-0.7833, 9.9167], [-0.8500, 9.9167],
                [-0.8500, 9.8500]
            ]]
        }
    },
    {
        "name": "Nanumba North District Assembly",
        "type": "district",
        "region": "Northern",
        "contact_email": "info@nanumbanorth.gov.gh",
        "contact_phone": "+233372023600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.2167, 8.8667], [-0.1500, 8.8667],
                [-0.1500, 8.9333], [-0.2167, 8.9333],
                [-0.2167, 8.8667]
            ]]
        }
    },
    {
        "name": "Nanumba South District Assembly",
        "type": "district",
        "region": "Northern",
        "contact_email": "info@nanumbasouth.gov.gh",
        "contact_phone": "+233372023700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1500, 8.8667], [-0.0833, 8.8667],
                [-0.0833, 8.9333], [-0.1500, 8.9333],
                [-0.1500, 8.8667]
            ]]
        }
    },
    {
        "name": "Saboba District Assembly",
        "type": "district",
        "region": "Northern",
        "contact_email": "info@saboba.gov.gh",
        "contact_phone": "+233372023800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.3167, 9.7000], [0.3833, 9.7000],
                [0.3833, 9.7667], [0.3167, 9.7667],
                [0.3167, 9.7000]
            ]]
        }
    },

    # Savannah Region (5 districts)
    {
        "name": "Bole District Assembly",
        "type": "district",
        "region": "Savannah",
        "contact_email": "info@boledistrict.gov.gh",
        "contact_phone": "+233372023900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.4833, 9.0333], [-2.4167, 9.0333],
                [-2.4167, 9.1000], [-2.4833, 9.1000],
                [-2.4833, 9.0333]
            ]]
        }
    },
    {
        "name": "Central Gonja District Assembly",
        "type": "district",
        "region": "Savannah",
        "contact_email": "info@centralgonja.gov.gh",
        "contact_phone": "+233372024000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.5833, 9.2500], [-1.5167, 9.2500],
                [-1.5167, 9.3167], [-1.5833, 9.3167],
                [-1.5833, 9.2500]
            ]]
        }
    },
    {
        "name": "East Gonja District Assembly",
        "type": "district",
        "region": "Savannah",
        "contact_email": "info@eastgonja.gov.gh",
        "contact_phone": "+233372024100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.7333, 9.0833], [-0.6667, 9.0833],
                [-0.6667, 9.1500], [-0.7333, 9.1500],
                [-0.7333, 9.0833]
            ]]
        }
    },
    {
        "name": "North Gonja District Assembly",
        "type": "district",
        "region": "Savannah",
        "contact_email": "info@northgonja.gov.gh",
        "contact_phone": "+233372024200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.8167, 9.2167], [-1.7500, 9.2167],
                [-1.7500, 9.2833], [-1.8167, 9.2833],
                [-1.8167, 9.2167]
            ]]
        }
    },
    {
        "name": "West Gonja District Assembly",
        "type": "district",
        "region": "Savannah",
        "contact_email": "info@westgonja.gov.gh",
        "contact_phone": "+233372024300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.8167, 9.1500], [-1.7500, 9.1500],
                [-1.7500, 9.2167], [-1.8167, 9.2167],
                [-1.8167, 9.1500]
            ]]
        }
    },

    # North East Region (5 districts)
    {
        "name": "Bunkpurugu-Nyakpanduri District Assembly",
        "type": "district",
        "region": "North East",
        "contact_email": "info@bunkpurugu.gov.gh",
        "contact_phone": "+233372024400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1667, 10.3500], [-0.1000, 10.3500],
                [-0.1000, 10.4167], [-0.1667, 10.4167],
                [-0.1667, 10.3500]
            ]]
        }
    },
    {
        "name": "Chereponi District Assembly",
        "type": "district",
        "region": "North East",
        "contact_email": "info@chereponi.gov.gh",
        "contact_phone": "+233372024500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.3000, 10.1333], [0.3667, 10.1333],
                [0.3667, 10.2000], [0.3000, 10.2000],
                [0.3000, 10.1333]
            ]]
        }
    },
    {
        "name": "East Mamprusi District Assembly",
        "type": "district",
        "region": "North East",
        "contact_email": "info@eastmamprusi.gov.gh",
        "contact_phone": "+233372024600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3667, 10.5833], [-0.3000, 10.5833],
                [-0.3000, 10.6500], [-0.3667, 10.6500],
                [-0.3667, 10.5833]
            ]]
        }
    },
    {
        "name": "Mamprugu-Moagduri District Assembly",
        "type": "district",
        "region": "North East",
        "contact_email": "info@moagduri.gov.gh",
        "contact_phone": "+233372024700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.2500, 10.5833], [-1.1833, 10.5833],
                [-1.1833, 10.6500], [-1.2500, 10.6500],
                [-1.2500, 10.5833]
            ]]
        }
    },
    {
        "name": "West Mamprusi District Assembly",
        "type": "district",
        "region": "North East",
        "contact_email": "info@westmamprusi.gov.gh",
        "contact_phone": "+233372024800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.8333, 10.5167], [-0.7667, 10.5167],
                [-0.7667, 10.5833], [-0.8333, 10.5833],
                [-0.8333, 10.5167]
            ]]
        }
    },

    # Upper East Region (5 districts)
    {
        "name": "Bawku West District Assembly",
        "type": "district",
        "region": "Upper East",
        "contact_email": "info@bawkuwest.gov.gh",
        "contact_phone": "+233382022300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3167, 11.1167], [-0.2500, 11.1167],
                [-0.2500, 11.1833], [-0.3167, 11.1833],
                [-0.3167, 11.1167]
            ]]
        }
    },
    {
        "name": "Binduri District Assembly",
        "type": "district",
        "region": "Upper East",
        "contact_email": "info@binduri.gov.gh",
        "contact_phone": "+233382022400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.3167, 10.9833], [-0.2500, 10.9833],
                [-0.2500, 11.0500], [-0.3167, 11.0500],
                [-0.3167, 10.9833]
            ]]
        }
    },
    {
        "name": "Bolgatanga East District Assembly",
        "type": "district",
        "region": "Upper East",
        "contact_email": "info@bolgaeast.gov.gh",
        "contact_phone": "+233382022500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.7833, 10.7833], [-0.7167, 10.7833],
                [-0.7167, 10.8500], [-0.7833, 10.8500],
                [-0.7833, 10.7833]
            ]]
        }
    },
    {
        "name": "Bongo District Assembly",
        "type": "district",
        "region": "Upper East",
        "contact_email": "info@bongo.gov.gh",
        "contact_phone": "+233382022600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.8500, 10.8500], [-0.7833, 10.8500],
                [-0.7833, 10.9167], [-0.8500, 10.9167],
                [-0.8500, 10.8500]
            ]]
        }
    },
    {
        "name": "Nabdam District Assembly",
        "type": "district",
        "region": "Upper East",
        "contact_email": "info@nabdam.gov.gh",
        "contact_phone": "+233382022700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.7833, 10.9167], [-0.7167, 10.9167],
                [-0.7167, 10.9833], [-0.7833, 10.9833],
                [-0.7833, 10.9167]
            ]]
        }
    },

    # Upper West Region (5 districts)
    {
        "name": "Daffiama-Bussie-Issa District Assembly",
        "type": "district",
        "region": "Upper West",
        "contact_email": "info@daffiama.gov.gh",
        "contact_phone": "+233392022300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.7500, 10.4500], [-2.6833, 10.4500],
                [-2.6833, 10.5167], [-2.7500, 10.5167],
                [-2.7500, 10.4500]
            ]]
        }
    },
    {
        "name": "Lambussie Karni District Assembly",
        "type": "district",
        "region": "Upper West",
        "contact_email": "info@lambussie.gov.gh",
        "contact_phone": "+233392022400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.8667, 10.8000], [-2.8000, 10.8000],
                [-2.8000, 10.8667], [-2.8667, 10.8667],
                [-2.8667, 10.8000]
            ]]
        }
    },
    {
        "name": "Lawra District Assembly",
        "type": "district",
        "region": "Upper West",
        "contact_email": "info@lawra.gov.gh",
        "contact_phone": "+233392022500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.9167, 10.6333], [-2.8500, 10.6333],
                [-2.8500, 10.7000], [-2.9167, 10.7000],
                [-2.9167, 10.6333]
            ]]
        }
    },
    {
        "name": "Nandom District Assembly",
        "type": "district",
        "region": "Upper West",
        "contact_email": "info@nandom.gov.gh",
        "contact_phone": "+233392022600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.8500, 10.6333], [-2.7833, 10.6333],
                [-2.7833, 10.7000], [-2.8500, 10.7000],
                [-2.8500, 10.6333]
            ]]
        }
    },
    {
        "name": "Sissala East District Assembly",
        "type": "district",
        "region": "Upper West",
        "contact_email": "info@sissalaeast.gov.gh",
        "contact_phone": "+233392022700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.0833, 10.5167], [-2.0167, 10.5167],
                [-2.0167, 10.5833], [-2.0833, 10.5833],
                [-2.0833, 10.5167]
            ]]
        }
    },

    # Volta Region (5 districts)
    {
        "name": "Adaklu District Assembly",
        "type": "district",
        "region": "Volta",
        "contact_email": "info@adaklu.gov.gh",
        "contact_phone": "+233362022600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.5333, 6.6000], [0.6000, 6.6000],
                [0.6000, 6.6667], [0.5333, 6.6667],
                [0.5333, 6.6000]
            ]]
        }
    },
    {
        "name": "Agotime-Ziope District Assembly",
        "type": "district",
        "region": "Volta",
        "contact_email": "info@agotimeziope.gov.gh",
        "contact_phone": "+233362022700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.5333, 6.6667], [0.6000, 6.6667],
                [0.6000, 6.7333], [0.5333, 6.7333],
                [0.5333, 6.6667]
            ]]
        }
    },
    {
        "name": "Akatsi North District Assembly",
        "type": "district",
        "region": "Volta",
        "contact_email": "info@akatsinorth.gov.gh",
        "contact_phone": "+233362022800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.6000, 6.1000], [0.6667, 6.1000],
                [0.6667, 6.1667], [0.6000, 6.1667],
                [0.6000, 6.1000]
            ]]
        }
    },
    {
        "name": "Akatsi South District Assembly",
        "type": "district",
        "region": "Volta",
        "contact_email": "info@akatsisouth.gov.gh",
        "contact_phone": "+233362022900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.6667, 6.1000], [0.7333, 6.1000],
                [0.7333, 6.1667], [0.6667, 6.1667],
                [0.6667, 6.1000]
            ]]
        }
    },
    {
        "name": "Biakoye District Assembly",
        "type": "district",
        "region": "Volta",
        "contact_email": "info@biakoye.gov.gh",
        "contact_phone": "+233362023000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.4667, 7.2500], [0.5333, 7.2500],
                [0.5333, 7.3167], [0.4667, 7.3167],
                [0.4667, 7.2500]
            ]]
        }
    },

    # Oti Region (5 districts)
    {
        "name": "Biakoye District Assembly",
        "type": "district",
        "region": "Oti",
        "contact_email": "info@biakoyeoti.gov.gh",
        "contact_phone": "+233362023100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.4667, 7.2500], [0.5333, 7.2500],
                [0.5333, 7.3167], [0.4667, 7.3167],
                [0.4667, 7.2500]
            ]]
        }
    },
    {
        "name": "Krachi East District Assembly",
        "type": "district",
        "region": "Oti",
        "contact_email": "info@krachieast.gov.gh",
        "contact_phone": "+233362023200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.2333, 7.9833], [0.3000, 7.9833],
                [0.3000, 8.0500], [0.2333, 8.0500],
                [0.2333, 7.9833]
            ]]
        }
    },
    {
        "name": "Krachi Nchumuru District Assembly",
        "type": "district",
        "region": "Oti",
        "contact_email": "info@krachinchumuru.gov.gh",
        "contact_phone": "+233362023300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-0.1667, 8.1667], [-0.1000, 8.1667],
                [-0.1000, 8.2333], [-0.1667, 8.2333],
                [-0.1667, 8.1667]
            ]]
        }
    },
    {
        "name": "Nkwanta North District Assembly",
        "type": "district",
        "region": "Oti",
        "contact_email": "info@nkwantanorth.gov.gh",
        "contact_phone": "+233362023400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.5000, 8.2500], [0.5667, 8.2500],
                [0.5667, 8.3167], [0.5000, 8.3167],
                [0.5000, 8.2500]
            ]]
        }
    },
    {
        "name": "Nkwanta South District Assembly",
        "type": "district",
        "region": "Oti",
        "contact_email": "info@nkwantasouth.gov.gh",
        "contact_phone": "+233362023500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [0.5000, 8.3167], [0.5667, 8.3167],
                [0.5667, 8.3833], [0.5000, 8.3833],
                [0.5000, 8.3167]
            ]]
        }
    },

    # Western Region (5 districts)
    {
        "name": "Ahanta West District Assembly",
        "type": "district",
        "region": "Western",
        "contact_email": "info@ahantawestdistrict.gov.gh",
        "contact_phone": "+233312022700",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-1.9333, 4.9500], [-1.8667, 4.9500],
                [-1.8667, 5.0167], [-1.9333, 5.0167],
                [-1.9333, 4.9500]
            ]]
        }
    },
    {
        "name": "Amenfi Central District Assembly",
        "type": "district",
        "region": "Western",
        "contact_email": "info@amenficentral.gov.gh",
        "contact_phone": "+233312022800",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.0833, 5.8500], [-2.0167, 5.8500],
                [-2.0167, 5.9167], [-2.0833, 5.9167],
                [-2.0833, 5.8500]
            ]]
        }
    },
    {
        "name": "Amenfi East District Assembly",
        "type": "district",
        "region": "Western",
        "contact_email": "info@amenfieast.gov.gh",
        "contact_phone": "+233312022900",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.0167, 5.7833], [-1.9500, 5.7833],
                [-1.9500, 5.8500], [-2.0167, 5.8500],
                [-2.0167, 5.7833]
            ]]
        }
    },
    {
        "name": "Amenfi West District Assembly",
        "type": "district",
        "region": "Western",
        "contact_email": "info@amenfiwest.gov.gh",
        "contact_phone": "+233312023000",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.1667, 5.7833], [-2.1000, 5.7833],
                [-2.1000, 5.8500], [-2.1667, 5.8500],
                [-2.1667, 5.7833]
            ]]
        }
    },
    {
        "name": "Jomoro District Assembly",
        "type": "district",
        "region": "Western",
        "contact_email": "info@jomoro.gov.gh",
        "contact_phone": "+233312023100",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.7833, 4.9667], [-2.7167, 4.9667],
                [-2.7167, 5.0333], [-2.7833, 5.0333],
                [-2.7833, 4.9667]
            ]]
        }
    },

    # Western North Region (5 districts)
    {
        "name": "Bia East District Assembly",
        "type": "district",
        "region": "Western North",
        "contact_email": "info@biaeast.gov.gh",
        "contact_phone": "+233312023200",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-3.0167, 6.3167], [-2.9500, 6.3167],
                [-2.9500, 6.3833], [-3.0167, 6.3833],
                [-3.0167, 6.3167]
            ]]
        }
    },
    {
        "name": "Bia West District Assembly",
        "type": "district",
        "region": "Western North",
        "contact_email": "info@biawest.gov.gh",
        "contact_phone": "+233312023300",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-3.0167, 6.3833], [-2.9500, 6.3833],
                [-2.9500, 6.4500], [-3.0167, 6.4500],
                [-3.0167, 6.3833]
            ]]
        }
    },
    {
        "name": "Bibiani-Anhwiaso-Bekwai District Assembly",
        "type": "district",
        "region": "Western North",
        "contact_email": "info@bibianidistrict.gov.gh",
        "contact_phone": "+233312023400",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.3333, 6.5333], [-2.2667, 6.5333],
                [-2.2667, 6.6000], [-2.3333, 6.6000],
                [-2.3333, 6.5333]
            ]]
        }
    },
    {
        "name": "Sefwi Akontombra District Assembly",
        "type": "district",
        "region": "Western North",
        "contact_email": "info@sefwiakontombra.gov.gh",
        "contact_phone": "+233312023500",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.7833, 6.2167], [-2.7167, 6.2167],
                [-2.7167, 6.2833], [-2.7833, 6.2833],
                [-2.7833, 6.2167]
            ]]
        }
    },
    {
        "name": "Suaman District Assembly",
        "type": "district",
        "region": "Western North",
        "contact_email": "info@suaman.gov.gh",
        "contact_phone": "+233312023600",
        "jurisdiction_boundaries": {
            "type": "Polygon",
            "coordinates": [[
                [-2.9333, 6.2167], [-2.8667, 6.2167],
                [-2.8667, 6.2833], [-2.9333, 6.2833],
                [-2.9333, 6.2167]
            ]]
        }
    }
] 


DEPARTMENTS_DATA = [
{"name": "Physical Planning Department", "code": "PPD"},
{"name": "Works Department", "code": "WRK"},
{"name": "Finance Department", "code": "FIN"}
]

COMMITTEES_DATA = [
{"name": "Works Sub-Committee", "description": "Handles infrastructure projects"},
{"name": "Finance and Administration Sub-Committee", "description": "Oversees budget and administration"},
{"name": "Development Planning Sub-Committee", "description": "Handles development plans"}
]