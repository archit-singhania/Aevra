# Manual UPI tenant onboarding

VAE uses a free, manual verification gate rather than a payment gateway.

## Render configuration

Set these on the API service only. Never commit real values:

```ini
AEVRA_ADMIN_EMAIL=admin@example.com
AEVRA_ADMIN_PASSWORD=<strong-password>
AEVRA_ADMIN_DISPLAY_NAME=VAE Admin
AEVRA_PAYMENT_AMOUNT=<amount>
AEVRA_PAYMENT_CURRENCY=INR
AEVRA_PAYMENT_UPI_ID=<upi-id>
AEVRA_PAYMENT_QR_URL=https://<public-host>/vae-upi-qr.png
AEVRA_PAYMENT_SUPPORT_EMAIL=support@example.com
AEVRA_PAYMENT_EXPIRY_DAYS=7
```

The web app bundles `apps/web/public/payments/vae-upi-qr.png` and uses it automatically when this variable is empty. Set `AEVRA_PAYMENT_QR_URL` only when the API/mobile clients need a public absolute URL or you want to override the bundled asset. The QR should encode the configured UPI ID and amount.

## Migration

Deploy the API image, then run the migration inside the API container or Render shell:

```bash
alembic upgrade head
```

The migration creates account approval fields and `payment_submissions`. Take a PostgreSQL backup before running it.

## Verification

1. Register a normal user on the web app.
2. Confirm the user receives QR/UPI instructions and is not logged in.
3. Submit a UTR, proof image, or both.
4. Sign in as the configured admin.
5. Open **Payment review** and approve the submission.
6. Sign in as the user and confirm the tenant dashboard opens.
7. Repeat with Reject and confirm the user remains blocked and sees the review state.

Approval is deliberately manual. A screenshot or UTR is evidence only; the administrator must verify the payment in the UPI portal.
