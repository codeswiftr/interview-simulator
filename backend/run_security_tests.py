#!/usr/bin/env python3
"""Security test runner for Interview Simulator.

This script runs all security-related tests and generates a comprehensive
security report covering all implemented security features.

Usage:
    python run_security_tests.py [--verbose] [--output-report <file>]

Options:
    --verbose, -v     Show detailed test output
    --output-report    Save report to specified file (default: security_report.json)
    --coverage        Generate coverage report for security modules
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest


class SecurityTestRunner:
    """Runs and reports on security tests."""

    def __init__(self, verbose: bool = False, output_file: str = "security_report.json"):
        self.verbose = verbose
        self.output_file = Path(output_file)
        self.results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "duration": 0,
            },
            "categories": {
                "authentication": {},
                "api_security": {},
                "xss_prevention": {},
                "cors_security": {},
                "rate_limiting": {},
                "input_validation": {},
                "session_management": {},
                "file_upload": {},
                "error_handling": {},
                "headers_security": {},
            },
            "coverage": {},
            "recommendations": [],
            "critical_issues": [],
        }

    def run_tests(self) -> None:
        """Run all security test categories."""
        print("🔒 Running Security Test Suite")
        print("=" * 60)

        start_time = time.time()

        # Define test files for each category
        test_categories = {
            "authentication": [
                "tests/test_security_auth.py",
            ],
            "api_security": [
                "tests/test_security_api.py",
            ],
            "xss_prevention": [
                "tests/test_security_xss.py",
            ],
            "cors_security": [
                "tests/test_security_api.py::TestCORSSecurity",
            ],
            "rate_limiting": [
                "tests/test_security_api.py::TestRateLimitSecurity",
            ],
            "input_validation": [
                "tests/test_security_xss.py::TestInputValidationXSS",
                "tests/test_security_auth.py::TestPasswordComplexityValidation",
            ],
            "session_management": [
                "tests/test_security_auth.py::TestSessionSecurity",
                "tests/test_security_integration.py::TestSessionTimeoutSecurity",
            ],
            "file_upload": [
                "tests/test_security_integration.py::TestFileUploadSecurity",
            ],
            "error_handling": [
                "tests/test_security_integration.py::TestErrorHandlingSecurity",
            ],
            "headers_security": [
                "tests/test_security_auth.py::TestSecurityHeaders",
                "tests/test_security_integration.py::TestSecurityHeadersIntegration",
            ],
        }

        # Run each category
        for category, test_files in test_categories.items():
            print(f"\n📋 Running {category.replace('_', ' ').title()} Tests...")
            self._run_test_category(category, test_files)

        # Run integration tests
        print("\n🔗 Running Integration Tests...")
        self._run_test_category(
            "integration",
            ["tests/test_security_integration.py"]
        )

        # Calculate total duration
        self.results["summary"]["duration"] = time.time() - start_time

        # Generate report
        self._generate_report()

    def _run_test_category(self, category: str, test_files: list[str]) -> None:
        """Run tests for a specific category."""
        # Build pytest arguments
        args = [
            "-v" if self.verbose else "-q",
            "--tb=short",
            "--json-report",
            f"--json-report-file=/tmp/{category}_report.json",
        ]

        # Add test files
        args.extend(test_files)

        # Run pytest
        try:
            pytest.main(args)

            # Read JSON report if available
            try:
                with open(f"/tmp/{category}_report.json") as f:
                    report = json.load(f)

                    # Extract summary
                    summary = report.get("summary", {})
                    self.results["categories"][category] = {
                        "total": summary.get("total", 0),
                        "passed": summary.get("passed", 0),
                        "failed": summary.get("failed", 0),
                        "skipped": summary.get("skipped", 0),
                        "errors": summary.get("error", 0),
                        "duration": summary.get("duration", 0),
                    }

                    # Update totals
                    for key in ["total", "passed", "failed", "skipped", "errors"]:
                        self.results["summary"][key] += self.results["categories"][category][key]

                    # Check for critical failures
                    if self.results["categories"][category]["failed"] > 0:
                        self.results["critical_issues"].append(
                            f"Critical failures in {category}"
                        )

                    # Extract failed tests
                    for test in report.get("tests", []):
                        if test.get("outcome") in ["failed", "error"]:
                            self.results["recommendations"].append({
                                "category": category,
                                "test": test.get("nodeid", "unknown"),
                                "issue": "Test failed - check security implementation",
                                "severity": "high" if "security" in category else "medium",
                            })

            except FileNotFoundError:
                print(f"  ⚠️  Could not read report for {category}")
                self.results["categories"][category] = {"error": "Report not available"}

        except Exception as e:
            print(f"  ❌ Error running {category} tests: {e}")
            self.results["categories"][category] = {"error": str(e)}

    def _generate_report(self) -> None:
        """Generate comprehensive security report."""
        print("\n" + "=" * 60)
        print("📊 SECURITY TEST SUMMARY")
        print("=" * 60)

        # Print summary
        summary = self.results["summary"]
        print(f"\nTotal Tests: {summary['total']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⏭️  Skipped: {summary['skipped']}")
        print(f"💥 Errors: {summary['errors']}")
        print(f"⏱️  Duration: {summary['duration']:.2f}s")

        # Calculate pass rate
        if summary["total"] > 0:
            pass_rate = (summary["passed"] / summary["total"]) * 100
            print(f"📈 Pass Rate: {pass_rate:.1f}%")

        # Print category breakdown
        print("\n📋 Category Breakdown:")
        print("-" * 40)
        for category, results in self.results["categories"].items():
            if "error" in results:
                print(f"  {category}: ❌ {results['error']}")
            else:
                total = results.get("total", 0)
                passed = results.get("passed", 0)
                if total > 0:
                    status = "✅" if passed == total else "❌"
                    print(f"  {category}: {status} {passed}/{total}")

        # Print recommendations
        if self.results["recommendations"]:
            print("\n⚠️  RECOMMENDATIONS")
            print("-" * 40)
            for rec in self.results["recommendations"][:10]:  # Show first 10
                severity_icon = "🔴" if rec["severity"] == "high" else "🟡"
                print(f"  {severity_icon} [{rec['category']}] {rec['issue']}")

        # Print critical issues
        if self.results["critical_issues"]:
            print("\n🚨 CRITICAL ISSUES")
            print("-" * 40)
            for issue in self.results["critical_issues"]:
                print(f"  🔴 {issue}")

        # Save report
        self._save_report()

        # Overall status
        if summary["failed"] > 0 or summary["errors"] > 0:
            print("\n❌ SECURITY TESTS FAILED")
            print("   Review the recommendations above and fix critical issues")
            sys.exit(1)
        else:
            print("\n✅ ALL SECURITY TESTS PASSED")
            print("   Security implementation is solid")

    def _save_report(self) -> None:
        """Save detailed report to file."""
        try:
            with open(self.output_file, "w") as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📄 Detailed report saved to: {self.output_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save report: {e}")

    def run_coverage(self) -> None:
        """Generate coverage report for security modules."""
        print("\n📊 Generating Coverage Report...")

        args = [
            "--cov=app/security",
            "--cov=app/middleware/rate_limit.py",
            "--cov=app/api/users.py",
            "--cov-report=html:coverage_html",
            "--cov-report=json:coverage.json",
            "tests/test_security_*.py",
        ]

        try:
            pytest.main(args)

            # Read coverage report
            try:
                with open("coverage.json") as f:
                    coverage = json.load(f)
                    self.results["coverage"] = {
                        "total_coverage": coverage.get("totals", {}).get("percent_covered", 0),
                        "files": {}
                    }

                    for filename, file_data in coverage.get("files", {}).items():
                        if any(mod in filename for mod in ["security", "rate_limit", "users"]):
                            self.results["coverage"]["files"][filename] = {
                                "lines_covered": file_data.get("summary", {}).get("covered_lines", 0),
                                "lines_missing": file_data.get("summary", {}).get("missing_lines", 0),
                                "percent_covered": file_data.get("summary", {}).get("percent_covered", 0),
                            }

                    print(f"\n📊 Security Module Coverage: {self.results['coverage']['total_coverage']:.1f}%")

            except FileNotFoundError:
                print("  ⚠️  Could not read coverage report")

        except Exception as e:
            print(f"  ❌ Error generating coverage: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run security test suite")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "-o", "--output-report",
        default="security_report.json",
        help="Output report file (default: security_report.json)"
    )
    parser.add_argument(
        "-c", "--coverage", action="store_true",
        help="Generate coverage report for security modules"
    )

    args = parser.parse_args()

    # Create test runner
    runner = SecurityTestRunner(verbose=args.verbose, output_file=args.output_report)

    # Run tests
    runner.run_tests()

    # Generate coverage if requested
    if args.coverage:
        runner.run_coverage()

    # Final summary
    print("\n🔐 Security testing complete!")
    print(f"   View detailed report: {args.output_report}")
    if args.coverage:
        print("   View coverage report: coverage_html/index.html")


if __name__ == "__main__":
    main()
