"""
Billing routers for KiwiQ system.

This module defines the FastAPI routers for billing-related endpoints,
including subscription management, credit operations, and webhook handling.
It follows KiwiQ's established patterns for API design and error handling.
"""

import uuid
from typing import List, Optional, Annotated
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Query, Path, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

import stripe

from db.session import get_async_db_dependency

from kiwi_app.utils import get_kiwi_logger
from kiwi_app.settings import settings
from kiwi_app.auth.models import User
from kiwi_app.auth.utils import datetime_now_utc
from kiwi_app.auth.dependencies import get_current_active_verified_user, get_active_org_id, get_current_active_superuser

from kiwi_app.billing import schemas, services, dependencies
from kiwi_app.billing.models import CreditType
from kiwi_app.billing.exceptions import (
    InsufficientCreditsException,
    SubscriptionNotFoundException,
    SubscriptionPlanNotFoundException,
    InvalidSubscriptionStateException,
    PromotionCodeNotFoundException,
    PromotionCodeExpiredException,
    PromotionCodeExhaustedException,
    PromotionCodeAlreadyUsedException,
    PromotionCodeNotAllowedException,
    StripeIntegrationException,
    BillingException
)

# Get logger for billing operations
billing_logger = get_kiwi_logger(name="kiwi_app.billing")

# Create router instances
billing_router = APIRouter(prefix="/billing", tags=["billing"])
billing_admin_router = APIRouter(prefix="/billing/admin", tags=["billing-admin"])
billing_webhook_router = APIRouter(prefix="/billing/webhooks", tags=["billing-webhooks"])


def _get_base_url(request: Request, dev_env_suffix: str = ""):
    URL = f"{str(request.base_url).rstrip('/')}{settings.API_V1_PREFIX}{dev_env_suffix}"
    return URL
    return f"{settings.REDIRECT_BASE_URL}{dev_env_suffix}" if settings.APP_ENV == "PROD" else URL


# --- Subscription Management Endpoints --- #

@billing_router.get("/plans", response_model=List[schemas.SubscriptionPlanRead])
async def get_subscription_plans(
    active_only: bool = Query(True, description="Whether to return only active plans"),
    current_user: User = Depends(get_current_active_verified_user),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Get available subscription plans.
    
    This endpoint returns all available subscription plans that organizations
    can subscribe to. It follows KiwiQ's pattern of requiring organization context.
    """
    try:
        plans = await billing_service.get_subscription_plans(
            db=db,
            active_only=active_only
        )
        billing_logger.info(f"User {current_user.id} listed {len(plans)} subscription plans")
        return plans
    except Exception as e:
        billing_logger.error(f"Error fetching subscription plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription plans"
        )


@billing_router.post("/checkout/dollar-credits/session", response_model=schemas.CheckoutSessionResponse)
async def create_flexible_dollar_credit_checkout_session(
    request: Request,
    purchase_request: schemas.FlexibleDollarCreditPurchaseRequest,
    # success_url: Optional[str] = Query(None, description="Custom success URL"),
    # cancel_url: Optional[str] = Query(None, description="Custom cancel URL"),
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingReadActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Create a Stripe Checkout session for flexible dollar credit purchase (returns JSON).
    
    This endpoint is for API clients (mobile apps, SPAs) that need the checkout URL
    programmatically rather than being redirected. It returns the session details as JSON.
    
    The amount of credits received is calculated based on the dollar amount
    and the configured pricing ratio.
    
    Requires `billing:read` permission on the active organization.
    """
    try:
        # Construct success and cancel URLs using the auth pattern
        base_url = _get_base_url(request, "/billing/checkout-result")
        
        # Default URLs if not provided
        # if not success_url:
            # Include session_id placeholder that Stripe will replace
        success_url = f"{base_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}"
        
        # if not cancel_url:
        cancel_url = f"{base_url}?canceled=true"
        
        result = await billing_service.create_flexible_dollar_credit_checkout_session(
            db=db,
            org_id=active_org_id,
            user=current_user,
            dollar_amount=purchase_request.dollar_amount,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        billing_logger.info(
            f"User {current_user.id} created flexible dollar credit checkout session "
            f"for org {active_org_id} with amount ${purchase_request.dollar_amount} (API response)"
        )
        
        return result
        
    except StripeIntegrationException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.detail
        )
    except Exception as e:
        billing_logger.error(f"Error creating flexible dollar credit checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


# --- Checkout Result Endpoints --- #

@billing_router.get("/checkout-result", response_model=schemas.CheckoutResultResponse)
async def handle_checkout_result(
    request: Request,
    success: Optional[bool] = Query(None, description="Whether the checkout was successful"),
    canceled: Optional[bool] = Query(None, description="Whether the checkout was canceled"),
    session_id: Optional[str] = Query(None, description="Stripe checkout session ID"),
    redirect: Optional[bool] = Query(False, description="Whether to redirect to frontend after processing"),
    # current_user: User = Depends(get_current_active_verified_user),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Handle Stripe Checkout result (success or cancel).
    
    This endpoint is called after a user completes or cancels a Stripe Checkout session.
    For successful checkouts, it retrieves the session details from Stripe.
    
    Query Parameters:
        - success=true&session_id={CHECKOUT_SESSION_ID}: For successful checkouts
        - canceled=true: For canceled checkouts
        - redirect=true: To redirect to frontend after processing (optional)
    """
    try:
        # Handle canceled checkout
        if canceled:
            billing_logger.info(f"User canceled checkout")
            
            if redirect:
                # Redirect to frontend billing page with canceled status
                frontend_url = f"{settings.REDIRECT_BASE_URL}/billing?canceled=true"
                return RedirectResponse(url=frontend_url)
            
            return schemas.CheckoutResultResponse(
                success=False,
                message="Checkout was canceled",
                session_id=None
            )
        
        # Handle successful checkout
        if success and session_id:
            # Retrieve session details from Stripe
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                
                # Log successful checkout
                billing_logger.info(
                    f"User completed checkout session {session_id} "
                    f"(mode: {session.mode}, status: {session.status})"
                )
                
                if redirect:
                    # Redirect to frontend billing page with success status
                    frontend_url = f"{settings.REDIRECT_BASE_URL}/billing?success=true&session_id={session_id}"
                    return RedirectResponse(url=frontend_url)
                
                # Return success response with session details
                return schemas.CheckoutResultResponse(
                    success=True,
                    message="Checkout completed successfully",
                    session_id=session_id,
                    session_status=session.status,
                    customer_email=session.customer_email,
                    payment_status=session.payment_status
                )
                
            except stripe.StripeError as e:
                billing_logger.error(f"Error retrieving checkout session {session_id}: {e}")
                
                if redirect:
                    # Redirect to frontend with error status
                    frontend_url = f"{settings.REDIRECT_BASE_URL}/billing?error=invalid_session"
                    return RedirectResponse(url=frontend_url)
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired checkout session"
                )
        
        # Invalid request - neither success nor canceled
        if redirect:
            # Redirect to frontend billing page without status
            frontend_url = f"{settings.REDIRECT_BASE_URL}/billing"
            return RedirectResponse(url=frontend_url)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid checkout result parameters"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        billing_logger.error(f"Error handling checkout result: {e}", exc_info=True)
        
        if redirect:
            # Redirect to frontend with error status
            frontend_url = f"{settings.REDIRECT_BASE_URL}/billing?error=internal"
            return RedirectResponse(url=frontend_url)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process checkout result"
        )


# --- Credit Management Endpoints --- #

@billing_router.get("/credits", response_model=List[schemas.CreditBalance])
async def get_credit_balances(
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireCreditReadActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Get current credit balances for the active organization.
    
    Returns balances for all credit types including expiration information.
    Requires `credit:read` permission on the active organization.
    """
    try:
        balances = await billing_service.get_credit_balances(
            db=db,
            org_id=active_org_id
        )
        billing_logger.info(f"User {current_user.id} retrieved credit balances for org {active_org_id}")
        return balances
    except Exception as e:
        billing_logger.error(f"Error fetching credit balances: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch credit balances"
        )


@billing_router.get("/credits/list", response_model=List[schemas.OrganizationCreditsRead])
async def get_organization_credits_by_type(
    credit_type: CreditType = Query(None, description="Type of credits to retrieve"),
    include_expired: bool = Query(False, description="Whether to include expired credit records"),
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireCreditReadActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Get detailed credit records for the active organization by credit type.
    
    This endpoint returns individual credit allocation records showing the source,
    expiration, and detailed information for each credit allocation. Unlike the
    general credits endpoint which provides aggregated totals, this shows the
    itemized breakdown of all credit sources.
    
    Requires `credit:read` permission on the active organization.
    
    Args:
        credit_type (Optional): Type of credits to retrieve (workflows, web_searches, dollar_credits)
        include_expired: Whether to include expired credit records in the response
    
    Returns:
        List of detailed credit allocation records
    """
    try:
        credit_records = await billing_service.get_organization_credits_by_type(
            db=db,
            org_id=active_org_id,
            credit_type=credit_type,
            include_expired=include_expired
        )
        
        billing_logger.info(
            f"User {current_user.id} retrieved {len(credit_records)} {credit_type.value if credit_type else 'all'} "
            f"credit records for org {active_org_id} (include_expired={include_expired})"
        )
        
        return credit_records
        
    except BillingException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        billing_logger.error(f"Error fetching organization credits by type: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch {credit_type.value if credit_type else 'all'} credit records"
        )


@billing_router.post("/purchase-credits", response_model=schemas.CreditPurchaseRead)
async def purchase_credits(
    purchase_request: schemas.CreditPurchaseRequest,
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingManageActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Purchase additional credits through Stripe.
    
    Creates a payment intent and processes the credit purchase.
    Credits are allocated upon successful payment.
    Requires `billing:manage` permission on the active organization.
    """
    try:
        purchase = await billing_service.purchase_credits(
            db=db,
            org_id=active_org_id,
            user_id=current_user.id,
            purchase_request=purchase_request
        )
        
        billing_logger.info(f"User {current_user.id} created credit purchase for org {active_org_id}: {purchase.id}")
        return purchase
        
    except StripeIntegrationException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.detail
        )
    except Exception as e:
        billing_logger.error(f"Error purchasing credits: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to purchase credits"
        )

# --- Promotion Code Endpoints --- #

@billing_router.post("/promo-codes/apply", response_model=schemas.PromotionCodeApplyResult)
async def apply_promotion_code(
    code_application: schemas.PromotionCodeApply,
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingManageActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Apply a promotion code to grant credits to the organization.
    
    Validates the promotion code and applies credits if eligible.
    Requires `billing:manage` permission on the active organization.
    """
    try:
        result = await billing_service.apply_promotion_code(
            db=db,
            org_id=active_org_id,
            user_id=current_user.id,
            code_application=code_application
        )
        
        billing_logger.info(f"User {current_user.id} applied promotion code {code_application.code} to org {active_org_id}")
        return result
        
    except PromotionCodeNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion code not found"
        )
    except PromotionCodeExpiredException:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Promotion code has expired"
        )
    except PromotionCodeExhaustedException:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Promotion code has reached its usage limit"
        )
    except PromotionCodeAlreadyUsedException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Promotion code has already been used by this organization"
        )
    except PromotionCodeNotAllowedException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is not allowed to use this promotion code"
        )
    except Exception as e:
        billing_logger.error(f"Error applying promotion code: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply promotion code"
        )


# --- Usage Analytics Endpoints --- #

@billing_router.get("/usage", response_model=schemas.UsageSummary)
async def get_usage_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingReadActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Get usage summary for the active organization.
    
    Returns usage statistics for a specified date range.
    Defaults to the current billing period if no dates provided.
    Requires `billing:read` permission on the active organization.
    """
    try:
        # Default to current month if no dates provided
        if not start_date or not end_date:
            now = datetime_now_utc()
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_date = start_date.replace(year=now.year + 1, month=1) - timedelta(days=1)
            else:
                end_date = start_date.replace(month=now.month + 1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        summary = await billing_service.get_usage_summary(
            db=db,
            org_id=active_org_id,
            start_date=start_date,
            end_date=end_date
        )
        
        billing_logger.info(f"User {current_user.id} retrieved usage summary for org {active_org_id}")
        return summary
    except Exception as e:
        billing_logger.error(f"Error fetching usage summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch usage summary"
        )


@billing_router.get("/dashboard", response_model=schemas.BillingDashboard)
async def get_billing_dashboard(
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingReadActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Get comprehensive billing dashboard data for the active organization.
    
    Returns subscription details, credit balances, recent usage, and warnings.
    Requires `billing:read` permission on the active organization.
    """
    try:
        dashboard = await billing_service.get_billing_dashboard(
            db=db,
            org_id=active_org_id
        )
        
        billing_logger.info(f"User {current_user.id} retrieved billing dashboard for org {active_org_id}")
        return dashboard
    except Exception as e:
        billing_logger.error(f"Error fetching billing dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch billing dashboard"
        )


# --- Webhook Endpoints --- #

@billing_webhook_router.post("/stripe")
async def handle_stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Handle Stripe webhook events.
    
    This endpoint processes Stripe webhooks to keep the billing system
    in sync with Stripe's state. It includes signature verification and
    idempotency handling.
    """
    try:
        # Get raw body for signature verification
        raw_body = await request.body()
        stripe_signature = request.headers.get("stripe-signature")
        
        if not stripe_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature"
            )
        
        # Verify webhook signature
        
        try:
            event = stripe.Webhook.construct_event(
                raw_body,
                stripe_signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            billing_logger.info(f"Received Stripe webhook: {event['type']} (ID: {event['id']})")
            billing_logger.info(f"Event DATA: {event['data']}")
            # return {"status": "received"}
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        
        # Convert to our schema
        webhook_event = schemas.StripeWebhookEvent(
            id=event["id"],
            type=event["type"],
            created=event["created"],
            data=event["data"],
            livemode=event["livemode"]
        )
        
        # Process webhook in background to avoid timeout
        background_tasks.add_task(
            process_webhook_background,
            webhook_event,
            billing_service
        )
        
        billing_logger.info(f"Received Stripe webhook: {event['type']} (ID: {event['id']})")
        
        return {"status": "received"}
        
    except HTTPException:
        raise
    except Exception as e:
        billing_logger.error(f"Error handling Stripe webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


async def process_webhook_background(
    webhook_event: schemas.StripeWebhookEvent,
    billing_service: services.BillingService
):
    """
    Background task to process webhook events.
    
    This function handles the actual webhook processing in the background
    to avoid blocking the webhook response.
    """
    try:
        # Get database session
        async for db in get_async_db_dependency():
            success = await billing_service.process_stripe_webhook(db, webhook_event)
            
            if success:
                billing_logger.info(f"Successfully processed webhook: {webhook_event.id}")
            else:
                billing_logger.error(f"Failed to process webhook: {webhook_event.id}")
            
            break  # Exit the async generator
            
    except Exception as e:
        billing_logger.error(f"Error in webhook background processing: {e}", exc_info=True)



# --- Admin Endpoints --- #

@billing_admin_router.post("/plans", response_model=schemas.SubscriptionPlanRead)
async def create_subscription_plan(
    plan_data: schemas.SubscriptionPlanCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Create a new subscription plan (Admin only).
    
    Creates both the database record and corresponding Stripe product/prices.
    Requires superuser permissions.
    """
    try:
        plan = await billing_service.create_subscription_plan(db, plan_data)
        billing_logger.info(f"Admin {current_user.id} created subscription plan: {plan.name} (ID: {plan.id})")
        return plan
    except StripeIntegrationException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.detail
        )
    except Exception as e:
        billing_logger.error(f"Error creating subscription plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription plan"
        )


@billing_admin_router.get("/plans", response_model=List[schemas.SubscriptionPlanRead])
async def get_all_subscription_plans(
    active_only: bool = Query(False, description="Whether to return only active plans"),
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Get all subscription plans (Admin only).
    
    Returns all plans including inactive ones for administrative purposes.
    Requires superuser permissions.
    """
    try:
        plans = await billing_service.get_subscription_plans(db, active_only=active_only)
        billing_logger.info(f"Admin {current_user.id} retrieved {len(plans)} subscription plans")
        return plans
    except Exception as e:
        billing_logger.error(f"Error fetching admin subscription plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription plans"
        )





### TODO ###
################################################
# --- Subscription Management --- #
################################################



@billing_router.post("/subscribe", response_model=schemas.SubscriptionRead)
async def create_subscription(
    subscription_data: schemas.SubscriptionCreate,
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingManageActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Create a new subscription for the active organization.
    
    This endpoint handles the complete subscription creation process including
    Stripe integration and initial credit allocation.
    
    Requires `billing:manage` permission on the active organization.
    """
    try:
        subscription = await billing_service.create_subscription(
            db=db,
            org_id=active_org_id,
            subscription_data=subscription_data,
            user=current_user
        )
        
        billing_logger.info(f"User {current_user.id} created subscription for org {active_org_id}: {subscription.id}")
        return subscription
        
    except SubscriptionPlanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    except InvalidSubscriptionStateException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except StripeIntegrationException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.detail
        )
    except Exception as e:
        billing_logger.error(f"Error creating subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )


@billing_router.get("/subscription", response_model=Optional[schemas.SubscriptionReadWithPlan])
async def get_current_subscription(
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingReadActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Get the current subscription for the active organization.
    
    Returns subscription details including plan information and current status.
    Requires `billing:read` permission on the active organization.
    """
    try:
        subscription = await billing_service.get_organization_subscription(
            db=db,
            org_id=active_org_id
        )
        if subscription:
            billing_logger.info(f"User {current_user.id} retrieved subscription for org {active_org_id}")
        return subscription
    except Exception as e:
        billing_logger.error(f"Error fetching subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription"
        )


@billing_router.put("/subscription", response_model=schemas.SubscriptionRead)
async def update_subscription(
    subscription_update: schemas.SubscriptionUpdate,
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingManageActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Update the current subscription for the active organization.
    
    Supports plan changes, seat count updates, and cancellation scheduling.
    Requires `billing:manage` permission on the active organization.
    """
    try:
        subscription = await billing_service.update_subscription(
            db=db,
            org_id=active_org_id,
            subscription_update=subscription_update
        )
        
        billing_logger.info(f"User {current_user.id} updated subscription for org {active_org_id}: {subscription.id}")
        return subscription
        
    except SubscriptionNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    except SubscriptionPlanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target subscription plan not found"
        )
    except StripeIntegrationException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.detail
        )
    except Exception as e:
        billing_logger.error(f"Error updating subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )


@billing_router.post("/checkout/subscription")
async def create_subscription_checkout(
    request: Request,
    plan_id: uuid.UUID,
    is_annual: bool = Query(False, description="Whether to use annual billing"),
    success_url: Optional[str] = Query(None, description="Custom success URL"),
    cancel_url: Optional[str] = Query(None, description="Custom cancel URL"),
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingReadActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Create a Stripe Checkout session for subscription and redirect to Stripe.
    
    This endpoint creates a checkout session for subscribing to a plan
    using Stripe's hosted checkout page and immediately redirects the user.
    
    Requires `billing:read` permission on the active organization.
    """
    try:
        # Construct success and cancel URLs using the auth pattern
        base_url = _get_base_url(request, "/billing/checkout-result")
        
        # Default URLs if not provided
        if not success_url:
            # Include session_id placeholder that Stripe will replace
            success_url = f"{base_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}"
        
        if not cancel_url:
            cancel_url = f"{base_url}?canceled=true"
        
        result = await billing_service.create_checkout_session(
            db=db,
            org_id=active_org_id,
            user=current_user,
            plan_id=plan_id,
            is_annual=is_annual,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        billing_logger.info(f"User {current_user.id} created subscription checkout session for org {active_org_id}")
        
        # Redirect to Stripe checkout page
        return RedirectResponse(url=result["checkout_url"], status_code=303)
        
    except SubscriptionPlanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    except StripeIntegrationException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.detail
        )
    except Exception as e:
        billing_logger.error(f"Error creating checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@billing_router.post("/checkout/subscription/session", response_model=schemas.CheckoutSessionResponse)
async def create_subscription_checkout_session(
    request: Request,
    plan_id: uuid.UUID,
    is_annual: bool = Query(False, description="Whether to use annual billing"),
    success_url: Optional[str] = Query(None, description="Custom success URL"),
    cancel_url: Optional[str] = Query(None, description="Custom cancel URL"),
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingReadActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Create a Stripe Checkout session for subscription (returns JSON).
    
    This endpoint is for API clients that need the checkout URL programmatically.
    It returns the session details as JSON.
    
    Requires `billing:read` permission on the active organization.
    """
    try:
        # Construct success and cancel URLs using the auth pattern
        base_url = _get_base_url(request, "/billing/checkout-result")
        
        # Default URLs if not provided
        if not success_url:
            # Include session_id placeholder that Stripe will replace
            success_url = f"{base_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}"
        
        if not cancel_url:
            cancel_url = f"{base_url}?canceled=true"
        
        result = await billing_service.create_checkout_session(
            db=db,
            org_id=active_org_id,
            user=current_user,
            plan_id=plan_id,
            is_annual=is_annual,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        billing_logger.info(f"User {current_user.id} created subscription checkout session for org {active_org_id} (API response)")
        return result
        
    except SubscriptionPlanNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    except StripeIntegrationException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.detail
        )
    except Exception as e:
        billing_logger.error(f"Error creating checkout session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


# @billing_router.post("/checkout/credits")
# async def create_credit_purchase_checkout(
#     request: Request,
#     price_id: str = Query(..., description="Stripe price ID for the credit pack"),
#     success_url: Optional[str] = Query(None, description="Custom success URL"),
#     cancel_url: Optional[str] = Query(None, description="Custom cancel URL"),
#     active_org_id: uuid.UUID = Depends(get_active_org_id),
#     current_user: User = Depends(dependencies.RequireBillingReadActiveOrg),
#     db: AsyncSession = Depends(get_async_db_dependency),
#     billing_service: services.BillingService = Depends(dependencies.get_billing_service)
# ):
#     """
#     Create a Stripe Checkout session for credit purchase and redirect to Stripe.
    
#     This endpoint creates a checkout session for one-time credit purchases
#     using Stripe's hosted checkout page and immediately redirects the user.
    
#     Requires `billing:read` permission on the active organization.
#     """
#     try:
#         # Construct success and cancel URLs using the auth pattern
#         base_url = _get_base_url(request, "/billing/checkout-result")
        
#         # Default URLs if not provided
#         if not success_url:
#             # Include session_id placeholder that Stripe will replace
#             success_url = f"{base_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}"
        
#         if not cancel_url:
#             cancel_url = f"{base_url}?canceled=true"
        
#         result = await billing_service.create_checkout_session(
#             db=db,
#             org_id=active_org_id,
#             user=current_user,
#             price_id=price_id,
#             success_url=success_url,
#             cancel_url=cancel_url
#         )
        
#         billing_logger.info(f"User {current_user.id} created credit purchase checkout session for org {active_org_id}")
        
#         # Redirect to Stripe checkout page
#         return RedirectResponse(url=result["checkout_url"], status_code=303)
        
#     except StripeIntegrationException as e:
#         raise HTTPException(
#             status_code=status.HTTP_402_PAYMENT_REQUIRED,
#             detail=e.detail
#         )
#     except Exception as e:
#         billing_logger.error(f"Error creating checkout session: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to create checkout session"
#         )


# @billing_router.post("/checkout/credits/session", response_model=schemas.CheckoutSessionResponse)
# async def create_credit_purchase_checkout_session(
#     request: Request,
#     price_id: str = Query(..., description="Stripe price ID for the credit pack"),
#     success_url: Optional[str] = Query(None, description="Custom success URL"),
#     cancel_url: Optional[str] = Query(None, description="Custom cancel URL"),
#     active_org_id: uuid.UUID = Depends(get_active_org_id),
#     current_user: User = Depends(dependencies.RequireBillingReadActiveOrg),
#     db: AsyncSession = Depends(get_async_db_dependency),
#     billing_service: services.BillingService = Depends(dependencies.get_billing_service)
# ):
#     """
#     Create a Stripe Checkout session for credit purchase (returns JSON).
    
#     This endpoint is for API clients that need the checkout URL programmatically.
#     It returns the session details as JSON.
    
#     Requires `billing:read` permission on the active organization.
#     """
#     try:
#         # Construct success and cancel URLs using the auth pattern
#         base_url = _get_base_url(request, "/billing/checkout-result")
        
#         # Default URLs if not provided
#         if not success_url:
#             # Include session_id placeholder that Stripe will replace
#             success_url = f"{base_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}"
        
#         if not cancel_url:
#             cancel_url = f"{base_url}?canceled=true"
        
#         result = await billing_service.create_checkout_session(
#             db=db,
#             org_id=active_org_id,
#             user=current_user,
#             price_id=price_id,
#             success_url=success_url,
#             cancel_url=cancel_url
#         )
        
#         billing_logger.info(f"User {current_user.id} created credit purchase checkout session for org {active_org_id} (API response)")
#         return result
        
#     except StripeIntegrationException as e:
#         raise HTTPException(
#             status_code=status.HTTP_402_PAYMENT_REQUIRED,
#             detail=e.detail
#         )
#     except Exception as e:
#         billing_logger.error(f"Error creating checkout session: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to create checkout session"
#         )

@billing_router.post("/portal", response_model=schemas.CustomerPortalResponse)
async def create_customer_portal_session(
    return_url: str,
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(dependencies.RequireBillingManageActiveOrg),
    db: AsyncSession = Depends(get_async_db_dependency),
    billing_service: services.BillingService = Depends(dependencies.get_billing_service)
):
    """
    Create a Stripe Customer Portal session.
    
    This endpoint creates a portal session that allows customers to manage
    their subscription, update payment methods, and view invoices.
    Requires `billing:manage` permission on the active organization.
    """
    try:
        result = await billing_service.create_customer_portal_session(
            db=db,
            org_id=active_org_id,
            return_url=return_url
        )
        
        billing_logger.info(f"User {current_user.id} created customer portal session for org {active_org_id}")
        return result
        
    except SubscriptionNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    except StripeIntegrationException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.detail
        )
    except Exception as e:
        billing_logger.error(f"Error creating portal session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )


# # --- Error Handlers --- #

# @router.exception_handler(BillingException)
# async def billing_exception_handler(request: Request, exc: BillingException):
#     """
#     Global exception handler for billing-related exceptions.
    
#     Provides consistent error responses for all billing exceptions.
#     """
#     billing_logger.warning(f"Billing exception: {exc.detail}")
#     return HTTPException(
#         status_code=exc.status_code,
#         detail=exc.detail
#     )



# Set router prefixes (these will be set when including in main app)
# router.prefix = "/billing"
# admin_router.prefix = "/billing/admin"
# webhook_router.prefix = "/billing/webhooks" 