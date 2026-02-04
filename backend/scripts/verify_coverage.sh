#!/bin/bash
# Coverage Verification Script for Interview Simulator
# Runs new test files and generates coverage report

set -e

echo "========================================="
echo "Interview Simulator Coverage Verification"
echo "========================================="
echo ""

cd "$(dirname "$0")/.."

echo "Step 1: Running new interview_service edge case tests..."
uv run pytest tests/test_interview_service_edge_cases.py -v --tb=short

echo ""
echo "Step 2: Running interview_service state transition tests..."
uv run pytest tests/test_interview_state_transitions.py -v --tb=short

echo ""
echo "Step 3: Running new video_service edge case tests..."
uv run pytest tests/test_video_service_edge_cases.py -v --tb=short

echo ""
echo "Step 4: Generating coverage report for target services..."
uv run pytest tests/ \
    --cov=app/services/interview_service \
    --cov=app/services/video_service \
    --cov-report=term-missing \
    --cov-report=html \
    --tb=short

echo ""
echo "========================================="
echo "Coverage Verification Complete!"
echo "========================================="
echo ""
echo "Coverage report generated at: backend/htmlcov/index.html"
echo ""
echo "Open the HTML report with:"
echo "  open htmlcov/index.html"
echo ""
