# KiwiQ Billing Module

This module provides comprehensive billing functionality for the KiwiQ platform, including subscription management, credit tracking, and integration with Stripe for payment processing.

## Features

- **Subscription Management**: Support for multiple subscription tiers with different features and credit allocations
- **Credit System**: Track and manage credits for workflows, web searches, and API usage
- **One-time Purchases**: Allow users to purchase additional credits as needed
- **Stripe Integration**: Full integration with Stripe for payment processing, subscriptions, and customer management
- **Usage Tracking**: Detailed tracking of credit consumption with audit trails
- **Promotion Codes**: Support for promotional codes to grant free credits
- **Customer Portal**: Integration with Stripe Customer Portal for self-service subscription management

## Setup

### Prerequisites

1. **Stripe Account**: You need a Stripe account with API keys
2. **Environment Variables**: Set the following in your `.env` file:
   ```env
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_API_VERSION=2023-10-16
   STRIPE_SUCCESS_URL=https://yourapp.com/billing/success
   STRIPE_CANCEL_URL=https://yourapp.com/billing/cancel
   
   # Credit pricing (in dollars)
   CREDIT_PRICE_WORKFLOWS_DOLLARS=0.25
   CREDIT_PRICE_WEB_SEARCHES_DOLLARS=0.01
   CREDIT_PRICE_DOLLAR_CREDITS_RATIO=1.2
   
   # Credit expiration settings
   TRIAL_CREDITS_EXPIRE_DAYS=7
   SUBSCRIPTION_CREDITS_EXPIRE_DAYS=30
   PURCHASED_CREDITS_EXPIRE_DAYS=90
   ```

### Initial Setup

1. **Run Database Migrations**: Ensure all billing tables are created
   ```bash
   alembic upgrade head
   ```

2. **Setup Stripe Products**: Run the setup script to create products and prices in Stripe
   ```bash
   python -m kiwi_app.billing.setup_stripe_products
   ```
   
   This script will:
   - Create or update subscription products in Stripe
   - Create one-time purchase products for credits
   - Populate the SubscriptionPlan table in the database
   - Delete any unused products (marked with `kiwiq_managed=true`)

3. **Configure Stripe Webhooks**: In your Stripe dashboard, set up a webhook endpoint pointing to:
   ```
   https://yourapp.com/billing/webhooks/stripe
   ```
   
   Enable the following events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`

4. **Configure Customer Portal**: In Stripe Dashboard → Settings → Billing → Customer portal:
   - Enable the portal
   - Allow customers to update payment methods
   - Configure cancellation and plan change options

## API Endpoints

### Subscription Management

- `GET /billing/plans` - List available subscription plans
- `POST /billing/subscribe` - Create a subscription (deprecated, use checkout)
- `GET /billing/subscription` - Get current subscription
- `PUT /billing/subscription` - Update subscription (seats, plan, cancellation)
- `POST /billing/checkout/subscription` - Create Stripe Checkout session for subscription
- `POST /billing/portal` - Create Customer Portal session

### Credit Management

- `GET /billing/credits` - Get current credit balances
- `POST /billing/consume-credits` - Consume credits for operations
- `POST /billing/allocate-credits` - Pre-allocate credits for long operations
- `POST /billing/adjust-credits` - Adjust allocated credits with actual usage
- `POST /billing/purchase-credits` - Purchase additional credits
- `POST /billing/checkout/credits` - Create Stripe Checkout session for credit purchase

### Promotion Codes

- `POST /billing/promo-codes/apply` - Apply a promotion code

### Analytics

- `GET /billing/usage` - Get usage summary for date range
- `GET /billing/dashboard` - Get comprehensive billing dashboard

### Admin Endpoints

- `POST /billing/admin/plans` - Create new subscription plan
- `GET /billing/admin/plans` - List all plans (including inactive)

## Usage Examples

### Creating a Subscription Checkout Session

```python
# Frontend makes request to create checkout session
response = await client.post("/billing/checkout/subscription", json={
    "plan_id": "plan-uuid-here",
    "is_annual": False,
    "success_url": "https://app.com/billing/success",
    "cancel_url": "https://app.com/billing/cancel"
})

# Redirect user to Stripe Checkout
checkout_url = response.json()["checkout_url"]
```

### Consuming Credits

```python
# Consume credits for a workflow execution
response = await client.post("/billing/consume-credits", json={
    "credit_type": "workflows",
    "credits_consumed": 5.0,
    "event_type": "workflow_execution",
    "metadata": {
        "workflow_id": "wf_123",
        "execution_time": 45.3
    }
})
```

### Allocating Credits for Long Operations

```python
# Allocate credits before starting operation
allocation = await client.post("/billing/allocate-credits", json={
    "credit_type": "workflows",
    "estimated_credits": 10.0,
    "operation_id": "op_123",
    "metadata": {"workflow_id": "wf_123"}
})

# After operation completes, adjust with actual usage
adjustment = await client.post("/billing/adjust-credits", json={
    "operation_id": "op_123",
    "actual_credits": 7.5,
    "allocated_credits": 10.0
})
```

## Credit Types

The system supports three types of credits:

1. **Workflow Credits** (`workflows`): Used for workflow executions
2. **Web Search Credits** (`web_searches`): Used for web search operations
3. **Dollar Credits** (`dollar_credits`): Generic credits for API usage

## Subscription Plans

Default plans created by the setup script:

1. **Starter** - $29/month ($290/year)
   - 5 seats max
   - 100 workflow credits/month
   - 1,000 web search credits/month
   - $10 dollar credits/month
   - 14-day trial

2. **Professional** - $99/month ($990/year)
   - 20 seats max
   - 500 workflow credits/month
   - 5,000 web search credits/month
   - $50 dollar credits/month
   - 14-day trial
   - Priority support
   - Custom integrations

3. **Enterprise** - $299/month ($2,990/year)
   - 100 seats max
   - 2,000 workflow credits/month
   - 20,000 web search credits/month
   - $200 dollar credits/month
   - 30-day trial
   - SLA
   - Dedicated account manager

## Credit Purchase Options

One-time credit purchases available:

- **Workflow Credits**: Small (100), Medium (500), Large (2000) packs
- **Web Search Credits**: Small (1000), Large (10000) packs
- **Dollar Credits**: Small ($25), Large ($100) packs

## Webhook Processing

The system processes Stripe webhooks to maintain synchronization:

- Subscription creation/updates/cancellations
- Payment successes/failures
- Credit allocations after successful payments

## Error Handling

The module includes comprehensive error handling with specific exceptions:

- `InsufficientCreditsException`: Not enough credits available
- `SubscriptionNotFoundException`: No active subscription
- `StripeIntegrationException`: Stripe API errors
- `PromotionCodeException`: Various promotion code errors

## Development

### Running Tests

```bash
pytest services/kiwi_app/billing/tests/
```

### Updating Products/Prices

1. Modify the `SUBSCRIPTION_PLANS` or `CREDIT_PURCHASE_OPTIONS` in `setup_stripe_products.py`
2. Run the setup script again - it will update existing products and create new ones

### Adding New Credit Types

1. Add to `CreditType` enum in `models.py`
2. Update credit allocation logic in subscription plans
3. Add pricing configuration in settings
4. Run database migrations if needed

## Monitoring

Monitor billing operations through:

- Application logs (look for `kiwi_app.billing` logger)
- Stripe Dashboard for payment/subscription status
- Database queries on usage_event table for consumption analytics
- Credit balance monitoring for overage detection

## Security Considerations

- All Stripe webhooks are verified using signatures
- Credit consumption uses atomic database operations to prevent race conditions
- Overage limits prevent unlimited usage
- All billing operations require organization context
- Subscription management requires billing permissions