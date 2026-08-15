# Demo

## Quick Start

```bash
python scripts/demo.py
```

## What the Demo Shows

The demo uses a deterministic e-commerce repository (`demo_repo/`) with realistic Git history.

### Repository Structure

```
demo_repo/
  checkout.py     # Discount calculation + checkout flow
  payment.py      # Payment processing + refunds
  order.py        # Order creation + cancellation
  invoice.py      # Invoice generation + tax calculation
  refund.py       # Refund processing + status
  analytics.py    # Event tracking + metrics
  notification.py # Email + SMS notifications
```

### Scenario

The demo modifies `calculate_discount()` to add a `tax_rate` parameter, simulating a common business logic change.

### Output

```
WHAT CHANGED?
  checkout.py: modified (+3 -3)

CHANGED FUNCTIONS:
  - checkout.calculate_discount
  - checkout.checkout

Impact Score: 40/100
Risk Level: MEDIUM

Potentially Affected:
  checkout
  order

WHY:
`checkout.calculate_discount` has 1 direct caller(s): `checkout.checkout`.
1 transitive caller(s) depend on this change: `order.create_order`.
Impact spans 2 module(s), increasing blast radius.

DASHBOARD VISUALIZATION:
                    checkout.calculate_discount
                         /       \
                        v         v
                   checkout.checkout
                         |
                    order.create_order

WHAT COULD BREAK?
  - checkout
  - order

RECOMMENDED TESTS:
  [PASS] checkout_test
  [PASS] order_test
```

## GitHub Webhook Demo

To test GitHub integration locally:

1. Set environment variables:
   ```bash
   export GITHUB_WEBHOOK_SECRET="your-webhook-secret"
   export GITHUB_TOKEN="your-github-token"
   ```

2. Start the backend:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. Create a GitHub App or use a tool like `smee.io` to forward webhooks

4. Open a PR that modifies `checkout.py`

5. CodeGenome will:
   - Receive the webhook
   - Verify the signature
   - Clone the PR branch
   - Run full analysis
   - Post a comment with the impact report

## Security Notes

- Repository code is never executed on the host
- Webhook signatures are verified using HMAC-SHA256
- Secrets are loaded from environment variables only
- Cloned repositories are stored in a temp directory and cleaned up after analysis
