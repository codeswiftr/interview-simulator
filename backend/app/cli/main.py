"""Interview Simulator CLI - Agent-friendly automation interface.

This CLI provides automation capabilities for the Interview Simulator platform,
designed for both human operators and AI agents.

All commands support --json flag for structured output following FORGE standards.
"""

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_async_engine
from app.models.interview import InterviewResponse, InterviewSession, InterviewStatus
from app.models.question import Difficulty, Question, QuestionCategory
from app.services.feedback_service import FeedbackService

app = typer.Typer(
    name="interview-sim",
    help="Interview Simulator CLI - Automation for question generation, analysis, and metrics",
    add_completion=False,
)

console = Console()


# ============================================================================
# Output Helpers
# ============================================================================


def output_result(
    data: Any,
    error: str | None = None,
    error_code: str | None = None,
    json_output: bool = False,
    duration_ms: float = 0,
) -> None:
    """Output result in JSON or human-friendly format.

    Args:
        data: Result data (for success) or None (for error)
        error: Error message (if failed)
        error_code: Error code (if failed)
        json_output: Whether to output JSON
        duration_ms: Operation duration in milliseconds
    """
    if json_output:
        response = {
            "success": error is None,
            "data": data,
            "error": error,
            "error_code": error_code,
            "timestamp": datetime.now(UTC).isoformat(),
            "duration_ms": round(duration_ms, 2),
            "metadata": {
                "command": " ".join(sys.argv),
                "version": "0.1.0",
            },
        }
        console.print_json(json.dumps(response, default=str))
    else:
        if error:
            console.print(f"[red]Error ({error_code}): {error}[/red]")
            raise typer.Exit(1)
        # Human-friendly output handled by individual commands
        pass


def get_session_sync() -> AsyncSession:
    """Get database session synchronously for CLI operations."""
    from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

    engine = get_async_engine()
    return SQLModelAsyncSession(engine)


# ============================================================================
# Question Management Commands
# ============================================================================


@app.command("generate-questions")
def generate_questions(
    topic: str = typer.Option(..., "--topic", "-t", help="Question topic/category"),
    count: int = typer.Option(5, "--count", "-n", help="Number of questions to generate"),
    difficulty: str = typer.Option(
        "medium", "--difficulty", "-d", help="Question difficulty (easy/medium/hard)"
    ),
    category: str = typer.Option(
        "behavioral",
        "--category",
        "-c",
        help="Question category (behavioral/technical/system_design)",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Generate interview questions for a specific topic.

    Examples:
        interview-sim generate-questions --topic leadership --count 5
        interview-sim generate-questions -t arrays -n 3 -d hard -c technical --json
    """
    start = datetime.now(UTC)

    try:
        # Validate inputs
        try:
            difficulty_enum = Difficulty(difficulty.lower())
        except ValueError:
            output_result(
                None,
                error=f"Invalid difficulty: {difficulty}. Use easy/medium/hard",
                error_code="INVALID_INPUT",
                json_output=json_output,
            )
            return

        try:
            category_enum = QuestionCategory(category.lower())
        except ValueError:
            output_result(
                None,
                error=f"Invalid category: {category}. Use behavioral/technical/system_design",
                error_code="INVALID_INPUT",
                json_output=json_output,
            )
            return

        async def _generate():
            async with get_session_sync() as session:
                # Query existing questions on this topic
                stmt = (
                    select(Question)
                    .where(Question.category == category_enum)
                    .where(Question.difficulty == difficulty_enum)
                    .where(Question.topic_tags.contains([topic]))
                    .where(Question.is_active == True)  # noqa: E712
                    .limit(count)
                )
                result = await session.exec(stmt)
                questions = list(result.all())

                return [
                    {
                        "id": str(q.id),
                        "content": q.content,
                        "category": q.category.value,
                        "difficulty": q.difficulty.value,
                        "topic_tags": q.topic_tags,
                        "company_tags": q.company_tags,
                        "expected_duration_seconds": q.expected_duration_seconds,
                    }
                    for q in questions
                ]

        questions_data = asyncio.run(_generate())

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        if json_output:
            output_result(
                {
                    "questions": questions_data,
                    "count": len(questions_data),
                    "topic": topic,
                    "difficulty": difficulty,
                    "category": category,
                },
                json_output=True,
                duration_ms=duration,
            )
        else:
            console.print(
                f"\n[bold]Generated {len(questions_data)} questions for topic '{topic}'[/bold]\n"
            )

            for i, q in enumerate(questions_data, 1):
                console.print(f"[cyan]{i}. {q['content']}[/cyan]")
                console.print(
                    f"   Difficulty: {q['difficulty']} | Duration: {q['expected_duration_seconds']}s"
                )
                console.print(f"   Tags: {', '.join(q['topic_tags'])}\n")

            console.print(
                f"[green]✓ Generated {len(questions_data)} questions in {duration:.0f}ms[/green]"
            )

    except Exception as e:
        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        output_result(
            None,
            error=str(e),
            error_code="INTERNAL_ERROR",
            json_output=json_output,
            duration_ms=duration,
        )


# ============================================================================
# Transcript Analysis Commands
# ============================================================================


@app.command("analyze-transcript")
def analyze_transcript(
    file: Path = typer.Option(..., "--file", "-f", help="Path to transcript file"),
    session_id: str = typer.Option(
        None, "--session-id", "-s", help="Interview session ID (optional)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Analyze interview transcript and generate feedback.

    Examples:
        interview-sim analyze-transcript --file transcript.txt
        interview-sim analyze-transcript -f transcript.txt -s session-uuid --json
    """
    start = datetime.now(UTC)

    try:
        # Read transcript
        if not file.exists():
            output_result(
                None,
                error=f"Transcript file not found: {file}",
                error_code="NOT_FOUND",
                json_output=json_output,
            )
            return

        transcript_text = file.read_text()

        async def _analyze():
            async with get_session_sync() as session:
                feedback_service = FeedbackService()

                # If session_id provided, get actual responses
                if session_id:
                    try:
                        session_uuid = UUID(session_id)
                    except ValueError:
                        raise ValueError(f"Invalid session ID format: {session_id}")

                    # Get responses for this session
                    stmt = (
                        select(InterviewResponse)
                        .where(InterviewResponse.session_id == session_uuid)
                        .where(InterviewResponse.transcript.isnot(None))
                    )
                    result = await session.exec(stmt)
                    responses = list(result.all())

                    if not responses:
                        raise ValueError(
                            f"No responses with transcripts found for session {session_id}"
                        )

                    # Analyze each response
                    analyses = []
                    for response in responses:
                        # Check if feedback exists
                        existing = await feedback_service.get_response_feedback(
                            session, response.id
                        )
                        if not existing:
                            feedback = await feedback_service.generate_feedback(
                                session, response.id
                            )
                        else:
                            feedback = existing

                        analyses.append(
                            {
                                "response_id": str(response.id),
                                "question_id": str(response.question_id),
                                "overall_score": feedback.overall_content_score,
                                "technical_accuracy": feedback.technical_accuracy,
                                "star_adherence": feedback.star_adherence,
                                "answer_structure": feedback.answer_structure,
                                "completeness": feedback.completeness,
                                "relevance": feedback.relevance,
                                "strengths": feedback.strengths,
                                "improvements": feedback.improvements,
                                "detailed_feedback": feedback.detailed_feedback,
                            }
                        )

                    return {
                        "session_id": session_id,
                        "response_count": len(analyses),
                        "analyses": analyses,
                    }
                else:
                    # Standalone transcript analysis (not tied to a session)
                    return {
                        "transcript_length": len(transcript_text),
                        "word_count": len(transcript_text.split()),
                        "note": "Standalone analysis not yet implemented. Use --session-id to analyze session responses.",
                    }

        result_data = asyncio.run(_analyze())

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        if json_output:
            output_result(result_data, json_output=True, duration_ms=duration)
        else:
            if session_id:
                console.print(
                    f"\n[bold]Analyzed {result_data['response_count']} responses[/bold]\n"
                )

                for i, analysis in enumerate(result_data["analyses"], 1):
                    console.print(f"[cyan]Response {i}[/cyan]")
                    console.print(f"  Overall Score: {analysis['overall_score']:.1f}/100")
                    console.print(f"  Technical Accuracy: {analysis['technical_accuracy']:.1f}/100")
                    console.print(f"  STAR Adherence: {analysis['star_adherence']:.1f}/100")
                    console.print(f"  Strengths: {', '.join(analysis['strengths'][:3])}")
                    console.print(f"  Improvements: {', '.join(analysis['improvements'][:3])}\n")
            else:
                console.print(
                    f"\n[yellow]Transcript loaded: {result_data['word_count']} words[/yellow]"
                )
                console.print("[dim]Use --session-id to analyze actual session responses[/dim]\n")

            console.print(f"[green]✓ Analysis complete in {duration:.0f}ms[/green]")

    except Exception as e:
        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        output_result(
            None,
            error=str(e),
            error_code="INTERNAL_ERROR",
            json_output=json_output,
            duration_ms=duration,
        )


# ============================================================================
# Metrics Export Commands
# ============================================================================


@app.command("export-metrics")
def export_metrics(
    period: str = typer.Option("weekly", "--period", "-p", help="Time period (weekly/monthly)"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Output file path (optional)"),
    user_id: str = typer.Option(None, "--user-id", "-u", help="Filter by user ID (optional)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Export usage and performance metrics.

    Examples:
        interview-sim export-metrics --period weekly
        interview-sim export-metrics -p monthly -o metrics.json --json
        interview-sim export-metrics -p weekly -u user-uuid --json
    """
    start = datetime.now(UTC)

    try:
        # Validate period
        if period not in ["weekly", "monthly"]:
            output_result(
                None,
                error=f"Invalid period: {period}. Use weekly or monthly",
                error_code="INVALID_INPUT",
                json_output=json_output,
            )
            return

        async def _export():
            async with get_session_sync() as session:
                # Calculate date range
                from datetime import timedelta

                now = datetime.now(UTC)
                if period == "weekly":
                    start_date = now - timedelta(days=7)
                else:  # monthly
                    start_date = now - timedelta(days=30)

                # Build base query
                stmt = select(InterviewSession).where(InterviewSession.created_at >= start_date)

                # Filter by user if specified
                if user_id:
                    try:
                        user_uuid = UUID(user_id)
                    except ValueError:
                        raise ValueError(f"Invalid user ID format: {user_id}")
                    stmt = stmt.where(InterviewSession.user_id == user_uuid)

                result = await session.exec(stmt)
                sessions = list(result.all())

                # Calculate metrics
                total_sessions = len(sessions)
                completed_sessions = len(
                    [s for s in sessions if s.status == InterviewStatus.COMPLETED]
                )
                analyzed_sessions = len(
                    [s for s in sessions if s.status == InterviewStatus.ANALYZED]
                )

                # Score statistics
                scores = [s.overall_score for s in sessions if s.overall_score is not None]
                avg_score = sum(scores) / len(scores) if scores else 0

                # Category breakdown
                category_counts = {}
                for session in sessions:
                    cat = session.interview_type.value
                    category_counts[cat] = category_counts.get(cat, 0) + 1

                # Get total responses
                response_stmt = (
                    select(InterviewResponse)
                    .join(InterviewSession)
                    .where(InterviewSession.created_at >= start_date)
                )
                if user_id:
                    response_stmt = response_stmt.where(InterviewSession.user_id == user_uuid)

                response_result = await session.exec(response_stmt)
                responses = list(response_result.all())

                total_responses = len(responses)
                transcribed_responses = len([r for r in responses if r.transcript is not None])

                return {
                    "period": period,
                    "start_date": start_date.isoformat(),
                    "end_date": now.isoformat(),
                    "user_id": user_id,
                    "sessions": {
                        "total": total_sessions,
                        "completed": completed_sessions,
                        "analyzed": analyzed_sessions,
                        "completion_rate": round(completed_sessions / total_sessions * 100, 1)
                        if total_sessions > 0
                        else 0,
                    },
                    "responses": {
                        "total": total_responses,
                        "transcribed": transcribed_responses,
                        "transcription_rate": round(
                            transcribed_responses / total_responses * 100, 1
                        )
                        if total_responses > 0
                        else 0,
                    },
                    "performance": {
                        "average_score": round(avg_score, 1),
                        "scored_sessions": len(scores),
                    },
                    "category_breakdown": category_counts,
                }

        metrics = asyncio.run(_export())

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        # Write to file if specified
        if output_file:
            output_file.write_text(json.dumps(metrics, indent=2, default=str))
            if not json_output:
                console.print(f"[green]✓ Metrics exported to {output_file}[/green]")

        if json_output:
            output_result(metrics, json_output=True, duration_ms=duration)
        else:
            console.print(f"\n[bold]{period.title()} Metrics Report[/bold]")
            console.print(f"Period: {metrics['start_date'][:10]} to {metrics['end_date'][:10]}\n")

            # Sessions table
            table = Table(title="Session Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Sessions", str(metrics["sessions"]["total"]))
            table.add_row("Completed", str(metrics["sessions"]["completed"]))
            table.add_row("Analyzed", str(metrics["sessions"]["analyzed"]))
            table.add_row("Completion Rate", f"{metrics['sessions']['completion_rate']}%")

            console.print(table)
            console.print()

            # Performance
            console.print("[bold]Performance[/bold]")
            console.print(f"  Average Score: {metrics['performance']['average_score']}/100")
            console.print(f"  Scored Sessions: {metrics['performance']['scored_sessions']}\n")

            # Category breakdown
            if metrics["category_breakdown"]:
                console.print("[bold]Category Breakdown[/bold]")
                for cat, count in metrics["category_breakdown"].items():
                    console.print(f"  {cat}: {count}")

            console.print(f"\n[green]✓ Metrics calculated in {duration:.0f}ms[/green]")

    except Exception as e:
        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        output_result(
            None,
            error=str(e),
            error_code="INTERNAL_ERROR",
            json_output=json_output,
            duration_ms=duration,
        )


# ============================================================================
# Batch Feedback Commands
# ============================================================================


@app.command("batch-feedback")
def batch_feedback(
    session_ids_file: Path = typer.Option(
        ..., "--session-ids", "-f", help="File with session IDs (one per line)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Generate feedback for multiple sessions in batch.

    Examples:
        interview-sim batch-feedback --session-ids sessions.txt
        interview-sim batch-feedback -f sessions.txt --json
    """
    start = datetime.now(UTC)

    try:
        # Read session IDs
        if not session_ids_file.exists():
            output_result(
                None,
                error=f"Session IDs file not found: {session_ids_file}",
                error_code="NOT_FOUND",
                json_output=json_output,
            )
            return

        session_ids_raw = session_ids_file.read_text().strip().split("\n")
        session_ids = [sid.strip() for sid in session_ids_raw if sid.strip()]

        if not session_ids:
            output_result(
                None,
                error="No session IDs found in file",
                error_code="INVALID_INPUT",
                json_output=json_output,
            )
            return

        async def _batch_process():
            async with get_session_sync() as session:
                feedback_service = FeedbackService()
                results = []

                for sid_str in session_ids:
                    try:
                        session_uuid = UUID(sid_str)
                    except ValueError:
                        results.append(
                            {
                                "session_id": sid_str,
                                "success": False,
                                "error": "Invalid UUID format",
                            }
                        )
                        continue

                    try:
                        # Check if feedback already exists
                        existing = await feedback_service.get_session_feedback(
                            session, session_uuid
                        )

                        if existing:
                            results.append(
                                {
                                    "session_id": sid_str,
                                    "success": True,
                                    "status": "already_exists",
                                    "overall_score": existing.overall_score,
                                }
                            )
                        else:
                            # Generate new feedback
                            feedback = await feedback_service.generate_session_feedback(
                                session, session_uuid
                            )
                            results.append(
                                {
                                    "session_id": sid_str,
                                    "success": True,
                                    "status": "generated",
                                    "overall_score": feedback.overall_score,
                                    "audio_score": feedback.audio_score,
                                    "content_score": feedback.content_score,
                                }
                            )

                    except Exception as e:
                        results.append(
                            {
                                "session_id": sid_str,
                                "success": False,
                                "error": str(e),
                            }
                        )

                return results

        results = asyncio.run(_batch_process())

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        # Calculate summary
        successful = len([r for r in results if r["success"]])
        failed = len([r for r in results if not r["success"]])
        generated = len([r for r in results if r.get("status") == "generated"])
        existing = len([r for r in results if r.get("status") == "already_exists"])

        summary = {
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "generated": generated,
            "already_exists": existing,
            "results": results,
        }

        if json_output:
            output_result(summary, json_output=True, duration_ms=duration)
        else:
            console.print("\n[bold]Batch Feedback Processing Complete[/bold]\n")
            console.print(f"Total Sessions: {summary['total']}")
            console.print(f"[green]✓ Successful: {successful}[/green]")
            console.print(f"[red]✗ Failed: {failed}[/red]")
            console.print(f"  - Generated: {generated}")
            console.print(f"  - Already Exists: {existing}\n")

            if failed > 0:
                console.print("[bold]Failed Sessions:[/bold]")
                for r in results:
                    if not r["success"]:
                        console.print(f"  [red]{r['session_id']}: {r['error']}[/red]")

            console.print(f"\n[green]✓ Batch processing complete in {duration:.0f}ms[/green]")

    except Exception as e:
        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        output_result(
            None,
            error=str(e),
            error_code="INTERNAL_ERROR",
            json_output=json_output,
            duration_ms=duration,
        )


# ============================================================================
# Version Command
# ============================================================================


@app.command("version")
def version(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Display CLI version information."""
    version_info = {
        "version": "0.1.0",
        "app": "interview-simulator",
        "domain": "codeswiftr.com",
        "python_version": sys.version.split()[0],
    }

    if json_output:
        output_result(version_info, json_output=True, duration_ms=0)
    else:
        console.print("[bold]Interview Simulator CLI[/bold]")
        console.print(f"Version: {version_info['version']}")
        console.print(f"App: {version_info['app']}")
        console.print(f"Domain: {version_info['domain']}")


if __name__ == "__main__":
    app()
