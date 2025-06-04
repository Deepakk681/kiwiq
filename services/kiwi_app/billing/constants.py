"""
Billing constants for KiwiQ system.

This module defines constants used throughout the billing module,
including permission definitions.
"""
from enum import Enum

# --- Billing Permissions --- #

class BillingPermissions(str, Enum):
    """Billing-specific permissions that extend the auth system permissions."""
    
    # Billing management permissions
    BILLING_READ = "billing:read"  # View billing information
    BILLING_MANAGE = "billing:manage"  # Manage subscriptions and payment methods
    
    # Credit permissions
    CREDIT_READ = "credit:read"  # View credit balances
    # CREDIT_CONSUME = "credit:consume"  # Consume credits for operations
    
    # # Admin permissions
    # BILLING_ADMIN = "billing:admin"  # Admin billing operations

# --- Credit Consumption Event Types --- #

class CreditEventTypes:
    """Standard event types for credit consumption tracking."""
    
    # Workflow operations
    WORKFLOW_EXECUTION = "workflow_execution"
    WORKFLOW_NODE_EXECUTION = "workflow_node_execution"
    WORKFLOW_LONG_RUNNING = "workflow_long_running"
    
    # Search operations
    WEB_SEARCH = "web_search"
    WEB_SEARCH_BATCH = "web_search_batch"
    
    # LLM operations
    LLM_CALL = "llm_call"
    LLM_EMBEDDING = "llm_embedding"
    LLM_FINE_TUNING = "llm_fine_tuning"
    
    # Credit management
    CREDIT_ALLOCATION = "credit_allocation"
    CREDIT_ADJUSTMENT = "credit_adjustment"
    CREDIT_REFUND = "credit_refund"

# --- Billing Configuration --- #

# Default credit allocations for subscription plans
DEFAULT_CREDIT_ALLOCATIONS = {
    "starter": {
        "workflows": 100.0,
        "web_searches": 1000.0,
        "dollar_credits": 10.0
    },
    "professional": {
        "workflows": 500.0,
        "web_searches": 5000.0,
        "dollar_credits": 50.0
    },
    "enterprise": {
        "workflows": 2000.0,
        "web_searches": 20000.0,
        "dollar_credits": 200.0
    }
}

# Credit pack sizes for one-time purchases
CREDIT_PACK_SIZES = {
    "workflows": {
        "small": 100,
        "medium": 500,
        "large": 2000
    },
    "web_searches": {
        "small": 1000,
        "large": 10000
    },
    "dollar_credits": {
        "small": 25,
        "large": 100
    }
}

# Overage policy defaults
DEFAULT_OVERAGE_POLICY = {
    "allow_overage": True,
    "grace_percentage": 10,  # 10% grace period
    "notification_thresholds": [75, 90, 100]  # Notify at these usage percentages
} 