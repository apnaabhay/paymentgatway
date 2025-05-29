from pydantic import BaseModel, constr, validator, Field
from enum import Enum
from typing import Optional
import re

class CardType(str, Enum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMERICAN_EXPRESS = "amex"
    DISCOVER = "discover"
    UNKNOWN = "unknown"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    BANK_TRANSFER = "bank_transfer"
    CRYPTOCURRENCY = "cryptocurrency"
    BNPL = "bnpl"

class ProcessorType(str, Enum):
    VISA_PROCESSOR = "visa_processor"
    MASTERCARD_PROCESSOR = "mastercard_processor"
    AMEX_PROCESSOR = "amex_processor"
    DISCOVER_PROCESSOR = "discover_processor"
    PAYPAL_PROCESSOR = "paypal_processor"
    STRIPE_PROCESSOR = "stripe_processor"
    SQUARE_PROCESSOR = "square_processor"

class PaymentStatus(str, Enum):
    APPROVED = "approved"
    DECLINED = "declined"
    PENDING = "pending"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentRequest(BaseModel):
    # Card details
    card_number: constr(min_length=12, max_length=19)
    expiry_month: str
    expiry_year: str
    cvv: constr(min_length=3, max_length=4)
    
    # Transaction details
    amount: float = Field(gt=0, description="Amount must be greater than 0")
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    
    # Payment method and processor preferences
    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD
    preferred_processor: Optional[ProcessorType] = None
    
    # Customer details (optional for now)
    customer_email: Optional[str] = None
    billing_address: Optional[dict] = None
    
    @validator('card_number')
    def validate_card_number(cls, v):
        # Remove spaces and validate format
        card_number = re.sub(r'\s+', '', v)
        if not re.match(r'^\d{12,19}$', card_number):
            raise ValueError('Card number must contain only digits and be 12-19 characters long')
        return card_number
    
    @validator('expiry_month')
    def validate_expiry_month(cls, v):
        if not re.match(r'^(0[1-9]|1[0-2])$', v):
            raise ValueError('Expiry month must be in MM format (01-12)')
        return v
    
    @validator('expiry_year')
    def validate_expiry_year(cls, v):
        if not re.match(r'^\d{4}$', v):
            raise ValueError('Expiry year must be in YYYY format')
        current_year = 2024  # In production, use datetime.now().year
        if int(v) < current_year or int(v) > current_year + 20:
            raise ValueError('Expiry year must be between current year and 20 years in the future')
        return v

class PaymentResponse(BaseModel):
    status: PaymentStatus
    message: str
    transaction_id: Optional[str] = None
    processor_used: Optional[ProcessorType] = None
    card_type: Optional[CardType] = None
    processing_fee: Optional[float] = None
    net_amount: Optional[float] = None
    processor_response_code: Optional[str] = None
    risk_score: Optional[float] = None
