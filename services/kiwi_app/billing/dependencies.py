"""
Billing dependencies for KiwiQ system.

This module defines dependency injection functions for billing services and DAOs,
following KiwiQ's established patterns for dependency management.
"""

import uuid
from typing import Optional
from fastapi import Depends, Header, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_async_db_dependency
from kiwi_app.utils import get_kiwi_logger
from kiwi_app.auth import crud as auth_crud
from kiwi_app.auth.dependencies import get_organization_dao
from kiwi_app.billing import crud, services, models
from kiwi_app.auth.dependencies import (
    get_current_active_verified_user,
    get_active_org_id,
    PermissionChecker as AuthPermissionChecker,
    SpecificOrgPermissionChecker as AuthSpecificOrgPermissionChecker,
    get_current_active_superuser
)
from kiwi_app.auth.constants import Permissions
from kiwi_app.auth.models import User
from kiwi_app.billing.constants import BillingPermissions

billing_logger = get_kiwi_logger(name="kiwi_app.billing.dependencies")

# --- DAO Dependency Factories --- #

def get_subscription_plan_dao() -> crud.SubscriptionPlanDAO:
    """Get SubscriptionPlanDAO instance."""
    return crud.SubscriptionPlanDAO()


def get_organization_subscription_dao() -> crud.OrganizationSubscriptionDAO:
    """Get OrganizationSubscriptionDAO instance."""
    return crud.OrganizationSubscriptionDAO()


def get_organization_credits_dao() -> crud.OrganizationCreditsDAO:
    """Get OrganizationCreditsDAO instance."""
    return crud.OrganizationCreditsDAO()


def get_organization_net_credits_dao() -> crud.OrganizationNetCreditsDAO:
    """Get OrganizationNetCreditsDAO instance."""
    return crud.OrganizationNetCreditsDAO()


def get_usage_event_dao() -> crud.UsageEventDAO:
    """Get UsageEventDAO instance."""
    return crud.UsageEventDAO()


def get_credit_purchase_dao() -> crud.CreditPurchaseDAO:
    """Get CreditPurchaseDAO instance."""
    return crud.CreditPurchaseDAO()


def get_promotion_code_dao() -> crud.PromotionCodeDAO:
    """Get PromotionCodeDAO instance."""
    return crud.PromotionCodeDAO()


def get_promotion_code_usage_dao() -> crud.PromotionCodeUsageDAO:
    """Get PromotionCodeUsageDAO instance."""
    return crud.PromotionCodeUsageDAO()


# --- Service Dependency Factory --- #

def get_billing_service(
    subscription_plan_dao: crud.SubscriptionPlanDAO = Depends(get_subscription_plan_dao),
    org_subscription_dao: crud.OrganizationSubscriptionDAO = Depends(get_organization_subscription_dao),
    org_credits_dao: crud.OrganizationCreditsDAO = Depends(get_organization_credits_dao),
    org_net_credits_dao: crud.OrganizationNetCreditsDAO = Depends(get_organization_net_credits_dao),
    usage_event_dao: crud.UsageEventDAO = Depends(get_usage_event_dao),
    credit_purchase_dao: crud.CreditPurchaseDAO = Depends(get_credit_purchase_dao),
    promotion_code_dao: crud.PromotionCodeDAO = Depends(get_promotion_code_dao),
    promotion_code_usage_dao: crud.PromotionCodeUsageDAO = Depends(get_promotion_code_usage_dao),
    org_dao: auth_crud.OrganizationDAO = Depends(get_organization_dao),
) -> services.BillingService:
    """
    Dependency function to instantiate BillingService with its DAO dependencies.
    
    This follows KiwiQ's established pattern for service dependency injection,
    ensuring all required DAOs are properly injected into the service.
    """
    return services.BillingService(
        subscription_plan_dao=subscription_plan_dao,
        org_subscription_dao=org_subscription_dao,
        org_credits_dao=org_credits_dao,
        org_net_credits_dao=org_net_credits_dao,
        usage_event_dao=usage_event_dao,
        credit_purchase_dao=credit_purchase_dao,
        promotion_code_dao=promotion_code_dao,
        promotion_code_usage_dao=promotion_code_usage_dao,
        org_dao=org_dao,
    )


# --- Permission Checkers Using Billing Permissions--- #

# For billing operations on active org
RequireBillingReadActiveOrg = AuthPermissionChecker([BillingPermissions.BILLING_READ])
RequireBillingManageActiveOrg = AuthPermissionChecker([BillingPermissions.BILLING_MANAGE])

# For credit operations
RequireCreditReadActiveOrg = AuthPermissionChecker([BillingPermissions.CREDIT_READ])


# --- Resource Fetching Dependencies with Permission Checks --- #

async def get_subscription_for_org(
    active_org_id: uuid.UUID = Depends(get_active_org_id),
    db: AsyncSession = Depends(get_async_db_dependency),
    subscription_dao: crud.OrganizationSubscriptionDAO = Depends(get_organization_subscription_dao)
) -> Optional[models.OrganizationSubscription]:
    """
    Dependency to fetch subscription for the active organization.
    Permissions should be checked by a separate dependency before this one.
    """
    if not active_org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required"
        )
    
    subscription = await subscription_dao.get_by_org_id(db, org_id=active_org_id)
    return subscription 
