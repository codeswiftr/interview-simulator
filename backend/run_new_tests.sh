#!/bin/bash
# Run new test coverage tests for Interview Simulator backend

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running new test coverage tests...${NC}\n"

# Set database URL if not already set
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/interview_simulator}"

echo -e "${GREEN}Database URL: ${DATABASE_URL}${NC}\n"

# List of new test files
TEST_FILES=(
    "tests/test_auth_token_security.py"
    "tests/test_stripe_webhook_security.py"
    "tests/test_interview_session_edge_cases.py"
    "tests/test_password_reset_edge_cases.py"
    "tests/services/test_interview_service_error_paths.py"
)

# Run tests
echo -e "${YELLOW}Running tests...${NC}\n"

uv run pytest "${TEST_FILES[@]}" \
    -v \
    --tb=short \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:htmlcov_new_tests \
    -x  # Stop on first failure for debugging

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}\n"
    echo -e "${GREEN}Coverage report generated in htmlcov_new_tests/index.html${NC}\n"
else
    echo -e "\n${RED}✗ Some tests failed (exit code: $EXIT_CODE)${NC}\n"
fi

exit $EXIT_CODE
