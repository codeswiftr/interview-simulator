#!/bin/bash
# =============================================================================
# Docker Configuration Validation Script
# Validates environment setup before deployment
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env.staging"

echo "============================================================================="
echo "Interview Simulator - Docker Configuration Validation"
echo "============================================================================="
echo ""

# Check if .env.staging exists
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env.staging not found!"
    echo "  → Copy .env.staging.example to .env.staging and fill in values"
    echo "  → Run: cp .env.staging.example .env.staging"
    exit 1
fi

echo "[OK] .env.staging file found"

# Source environment file
set -a
source "$ENV_FILE"
set +a

# Validation functions
validate_required() {
    local var_name=$1
    local var_value=${!var_name}

    if [ -z "$var_value" ]; then
        echo "  [FAIL] $var_name is not set"
        return 1
    elif [ "$var_value" = "CHANGE_ME"* ]; then
        echo "  [FAIL] $var_name still contains CHANGE_ME placeholder"
        return 1
    else
        echo "  [OK] $var_name is set"
        return 0
    fi
}

validate_min_length() {
    local var_name=$1
    local min_length=$2
    local var_value=${!var_name}

    if [ ${#var_value} -lt $min_length ]; then
        echo "  [FAIL] $var_name is too short (minimum $min_length characters)"
        return 1
    else
        echo "  [OK] $var_name length is sufficient (${#var_value} chars)"
        return 0
    fi
}

validate_email() {
    local var_name=$1
    local var_value=${!var_name}

    if [[ ! "$var_value" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        echo "  [FAIL] $var_name is not a valid email address"
        return 1
    elif [[ "$var_value" == *"resend.dev"* ]]; then
        echo "  [WARN] $var_name uses resend.dev sandbox (limited to your email only)"
        return 0
    else
        echo "  [OK] $var_name is a valid email"
        return 0
    fi
}

# Track validation errors
ERRORS=0

echo ""
echo "Validating critical environment variables..."
echo "---------------------------------------------"

# Database
echo ""
echo "Database Configuration:"
validate_required "POSTGRES_PASSWORD" || ((ERRORS++))
validate_min_length "POSTGRES_PASSWORD" 16 || ((ERRORS++))

# Redis
echo ""
echo "Redis Configuration:"
validate_required "REDIS_PASSWORD" || ((ERRORS++))
validate_min_length "REDIS_PASSWORD" 16 || ((ERRORS++))

# Security
echo ""
echo "Security Configuration:"
validate_required "SECRET_KEY" || ((ERRORS++))
validate_min_length "SECRET_KEY" 32 || ((ERRORS++))

# AI Services
echo ""
echo "AI Services Configuration:"
if [ "$TRANSCRIPTION_PROVIDER" = "groq" ]; then
    validate_required "GROQ_API_KEY" || echo "  [WARN] GROQ_API_KEY not set - transcription will fail"
else
    validate_required "OPENAI_API_KEY" || echo "  [WARN] OPENAI_API_KEY not set - transcription will fail"
fi

if [ "$CONTENT_ANALYSIS_PROVIDER" = "openrouter" ]; then
    validate_required "OPENROUTER_API_KEY" || echo "  [WARN] OPENROUTER_API_KEY not set - feedback will fail"
else
    validate_required "ANTHROPIC_API_KEY" || echo "  [WARN] ANTHROPIC_API_KEY not set - feedback will fail"
fi

# Email
echo ""
echo "Email Configuration:"
validate_required "RESEND_API_KEY" || echo "  [WARN] RESEND_API_KEY not set - password reset emails will fail"
validate_email "RESEND_FROM_EMAIL" || echo "  [WARN] Email validation failed"

# Frontend URL
echo ""
echo "Frontend Configuration:"
validate_required "FRONTEND_URL" || ((ERRORS++))

echo ""
echo "---------------------------------------------"

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "VALIDATION FAILED: Found $ERRORS critical error(s)"
    echo "  → Fix the errors above before deploying"
    exit 1
else
    echo ""
    echo "VALIDATION PASSED: Configuration looks good!"
    echo ""
    echo "Next steps:"
    echo "  1. Review the configuration above"
    echo "  2. Build images: docker compose -f docker-compose.staging.yml build"
    echo "  3. Start services: docker compose -f docker-compose.staging.yml up -d"
    echo "  4. Check health: docker compose -f docker-compose.staging.yml ps"
    echo ""
fi
