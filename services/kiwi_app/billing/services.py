"""
Billing services for KiwiQ system.

This module defines the service layer for billing operations, including subscription management,
credit tracking, usage events, and Stripe integration. It follows KiwiQ's established patterns
for service layer architecture with dependency injection.
"""

import uuid
import stripe
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

# from kiwi_app.auth import crud as auth_crud
from kiwi_app.auth.models import Organization, User
from kiwi_app.auth.utils import datetime_now_utc
from kiwi_app.settings import settings
from kiwi_app.utils import get_kiwi_logger

from kiwi_app.billing import crud, models, schemas
from kiwi_app.billing.models import CreditType, SubscriptionStatus, CreditSourceType, PaymentStatus
from kiwi_app.billing.exceptions import (
    InsufficientCreditsException,
    SubscriptionNotFoundException,
    SubscriptionPlanNotFoundException,
    InvalidSubscriptionStateException,
    PaymentMethodRequiredException,
    StripeIntegrationException,
    PromotionCodeNotFoundException,
    PromotionCodeExpiredException,
    PromotionCodeExhaustedException,
    PromotionCodeAlreadyUsedException,
    PromotionCodeNotAllowedException,
    CreditPurchaseNotFoundException,
    OveragePolicyViolationException,
    SeatLimitExceededException,
    BillingConfigurationException,
    BillingException
)

# Get logger for billing operations
billing_logger = get_kiwi_logger(name="kiwi_app.billing")

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION


class BillingService:
    """Service layer for billing operations."""
    
    def __init__(
        self,
        subscription_plan_dao: crud.SubscriptionPlanDAO,
        org_subscription_dao: crud.OrganizationSubscriptionDAO,
        org_credits_dao: crud.OrganizationCreditsDAO,
        org_net_credits_dao: crud.OrganizationNetCreditsDAO,
        usage_event_dao: crud.UsageEventDAO,
        credit_purchase_dao: crud.CreditPurchaseDAO,
        promotion_code_dao: crud.PromotionCodeDAO,
        promotion_code_usage_dao: crud.PromotionCodeUsageDAO,
        org_dao,  # : auth_crud.OrganizationDAO
    ):
        """Initialize service with DAO instances."""
        self.subscription_plan_dao = subscription_plan_dao
        self.org_subscription_dao = org_subscription_dao
        self.org_credits_dao = org_credits_dao
        self.org_net_credits_dao = org_net_credits_dao
        self.usage_event_dao = usage_event_dao
        self.credit_purchase_dao = credit_purchase_dao
        self.promotion_code_dao = promotion_code_dao
        self.promotion_code_usage_dao = promotion_code_usage_dao
        self.org_dao = org_dao
    
    # --- Credit Management --- #
    
    async def get_credit_balances(
        self,
        db: AsyncSession,
        org_id: uuid.UUID
    ) -> List[schemas.CreditBalance]:
        """
        Get credit balances for an organization.
        
        This method aggregates credits from all sources and provides current
        available balances with overage information for each credit type.
        
        Args:
            db: Database session
            org_id: Organization ID
            
        Returns:
            List of credit balances by type
        """
        try:
            balances = []
            
            # Check each credit type
            for credit_type in CreditType:
                net_credits = await self.org_net_credits_dao.get_net_credits_read(
                    db, org_id, credit_type
                )
                
                if net_credits:
                    balance = schemas.CreditBalance(
                        credit_type=credit_type,
                        credits_balance=net_credits.current_balance,
                        credits_granted=net_credits.credits_granted,
                        credits_consumed=net_credits.credits_consumed,
                        is_overage=net_credits.is_overage,
                        overage_amount=net_credits.overage_amount
                    )
                else:
                    # No credits allocated yet for this type
                    balance = schemas.CreditBalance(
                        credit_type=credit_type,
                        credits_balance=0.0,
                        credits_granted=0.0,
                        credits_consumed=0.0,
                        is_overage=False,
                        overage_amount=0.0
                    )
                
                balances.append(balance)
            
            return balances
            
        except Exception as e:
            billing_logger.error(f"Error getting credit balances for org {org_id}: {e}", exc_info=True)
            raise
    
    async def get_organization_credits_by_type(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        credit_type: Optional[CreditType] = None,
        include_expired: bool = False
    ) -> List[schemas.OrganizationCreditsRead]:
        """
        Get detailed credit records for an organization by credit type.
        
        This method returns individual credit allocation records showing
        the source, expiration, and detailed information for each credit
        allocation. Unlike get_credit_balances which provides aggregated
        totals, this shows the itemized breakdown.
        
        Args:
            db: Database session
            org_id: Organization ID
            credit_type: Type of credits to retrieve (None for all types)
            include_expired: Whether to include expired credits
            
        Returns:
            List of detailed credit records
            
        Raises:
            BillingException: If there's an error retrieving credit records
        """
        try:
            credit_list = []
            
            # Determine which credit types to query
            credit_types_to_query = [credit_type] if credit_type else list(CreditType)
            
            for current_credit_type in credit_types_to_query:
                # Use the CRUD method to get detailed credit records for each type
                credit_records = await self.org_credits_dao.get_by_org_and_type(
                    db=db,
                    org_id=org_id,
                    credit_type=current_credit_type,
                    include_expired=include_expired
                )
                
                # Convert to response schemas
                for record in credit_records:
                    # Calculate remaining balance for this specific record
                    # Note: This shows the granted amount for this allocation - consumed is tracked globally
                    credits_balance = max(0.0, record.credits_granted)
                    
                    # Calculate period_end - use expires_at if available, otherwise use a default period
                    period_end = record.expires_at
                    if not period_end:
                        # If no expiration, assume a monthly period from period_start
                        period_end = record.period_start + timedelta(days=30)
                    
                    credit_read = schemas.OrganizationCreditsRead(
                        id=record.id,
                        org_id=record.org_id,
                        credit_type=record.credit_type,
                        credits_balance=credits_balance,  # This record's granted amount
                        credits_consumed=0.0,  # Consumption is tracked globally, not per allocation
                        credits_granted=record.credits_granted,
                        source_type=record.source_type,
                        source_id=record.source_id,
                        source_metadata=record.source_metadata,
                        expires_at=record.expires_at,
                        is_expired=record.is_expired,
                        period_start=record.period_start,
                        period_end=period_end,
                        created_at=record.created_at,
                        updated_at=record.updated_at
                    )
                    credit_list.append(credit_read)
            
            # Sort by credit type and then by creation date for consistent ordering
            credit_list.sort(key=lambda x: (x.credit_type.value, x.created_at))
            
            billing_logger.info(
                f"Retrieved {len(credit_list)} credit records for org {org_id}, "
                f"type {credit_type.value if credit_type else 'all'}, include_expired={include_expired}"
            )
            
            return credit_list
            
        except Exception as e:
            billing_logger.error(
                f"Error getting organization credits for org {org_id}, "
                f"type {credit_type.value if credit_type else 'all'}: {e}", exc_info=True
            )
            raise BillingException(
                status_code=500,
                detail=f"Failed to retrieve {credit_type.value if credit_type else 'all'} credit records"
            )
    
    async def consume_credits(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        consumption_request: schemas.CreditConsumptionRequest
    ) -> schemas.CreditConsumptionResult:
        """
        Consume credits with optimized atomic updates and overage handling.
        
        This method uses the new high-performance credit consumption approach
        with direct UPDATE queries and transaction locks for better scalability.
        
        Args:
            db: Database session
            org_id: Organization ID
            user_id: User ID consuming credits
            consumption_request: Credit consumption details
            
        Returns:
            CreditConsumptionResult: Consumption result with balance info
            
        Raises:
            InsufficientCreditsException: If not enough credits available
        """
        try:
            # Get overage policy for this organization and credit type
            overage_settings = await self._get_overage_settings(org_id, consumption_request.credit_type)
            max_overage_allowed_fraction = overage_settings.get("overage_percentage", 10) / 100.0
            
            # Use atomic credit consumption
            consumption_result = await self.org_net_credits_dao.consume_credits_atomic(
                db=db,
                org_id=org_id,
                credit_type=consumption_request.credit_type,
                credits_to_consume=consumption_request.credits_consumed,
                max_overage_allowed_fraction=max_overage_allowed_fraction,
                commit=False
            )
            
            # Create usage event for audit and analytics
            await self._create_usage_event(
                db=db,
                org_id=org_id,
                user_id=user_id,
                consumption_request=consumption_request,
                is_overage=consumption_result.is_overage
            )
            
            # Commit the transaction
            await db.commit()
            
            # Prepare result
            result = schemas.CreditConsumptionResult(
                success=True,
                credits_consumed=consumption_result.credits_consumed,
                remaining_balance=consumption_result.remaining_balance,
                is_overage=consumption_result.is_overage,
                grace_credits_used=consumption_result.overage_amount,
                warning="Using overage grace credits" if consumption_result.is_overage else None
            )
            
            # Log consumption for monitoring
            billing_logger.info(
                f"Consumed {consumption_request.credits_consumed} {consumption_request.credit_type.value} "
                f"credits for org {org_id} (event: {consumption_request.event_type}, "
                f"overage: {consumption_result.is_overage})"
            )
            
            return result
            
        except InsufficientCreditsException:
            # Re-raise insufficient credits exceptions
            raise
        except Exception as e:
            # Rollback transaction on error
            await db.rollback()
            billing_logger.error(f"Error consuming credits: {e}", exc_info=True)
            raise BillingException(
                status_code=500,
                detail=f"Failed to consume credits: {str(e)}"
            )
    
    async def allocate_credits_for_operation(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        credit_type: CreditType,
        estimated_credits: float,
        operation_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> schemas.CreditAllocationResult:
        """
        Allocate credits for a long-running operation.
        
        This method pre-allocates credits to prevent race conditions in
        concurrent usage scenarios, particularly useful for long-running
        operations like complex workflows or batch processing.
        
        Args:
            db: Database session
            org_id: Organization ID
            user_id: User ID performing the operation
            credit_type: Type of credits to allocate
            estimated_credits: Estimated credits needed
            operation_id: Unique operation identifier
            metadata: Optional operation metadata
            
        Returns:
            CreditAllocationResult: Allocation result with tracking info
        """
        try:
            # Get overage policy
            overage_settings = await self._get_overage_settings(org_id, credit_type)
            max_overage_allowed_fraction = overage_settings.get("overage_percentage", 10) / 100.0
            
            # Allocate credits using atomic operation
            allocation_result = await self.org_net_credits_dao.allocate_credits_for_operation(
                db=db,
                org_id=org_id,
                credit_type=credit_type,
                estimated_credits=estimated_credits,
                operation_id=operation_id,
                max_overage_allowed_fraction=max_overage_allowed_fraction,
                commit=False
            )
            
            # Create usage event for the allocation
            allocation_event = schemas.CreditConsumptionRequest(
                credit_type=credit_type,
                credits_consumed=estimated_credits,
                event_type="credit_allocation",
                metadata={
                    "operation_id": operation_id,
                    "is_allocation": True,
                    "estimated_credits": estimated_credits,
                    **(metadata or {})
                }
            )
            
            await self._create_usage_event(
                db=db,
                org_id=org_id,
                user_id=user_id,
                consumption_request=allocation_event,
                is_overage=allocation_result.is_overage
            )
            
            # Commit the transaction
            await db.commit()
            
            return allocation_result
            
        except InsufficientCreditsException:
            raise
        except Exception as e:
            # Rollback transaction on error
            await db.rollback()
            billing_logger.error(f"Error allocating credits: {e}", exc_info=True)
            raise BillingException(
                status_code=500,
                detail=f"Failed to allocate credits: {str(e)}"
            )
    
    async def adjust_allocated_credits(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        credit_type: CreditType,
        operation_id: str,
        actual_credits: float,
        allocated_credits: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> schemas.CreditAdjustmentResult:
        """
        Adjust allocated credits with actual consumption.
        
        This method handles the final adjustment between estimated and actual
        credit consumption, ensuring accurate billing for long-running operations.
        
        Args:
            db: Database session
            org_id: Organization ID
            user_id: User ID
            credit_type: Type of credits
            operation_id: Operation identifier
            actual_credits: Actual credits consumed
            allocated_credits: Previously allocated credits
            metadata: Optional adjustment metadata
            
        Returns:
            CreditAdjustmentResult: Adjustment result
        """
        try:
            # Perform the adjustment using atomic operation
            adjustment_result = await self.org_net_credits_dao.adjust_allocation_with_actual(
                db=db,
                org_id=org_id,
                credit_type=credit_type,
                operation_id=operation_id,
                actual_credits=actual_credits,
                allocated_credits=allocated_credits,
                commit=False
            )
            
            # Create usage event for the adjustment
            if adjustment_result.adjustment_needed:
                adjustment_event = schemas.CreditConsumptionRequest(
                    credit_type=credit_type,
                    credits_consumed=abs(adjustment_result.credit_difference),  # Use absolute value
                    event_type="credit_adjustment",
                    metadata={
                        "operation_id": operation_id,
                        "is_adjustment": True,
                        "allocated_credits": allocated_credits,
                        "actual_credits": actual_credits,
                        "credit_difference": adjustment_result.credit_difference,
                        "adjustment_type": adjustment_result.adjustment_type,
                        **(metadata or {})
                    }
                )
                
                await self._create_usage_event(
                    db=db,
                    org_id=org_id,
                    user_id=user_id,
                    consumption_request=adjustment_event,
                    is_overage=False  # Adjustments don't create new overage
                )
            
            # Commit the transaction
            await db.commit()
            
            return adjustment_result
            
        except Exception as e:
            # Rollback transaction on error
            await db.rollback()
            billing_logger.error(f"Error adjusting allocated credits: {e}", exc_info=True)
            raise BillingException(
                status_code=500,
                detail=f"Failed to adjust allocated credits: {str(e)}"
            )
    
    async def add_credits_to_organization(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        credit_type: CreditType,
        credits_to_add: float,
        source_type: CreditSourceType,
        source_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> schemas.CreditAdditionResult:
        """
        Add credits to organization with automatic overage adjustment.
        
        This method uses the optimized credit addition logic that automatically
        handles overage adjustments when new credits are added.
        
        Args:
            db: Database session
            org_id: Organization ID
            credit_type: Type of credits to add
            credits_to_add: Number of credits to add
            source_type: Source of the credits
            source_id: Source identifier
            expires_at: Expiration date
            metadata: Additional metadata
            
        Returns:
            CreditAdditionResult: Addition result with overage adjustment info
        """
        try:
            # Create audit record for the allocation
            await self.org_credits_dao.allocate_credits(
                db=db,
                org_id=org_id,
                credit_type=credit_type,
                amount=credits_to_add,
                source_type=source_type,
                source_id=source_id,
                source_metadata=metadata,
                expires_at=expires_at,
                commit=False,
            )
            
            # Use the optimized credit addition
            result = await self.org_net_credits_dao.add_credits(
                db=db,
                org_id=org_id,
                credit_type=credit_type,
                credits_to_add=credits_to_add,
                source_type=source_type,
                source_id=source_id,
                expires_at=expires_at,
                commit=False
            )
            
            # Commit the transaction
            await db.commit()
            
            billing_logger.info(
                f"Added {credits_to_add} {credit_type.value} credits to org {org_id} "
                f"from {source_type.value}"
            )
            
            return result
            
        except Exception as e:
            # Rollback transaction on error
            await db.rollback()
            billing_logger.error(f"Error adding credits to organization: {e}", exc_info=True)
            raise BillingException(
                status_code=500,
                detail=f"Failed to add credits: {str(e)}"
            )
    
    async def _get_overage_settings(
        self,
        org_id: uuid.UUID,
        credit_type: CreditType
    ) -> Dict[str, Any]:
        """
        Get overage settings for organization and credit type.
        
        This method determines the overage policy for credit consumption,
        including grace periods and maximum allowed overage.
        
        Args:
            org_id: Organization ID
            credit_type: Type of credits
            
        Returns:
            dict: Overage settings
        """
        try:
            # For now, use default overage settings
            # In production, these could be stored per organization or plan
            default_overage_percentage = 10  # 10% grace period
            
            # Calculate overage based on current granted credits
            # This would ideally be cached or stored in the organization settings
            base_credits = 100  # Default base for calculation
            
            max_overage_credits = int(base_credits * (default_overage_percentage / 100))
            
            return {
                "allow_overage": True,
                "overage_percentage": default_overage_percentage,
                "max_overage_credits": max_overage_credits,
                "grace_period_days": 3
            }
            
        except Exception as e:
            billing_logger.warning(f"Error getting overage settings, using defaults: {e}")
            return {
                "allow_overage": True,
                "overage_percentage": 10,
                "max_overage_credits": 10,
                "grace_period_days": 3
            }
    
    # --- Promotion Code Management --- #
    
    async def apply_promotion_code(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        code_application: schemas.PromotionCodeApply
    ) -> schemas.PromotionCodeApplyResult:
        """Apply a promotion code to grant credits to an organization."""
        try:
            # Get the promotion code
            promo_code = await self.promotion_code_dao.get_by_code(db, code_application.code)
            if not promo_code:
                raise PromotionCodeNotFoundException(code_application.code)
            
            # Check eligibility
            is_eligible, reason = await self.promotion_code_dao.check_usage_eligibility(db, promo_code, org_id)
            if not is_eligible:
                if "expired" in reason.lower():
                    raise PromotionCodeExpiredException(code_application.code)
                elif "usage limit" in reason.lower():
                    raise PromotionCodeExhaustedException(code_application.code)
                elif "already used" in reason.lower():
                    raise PromotionCodeAlreadyUsedException(code_application.code)
                elif "not allowed" in reason.lower():
                    raise PromotionCodeNotAllowedException(code_application.code)
                elif "not active" in reason.lower():
                    raise PromotionCodeNotAllowedException(code_application.code)
                else:
                    raise HTTPException(status_code=400, detail=reason)
            
            # Calculate expiration for granted credits
            expires_at = None
            if promo_code.granted_credits_expire_days:
                expires_at = datetime_now_utc() + timedelta(days=promo_code.granted_credits_expire_days)
            
            # Create audit record for the allocation
            await self.org_credits_dao.allocate_credits(
                db=db,
                org_id=org_id,
                credit_type=promo_code.credit_type,
                amount=promo_code.credits_amount,
                source_type=CreditSourceType.PROMOTION,
                source_id=code_application.code,
                source_metadata={"promo_code_id": str(promo_code.id)},
                expires_at=expires_at,
                commit=False,
            )
            
            # Add to net credits
            await self.org_net_credits_dao.add_credits(
                db=db,
                org_id=org_id,
                credit_type=promo_code.credit_type,
                credits_to_add=promo_code.credits_amount,
                source_type=CreditSourceType.PROMOTION,
                source_id=code_application.code,
                expires_at=expires_at,
                commit=False
            )
            
            # Record usage
            await self.promotion_code_usage_dao.create_usage(
                db=db,
                promo_code_id=promo_code.id,
                org_id=org_id,
                user_id=user_id,
                credits_applied=promo_code.credits_amount
            )
            
            # Update promotion code usage count
            promo_code.uses_count += 1
            promo_code.updated_at = datetime_now_utc()
            await self.promotion_code_dao.update(db, db_obj=promo_code, obj_in=schemas.PromotionCodeUpdate())
            
            # Commit the transaction
            await db.commit()
            
            billing_logger.info(f"Applied promotion code {code_application.code} to org {org_id}")
            
            return schemas.PromotionCodeApplyResult(
                success=True,
                credits_applied=promo_code.credits_amount,
                credit_type=promo_code.credit_type,
                message=f"Successfully applied {promo_code.credits_amount} {promo_code.credit_type.value} credits"
            )
            
        except (PromotionCodeNotFoundException, PromotionCodeExpiredException, 
                PromotionCodeExhaustedException, PromotionCodeAlreadyUsedException,
                PromotionCodeNotAllowedException, HTTPException):
            # Re-raise promotion code specific exceptions
            raise
        except Exception as e:
            # Rollback transaction on error
            await db.rollback()
            billing_logger.error(f"Error applying promotion code: {e}", exc_info=True)
            raise BillingException(
                status_code=500,
                detail=f"Failed to apply promotion code: {str(e)}"
            )
    
    # --- Usage Analytics --- #
    
    async def get_usage_summary(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime
    ) -> schemas.UsageSummary:
        """Get usage summary for an organization within a date range."""
        # Get usage summary from DAO
        summary_data = await self.usage_event_dao.get_usage_summary(db, org_id, start_date, end_date)
        
        # Get current credit balances
        credit_balances = await self.get_credit_balances(db, org_id)
        
        return schemas.UsageSummary(
            org_id=org_id,
            period_start=start_date,
            period_end=end_date,
            credit_balances=credit_balances,
            total_events=summary_data['total_events'],
            events_by_type=summary_data['events_by_type'],
            overage_events=summary_data['overage_events']
        )
    
    async def get_billing_dashboard(
        self,
        db: AsyncSession,
        org_id: uuid.UUID
    ) -> schemas.BillingDashboard:
        """Get comprehensive billing dashboard data for an organization."""
        # Get subscription with plan details
        subscription = await self.org_subscription_dao.get_by_org_id(db, org_id)
        
        # Get credit balances
        credit_balances = await self.get_credit_balances(db, org_id)
        
        # Get recent usage events (last 30 days)
        end_date = datetime_now_utc()
        start_date = end_date - timedelta(days=30)
        recent_usage = await self.usage_event_dao.get_by_org_and_period(
            db, org_id, start_date, end_date, limit=10
        )
        
        # Get recent credit purchases
        recent_purchases = await self.credit_purchase_dao.get_by_org_id(db, org_id, limit=5)
        
        # Check for overage warnings
        overage_warnings = []
        for balance in credit_balances:
            if balance.credits_balance == 0:
                overage_warnings.append(f"No {balance.credit_type.value} credits remaining")
            elif balance.credits_balance < 10:  # Low balance warning
                overage_warnings.append(f"Low {balance.credit_type.value} credits: {balance.credits_balance} remaining")
        
        # Get upcoming renewal date
        upcoming_renewal = None
        if subscription and subscription.status == SubscriptionStatus.ACTIVE:
            upcoming_renewal = subscription.current_period_end
        
        return schemas.BillingDashboard(
            org_id=org_id,
            subscription=subscription,
            credit_balances=credit_balances,
            recent_usage=[
                schemas.UsageEventRead(
                    id=event.id,
                    org_id=event.org_id,
                    user_id=event.user_id,
                    event_type=event.event_type,
                    credit_type=event.credit_type,
                    credits_consumed=event.credits_consumed,
                    usage_metadata=event.usage_metadata,
                    is_overage=event.is_overage,
                    grace_credits_used=0,  # Default value for events without this field
                    cost_cents=None,  # Default value for events without this field
                    created_at=event.created_at
                ) for event in recent_usage
            ],
            recent_purchases=[schemas.CreditPurchaseRead.model_validate(purchase) for purchase in recent_purchases],
            upcoming_renewal=upcoming_renewal,
            overage_warnings=overage_warnings
        )
    
    # --- New Credit Management Methods --- #
    
    async def expire_organization_credits(
        self,
        db: AsyncSession,
        org_id: Optional[uuid.UUID] = None,
        cutoff_datetime: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Expire all expiring organization credits based on current timestamp and update net credits.
        
        This method processes all expiring credits for an organization (or all organizations)
        and updates the net credits accordingly using batch operations.
        
        Args:
            db: Database session
            org_id: Organization ID (None for all organizations)
            cutoff_datetime: Cutoff datetime for expiration (defaults to current time)
            
        Returns:
            Dictionary with expiration summary
        """
        try:
            if cutoff_datetime is None:
                cutoff_datetime = datetime_now_utc()
            
            # Get all expiring credits using CRUD method
            expiring_credits = await self.org_credits_dao.get_expiring_credits_by_cutoff(
                db=db,
                org_id=org_id,
                cutoff_datetime=cutoff_datetime
            )

            if not expiring_credits:
                return {
                    "success": True,
                    "total_expired_credits": 0,
                    "total_organizations_affected": 0,
                    "organizations_processed": [],
                    "expiration_details": [],
                    "cutoff_datetime": cutoff_datetime
                }

            # Mark credits as expired in audit table using CRUD method
            await self.org_credits_dao.mark_credits_expired_by_cutoff(
                db=db,
                org_id=org_id,
                cutoff_datetime=cutoff_datetime,
            )
            
            # Group by organization and credit type to calculate totals
            expiration_batches = {}
            for credit in expiring_credits:
                key = (credit.org_id, credit.credit_type)
                if key not in expiration_batches:
                    expiration_batches[key] = 0
                expiration_batches[key] += credit.credits_granted
            
            # Process expirations using batch operations by organization
            total_expired = 0
            total_organizations = set()
            all_expiration_results = []
            
            # Group by organization for batch processing
            org_expiration_data = {}
            for (batch_org_id, credit_type), expired_amount in expiration_batches.items():
                if batch_org_id not in org_expiration_data:
                    org_expiration_data[batch_org_id] = {}
                org_expiration_data[batch_org_id][credit_type] = expired_amount
                total_expired += expired_amount
                total_organizations.add(batch_org_id)
            
            # Use batch expire for each organization
            for batch_org_id, expiration_data in org_expiration_data.items():
                # Convert to CreditExpirationBatch list
                credit_expirations = [
                    schemas.CreditExpirationBatch(
                        credit_type=credit_type,
                        expired_credits=expired_amount
                    )
                    for credit_type, expired_amount in expiration_data.items()
                ]
                
                expiration_results = await self.org_net_credits_dao.batch_expire_credits_and_adjust_consumption(
                    db=db,
                    org_id=batch_org_id,
                    credit_expirations=credit_expirations,
                    commit=False
                )
                all_expiration_results.extend(expiration_results)
            
            # Commit the transaction
            await db.commit()
            
            summary = {
                "success": True,
                "total_expired_credits": total_expired,
                "total_organizations_affected": len(total_organizations),
                "organizations_processed": list(total_organizations),
                "expiration_details": all_expiration_results,
                "cutoff_datetime": cutoff_datetime
            }
            
            billing_logger.info(
                f"Expired credits for {len(total_organizations)} organizations: "
                f"{total_expired} total credits expired"
            )
            
            return summary
            
        except Exception as e:
            # Rollback transaction on error
            await db.rollback()
            billing_logger.error(f"Error expiring organization credits: {e}", exc_info=True)
            raise BillingException(
                status_code=500,
                detail=f"Failed to expire organization credits: {str(e)}"
            )
    
    async def create_flexible_dollar_credit_checkout_session(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user: User,
        dollar_amount: int,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for flexible dollar credit purchase.
        
        This method allows users to purchase any amount of dollar credits
        using Stripe's dynamic pricing with line_items. It creates a purchase
        record with PENDING status immediately for tracking.
        
        Args:
            db: Database session
            org_id: Organization ID
            user: User initiating the checkout
            dollar_amount: Dollar amount to spend on credits
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            
        Returns:
            Dict containing checkout session URL and ID
        """
        try:
            # Get or create Stripe customer
            stripe_customer = await self._get_or_create_stripe_customer(db, org_id, user)
            
            # Calculate the amount of credits the user will receive
            credits_amount = dollar_amount
            
            # Convert dollar amount to cents for Stripe
            amount_cents = int(dollar_amount * 100)
            
            # Calculate expiration for purchased credits
            expires_at = None
            if settings.PURCHASED_CREDITS_EXPIRE_DAYS:
                expires_at = datetime_now_utc() + timedelta(days=settings.PURCHASED_CREDITS_EXPIRE_DAYS)
            
            # Create purchase record with PENDING status BEFORE creating checkout session
            purchase = await self.credit_purchase_dao.create_purchase(
                db=db,
                org_id=org_id,
                user_id=user.id,
                stripe_checkout_id="",  # Will be updated with actual session ID
                credit_type=CreditType.DOLLAR_CREDITS,
                credits_amount=credits_amount,
                amount_paid=dollar_amount,
                currency="usd",
                expires_at=expires_at
            )
            
            # Prepare checkout session parameters with dynamic pricing
            checkout_params = {
                "customer": stripe_customer.id,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "mode": "payment",
                "line_items": [{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"${credits_amount:.2f} Dollar Credits",
                            "description": f"Purchase ${credits_amount:.2f} in dollar credits for ${dollar_amount:.2f}",
                            "metadata": {
                                "kiwiq_type": "dollar_credits"
                            }
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                "payment_intent_data": {
                    "metadata": {
                        "kiwiq_org_id": str(org_id),
                        "kiwiq_user_id": str(user.id),
                        "kiwiq_type": "flexible_dollar_credit_purchase",
                        "kiwiq_purchase_id": str(purchase.id),
                        "credit_type": CreditType.DOLLAR_CREDITS.value,
                        "credits_amount": str(credits_amount),
                        "dollar_amount": str(dollar_amount)
                    }
                },
                "metadata": {
                    "kiwiq_org_id": str(org_id),
                    "kiwiq_user_id": str(user.id),
                    "kiwiq_type": "flexible_dollar_credit_purchase",
                    "kiwiq_purchase_id": str(purchase.id)
                }
            }
            
            # Create checkout session
            session = stripe.checkout.Session.create(**checkout_params)
            
            # Update purchase record with actual checkout session ID and add session ID to payment intent metadata
            purchase.stripe_checkout_id = session.id
            purchase.updated_at = datetime_now_utc()
            db.add(purchase)
            
            # # Update the payment intent with the checkout session ID for easier lookup in webhooks
            # if session.payment_intent:
            #     try:
            #         stripe.PaymentIntent.modify(
            #             session.payment_intent,
            #             metadata={
            #                 "checkout_session_id": session.id,
            #                 "kiwiq_org_id": str(org_id),
            #                 "kiwiq_user_id": str(user.id),
            #                 "kiwiq_type": "flexible_dollar_credit_purchase",
            #                 "kiwiq_purchase_id": str(purchase.id),
            #                 "credit_type": CreditType.DOLLAR_CREDITS.value,
            #                 "credits_amount": str(credits_amount),
            #                 "dollar_amount": str(dollar_amount)
            #             }
            #         )
            #     except stripe.StripeError as e:
            #         billing_logger.warning(f"Failed to update payment intent metadata: {e}")
            
            await db.commit()
            await db.refresh(purchase)
            
            billing_logger.info(
                f"Created flexible dollar credit checkout session {session.id} for org {org_id}: "
                f"${dollar_amount} for {credits_amount:.2f} credits (purchase ID: {purchase.id})"
            )
            
            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "purchase_id": str(purchase.id),
                "expires_at": datetime.fromtimestamp(session.expires_at)
            }
            
        except stripe.StripeError as e:
            # If Stripe fails after we created the purchase record, mark it as failed
            if 'purchase' in locals():
                purchase.status = PaymentStatus.FAILED
                purchase.updated_at = datetime_now_utc()
                db.add(purchase)
                await db.commit()
            
            billing_logger.error(f"Stripe error creating flexible dollar credit checkout session: {e}")
            raise StripeIntegrationException(
                detail="Failed to create checkout session",
                stripe_error_code=e.code,
                stripe_error_message=str(e)
            )
        except Exception as e:
            # If any other error occurs after creating purchase record, mark it as failed
            if 'purchase' in locals():
                purchase.status = PaymentStatus.FAILED
                purchase.updated_at = datetime_now_utc()
                db.add(purchase)
                await db.commit()
            
            billing_logger.error(f"Error creating flexible dollar credit checkout session: {e}")
            raise BillingException(
                status_code=500,
                detail=f"Failed to create checkout session: {str(e)}"
            )

    # --- Webhook Processing --- #
    
    async def process_stripe_webhook(
        self,
        db: AsyncSession,
        webhook_event: schemas.StripeWebhookEvent
    ) -> bool:
        """
        Process Stripe webhook events.
        
        This method handles various Stripe events to keep the billing system
        in sync with Stripe's state.
        """
        try:
            event_type = webhook_event.type
            event_data = webhook_event.data
            session = event_data["object"]
            mode = session.get("mode")
            
            billing_logger.info(f"Processing Stripe webhook: {event_type} (ID: {webhook_event.id})")
            
            if mode == "payment":
                if event_type in ["checkout.session.completed", "checkout.session.async_payment_succeeded"]:
                    await self._handle_payment_session_succeeded(db, event_data)
                elif event_type in ["checkout.session.async_payment_failed", "checkout.session.expired"]:
                    await self._handle_payment_session_failed(db, event_data)
            elif mode == "subscription":
                if event_type == "customer.subscription.created":
                    await self._handle_subscription_created(db, event_data)
                elif event_type == "customer.subscription.updated":
                    await self._handle_subscription_updated(db, event_data)
                elif event_type == "customer.subscription.deleted":
                    await self._handle_subscription_deleted(db, event_data)
            elif event_type == "charge.succeeded":
                await self._handle_charge_succeeded(db, event_data)
            # elif event_type == "invoice.payment_succeeded":
            #     await self._handle_payment_succeeded(db, event_data)
            # elif event_type == "invoice.payment_failed":
            #     await self._handle_payment_failed(db, event_data)
            # elif event_type == "payment_intent.succeeded":
            #     await self._handle_payment_session_succeeded(db, event_data)
            # elif event_type == "payment_intent.payment_failed":
            #     await self._handle_payment_intent_failed(db, event_data)
            else:
                billing_logger.info(f"Unhandled webhook event type: {event_type}")
            
            return True
            
        except Exception as e:
            billing_logger.error(f"Error processing webhook {webhook_event.id}: {e}", exc_info=True)
            return False
    
    # --- Webhook Event Handlers --- #
    
    
    
    async def _handle_payment_session_succeeded(self, db: AsyncSession, event_data: Dict[str, Any]) -> None:
        """Handle successful payment intent webhook (for credit purchases)."""
        checkout_session_object = event_data["object"]
        
        # Check payment status for checkout.session.completed events
        payment_status = checkout_session_object.get("payment_status")
        if payment_status == "unpaid":
            # Session completed but payment failed - delegate to failure handler
            await self._handle_payment_session_failed(db, event_data)
            return
        
        # Check if this is a flexible dollar credit purchase from metadata
        kiwiq_type = checkout_session_object.get("metadata", {}).get("kiwiq_type")
        
        if kiwiq_type == "flexible_dollar_credit_purchase":
            # Handle flexible dollar credit purchase by updating existing purchase record
            metadata = checkout_session_object.get("metadata", {})
            purchase_id = metadata.get("kiwiq_purchase_id")
            
            if not purchase_id:
                billing_logger.error(f"Missing purchase_id in metadata for flexible dollar credit purchase: {checkout_session_object['id']}")
                return
            
            # Get existing purchase record
            try:
                purchase = await self.credit_purchase_dao.get(db, uuid.UUID(purchase_id))
                if not purchase:
                    billing_logger.error(f"Purchase record not found for ID {purchase_id} (checkout session: {checkout_session_object['id']})")
                    return
                
                # Update status to succeeded
                purchase = await self.credit_purchase_dao.update_payment_status(
                    db, purchase, PaymentStatus.SUCCEEDED
                )
                
                # Allocate credits
                await self._allocate_purchased_credits(db, purchase)
                
                billing_logger.info(
                    f"Processed flexible dollar credit purchase: ${purchase.amount_paid} for {purchase.credits_amount} credits "
                    f"(org: {purchase.org_id}, purchase ID: {purchase.id}, checkout_session: {checkout_session_object['id']})"
                )
                
            except Exception as e:
                billing_logger.error(f"Error processing flexible dollar credit purchase success: {e}", exc_info=True)
                return
        else:
            # Handle regular credit purchase (existing logic)
            purchase = await self.credit_purchase_dao.get_by_stripe_checkout_id(
                db, checkout_session_object["id"]
            )
            
            if purchase and purchase.status == PaymentStatus.PENDING:
                # Update purchase status and allocate credits
                purchase = await self.credit_purchase_dao.update_payment_status(
                    db, purchase, PaymentStatus.SUCCEEDED
                )
                await self._allocate_purchased_credits(db, purchase)
    
    async def _handle_payment_session_failed(self, db: AsyncSession, event_data: Dict[str, Any]) -> None:
        """Handle failed payment session webhook (for credit purchases)."""
        checkout_session_object = event_data["object"]
        
        # Check if this is a flexible dollar credit purchase from metadata
        kiwiq_type = checkout_session_object.get("metadata", {}).get("kiwiq_type")
        
        if kiwiq_type == "flexible_dollar_credit_purchase":
            # Handle flexible dollar credit purchase failure by updating existing purchase record
            metadata = checkout_session_object.get("metadata", {})
            purchase_id = metadata.get("kiwiq_purchase_id")
            
            if not purchase_id:
                billing_logger.error(f"Missing purchase_id in metadata for failed flexible dollar credit purchase: {checkout_session_object['id']}")
                return
            
            # Get existing purchase record
            try:
                purchase = await self.credit_purchase_dao.get(db, uuid.UUID(purchase_id))
                if not purchase:
                    billing_logger.error(f"Purchase record not found for ID {purchase_id} (failed checkout session: {checkout_session_object['id']})")
                    return
                
                # Update status to failed
                purchase = await self.credit_purchase_dao.update_payment_status(
                    db, purchase, PaymentStatus.FAILED
                )
                
                billing_logger.info(
                    f"Marked flexible dollar credit purchase as failed: ${purchase.amount_paid} for {purchase.credits_amount} credits "
                    f"(org: {purchase.org_id}, purchase ID: {purchase.id}, checkout_session: {checkout_session_object['id']})"
                )
                
            except Exception as e:
                billing_logger.error(f"Error processing flexible dollar credit purchase failure: {e}", exc_info=True)
                return
        else:
            # Handle regular credit purchase failure (existing logic)
            purchase = await self.credit_purchase_dao.get_by_stripe_checkout_id(
                db, checkout_session_object["id"]
            )
            
            if purchase and purchase.status == PaymentStatus.PENDING:
                await self.credit_purchase_dao.update_payment_status(
                    db, purchase, PaymentStatus.FAILED
                )
                
                billing_logger.info(f"Marked credit purchase as failed (checkout session: {checkout_session_object['id']})")
    
    async def _handle_charge_succeeded(self, db: AsyncSession, event_data: Dict[str, Any]) -> None:
        """Handle charge succeeded webhook to update receipt URL for credit purchases."""
        try:
            charge_object = event_data["object"]
            
            # Extract key information from the charge
            metadata = charge_object.get("metadata", {})
            kiwiq_purchase_id = metadata.get("kiwiq_purchase_id")
            receipt_url = charge_object.get("receipt_url")
            
            if not receipt_url:
                billing_logger.warning(f"No receipt URL found in charge.succeeded event")
                return
            
            # Get payment intent to find the checkout session
            if kiwiq_purchase_id:
                try:
                    if kiwiq_purchase_id:
                        # Find the purchase record
                        purchase = await self.credit_purchase_dao.get(db, uuid.UUID(kiwiq_purchase_id))
                        if purchase:
                            # Update receipt URL
                            await self.credit_purchase_dao.update_receipt_url(
                                db=db,
                                purchase=purchase,
                                receipt_url=receipt_url
                            )
                            
                            billing_logger.info(
                                f"Updated receipt URL for purchase {purchase.id} "
                                f"from charge {charge_object['id']}"
                            )
                        else:
                            billing_logger.warning(
                                f"No purchase found for purchase ID {kiwiq_purchase_id} "
                                f"from charge {charge_object['id']}"
                            )
                    else:
                        billing_logger.warning(
                            f"No purchase ID found for charge {charge_object['id']}"
                        )
                        
                except stripe.StripeError as e:
                    billing_logger.error(f"Error retrieving purchase {kiwiq_purchase_id}: {e}")
            else:
                billing_logger.warning(f"No purchase ID found in charge.succeeded event")
                
        except Exception as e:
            billing_logger.error(f"Error handling charge.succeeded event: {e}", exc_info=True)
    
    async def _create_usage_event(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        consumption_request: schemas.CreditConsumptionRequest,
        is_overage: bool
    ) -> None:
        """Create a usage event for the given consumption request."""
        await self.usage_event_dao.create_usage_event(
            db=db,
            org_id=org_id,
            user_id=user_id,
            event_type=consumption_request.event_type,
            credit_type=consumption_request.credit_type,
            credits_consumed=consumption_request.credits_consumed,
            usage_metadata=consumption_request.metadata,
            is_overage=is_overage
        )

    # --- Private Helper Methods --- #
    
    async def _get_or_create_stripe_customer(self, db: AsyncSession, org_id: uuid.UUID, user: User) -> stripe.Customer:
        """Get or create a Stripe customer for an organization using external_billing_id."""
        # Get the organization 
        organization = await self.org_dao.get(db, org_id)
        if not organization:
            raise BillingException(
                status_code=404,
                detail="Organization not found"
            )
        
        # Check if customer already exists using external_billing_id
        if organization.external_billing_id:
            try:
                customer = stripe.Customer.retrieve(organization.external_billing_id)
                modify_kwargs = {}
                if customer.email != user.email:
                    modify_kwargs["email"] = user.email
                if customer.name != organization.name:
                    modify_kwargs["name"] = organization.name
                if modify_kwargs:
                    modify_kwargs["id"] = customer.id
                    customer.modify(**modify_kwargs)
                return customer
            except stripe.StripeError as e:
                billing_logger.warning(f"Failed to retrieve Stripe customer {organization.external_billing_id}: {e}")
                # Continue to create new customer if retrieval fails
        
        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            name=organization.name,
            metadata={
                "kiwiq_org_id": str(org_id),
                "kiwiq_user_id": str(user.id)
            }
        )
        
        # Update organization with Stripe customer ID
        organization.external_billing_id = customer.id
        db.add(organization)
        await db.commit()
        
        billing_logger.info(f"Created and linked Stripe customer {customer.id} for org {org_id}")
        
        return customer
    
    async def _allocate_purchased_credits(
        self,
        db: AsyncSession,
        purchase: models.CreditPurchase
    ) -> None:
        """Allocate credits from a successful purchase."""
        # Create audit record
        try:
            await self.org_credits_dao.allocate_credits(
                db=db,
                org_id=purchase.org_id,
                credit_type=purchase.credit_type,
                amount=purchase.credits_amount,
                source_type=CreditSourceType.PURCHASE,
                source_id=purchase.stripe_checkout_id,
                source_metadata={"purchase_id": str(purchase.id)},
                expires_at=purchase.expires_at,
                commit=False,
            )
            
            # Add to net credits
            await self.org_net_credits_dao.add_credits(
                db=db,
                org_id=purchase.org_id,
                credit_type=purchase.credit_type,
                credits_to_add=purchase.credits_amount,
                source_type=CreditSourceType.PURCHASE,
                source_id=purchase.stripe_checkout_id,
                expires_at=purchase.expires_at,
                commit=False,
            )

            await db.commit()
            
        except Exception as e:
            await db.rollback()
            billing_logger.error(f"Error allocating purchased credits: {e}", exc_info=True)
            raise
    
    
    
    async def _create_usage_event(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        consumption_request: schemas.CreditConsumptionRequest,
        is_overage: bool
    ) -> None:
        """Create a usage event for the given consumption request."""
        await self.usage_event_dao.create_usage_event(
            db=db,
            org_id=org_id,
            user_id=user_id,
            event_type=consumption_request.event_type,
            credit_type=consumption_request.credit_type,
            credits_consumed=consumption_request.credits_consumed,
            usage_metadata=consumption_request.metadata,
            is_overage=is_overage
        ) 

    
    ### TODO ###
    ################################################
    # --- Subscription Management --- #
    ################################################
    
    async def rotate_subscription_credits(
        self,
        db: AsyncSession,
        subscription_id: uuid.UUID,
        new_credits: Dict[CreditType, int],
        new_expires_at: datetime
    ) -> Dict[str, Any]:
        """
        Rotate subscription credits by expiring previous period credits and adding new ones.
        
        This method handles subscription renewal by:
        1. Expiring all previous subscription credits for this subscription
        2. Adding new credits for the current period
        
        Args:
            db: Database session
            subscription_id: Subscription ID
            new_credits: Dictionary of credit types and amounts to add
            new_expires_at: Expiration date for new credits
            
        Returns:
            Dictionary with rotation summary
        """
        try:
            # Get subscription details using CRUD method
            subscription = await self.org_subscription_dao.get(db, subscription_id)
            if not subscription:
                raise SubscriptionNotFoundException()
            
            # Step 1: Find all existing subscription credits for this subscription using CRUD method
            existing_credits = await self.org_credits_dao.get_subscription_credits_by_subscription_id(
                db=db,
                org_id=subscription.org_id,
                subscription_id=subscription_id,
                include_expired=False
            )
            
            # Group existing credits by credit type for expiration
            expiration_batches = {}
            for credit in existing_credits:
                credit_type = credit.credit_type
                if credit_type not in expiration_batches:
                    expiration_batches[credit_type] = 0
                expiration_batches[credit_type] += credit.credits_granted
            
            # Step 2: Mark existing credits as expired using CRUD method
            if existing_credits:
                await self.org_credits_dao.mark_subscription_credits_expired(
                    db=db,
                    org_id=subscription.org_id,
                    subscription_id=subscription_id
                )
            
            # Step 3: Process expirations for ALL credit types using batch operations
            all_credit_types = set(expiration_batches.keys())
            all_credit_types.update(new_credits.keys())
            
            expiration_results = []
            if expiration_batches:
                # Convert to CreditExpirationBatch list
                credit_expirations = [
                    schemas.CreditExpirationBatch(
                        credit_type=credit_type,
                        expired_credits=expired_amount
                    )
                    for credit_type, expired_amount in expiration_batches.items()
                ]
                
                expiration_results = await self.org_net_credits_dao.batch_expire_credits_and_adjust_consumption(
                    db=db,
                    org_id=subscription.org_id,
                    credit_expirations=credit_expirations,
                    commit=False
                )
            
            # Step 4: Add new credits using individual operations with commit=False
            addition_results = []
            for credit_type, amount in new_credits.items():
                # Create audit record
                await self.org_credits_dao.allocate_credits(
                    db=db,
                    org_id=subscription.org_id,
                    credit_type=credit_type,
                    amount=amount,
                    source_type=CreditSourceType.SUBSCRIPTION,
                    source_id=str(subscription.id),
                    source_metadata={
                        "subscription_id": str(subscription.id),
                        "stripe_subscription_id": subscription.stripe_subscription_id,
                        "plan_id": str(subscription.plan_id),
                        "billing_period": "trial" if subscription.is_trial_active else "monthly",
                        "period_start": subscription.current_period_start.isoformat(),
                        "period_end": subscription.current_period_end.isoformat(),
                        "is_renewal": False
                    },
                    expires_at=new_expires_at,
                    commit=False,
                )
                
                # Add to net credits
                addition_result = await self.org_net_credits_dao.add_credits(
                    db=db,
                    org_id=subscription.org_id,
                    credit_type=credit_type,
                    credits_to_add=amount,
                    source_type=CreditSourceType.SUBSCRIPTION,
                    source_id=str(subscription.id),
                    expires_at=new_expires_at,
                    commit=False,
                )
                addition_results.append(addition_result)
            
            # Commit the transaction
            await db.commit()
            
            # Prepare summary
            total_expired = sum(r.expired_credits for r in expiration_results)
            total_added = sum(new_credits.values())
            
            summary = {
                "success": True,
                "subscription_id": subscription.id,
                "org_id": subscription.org_id,
                "total_expired_credits": total_expired,
                "total_added_credits": total_added,
                "expired_by_type": {ct.value: expiration_batches.get(ct, 0) for ct in all_credit_types},
                "added_by_type": {ct.value: amount for ct, amount in new_credits.items()},
                "expiration_results": expiration_results,
                "addition_results": addition_results,
                "new_expires_at": new_expires_at
            }
            
            billing_logger.info(
                f"Rotated subscription credits for org {subscription.org_id}: "
                f"expired {total_expired}, added {total_added}"
            )
            
            return summary
            
        except Exception as e:
            # Rollback transaction on error
            await db.rollback()
            billing_logger.error(f"Error rotating subscription credits: {e}", exc_info=True)
            raise BillingException(
                status_code=500,
                detail=f"Failed to rotate subscription credits: {str(e)}"
            )



    async def _handle_checkout_session_completed(self, db: AsyncSession, event_data: Dict[str, Any]) -> None:
        """Handle checkout session completed webhook."""
        session = event_data["object"]
        mode = session.get("mode")
        
        if mode == "subscription":
            # Subscription checkout completed - the subscription will be created by Stripe
            # and we'll handle it in the customer.subscription.created webhook
            billing_logger.info(f"Subscription checkout completed: {session['id']}")
        elif mode == "payment":
            # One-time payment checkout completed
            payment_intent_id = session.get("payment_intent")
            if payment_intent_id:
                # The payment will be handled by payment_intent.succeeded webhook
                billing_logger.info(f"Payment checkout completed: {session['id']}")

    async def _handle_subscription_created(self, db: AsyncSession, event_data: Dict[str, Any]) -> None:
        """Handle subscription created webhook."""
        stripe_subscription = event_data["object"]
        
        # Extract metadata
        org_id = stripe_subscription["metadata"].get("kiwiq_org_id")
        plan_id = stripe_subscription["metadata"].get("kiwiq_plan_id")
        
        if not org_id or not plan_id:
            billing_logger.error(f"Missing metadata in subscription: {stripe_subscription['id']}")
            return
        
        # Check if subscription already exists
        existing_subscription = await self.org_subscription_dao.get_by_stripe_subscription_id(
            db, stripe_subscription["id"]
        )
        
        if existing_subscription:
            billing_logger.info(f"Subscription already exists: {stripe_subscription['id']}")
            return
        
        # Get the plan
        plan = await self.subscription_plan_dao.get(db, uuid.UUID(plan_id))
        if not plan:
            billing_logger.error(f"Plan not found: {plan_id}")
            return
        
        # Ensure organization has the correct external_billing_id
        organization = await self.org_dao.get(db, uuid.UUID(org_id))
        if organization and not organization.external_billing_id:
            organization.external_billing_id = stripe_subscription["customer"]
            db.add(organization)
            billing_logger.info(f"Updated organization {org_id} with Stripe customer ID {stripe_subscription['customer']}")
        
        # Create subscription record
        now = datetime_now_utc()
        trial_end = None
        is_trial_active = False
        
        if stripe_subscription.get("trial_end"):
            trial_end = datetime.fromtimestamp(stripe_subscription["trial_end"])
            is_trial_active = trial_end > now
        
        subscription = models.OrganizationSubscription(
            org_id=uuid.UUID(org_id),
            plan_id=uuid.UUID(plan_id),
            stripe_subscription_id=stripe_subscription["id"],
            status=SubscriptionStatus(stripe_subscription["status"]),
            current_period_start=datetime.fromtimestamp(stripe_subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(stripe_subscription["current_period_end"]),
            seats_count=stripe_subscription["items"]["data"][0]["quantity"],
            is_annual=stripe_subscription["items"]["data"][0]["price"]["recurring"]["interval"] == "year",
            trial_start=now if is_trial_active else None,
            trial_end=trial_end,
            is_trial_active=is_trial_active,
            created_at=now,
            updated_at=now
        )
        
        subscription = await self.org_subscription_dao.create(db, obj_in=subscription)
        
        # Allocate initial credits
        await self._allocate_subscription_credits(db, subscription, plan)
        
        billing_logger.info(f"Created subscription from webhook: {subscription.id}")
    
    async def _handle_subscription_updated(self, db: AsyncSession, event_data: Dict[str, Any]) -> None:
        """Handle subscription updated webhook."""
        stripe_subscription = event_data["object"]
        subscription = await self.org_subscription_dao.get_by_stripe_subscription_id(
            db, stripe_subscription["id"]
        )
        
        if subscription:
            # Update subscription status and period
            subscription.status = SubscriptionStatus(stripe_subscription["status"])
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription["current_period_start"])
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription["current_period_end"])
            subscription.cancel_at_period_end = stripe_subscription.get("cancel_at_period_end", False)
            subscription.updated_at = datetime_now_utc()
            
            await self.org_subscription_dao.update(db, db_obj=subscription, obj_in=schemas.SubscriptionUpdate())
    
    async def _handle_subscription_deleted(self, db: AsyncSession, event_data: Dict[str, Any]) -> None:
        """Handle subscription deleted webhook."""
        stripe_subscription = event_data["object"]
        subscription = await self.org_subscription_dao.get_by_stripe_subscription_id(
            db, stripe_subscription["id"]
        )
        
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime_now_utc()
            subscription.updated_at = datetime_now_utc()
            
            await self.org_subscription_dao.update(db, db_obj=subscription, obj_in=schemas.SubscriptionUpdate())
    
    async def _handle_payment_succeeded(self, db: AsyncSession, event_data: Dict[str, Any]) -> None:
        """Handle successful payment webhook."""
        invoice = event_data["object"]
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            subscription = await self.org_subscription_dao.get_by_stripe_subscription_id(db, subscription_id)
            if subscription and subscription.plan:
                # Allocate credits for the new billing period
                await self._allocate_subscription_credits(db, subscription, subscription.plan)
    
    async def _handle_payment_failed(self, db: AsyncSession, event_data: Dict[str, Any]) -> None:
        """Handle failed payment webhook."""
        invoice = event_data["object"]
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            subscription = await self.org_subscription_dao.get_by_stripe_subscription_id(db, subscription_id)
            if subscription:
                subscription.status = SubscriptionStatus.PAST_DUE
                subscription.updated_at = datetime_now_utc()
                
                await self.org_subscription_dao.update(db, db_obj=subscription, obj_in=schemas.SubscriptionUpdate())
    
    async def process_subscription_renewal(
        self,
        db: AsyncSession,
        subscription: models.OrganizationSubscription
    ) -> Dict[str, Any]:
        """
        Process subscription renewal by rotating credits.
        
        This method handles both trial-to-paid transitions and regular renewals.
        """
        try:
            # Get the subscription plan
            plan = subscription.plan
            if not plan:
                raise SubscriptionPlanNotFoundException()
            
            # Update subscription period info (this would typically come from Stripe webhook)
            old_period_end = subscription.current_period_end
            subscription.current_period_start = old_period_end
            
            if subscription.is_annual:
                subscription.current_period_end = old_period_end + timedelta(days=365)
            else:
                subscription.current_period_end = old_period_end + timedelta(days=30)
            
            # Handle trial-to-paid transition
            was_trial_active = subscription.is_trial_active and datetime_now_utc() >= subscription.trial_end
            
            if was_trial_active:
                subscription.is_trial_active = False
                subscription.status = SubscriptionStatus.ACTIVE
                billing_logger.info(f"Trial ended for subscription {subscription.id}, transitioning to paid")
            
            subscription.updated_at = datetime_now_utc()
            await self.org_subscription_dao.update(db, db_obj=subscription, obj_in=schemas.SubscriptionUpdate())
            
            # Allocate new credits using rotation
            await self._allocate_subscription_credits(db, subscription, plan, is_renewal=True)
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "org_id": subscription.org_id,
                "renewal_type": "trial_to_paid" if was_trial_active else "regular",
                "new_period_start": subscription.current_period_start,
                "new_period_end": subscription.current_period_end
            }
            
        except Exception as e:
            billing_logger.error(f"Error processing subscription renewal: {e}", exc_info=True)
            raise BillingException(
                status_code=500,
                detail=f"Failed to process subscription renewal: {str(e)}"
            )
    
    
    
    async def _allocate_subscription_credits(
        self,
        db: AsyncSession,
        subscription: models.OrganizationSubscription,
        plan: models.SubscriptionPlan,
        is_renewal: bool = False
    ) -> None:
        """Allocate monthly credits for a subscription, with optional credit rotation for renewals."""
        now = datetime_now_utc()
        period_end = subscription.current_period_end
        
        # Determine expiration based on subscription type
        if subscription.is_trial_active:
            expires_at = now + timedelta(days=settings.TRIAL_CREDITS_EXPIRE_DAYS)
        else:
            expires_at = period_end + timedelta(days=settings.SUBSCRIPTION_CREDITS_EXPIRE_DAYS)
        
        # If this is a renewal and not a trial, use credit rotation
        if is_renewal and not subscription.is_trial_active:
            # Use credit rotation for subscription renewals
            new_credits = {CreditType(credit_type): amount for credit_type, amount in plan.monthly_credits.items()}
            
            rotation_result = await self.rotate_subscription_credits(
                db=db,
                subscription_id=subscription.id,
                new_credits=new_credits,
                new_expires_at=expires_at
            )
            
            billing_logger.info(
                f"Rotated subscription credits for subscription {subscription.id}: "
                f"expired {rotation_result['total_expired_credits']}, "
                f"added {rotation_result['total_added_credits']} credits"
            )
        else:
            # For new subscriptions or trial-to-paid transitions, allocate fresh credits
            try:
                for credit_type_str, amount in plan.monthly_credits.items():
                    credit_type = CreditType(credit_type_str)
                    
                    # Create audit record
                    await self.org_credits_dao.allocate_credits(
                        db=db,
                        org_id=subscription.org_id,
                        credit_type=credit_type,
                        amount=amount,
                        source_type=CreditSourceType.SUBSCRIPTION,
                        source_id=str(subscription.id),
                        source_metadata={
                            "subscription_id": str(subscription.id),
                            "stripe_subscription_id": subscription.stripe_subscription_id,
                            "plan_id": str(subscription.plan_id),
                            "billing_period": "trial" if subscription.is_trial_active else "monthly",
                            "period_start": now.isoformat(),
                            "period_end": period_end.isoformat(),
                            "is_renewal": is_renewal
                        },
                        expires_at=expires_at,
                        commit=False,
                    )
                    
                    # Add to net credits
                    await self.org_net_credits_dao.add_credits(
                        db=db,
                        org_id=subscription.org_id,
                        credit_type=credit_type,
                        credits_to_add=amount,
                        source_type=CreditSourceType.SUBSCRIPTION,
                        source_id=str(subscription.id),
                        expires_at=expires_at,
                        commit=False,
                    )
                    
                    billing_logger.info(
                        f"Allocated {amount} {credit_type.value} credits to org {subscription.org_id} "
                        f"from subscription {subscription.id} (expires: {expires_at})"
                    )
                
                await db.commit()

            except Exception as e:
                await db.rollback()
                billing_logger.error(f"Error allocating subscription credits: {e}", exc_info=True)
                raise
    

#################################
    # --- Subscription Plan Management --- #
    
    async def create_subscription_plan(
        self,
        db: AsyncSession,
        plan_data: schemas.SubscriptionPlanCreate
    ) -> models.SubscriptionPlan:
        """
        Create a new subscription plan with Stripe integration.
        
        This method creates both the database record and the corresponding
        Stripe product and price objects for billing integration.
        """
        try:
            # Create Stripe product if not provided
            if not plan_data.stripe_product_id:
                stripe_product = stripe.Product.create(
                    name=plan_data.name,
                    description=plan_data.description,
                    metadata={
                        "kiwiq_plan": "true",
                        "max_seats": str(plan_data.max_seats),
                        "trial_days": str(plan_data.trial_days)
                    }
                )
                plan_data.stripe_product_id = stripe_product.id
            
            # Create the plan in database
            plan = await self.subscription_plan_dao.create(db, obj_in=plan_data)
            
            # Create Stripe prices for monthly and annual billing
            # Convert dollars to cents for Stripe
            monthly_price = stripe.Price.create(
                product=plan.stripe_product_id,
                unit_amount=int(plan.monthly_price * 100),  # Convert dollars to cents
                currency="usd",
                recurring={"interval": "month"},
                metadata={"kiwiq_plan_id": str(plan.id), "billing_period": "monthly"}
            )
            
            annual_price = stripe.Price.create(
                product=plan.stripe_product_id,
                unit_amount=int(plan.annual_price * 100),  # Convert dollars to cents
                currency="usd",
                recurring={"interval": "year"},
                metadata={"kiwiq_plan_id": str(plan.id), "billing_period": "annual"}
            )
            
            # Update plan with Stripe price IDs
            plan_update = schemas.SubscriptionPlanUpdate(
                stripe_price_id_monthly=monthly_price.id,
                stripe_price_id_annual=annual_price.id
            )
            plan = await self.subscription_plan_dao.update(db, db_obj=plan, obj_in=plan_update)
            
            billing_logger.info(f"Created subscription plan: {plan.name} (ID: {plan.id})")
            return plan
            
        except stripe.StripeError as e:
            billing_logger.error(f"Stripe error creating plan: {e}")
            raise StripeIntegrationException(
                detail="Failed to create subscription plan",
                stripe_error_code=e.code,
                stripe_error_message=str(e)
            )
    
    async def process_subscription_renewal(
        self,
        db: AsyncSession,
        subscription: models.OrganizationSubscription
    ) -> Dict[str, Any]:
        """
        Process subscription renewal by rotating credits.
        
        This method handles both trial-to-paid transitions and regular renewals.
        """
        try:
            # Get the subscription plan
            plan = subscription.plan
            if not plan:
                raise SubscriptionPlanNotFoundException()
            
            # Update subscription period info (this would typically come from Stripe webhook)
            old_period_end = subscription.current_period_end
            subscription.current_period_start = old_period_end
            
            if subscription.is_annual:
                subscription.current_period_end = old_period_end + timedelta(days=365)
            else:
                subscription.current_period_end = old_period_end + timedelta(days=30)
            
            # Handle trial-to-paid transition
            was_trial_active = subscription.is_trial_active and datetime_now_utc() >= subscription.trial_end
            
            if was_trial_active:
                subscription.is_trial_active = False
                subscription.status = SubscriptionStatus.ACTIVE
                billing_logger.info(f"Trial ended for subscription {subscription.id}, transitioning to paid")
            
            subscription.updated_at = datetime_now_utc()
            await self.org_subscription_dao.update(db, db_obj=subscription, obj_in=schemas.SubscriptionUpdate())
            
            # Allocate new credits using rotation
            await self._allocate_subscription_credits(db, subscription, plan, is_renewal=True)
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "org_id": subscription.org_id,
                "renewal_type": "trial_to_paid" if was_trial_active else "regular",
                "new_period_start": subscription.current_period_start,
                "new_period_end": subscription.current_period_end
            }
            
        except Exception as e:
            billing_logger.error(f"Error processing subscription renewal: {e}", exc_info=True)
            raise BillingException(
                status_code=500,
                detail=f"Failed to process subscription renewal: {str(e)}"
            ) 
    
    async def get_subscription_plans(
        self,
        db: AsyncSession,
        active_only: bool = True
    ) -> List[models.SubscriptionPlan]:
        """Get available subscription plans."""
        if active_only:
            return await self.subscription_plan_dao.get_active_plans(db)
        else:
            return await self.subscription_plan_dao.get_multi(db)
    
    # --- Subscription Management --- #
    
    async def create_subscription(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        subscription_data: schemas.SubscriptionCreate,
        user: User
    ) -> models.OrganizationSubscription:
        """
        Create a new subscription for an organization.
        
        This method handles the complete subscription creation process including
        Stripe customer creation, subscription setup, and initial credit allocation.
        """
        # Get the subscription plan
        plan = await self.subscription_plan_dao.get(db, subscription_data.plan_id)
        if not plan:
            raise SubscriptionPlanNotFoundException()
        
        # Check if organization already has a subscription
        existing_subscription = await self.org_subscription_dao.get_by_org_id(db, org_id)
        if existing_subscription:
            raise InvalidSubscriptionStateException("Organization already has an active subscription")
        
        try:
            # Create or get Stripe customer
            stripe_customer = await self._get_or_create_stripe_customer(db, org_id, user)
            
            # Attach payment method if provided
            if subscription_data.payment_method_id:
                stripe.PaymentMethod.attach(
                    subscription_data.payment_method_id,
                    customer=stripe_customer.id
                )
                
                # Set as default payment method
                stripe.Customer.modify(
                    stripe_customer.id,
                    invoice_settings={"default_payment_method": subscription_data.payment_method_id}
                )
            
            # Determine trial period
            trial_days = subscription_data.trial_days or plan.trial_days
            trial_end = None
            if trial_days > 0 and plan.is_trial_eligible:
                trial_end = datetime_now_utc() + timedelta(days=trial_days)
            
            # Create Stripe subscription
            stripe_price_id = plan.stripe_price_id_annual if subscription_data.is_annual else plan.stripe_price_id_monthly
            
            stripe_subscription_params = {
                "customer": stripe_customer.id,
                "items": [{"price": stripe_price_id, "quantity": subscription_data.seats_count}],
                "metadata": {
                    "kiwiq_org_id": str(org_id),
                    "kiwiq_plan_id": str(plan.id),
                    "kiwiq_user_id": str(user.id)
                }
            }
            
            if trial_end:
                stripe_subscription_params["trial_end"] = int(trial_end.timestamp())
            
            stripe_subscription = stripe.Subscription.create(**stripe_subscription_params)
            
            # Create subscription record in database
            now = datetime_now_utc()
            subscription = models.OrganizationSubscription(
                org_id=org_id,
                plan_id=plan.id,
                stripe_subscription_id=stripe_subscription.id,
                status=SubscriptionStatus.TRIAL if trial_end else SubscriptionStatus.ACTIVE,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                seats_count=subscription_data.seats_count,
                is_annual=subscription_data.is_annual,
                trial_start=now if trial_end else None,
                trial_end=trial_end,
                is_trial_active=bool(trial_end),
                created_at=now,
                updated_at=now
            )
            
            subscription = await self.org_subscription_dao.create(db, obj_in=subscription)
            
            # Allocate initial credits
            await self._allocate_subscription_credits(db, subscription, plan)
            
            billing_logger.info(f"Created subscription for org {org_id}: {subscription.id}")
            return subscription
            
        except stripe.StripeError as e:
            billing_logger.error(f"Stripe error creating subscription: {e}")
            raise StripeIntegrationException(
                detail="Failed to create subscription",
                stripe_error_code=e.code,
                stripe_error_message=str(e)
            )
    
    async def get_organization_subscription(
        self,
        db: AsyncSession,
        org_id: uuid.UUID
    ) -> Optional[models.OrganizationSubscription]:
        """Get the active subscription for an organization."""
        return await self.org_subscription_dao.get_by_org_id(db, org_id)
    
    async def update_subscription(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        subscription_update: schemas.SubscriptionUpdate
    ) -> models.OrganizationSubscription:
        """Update an existing subscription."""
        subscription = await self.org_subscription_dao.get_by_org_id(db, org_id)
        if not subscription:
            raise SubscriptionNotFoundException()
        
        try:
            # Handle plan changes
            if subscription_update.plan_id and subscription_update.plan_id != subscription.plan_id:
                new_plan = await self.subscription_plan_dao.get(db, subscription_update.plan_id)
                if not new_plan:
                    raise SubscriptionPlanNotFoundException()
                
                # Update Stripe subscription
                stripe_price_id = new_plan.stripe_price_id_annual if subscription.is_annual else new_plan.stripe_price_id_monthly
                stripe.SubscriptionItem.modify(
                    subscription.stripe_subscription_id,
                    price=stripe_price_id,
                    proration_behavior="create_prorations"
                )
                
                subscription.plan_id = new_plan.id
                
                # Allocate credits for new plan
                await self._allocate_subscription_credits(db, subscription, new_plan)
            
            # Handle seat count changes
            if subscription_update.seats_count and subscription_update.seats_count != subscription.seats_count:
                stripe.SubscriptionItem.modify(
                    subscription.stripe_subscription_id,
                    quantity=subscription_update.seats_count,
                    proration_behavior="create_prorations"
                )
                subscription.seats_count = subscription_update.seats_count
            
            # Handle cancellation
            if subscription_update.cancel_at_period_end is not None:
                if subscription_update.cancel_at_period_end:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                else:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=False
                    )
                subscription.cancel_at_period_end = subscription_update.cancel_at_period_end
            
            subscription.updated_at = datetime_now_utc()
            subscription = await self.org_subscription_dao.update(db, db_obj=subscription, obj_in=subscription_update)
            
            billing_logger.info(f"Updated subscription for org {org_id}: {subscription.id}")
            return subscription
            
        except stripe.StripeError as e:
            billing_logger.error(f"Stripe error updating subscription: {e}")
            raise StripeIntegrationException(
                detail="Failed to update subscription",
                stripe_error_code=e.code,
                stripe_error_message=str(e)
            )
    
    async def create_checkout_session(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user: User,
        plan_id: Optional[uuid.UUID] = None,
        is_annual: bool = False,
        price_id: Optional[str] = None,
        success_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for subscription or one-time purchase.
        
        This method handles both subscription creation and one-time credit purchases
        through Stripe Checkout, providing a consistent payment flow.
        
        Args:
            db: Database session
            org_id: Organization ID
            user: User initiating the checkout
            plan_id: Subscription plan ID (for subscriptions)
            is_annual: Whether to use annual billing (for subscriptions)
            price_id: Stripe price ID (for one-time purchases)
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            
        Returns:
            Dict containing checkout session URL and ID
        """
        try:
            # Get or create Stripe customer
            stripe_customer = await self._get_or_create_stripe_customer(db, org_id, user)
            
            # Prepare checkout session parameters
            checkout_params = {
                "customer": stripe_customer.id,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "kiwiq_org_id": str(org_id),
                    "kiwiq_user_id": str(user.id)
                }
            }
            
            if plan_id:
                # Subscription checkout
                plan = await self.subscription_plan_dao.get(db, plan_id)
                if not plan:
                    raise SubscriptionPlanNotFoundException()
                
                stripe_price_id = plan.stripe_price_id_annual if is_annual else plan.stripe_price_id_monthly
                
                checkout_params.update({
                    "mode": "subscription",
                    "line_items": [{
                        "price": stripe_price_id,
                        "quantity": 1
                    }],
                    "subscription_data": {
                        "metadata": {
                            "kiwiq_org_id": str(org_id),
                            "kiwiq_plan_id": str(plan_id)
                        }
                    }
                })
                
                # Add trial period if eligible
                if plan.is_trial_eligible and plan.trial_days > 0:
                    checkout_params["subscription_data"]["trial_period_days"] = plan.trial_days
                
            elif price_id:
                # One-time purchase checkout
                checkout_params.update({
                    "mode": "payment",
                    "line_items": [{
                        "price": price_id,
                        "quantity": 1
                    }],
                    "payment_intent_data": {
                        "metadata": {
                            "kiwiq_org_id": str(org_id),
                            "kiwiq_user_id": str(user.id),
                            "kiwiq_type": "credit_purchase"
                        }
                    }
                })
            else:
                raise BillingConfigurationException("Either plan_id or price_id must be provided")
            
            # Create checkout session
            session = stripe.checkout.Session.create(**checkout_params)
            
            billing_logger.info(f"Created checkout session {session.id} for org {org_id}")
            
            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "expires_at": datetime.fromtimestamp(session.expires_at)
            }
            
        except stripe.StripeError as e:
            billing_logger.error(f"Stripe error creating checkout session: {e}")
            raise StripeIntegrationException(
                detail="Failed to create checkout session",
                stripe_error_code=e.code,
                stripe_error_message=str(e)
            )
    
    
    def _calculate_credit_price(self, credit_type: CreditType, amount: float) -> float:
        """Calculate the price in dollars for purchasing credits."""
        if credit_type == CreditType.WORKFLOWS:
            return amount * settings.CREDIT_PRICE_WORKFLOWS_DOLLARS
        elif credit_type == CreditType.WEB_SEARCHES:
            return amount * settings.CREDIT_PRICE_WEB_SEARCHES_DOLLARS
        elif credit_type == CreditType.DOLLAR_CREDITS:
            # Dollar credits are priced with a markup ratio
            return amount * settings.CREDIT_PRICE_DOLLAR_CREDITS_RATIO
        else:
            raise BillingConfigurationException(f"No pricing configured for credit type: {credit_type}")

    async def purchase_credits(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        purchase_request: schemas.CreditPurchaseRequest
    ) -> models.CreditPurchase:
        """
        Purchase additional credits through Stripe.
        
        This method creates a payment intent for one-time credit purchases,
        allowing organizations to buy credits outside of their subscription.
        
        Args:
            db: Database session
            org_id: Organization ID
            user_id: User ID initiating the purchase
            purchase_request: Credit purchase details
            
        Returns:
            CreditPurchase record with payment intent details
        """
        try:
            # Get or create Stripe customer
            user = await db.get(User, user_id)
            if not user:
                raise BillingException(
                    status_code=404,
                    detail="User not found"
                )
            
            stripe_customer = await self._get_or_create_stripe_customer(db, org_id, user)
            
            # Calculate price for the credits
            amount_dollars = self._calculate_credit_price(
                purchase_request.credit_type,
                purchase_request.credits_amount
            )
            amount_cents = int(amount_dollars * 100)
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                customer=stripe_customer.id,
                payment_method=purchase_request.payment_method_id,
                confirm=True,
                metadata={
                    "kiwiq_org_id": str(org_id),
                    "kiwiq_user_id": str(user_id),
                    "kiwiq_type": "credit_purchase",
                    "credit_type": purchase_request.credit_type.value,
                    "credits_amount": str(purchase_request.credits_amount)
                }
            )
            
            # Calculate expiration (purchased credits expire after configured days)
            expires_at = None
            if settings.PURCHASED_CREDITS_EXPIRE_DAYS:
                expires_at = datetime_now_utc() + timedelta(days=settings.PURCHASED_CREDITS_EXPIRE_DAYS)
            
            # Create purchase record
            purchase = await self.credit_purchase_dao.create_purchase(
                db=db,
                org_id=org_id,
                user_id=user_id,
                stripe_checkout_id=payment_intent.id,
                credit_type=purchase_request.credit_type,
                credits_amount=purchase_request.credits_amount,
                amount_paid=amount_dollars,
                currency="usd",
                expires_at=expires_at
            )
            
            # If payment is immediately successful, allocate credits
            if payment_intent.status == "succeeded":
                await self._allocate_purchased_credits(db, purchase)
                purchase = await self.credit_purchase_dao.update_payment_status(
                    db, purchase, PaymentStatus.SUCCEEDED
                )
            
            billing_logger.info(
                f"Created credit purchase for org {org_id}: "
                f"{purchase_request.credits_amount} {purchase_request.credit_type.value} credits"
            )
            
            return purchase
            
        except stripe.StripeError as e:
            billing_logger.error(f"Stripe error purchasing credits: {e}")
            raise StripeIntegrationException(
                detail="Failed to process credit purchase",
                stripe_error_code=e.code,
                stripe_error_message=str(e)
            )
    
    async def create_customer_portal_session(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        return_url: str
    ) -> Dict[str, str]:
        """
        Create a Stripe Customer Portal session.
        
        This allows customers to manage their subscription, update payment methods,
        and view invoices through Stripe's hosted portal.
        
        Args:
            db: Database session
            org_id: Organization ID
            return_url: URL to return to after portal session
            
        Returns:
            Dict with portal URL
        """
        try:
            # Get organization to find customer ID
            organization = await self.org_dao.get(db, org_id)
            if not organization or not organization.external_billing_id:
                raise SubscriptionNotFoundException("No Stripe customer found for organization")
            
            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=organization.external_billing_id,
                return_url=return_url
            )
            
            billing_logger.info(f"Created customer portal session for org {org_id}")
            
            return {
                "portal_url": session.url
            }
            
        except stripe.StripeError as e:
            billing_logger.error(f"Stripe error creating portal session: {e}")
            raise StripeIntegrationException(
                detail="Failed to create customer portal session",
                stripe_error_code=e.code,
                stripe_error_message=str(e)
            )