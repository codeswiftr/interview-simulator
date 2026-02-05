#!/bin/bash
# Test script for interview-sim CLI
# Validates JSON output and basic functionality

set -e  # Exit on error

echo "========================================="
echo "Interview Simulator CLI Test Suite"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to test JSON output
test_json_output() {
    local test_name="$1"
    local command="$2"

    echo -n "Testing: $test_name ... "

    # Run command and capture output
    if output=$(eval "$command" 2>&1); then
        # Validate JSON structure
        if echo "$output" | jq -e '.success, .data, .timestamp' > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PASSED${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC} - Invalid JSON structure"
            echo "Output: $output"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC} - Command failed"
        echo "Output: $output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Helper function to test command exists
test_command_exists() {
    local test_name="$1"
    local command="$2"

    echo -n "Testing: $test_name ... "

    if command -v "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} - Command not found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# 1. Check if interview-sim is installed
test_command_exists "CLI installed" "interview-sim"

# 2. Test version command
test_json_output "version --json" "interview-sim version --json"

# 3. Test generate-questions with JSON output
test_json_output "generate-questions --json" \
    "interview-sim generate-questions --topic leadership --count 2 --json"

# 4. Test export-metrics with JSON output
test_json_output "export-metrics --json" \
    "interview-sim export-metrics --period weekly --json"

# 5. Test invalid input handling
echo -n "Testing: Invalid difficulty handling ... "
if output=$(interview-sim generate-questions --topic test --difficulty invalid --json 2>&1); then
    if echo "$output" | jq -e '.success == false and .error_code == "INVALID_INPUT"' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC} - Should return INVALID_INPUT error"
        echo "Output: $output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠ SKIPPED${NC} - Command exited with error (expected)"
fi

# 6. Test invalid category handling
echo -n "Testing: Invalid category handling ... "
if output=$(interview-sim generate-questions --topic test --category invalid --json 2>&1); then
    if echo "$output" | jq -e '.success == false and .error_code == "INVALID_INPUT"' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC} - Should return INVALID_INPUT error"
        echo "Output: $output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠ SKIPPED${NC} - Command exited with error (expected)"
fi

# Summary
echo ""
echo "========================================="
echo "Test Results"
echo "========================================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
