#!/usr/bin/env bash
# Deploy readiness check for Interview Simulator
# Usage: ./scripts/check-deploy.sh

MISSING=0

check_required() {
  local var="$1"
  if [ -z "${!var}" ]; then
    echo "  ✗ $var — missing"
    MISSING=$((MISSING + 1))
  else
    echo "  ✓ $var"
  fi
}

check_optional() {
  local var="$1"
  if [ -z "${!var}" ]; then
    echo "  - $var — not set"
  else
    echo "  - $var — set"
  fi
}

echo "REQUIRED:"
# Core runtime
check_required DATABASE_URL
check_required SECRET_KEY
check_required REDIS_URL
# AI services (both needed: Whisper for transcription, Claude for feedback)
check_required OPENAI_API_KEY
check_required ANTHROPIC_API_KEY
# Email (password reset)
check_required RESEND_API_KEY
check_required FRONTEND_URL

echo ""
echo "OPTIONAL:"
check_optional STRIPE_SECRET_KEY
check_optional STRIPE_WEBHOOK_SECRET
check_optional STRIPE_PRICE_ID_PRO_MONTHLY
check_optional STRIPE_PRICE_ID_PRO_ANNUAL
check_optional POSTHOG_API_KEY
check_optional SENTRY_DSN

echo ""
if [ "$MISSING" -gt 0 ]; then
  echo "RESULT: $MISSING required variable(s) missing. Cannot deploy."
  exit 1
else
  echo "RESULT: All required variables set. Ready to deploy."
fi
