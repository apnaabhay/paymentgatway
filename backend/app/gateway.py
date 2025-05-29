import logging
from typing import List, Optional
from .models import PaymentRequest, PaymentResponse, PaymentStatus, ProcessorType, CardType
from .card_validator import CardValidator
from .processors import processor_registry, BaseProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentGateway:
    """
    Smart payment gateway with routing, failover, and load balancing.
    """
    
    def __init__(self):
        self.processor_registry = processor_registry
        self.validator = CardValidator()
    
    def process_payment(self, payment: PaymentRequest) -> PaymentResponse:
        """
        Process a payment with smart routing and failover.
        
        Args:
            payment: Payment request details
            
        Returns:
            PaymentResponse: Processing result
        """
        logger.info(f"Processing payment for amount {payment.amount} {payment.currency}")
        
        # Step 1: Comprehensive card validation
        validation_result = self._validate_payment(payment)
        if not validation_result["is_valid"]:
            logger.warning(f"Payment validation failed: {validation_result['errors']}")
            return PaymentResponse(
                status=PaymentStatus.DECLINED,
                message=f"Validation failed: {', '.join(validation_result['errors'])}",
                card_type=validation_result.get("card_type")
            )
        
        # Step 2: Detect card type
        card_type = validation_result["card_type"]
        logger.info(f"Detected card type: {card_type}")
        
        # Step 3: Smart processor selection
        selected_processors = self._select_processors(payment, card_type)
        if not selected_processors:
            logger.error("No available processors for this payment")
            return PaymentResponse(
                status=PaymentStatus.FAILED,
                message="No available payment processors",
                card_type=card_type
            )
        
        # Step 4: Attempt processing with failover
        return self._process_with_failover(payment, selected_processors, card_type)
    
    def _validate_payment(self, payment: PaymentRequest) -> dict:
        """Validate payment details comprehensively."""
        return self.validator.validate_card_comprehensive(
            payment.card_number,
            payment.cvv,
            payment.expiry_month,
            payment.expiry_year
        )
    
    def _select_processors(self, payment: PaymentRequest, card_type: CardType) -> List[BaseProcessor]:
        """
        Smart processor selection based on card type, preferences, and availability.
        
        Args:
            payment: Payment request
            card_type: Detected card type
            
        Returns:
            List[BaseProcessor]: Ordered list of processors to try
        """
        processors = []
        
        # Priority 1: User's preferred processor (if specified and available)
        if payment.preferred_processor:
            preferred = self.processor_registry.get_processor(payment.preferred_processor)
            if preferred and preferred.is_available:
                processors.append(preferred)
                logger.info(f"Using preferred processor: {preferred.name}")
        
        # Priority 2: Card-specific processors
        card_processors = self.processor_registry.get_available_processors_for_card(card_type)
        for processor in card_processors:
            if processor not in processors:  # Avoid duplicates
                processors.append(processor)
        
        # Priority 3: Universal processors (like Stripe) as fallback
        if not processors:
            stripe_processor = self.processor_registry.get_processor(ProcessorType.STRIPE_PROCESSOR)
            if stripe_processor and stripe_processor.is_available:
                processors.append(stripe_processor)
        
        # Apply load balancing logic (simple round-robin for now)
        processors = self._apply_load_balancing(processors)
        
        logger.info(f"Selected processors: {[p.name for p in processors]}")
        return processors
    
    def _apply_load_balancing(self, processors: List[BaseProcessor]) -> List[BaseProcessor]:
        """
        Apply load balancing to distribute traffic across processors.
        For now, this is a simple implementation. In production, you might
        consider factors like processor load, response times, etc.
        """
        # Simple strategy: prioritize processors with lower fees
        return sorted(processors, key=lambda p: p.processing_fee_rate)
    
    def _process_with_failover(self, payment: PaymentRequest, processors: List[BaseProcessor], card_type: CardType) -> PaymentResponse:
        """
        Attempt payment processing with automatic failover.
        
        Args:
            payment: Payment request
            processors: List of processors to try
            card_type: Detected card type
            
        Returns:
            PaymentResponse: Final processing result
        """
        last_error = None
        
        for i, processor in enumerate(processors):
            try:
                logger.info(f"Attempting payment with {processor.name} (attempt {i + 1}/{len(processors)})")
                
                # Process payment
                response = processor.process_payment(payment)
                
                # If successful, return immediately
                if response.status == PaymentStatus.APPROVED:
                    logger.info(f"Payment approved by {processor.name}")
                    return response
                
                # If declined by processor (not a system error), don't retry
                elif response.status == PaymentStatus.DECLINED:
                    logger.warning(f"Payment declined by {processor.name}: {response.message}")
                    return response
                
                # If failed due to system error, try next processor
                else:
                    logger.warning(f"Payment failed with {processor.name}, trying next processor")
                    last_error = response
                    continue
                    
            except Exception as e:
                logger.error(f"Error processing with {processor.name}: {str(e)}")
                # Mark processor as temporarily unavailable
                processor.is_available = False
                last_error = PaymentResponse(
                    status=PaymentStatus.FAILED,
                    message=f"Processor error: {str(e)}",
                    card_type=card_type
                )
                continue
        
        # All processors failed
        logger.error("All processors failed")
        return last_error or PaymentResponse(
            status=PaymentStatus.FAILED,
            message="All payment processors are currently unavailable",
            card_type=card_type
        )
    
    def get_processor_status(self) -> dict:
        """Get status of all processors for monitoring."""
        return {
            processor_type.value: {
                "name": processor.name,
                "available": processor.is_available,
                "fee_rate": processor.processing_fee_rate,
                "fixed_fee": processor.fixed_fee
            }
            for processor_type, processor in self.processor_registry.processors.items()
        }
    
    def set_processor_availability(self, processor_type: ProcessorType, available: bool):
        """Manually set processor availability (for maintenance, etc.)."""
        self.processor_registry.set_processor_availability(processor_type, available)
        logger.info(f"Set {processor_type.value} availability to {available}")

# Global gateway instance
payment_gateway = PaymentGateway()

# Legacy function for backward compatibility
def process_payment(payment: PaymentRequest) -> PaymentResponse:
    """Legacy function that uses the new gateway."""
    return payment_gateway.process_payment(payment)
