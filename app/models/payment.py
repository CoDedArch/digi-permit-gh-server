from sqlalchemy import Column, Enum, Integer,Boolean, ForeignKey, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
from app.core.constants import PaymentStatus, PaymentMethod, PaymentPurpose


class Payment(Base, TimestampMixin):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('permit_applications.id'))  # Optional for pre-application payments
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    method = Column(Enum(PaymentMethod))
    purpose = Column(Enum(PaymentPurpose), nullable=False)  # What the payment is for
    transaction_reference = Column(String(100), unique=True)
    receipt_number = Column(String(50), unique=True)
    payment_date = Column(DateTime)
    due_date = Column(DateTime)  # When payment is required by
    notes = Column(Text)
    
    # Relationships
    application = relationship("PermitApplication", back_populates="payments")
    user = relationship("User")
    
    def __repr__(self):
        return f"<Payment {self.purpose.value} GHS {self.amount} ({self.status.value})>"

# Additional model for fee structure (optional)
class FeeStructure(Base, TimestampMixin):
    __tablename__ = 'fee_structures'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    purpose = Column(Enum(PaymentPurpose), nullable=False, unique=True)
    amount = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    
    def __repr__(self):
        return f"<Fee {self.name}: GHS {self.amount}>"