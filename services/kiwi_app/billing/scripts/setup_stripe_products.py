"""
Setup script for Stripe products and prices.

This script creates/updates Stripe products and prices, and populates
the SubscriptionPlan table in the database.

Usage:
    python -m kiwi_app.billing.setup_stripe_products
"""

import asyncio
import stripe
from typing import Dict, List, Optional, Any
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_async_session
from kiwi_app.settings import settings
from kiwi_app.billing import models, crud, schemas
from kiwi_app.utils import get_kiwi_logger

# Configure logger
logger = get_kiwi_logger(name="kiwi_app.billing.setup_stripe")

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION


# Define subscription plans to create
SUBSCRIPTION_PLANS = [
    {
        "name": "Starter",
        "description": "Perfect for individuals and small teams getting started with KiwiQ",
        "monthly_price": 29.0,  # in dollars
        "annual_price": 290.0,  # in dollars (2 months free)
        "max_seats": 5,
        "monthly_credits": {
            "workflows": 100.0,
            "web_searches": 1000.0,
            "dollar_credits": 10.0
        },
        "features": {
            "api_access": True,
            # "custom_integrations": False,
            "priority_support": False,
            # "advanced_analytics": False,
            # "sla": False
        },
        "is_trial_eligible": True,
        "trial_days": 14
    },
    {
        "name": "Professional",
        "description": "For growing teams that need more power and flexibility",
        "monthly_price": 99.0,
        "annual_price": 990.0,  # 2 months free
        "max_seats": 20,
        "monthly_credits": {
            "workflows": 500.0,
            "web_searches": 5000.0,
            "dollar_credits": 50.0
        },
        "features": {
            "api_access": True,
            # "custom_integrations": True,
            "priority_support": True,
            # "advanced_analytics": True,
            # "sla": False
        },
        "is_trial_eligible": True,
        "trial_days": 14
    },
    {
        "name": "Enterprise",
        "description": "For large organizations with advanced needs and dedicated support",
        "monthly_price": 299.0,
        "annual_price": 2990.0,  # 2 months free
        "max_seats": 100,
        "monthly_credits": {
            "workflows": 2000.0,
            "web_searches": 20000.0,
            "dollar_credits": 200.0
        },
        "features": {
            "api_access": True,
            # "custom_integrations": True,
            "priority_support": True,
            # "advanced_analytics": True,
            # "sla": True,
            "dedicated_account_manager": True,
            # "custom_credit_packages": True
        },
        "is_trial_eligible": True,
        "trial_days": 30
    }
]


class StripeProductManager:
    """Manages Stripe product and price creation/updates."""
    
    def __init__(self):
        """Initialize the manager."""
        self.existing_products = {}
        self.existing_prices = {}
    
    async def setup(self):
        """Load existing Stripe products and prices."""
        logger.info("Loading existing Stripe products...")
        
        # Load all products
        products = stripe.Product.list(limit=100)
        for product in products.auto_paging_iter():
            self.existing_products[product.name] = product
        
        logger.info(f"Found {len(self.existing_products)} existing products")
        
        # Load all prices
        prices = stripe.Price.list(limit=100)
        for price in prices.auto_paging_iter():
            self.existing_prices[price.id] = price
        
        logger.info(f"Found {len(self.existing_prices)} existing prices")
    
    def find_existing_product(self, name: str) -> Optional[stripe.Product]:
        """Find an existing product by name."""
        return self.existing_products.get(name)
    
    def create_or_update_product(self, name: str, description: str, metadata: Dict[str, str]) -> stripe.Product:
        """Create a new product or update existing one."""
        existing_product = self.find_existing_product(name)
        
        if existing_product:
            logger.info(f"Updating existing product: {name}")
            # Update existing product
            product = stripe.Product.modify(
                existing_product.id,
                description=description,
                metadata=metadata
            )
            # Update cache
            self.existing_products[name] = product
            return product
        else:
            logger.info(f"Creating new product: {name}")
            # Create new product
            product = stripe.Product.create(
                name=name,
                description=description,
                metadata=metadata
            )
            # Update cache
            self.existing_products[name] = product
            return product
    
    def create_price(self, product_id: str, unit_amount: int, currency: str, 
                     recurring: Optional[Dict[str, Any]] = None, metadata: Dict[str, str] = None) -> stripe.Price:
        """Create a new price for a product."""
        price_data = {
            "product": product_id,
            "unit_amount": unit_amount,
            "currency": currency,
            "metadata": metadata or {}
        }
        
        if recurring:
            price_data["recurring"] = recurring
        
        return stripe.Price.create(**price_data)
    
    def delete_unused_products(self, keep_product_names: List[str]):
        """Delete products that are not in the keep list."""
        for name, product in list(self.existing_products.items()):
            if name not in keep_product_names and product.metadata.get("kiwiq_managed") == "true":
                try:
                    logger.warning(f"Deleting unused product: {name}")
                    stripe.Product.modify(product.id, active=False)
                    del self.existing_products[name]
                except Exception as e:
                    logger.error(f"Failed to delete product {name}: {e}")


async def setup_subscription_products(db: AsyncSession, manager: StripeProductManager) -> None:
    """Setup subscription products and prices in Stripe and database."""
    logger.info("Setting up subscription products...")
    
    plan_dao = crud.SubscriptionPlanDAO()
    keep_product_names = []
    
    for plan_config in SUBSCRIPTION_PLANS:
        keep_product_names.append(plan_config["name"])
        
        # Create or update Stripe product
        product = manager.create_or_update_product(
            name=plan_config["name"],
            description=plan_config["description"],
            metadata={
                "kiwiq_managed": "true",
                "type": "subscription",
                "max_seats": str(plan_config["max_seats"]),
                "trial_days": str(plan_config["trial_days"])
            }
        )
        
        # Check if plan exists in database
        existing_plan = await plan_dao.get_by_name(db, plan_config["name"])
        
        if existing_plan:
            logger.info(f"Updating existing plan in database: {plan_config['name']}")
            
            # Update the plan
            plan_update = schemas.SubscriptionPlanUpdate(
                description=plan_config["description"],
                max_seats=plan_config["max_seats"],
                monthly_credits=plan_config["monthly_credits"],
                monthly_price=plan_config["monthly_price"],
                annual_price=plan_config["annual_price"],
                features=plan_config["features"],
                is_trial_eligible=plan_config["is_trial_eligible"],
                trial_days=plan_config["trial_days"],
                is_active=True
            )
            
            # Update plan but keep existing Stripe IDs
            updated_plan = await plan_dao.update(db, db_obj=existing_plan, obj_in=plan_update)
            
            # Create new prices if they don't exist or prices changed
            if not existing_plan.stripe_price_id_monthly or existing_plan.monthly_price != plan_config["monthly_price"]:
                logger.info(f"Creating new monthly price for {plan_config['name']}")
                monthly_price = manager.create_price(
                    product_id=product.id,
                    unit_amount=int(plan_config["monthly_price"] * 100),  # Convert to cents
                    currency="usd",
                    recurring={"interval": "month"},
                    metadata={
                        "kiwiq_plan_id": str(existing_plan.id),
                        "billing_period": "monthly"
                    }
                )
                updated_plan.stripe_price_id_monthly = monthly_price.id
            
            if not existing_plan.stripe_price_id_annual or existing_plan.annual_price != plan_config["annual_price"]:
                logger.info(f"Creating new annual price for {plan_config['name']}")
                annual_price = manager.create_price(
                    product_id=product.id,
                    unit_amount=int(plan_config["annual_price"] * 100),  # Convert to cents
                    currency="usd",
                    recurring={"interval": "year"},
                    metadata={
                        "kiwiq_plan_id": str(existing_plan.id),
                        "billing_period": "annual"
                    }
                )
                updated_plan.stripe_price_id_annual = annual_price.id
            
            # Save price updates
            await plan_dao.update(db, db_obj=updated_plan, obj_in=schemas.SubscriptionPlanUpdate())
            
        else:
            logger.info(f"Creating new plan in database: {plan_config['name']}")
            
            # Create monthly price
            monthly_price = manager.create_price(
                product_id=product.id,
                unit_amount=int(plan_config["monthly_price"] * 100),  # Convert to cents
                currency="usd",
                recurring={"interval": "month"},
                metadata={"billing_period": "monthly"}
            )
            
            # Create annual price
            annual_price = manager.create_price(
                product_id=product.id,
                unit_amount=int(plan_config["annual_price"] * 100),  # Convert to cents
                currency="usd",
                recurring={"interval": "year"},
                metadata={"billing_period": "annual"}
            )
            
            # Create plan in database
            plan_create = schemas.SubscriptionPlanCreate(
                name=plan_config["name"],
                description=plan_config["description"],
                stripe_product_id=product.id,
                stripe_price_id_monthly=monthly_price.id,
                stripe_price_id_annual=annual_price.id,
                max_seats=plan_config["max_seats"],
                monthly_credits=plan_config["monthly_credits"],
                monthly_price=plan_config["monthly_price"],
                annual_price=plan_config["annual_price"],
                features=plan_config["features"],
                is_trial_eligible=plan_config["is_trial_eligible"],
                trial_days=plan_config["trial_days"],
                is_active=True
            )
            
            await plan_dao.create(db, obj_in=plan_create)
    
    return keep_product_names


async def main():
    """Main setup function."""
    logger.info("Starting Stripe product setup...")
    
    try:
        # Initialize Stripe manager
        manager = StripeProductManager()
        await manager.setup()
        
        # Get database session
        async with get_async_session() as db:
            # Setup subscription products
            subscription_product_names = await setup_subscription_products(db, manager)
            
            # Combine all product names to keep
            all_product_names = subscription_product_names
            
            # Delete unused products
            manager.delete_unused_products(all_product_names)
            
            # Commit database changes
            await db.commit()
            
        logger.info("Stripe product setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during setup: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main()) 