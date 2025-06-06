"""
Setup script for Stripe products and prices.

This script creates/updates Stripe products and prices, and populates
the SubscriptionPlan table in the database.

Usage:
    python -m services.kiwi_app.billing.scripts.setup_stripe_products
    python -m services.kiwi_app.billing.scripts.setup_stripe_products --cleanup
"""

import asyncio
import argparse
import json
import time
import stripe
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_async_db_as_manager
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
            "priority_support": False,
        },
        "marketing_features": [
            "Up to 5 team members",
            "100 workflow runs per month",
            "1,000 web searches per month",
            "$10 in dollar credits",
            "API access included",
            "Community support",
            "Basic integrations",
            "Standard response time",
            "Email notifications",
            "Basic usage analytics",
            "SSL encryption",
            "99.5% uptime SLA",
            "Monthly billing available",
            f"{settings.TRIAL_CREDITS_EXPIRE_DAYS}-day free trial",
            "Cancel anytime"
        ],
        "is_trial_eligible": True,
        "trial_days": settings.TRIAL_CREDITS_EXPIRE_DAYS,
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
            "priority_support": True,
        },
        "marketing_features": [
            "Up to 20 team members",
            "500 workflow runs per month",
            "5,000 web searches per month",
            "$50 in dollar credits",
            "Advanced API access",
            "Priority email support",
            "Custom integrations available",
            "Priority response time (24h)",
            "Email & Slack notifications",
            "Advanced usage analytics",
            "SSL encryption",
            "99.9% uptime SLA",
            "Role-based access control",
            "Team collaboration tools",
            "2 months free with annual plan"
        ],
        "is_trial_eligible": True,
        "trial_days": settings.TRIAL_CREDITS_EXPIRE_DAYS,
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
            "priority_support": True,
            "dedicated_account_manager": True,
        },
        "marketing_features": [
            "Up to 100 team members",
            "2,000 workflow runs per month",
            "20,000 web searches per month",
            "$200 in dollar credits",
            "Enterprise API access",
            "24/7 phone & email support",
            "Unlimited custom integrations",
            "Dedicated account manager",
            "1-hour response time SLA",
            "All notification channels",
            "Advanced analytics & reporting",
            "Enterprise-grade security",
            "99.99% uptime SLA",
            "Single sign-on (SSO)",
            "30-day free trial"
        ],
        "is_trial_eligible": True,
        "trial_days": settings.TRIAL_CREDITS_EXPIRE_DAYS,
    }
]


class StripeProductManager:
    """Manages Stripe product and price creation/updates with proper duplicate handling."""
    
    def __init__(self):
        """Initialize the manager."""
        # Store products by name (list to handle duplicates)
        self.products_by_name: Dict[str, List[stripe.Product]] = defaultdict(list)
        # Store all products by ID for quick lookup
        self.products_by_id: Dict[str, stripe.Product] = {}
        # Store all prices by ID
        self.prices_by_id: Dict[str, stripe.Price] = {}
    
    async def setup(self):
        """Load existing Stripe products and prices."""
        logger.info("Loading existing Stripe products...")
        
        # Clear existing data
        self.products_by_name.clear()
        self.products_by_id.clear()
        self.prices_by_id.clear()
        
        # Load all products
        products = stripe.Product.list(limit=100)
        active_count = 0
        inactive_count = 0
        duplicate_count = 0
        
        for product in products.auto_paging_iter():
            self.products_by_name[product.name].append(product)
            self.products_by_id[product.id] = product
            
            if product.active:
                active_count += 1
            else:
                inactive_count += 1
        
        # Log duplicate products
        for name, products_list in self.products_by_name.items():
            if len(products_list) > 1:
                duplicate_count += len(products_list) - 1
                logger.warning(f"Found {len(products_list)} products with name '{name}':")
                for prod in products_list:
                    logger.warning(f"  - ID: {prod.id}, Active: {prod.active}, Created: {prod.created}")
        
        logger.info(
            f"Found {len(self.products_by_id)} total products "
            f"({active_count} active, {inactive_count} inactive, {duplicate_count} duplicates)"
        )
        
        # Load all prices
        prices = stripe.Price.list(limit=100)
        for price in prices.auto_paging_iter():
            self.prices_by_id[price.id] = price
        
        logger.info(f"Found {len(self.prices_by_id)} existing prices")
    
    def find_best_existing_product(self, name: str) -> Optional[stripe.Product]:
        """
        Find the best existing product by name.
        
        Prioritizes:
        1. Active KiwiQ-managed products
        2. Active non-KiwiQ products
        3. Most recently created active product
        
        Returns None if no suitable product found.
        """
        products = self.products_by_name.get(name, [])
        if not products:
            return None
        
        # Filter active products
        active_products = [p for p in products if p.active]
        if not active_products:
            logger.info(f"No active products found for name: {name}")
            return None
        
        # Sort by: KiwiQ-managed first, then by creation date (newest first)
        active_products.sort(
            key=lambda p: (
                p.metadata.get("kiwiq_managed") == "true",
                p.created
            ),
            reverse=True
        )
        
        best_product = active_products[0]
        
        # Log if we have duplicates
        if len(active_products) > 1:
            logger.warning(
                f"Found {len(active_products)} active products for '{name}'. "
                f"Using product ID: {best_product.id}"
            )
            for i, prod in enumerate(active_products[1:], 1):
                logger.warning(
                    f"  Duplicate #{i}: ID: {prod.id}, "
                    f"KiwiQ: {prod.metadata.get('kiwiq_managed', 'false')}, "
                    f"Created: {prod.created}"
                )
        
        return best_product
    
    def cleanup_duplicate_products(self, name: str, keep_product_id: str):
        """Deactivate duplicate products with the same name."""
        products = self.products_by_name.get(name, [])
        deactivated_count = 0
        
        for product in products:
            if product.id != keep_product_id and product.active:
                try:
                    logger.warning(
                        f"Deactivating duplicate product '{name}' "
                        f"(ID: {product.id}, keeping: {keep_product_id})"
                    )
                    stripe.Product.modify(product.id, active=False)
                    # Update our cache
                    product.active = False
                    self.products_by_id[product.id] = product
                    deactivated_count += 1
                except Exception as e:
                    logger.error(f"Failed to deactivate duplicate product {product.id}: {e}")
        
        if deactivated_count > 0:
            logger.info(f"Deactivated {deactivated_count} duplicate products for '{name}'")
    
    def find_existing_price(self, product_id: str, unit_amount: int, interval: str) -> Optional[stripe.Price]:
        """Find an existing active price for a product with specific amount and interval."""
        try:
            prices = stripe.Price.list(product=product_id, active=True, limit=100)
            for price in prices.auto_paging_iter():
                if (price.unit_amount == unit_amount and 
                    price.recurring and 
                    price.recurring.interval == interval):
                    return price
        except Exception as e:
            logger.error(f"Error finding existing price: {e}")
        return None
    
    def create_or_update_product(
        self, 
        name: str, 
        description: str, 
        metadata: Dict[str, str], 
        features: Dict[str, Any], 
        marketing_features: List[str], 
        unit_label: str = "seat(s)"
    ) -> stripe.Product:
        """Create a new product or update existing one, handling duplicates properly."""
        
        # Find the best existing product
        existing_product = self.find_best_existing_product(name)
        
        # Convert features to JSON string for metadata
        metadata["features"] = json.dumps(features)
        
        # Convert marketing features to Stripe format (limit 15)
        stripe_marketing_features = [{"name": feature} for feature in marketing_features[:15]]
        
        if existing_product:
            # Clean up any duplicates first
            self.cleanup_duplicate_products(name, existing_product.id)
            
            # Check if update is needed
            needs_update = self._check_product_needs_update(
                existing_product, 
                description, 
                metadata, 
                features, 
                stripe_marketing_features, 
                unit_label
            )
            
            if needs_update:
                logger.info(f"Updating existing product: {name} (ID: {existing_product.id})")
                product = stripe.Product.modify(
                    existing_product.id,
                    description=description,
                    metadata=metadata,
                    marketing_features=stripe_marketing_features,
                    unit_label=unit_label
                )
                # Update cache
                self.products_by_id[product.id] = product
                # Update in the list
                for i, p in enumerate(self.products_by_name[name]):
                    if p.id == product.id:
                        self.products_by_name[name][i] = product
                        break
                return product
            else:
                logger.info(f"Product {name} is up to date, no changes needed")
                return existing_product
        else:
            # Log if there are inactive products with this name
            inactive_products = [p for p in self.products_by_name.get(name, []) if not p.active]
            if inactive_products:
                logger.info(
                    f"Creating new product '{name}' "
                    f"({len(inactive_products)} inactive products exist with this name)"
                )
            
            logger.info(f"Creating new product: {name}")
            product = stripe.Product.create(
                name=name,
                description=description,
                metadata=metadata,
                marketing_features=stripe_marketing_features,
                unit_label=unit_label
            )
            # Update cache
            self.products_by_name[name].append(product)
            self.products_by_id[product.id] = product
            
            # Clean up any duplicates that might have been created concurrently
            self.cleanup_duplicate_products(name, product.id)
            
            return product
    
    def _check_product_needs_update(
        self,
        existing_product: stripe.Product,
        description: str,
        metadata: Dict[str, str],
        features: Dict[str, Any],
        stripe_marketing_features: List[Dict[str, str]],
        unit_label: str
    ) -> bool:
        """Check if a product needs to be updated."""
        needs_update = False
        
        # Check description
        if existing_product.description != description:
            needs_update = True
            logger.info(f"Product {existing_product.name}: description changed")
        
        # Check unit_label
        if existing_product.get("unit_label") != unit_label:
            needs_update = True
            logger.info(f"Product {existing_product.name}: unit_label changed")
        
        # Check features
        existing_features_json = existing_product.metadata.get("features", "{}")
        try:
            existing_features = json.loads(existing_features_json)
        except json.JSONDecodeError:
            existing_features = {}
        
        if existing_features != features:
            needs_update = True
            logger.info(f"Product {existing_product.name}: features changed")
        
        # Check marketing_features
        existing_marketing = existing_product.get("marketing_features", [])
        existing_names = [f.get("name", "") for f in existing_marketing]
        new_names = [f["name"] for f in stripe_marketing_features]
        
        if existing_names != new_names:
            needs_update = True
            logger.info(f"Product {existing_product.name}: marketing_features changed")
        
        # Check metadata
        for key, value in metadata.items():
            if existing_product.metadata.get(key) != value:
                needs_update = True
                logger.info(f"Product {existing_product.name}: metadata[{key}] changed")
        
        return needs_update
    
    def create_or_find_price(
        self,
        product_id: str,
        unit_amount: int,
        currency: str,
        interval: str,
        plan_id: Optional[str] = None
    ) -> Tuple[stripe.Price, bool]:
        """
        Create a new price or find an existing one.
        
        Returns:
            Tuple of (price, is_new) where is_new indicates if a new price was created
        """
        # Check for existing price
        existing_price = self.find_existing_price(product_id, unit_amount, interval)
        
        if existing_price:
            logger.info(
                f"Found existing {interval} price {existing_price.id} "
                f"(${unit_amount/100})"
            )
            return existing_price, False
        
        # Create new price
        metadata = {"billing_period": interval}
        if plan_id:
            metadata["kiwiq_plan_id"] = str(plan_id)
        
        new_price = stripe.Price.create(
            product=product_id,
            unit_amount=unit_amount,
            currency=currency,
            recurring={"interval": interval},
            metadata=metadata
        )
        
        logger.info(
            f"Created new {interval} price {new_price.id} "
            f"(${unit_amount/100})"
        )
        
        # Update cache
        self.prices_by_id[new_price.id] = new_price
        
        return new_price, True
    
    def deactivate_old_prices(self, product_id: str, keep_price_ids: List[str]):
        """Deactivate prices for a product that are not in the keep list."""
        try:
            prices = stripe.Price.list(product=product_id, active=True, limit=100)
            for price in prices.auto_paging_iter():
                if price.id not in keep_price_ids:
                    try:
                        stripe.Price.modify(price.id, active=False)
                        logger.info(f"Deactivated old price {price.id} (${price.unit_amount/100})")
                    except Exception as e:
                        logger.error(f"Failed to deactivate price {price.id}: {e}")
        except Exception as e:
            logger.error(f"Error deactivating old prices: {e}")
    
    def cleanup_unused_products(self, keep_product_names: List[str]):
        """Deactivate KiwiQ-managed products that are not in the keep list."""
        deactivated_count = 0
        
        for name, products in self.products_by_name.items():
            if name not in keep_product_names:
                for product in products:
                    if product.active and product.metadata.get("kiwiq_managed") == "true":
                        try:
                            logger.warning(
                                f"Deactivating unused KiwiQ product: {name} (ID: {product.id})"
                            )
                            stripe.Product.modify(product.id, active=False)
                            product.active = False
                            self.products_by_id[product.id] = product
                            deactivated_count += 1
                        except Exception as e:
                            logger.error(f"Failed to deactivate product {product.id}: {e}")
        
        if deactivated_count > 0:
            logger.info(f"Deactivated {deactivated_count} unused KiwiQ products")
    
    def cleanup_all_kiwiq_products(self):
        """Deactivate all KiwiQ-managed products and their prices."""
        logger.warning("=== CLEANUP MODE: Deactivating all KiwiQ-managed products ===")
        
        deactivated_products = 0
        deactivated_prices = 0
        
        for products in self.products_by_name.values():
            for product in products:
                if product.metadata.get("kiwiq_managed") == "true":
                    logger.info(
                        f"Processing product: {product.name} "
                        f"(ID: {product.id}, active: {product.active})"
                    )
                    
                    if product.active:
                        # Deactivate all prices first
                        try:
                            prices = stripe.Price.list(product=product.id, active=True, limit=100)
                            for price in prices.auto_paging_iter():
                                try:
                                    stripe.Price.modify(price.id, active=False)
                                    deactivated_prices += 1
                                    logger.info(f"Deactivated price {price.id}")
                                except Exception as e:
                                    logger.error(f"Failed to deactivate price {price.id}: {e}")
                        except Exception as e:
                            logger.error(f"Error listing prices for product {product.id}: {e}")
                        
                        # Deactivate the product
                        try:
                            stripe.Product.modify(product.id, active=False)
                            product.active = False
                            self.products_by_id[product.id] = product
                            deactivated_products += 1
                            logger.info(f"Deactivated product: {product.name} (ID: {product.id})")
                        except Exception as e:
                            logger.error(f"Failed to deactivate product {product.id}: {e}")
        
        logger.warning(
            f"=== CLEANUP COMPLETE: Deactivated {deactivated_products} products "
            f"and {deactivated_prices} prices ==="
        )
        
        return deactivated_products, deactivated_prices
    
    def create_or_update_portal_configuration(
        self, 
        product_configs: List[Dict[str, Any]]
    ) -> Optional[stripe.billing_portal.Configuration]:
        """Create or update the customer portal configuration."""
        logger.info("Setting up customer portal configuration...")
        
        try:
            # Build the products list for subscription updates
            portal_products = []
            for config in product_configs:
                if config.get("product_id") and config.get("price_ids"):
                    portal_products.append({
                        "product": config["product_id"],
                        "prices": config["price_ids"]
                    })
            
            if not portal_products:
                logger.warning("No products found for portal configuration")
                return None
            
            # Check for existing KiwiQ-managed portal configurations
            existing_configs = stripe.billing_portal.Configuration.list(limit=100)
            kiwiq_config = None
            
            for config in existing_configs.auto_paging_iter():
                if config.metadata.get("kiwiq_managed") == "true":
                    kiwiq_config = config
                    logger.info(f"Found existing KiwiQ portal configuration: {config.id}")
                    break
            
            # Portal configuration settings
            portal_features = {
                "customer_update": {
                    "allowed_updates": ["email", "tax_id"],
                    "enabled": True
                },
                "invoice_history": {
                    "enabled": True
                },
                "payment_method_update": {
                    "enabled": True
                },
                "subscription_cancel": {
                    "enabled": True,
                    "mode": "at_period_end",
                    "proration_behavior": "none",
                    "cancellation_reason": {
                        "enabled": True,
                        "options": [
                            "too_expensive",
                            "missing_features", 
                            "switched_service",
                            "unused",
                            "customer_service",
                            "too_complex",
                            "other"
                        ]
                    }
                },
                "subscription_update": {
                    "enabled": True,
                    "default_allowed_updates": ["price", "quantity", "promotion_code"],
                    "products": portal_products,
                    "proration_behavior": "always_invoice",
                    "schedule_at_period_end": {
                        "conditions": [
                            {"type": "decreasing_item_amount"},
                            {"type": "shortening_interval"}
                        ]
                    }
                }
            }
            
            # Business profile settings
            business_profile = {
                "headline": "Manage Your KiwiQ Subscription",
                "privacy_policy_url": getattr(settings, 'PRIVACY_POLICY_URL', None),
                "terms_of_service_url": getattr(settings, 'TERMS_OF_SERVICE_URL', None)
            }
            
            # Metadata
            metadata = {
                "kiwiq_managed": "true",
                "updated_at": str(int(time.time()))
            }
            
            config_params = {
                "active": True,
                "features": portal_features,
                "business_profile": business_profile,
                "metadata": metadata,
                "default_return_url": getattr(settings, 'FRONTEND_URL', None)
            }
            
            if kiwiq_config:
                # Update existing configuration
                logger.info("Updating existing portal configuration...")
                try:
                    updated_config = stripe.billing_portal.Configuration.modify(
                        kiwiq_config.id,
                        **config_params
                    )
                    logger.info(f"Successfully updated portal configuration: {updated_config.id}")
                    return updated_config
                except Exception as e:
                    logger.error(f"Failed to update portal configuration: {e}")
                    logger.info("Attempting to create new portal configuration...")
            
            # Create new configuration
            logger.info("Creating new portal configuration...")
            new_config = stripe.billing_portal.Configuration.create(**config_params)
            logger.info(f"Successfully created portal configuration: {new_config.id}")
            
            return new_config
            
        except Exception as e:
            logger.error(f"Failed to create/update portal configuration: {e}", exc_info=True)
            return None


async def setup_subscription_plan(
    db: AsyncSession,
    manager: StripeProductManager,
    plan_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Setup a single subscription plan in Stripe and database.
    
    Returns:
        Dictionary with product_id and price_ids for portal configuration
    """
    plan_dao = crud.SubscriptionPlanDAO()
    
    # Create or update Stripe product
    product = manager.create_or_update_product(
        name=plan_config["name"],
        description=plan_config["description"],
        metadata={
            "kiwiq_managed": "true",
            "type": "subscription",
            "max_seats": str(plan_config["max_seats"]),
            "trial_days": str(plan_config["trial_days"])
        },
        features=plan_config["features"],
        marketing_features=plan_config["marketing_features"],
        unit_label="seat(s)"
    )
    
    # Check if plan exists in database
    existing_plan = await plan_dao.get_by_name(db, plan_config["name"])
    
    # Calculate amounts in cents
    monthly_amount_cents = int(plan_config["monthly_price"] * 100)
    annual_amount_cents = int(plan_config["annual_price"] * 100)
    
    # Track price IDs to keep active
    keep_price_ids = []
    
    if existing_plan:
        logger.info(f"Updating existing plan in database: {plan_config['name']}")
        
        # Update the plan configuration
        plan_update = schemas.SubscriptionPlanUpdate(
            description=plan_config["description"],
            stripe_product_id=product.id,
            max_seats=plan_config["max_seats"],
            monthly_credits=plan_config["monthly_credits"],
            monthly_price=plan_config["monthly_price"],
            annual_price=plan_config["annual_price"],
            features=plan_config["features"],
            is_trial_eligible=plan_config["is_trial_eligible"],
            trial_days=plan_config["trial_days"],
            is_active=True
        )
        
        # Update plan
        updated_plan = await plan_dao.update(db, db_obj=existing_plan, obj_in=plan_update)
        
        # Create or find prices
        monthly_price, monthly_is_new = manager.create_or_find_price(
            product_id=product.id,
            unit_amount=monthly_amount_cents,
            currency="usd",
            interval="month",
            plan_id=updated_plan.id
        )
        keep_price_ids.append(monthly_price.id)
        
        annual_price, annual_is_new = manager.create_or_find_price(
            product_id=product.id,
            unit_amount=annual_amount_cents,
            currency="usd",
            interval="year",
            plan_id=updated_plan.id
        )
        keep_price_ids.append(annual_price.id)
        
        # Update plan with price IDs if they changed
        price_update_needed = False
        price_update = schemas.SubscriptionPlanUpdate()
        
        if updated_plan.stripe_price_id_monthly != monthly_price.id:
            price_update.stripe_price_id_monthly = monthly_price.id
            price_update_needed = True
        
        if updated_plan.stripe_price_id_annual != annual_price.id:
            price_update.stripe_price_id_annual = annual_price.id
            price_update_needed = True
        
        if price_update_needed:
            updated_plan = await plan_dao.update(db, db_obj=updated_plan, obj_in=price_update)
            logger.info(f"Updated plan {plan_config['name']} with new price IDs")
        
        final_plan = updated_plan
        
    else:
        logger.info(f"Creating new plan in database: {plan_config['name']}")
        
        # Create prices first (without plan_id)
        monthly_price, _ = manager.create_or_find_price(
            product_id=product.id,
            unit_amount=monthly_amount_cents,
            currency="usd",
            interval="month"
        )
        keep_price_ids.append(monthly_price.id)
        
        annual_price, _ = manager.create_or_find_price(
            product_id=product.id,
            unit_amount=annual_amount_cents,
            currency="usd",
            interval="year"
        )
        keep_price_ids.append(annual_price.id)
        
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
        
        new_plan = await plan_dao.create(db, obj_in=plan_create)
        logger.info(f"Created new plan {plan_config['name']} with ID {new_plan.id}")
        
        # Update price metadata with plan ID
        try:
            stripe.Price.modify(
                monthly_price.id,
                metadata={
                    "kiwiq_plan_id": str(new_plan.id),
                    "billing_period": "month"
                }
            )
            stripe.Price.modify(
                annual_price.id,
                metadata={
                    "kiwiq_plan_id": str(new_plan.id),
                    "billing_period": "year"
                }
            )
            logger.info(f"Updated price metadata with plan ID {new_plan.id}")
        except Exception as e:
            logger.warning(f"Failed to update price metadata: {e}")
        
        final_plan = new_plan
    
    # Deactivate old prices
    manager.deactivate_old_prices(product.id, keep_price_ids)
    
    # Return configuration for portal
    return {
        "product_id": product.id,
        "price_ids": keep_price_ids,
        "name": plan_config["name"]
    }


async def verify_plans(db: AsyncSession) -> None:
    """Verify that all plans have proper Stripe IDs set."""
    logger.info("\n=== Verifying Subscription Plans ===")
    
    plan_dao = crud.SubscriptionPlanDAO()
    
    # Ensure fresh data
    await db.commit()
    
    all_plans = await plan_dao.get_multi(db)
    
    for plan in all_plans:
        logger.info(f"\nPlan: {plan.name}")
        logger.info(f"  ID: {plan.id}")
        logger.info(f"  Stripe Product ID: {plan.stripe_product_id}")
        logger.info(f"  Monthly Price ID: {plan.stripe_price_id_monthly}")
        logger.info(f"  Annual Price ID: {plan.stripe_price_id_annual}")
        logger.info(f"  Monthly Price: ${plan.monthly_price}")
        logger.info(f"  Annual Price: ${plan.annual_price}")
        logger.info(f"  Active: {plan.is_active}")
        
        # Verify Stripe prices exist
        if plan.stripe_price_id_monthly:
            try:
                monthly_price = stripe.Price.retrieve(plan.stripe_price_id_monthly)
                logger.info(f"  ✓ Monthly price verified: ${monthly_price.unit_amount/100}")
            except Exception as e:
                logger.error(f"  ✗ Monthly price NOT found: {e}")
        else:
            logger.warning(f"  ⚠ No monthly price ID set")
        
        if plan.stripe_price_id_annual:
            try:
                annual_price = stripe.Price.retrieve(plan.stripe_price_id_annual)
                logger.info(f"  ✓ Annual price verified: ${annual_price.unit_amount/100}")
            except Exception as e:
                logger.error(f"  ✗ Annual price NOT found: {e}")
        else:
            logger.warning(f"  ⚠ No annual price ID set")
    
    logger.info("\n=== Verification Complete ===\n")


async def cleanup_database_plans(db: AsyncSession) -> int:
    """Delete all subscription plans from the database."""
    logger.warning("=== Deleting all subscription plans from database ===")
    
    plan_dao = crud.SubscriptionPlanDAO()
    all_plans = await plan_dao.get_multi(db)
    
    deleted_count = 0
    for plan in all_plans:
        try:
            await plan_dao.remove(db, id=plan.id)
            deleted_count += 1
            logger.info(f"Deleted plan: {plan.name} (ID: {plan.id})")
        except Exception as e:
            logger.error(f"Failed to delete plan {plan.name}: {e}")
    
    logger.warning(f"=== Deleted {deleted_count} plans from database ===")
    return deleted_count


async def main(cleanup_mode: bool = False):
    """Main setup function."""
    logger.info("Starting Stripe product setup...")
    logger.info(f"Cleanup mode: {'ENABLED' if cleanup_mode else 'DISABLED'}")
    
    try:
        # Initialize Stripe manager
        manager = StripeProductManager()
        await manager.setup()
        
        # Handle cleanup if requested
        if cleanup_mode:
            logger.warning("!!! CLEANUP MODE ENABLED !!!")
            logger.warning("This will deactivate all KiwiQ products and delete database plans!")
            
            # Cleanup Stripe products and prices
            deactivated_products, deactivated_prices = manager.cleanup_all_kiwiq_products()
            
            # Cleanup database plans
            async with get_async_db_as_manager() as db:
                deleted_plans = await cleanup_database_plans(db)
            
            logger.warning(
                f"Cleanup complete: {deactivated_products} products, "
                f"{deactivated_prices} prices deactivated, "
                f"{deleted_plans} database plans deleted"
            )
            
            # Refresh the manager's cache after cleanup
            await manager.setup()
        
        # Setup subscription products
        async with get_async_db_as_manager() as db:
            keep_product_names = []
            product_configs = []
            
            # Process each plan
            for plan_config in SUBSCRIPTION_PLANS:
                keep_product_names.append(plan_config["name"])
                config = await setup_subscription_plan(db, manager, plan_config)
                product_configs.append(config)
            
            # Cleanup unused products (only if not in cleanup mode)
            if not cleanup_mode:
                manager.cleanup_unused_products(keep_product_names)
            
            # Setup customer portal configuration
            portal_config = manager.create_or_update_portal_configuration(product_configs)
            if portal_config:
                logger.info(f"Customer portal configuration ready: {portal_config.id}")
            else:
                logger.warning("Failed to create/update customer portal configuration")
            
            # Verify plans are properly set up
            await verify_plans(db)
        
        logger.info("✅ Stripe product setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during setup: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Stripe products and prices")
    parser.add_argument(
        "--cleanup", 
        action="store_true", 
        help="Enable cleanup mode - deactivates all KiwiQ products before setup"
    )
    args = parser.parse_args()
    
    asyncio.run(main(cleanup_mode=args.cleanup)) 
