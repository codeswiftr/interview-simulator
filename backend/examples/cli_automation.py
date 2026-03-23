#!/usr/bin/env python3
"""
Example automation workflows using interview-sim CLI.

Demonstrates how to:
1. Generate questions programmatically
2. Analyze transcripts in batch
3. Export metrics for reporting
4. Process feedback for multiple sessions

This script can be used as a template for building automated workflows
on top of the Interview Simulator platform.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def run_cli(cmd: list[str], capture_json: bool = True) -> dict[str, Any] | str:
    """Run CLI command and parse output.

    Args:
        cmd: Command and arguments as list
        capture_json: If True, parse JSON output and return dict

    Returns:
        Parsed JSON dict if capture_json=True, otherwise raw stdout

    Raises:
        Exception: If command fails or JSON parsing fails
    """
    if capture_json and "--json" not in cmd:
        cmd.append("--json")

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if capture_json:
        try:
            response = json.loads(result.stdout)
            if not response.get("success"):
                error_code = response.get("error_code", "UNKNOWN")
                error_msg = response.get("error", "Unknown error")
                raise Exception(f"{error_code}: {error_msg}")
            return response
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON: {e}\nOutput: {result.stdout}") from e
    else:
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")
        return result.stdout


def generate_question_bank(
    topics: list[str], questions_per_topic: int = 5
) -> dict[str, list[dict]]:
    """Generate a question bank for multiple topics.

    Args:
        topics: List of topic names
        questions_per_topic: Number of questions to generate per topic

    Returns:
        Dictionary mapping topic to list of questions
    """
    print("=" * 60)
    print("Generating Question Bank")
    print("=" * 60)

    question_bank = {}

    for topic in topics:
        print(f"\nGenerating {questions_per_topic} questions for: {topic}")

        response = run_cli(
            [
                "interview-sim",
                "generate-questions",
                "--topic",
                topic,
                "--count",
                str(questions_per_topic),
            ]
        )

        questions = response["data"]["questions"]
        question_bank[topic] = questions

        print(f"  ✓ Generated {len(questions)} questions")
        for q in questions[:2]:  # Show first 2
            print(f"    - {q['content'][:80]}...")

    return question_bank


def analyze_session_transcripts(session_ids: list[str]) -> dict[str, Any]:
    """Analyze transcripts for multiple sessions.

    Args:
        session_ids: List of interview session UUIDs

    Returns:
        Summary of analysis results
    """
    print("\n" + "=" * 60)
    print("Analyzing Session Transcripts")
    print("=" * 60)

    # Create temporary file with session IDs
    sessions_file = Path("/tmp/interview_sessions.txt")
    sessions_file.write_text("\n".join(session_ids))

    print(f"\nProcessing {len(session_ids)} sessions...")

    response = run_cli(
        [
            "interview-sim",
            "batch-feedback",
            "--session-ids",
            str(sessions_file),
        ]
    )

    results = response["data"]

    print("\n✓ Batch processing complete:")
    print(f"  Total: {results['total']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Generated: {results['generated']}")
    print(f"  Already exists: {results['already_exists']}")

    # Cleanup
    sessions_file.unlink()

    return results


def export_weekly_metrics(user_id: str | None = None) -> dict[str, Any]:
    """Export weekly metrics.

    Args:
        user_id: Optional user ID to filter by

    Returns:
        Metrics data
    """
    print("\n" + "=" * 60)
    print("Exporting Weekly Metrics")
    print("=" * 60)

    cmd = [
        "interview-sim",
        "export-metrics",
        "--period",
        "weekly",
    ]

    if user_id:
        cmd.extend(["--user-id", user_id])

    response = run_cli(cmd)
    metrics = response["data"]

    print(f"\nPeriod: {metrics['start_date'][:10]} to {metrics['end_date'][:10]}")
    print("\nSession Metrics:")
    print(f"  Total sessions: {metrics['sessions']['total']}")
    print(f"  Completed: {metrics['sessions']['completed']}")
    print(f"  Completion rate: {metrics['sessions']['completion_rate']}%")

    print("\nPerformance:")
    print(f"  Average score: {metrics['performance']['average_score']}/100")
    print(f"  Scored sessions: {metrics['performance']['scored_sessions']}")

    if metrics["category_breakdown"]:
        print("\nCategory Breakdown:")
        for category, count in metrics["category_breakdown"].items():
            print(f"  {category}: {count}")

    return metrics


def generate_weekly_report(output_dir: Path) -> Path:
    """Generate a comprehensive weekly report.

    Args:
        output_dir: Directory to save report files

    Returns:
        Path to main report file
    """
    print("\n" + "=" * 60)
    print("Generating Weekly Report")
    print("=" * 60)

    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Export metrics
    metrics_file = output_dir / f"metrics_{timestamp}.json"
    run_cli(
        [
            "interview-sim",
            "export-metrics",
            "--period",
            "weekly",
            "--output",
            str(metrics_file),
        ]
    )
    print(f"\n✓ Metrics exported to: {metrics_file}")

    # 2. Generate summary report
    with open(metrics_file) as f:
        metrics = json.load(f)

    report_file = output_dir / f"report_{timestamp}.md"
    with open(report_file, "w") as f:
        f.write("# Interview Simulator Weekly Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Session Statistics\n\n")
        f.write(f"- Total Sessions: {metrics['sessions']['total']}\n")
        f.write(f"- Completed: {metrics['sessions']['completed']}\n")
        f.write(f"- Analyzed: {metrics['sessions']['analyzed']}\n")
        f.write(f"- Completion Rate: {metrics['sessions']['completion_rate']}%\n\n")

        f.write("## Performance Metrics\n\n")
        f.write(f"- Average Score: {metrics['performance']['average_score']}/100\n")
        f.write(f"- Scored Sessions: {metrics['performance']['scored_sessions']}\n\n")

        f.write("## Category Breakdown\n\n")
        for category, count in metrics["category_breakdown"].items():
            f.write(f"- {category.title()}: {count}\n")

    print(f"✓ Report saved to: {report_file}")

    return report_file


def main():
    """Run example automation workflows."""
    print("\n" + "=" * 60)
    print("Interview Simulator CLI Automation Examples")
    print("=" * 60)

    # Example 1: Generate question bank for multiple topics
    topics = ["leadership", "communication", "problem-solving"]
    question_bank = generate_question_bank(topics, questions_per_topic=3)

    print(
        f"\n✓ Generated question bank with {sum(len(qs) for qs in question_bank.values())} total questions"
    )

    # Example 2: Export weekly metrics
    export_weekly_metrics()

    # Example 3: Generate weekly report
    report_dir = Path("/tmp/interview_reports")
    generate_weekly_report(report_dir)

    print("\n" + "=" * 60)
    print("All automation workflows completed successfully!")
    print("=" * 60)

    # Cleanup
    print(f"\nReport files saved to: {report_dir}")


if __name__ == "__main__":
    main()
