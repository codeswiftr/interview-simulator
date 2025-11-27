"""Example script to test ContentAnalyzer with real Claude API.

This script demonstrates how to use the ContentAnalyzer class to analyze
interview responses. It requires a valid ANTHROPIC_API_KEY in the environment.

Usage:
    export ANTHROPIC_API_KEY=your_api_key
    uv run python examples/test_content_analyzer_live.py
"""

import asyncio
import os

from app.ai.content_analyzer import ContentAnalyzer


async def test_behavioral_question():
    """Test analyzing a behavioral question response."""
    print("\n" + "=" * 80)
    print("Testing BEHAVIORAL Question Analysis")
    print("=" * 80)

    analyzer = ContentAnalyzer()

    question = "Tell me about a time when you had to work under a tight deadline."
    transcript = """
    In my previous role at TechCorp, we had a critical feature release scheduled for
    our flagship product. The client needed it for their annual conference, which was
    just two weeks away. I was the technical lead responsible for coordinating a team
    of five engineers. I broke down the work into manageable tasks, established daily
    stand-ups to track progress, and personally handled the most complex integration
    work. We delivered the feature three days before the deadline, which gave us time
    for thorough testing. The client was thrilled, and the feature became one of their
    most-used capabilities, with over 10,000 users in the first month.
    """

    print(f"\nQuestion: {question}")
    print(f"\nTranscript: {transcript.strip()}")
    print("\nAnalyzing...")

    metrics = await analyzer.analyze(
        question=question,
        transcript=transcript,
        question_type="behavioral",
    )

    overall_score = analyzer.calculate_overall_score(metrics, "behavioral")

    print(f"\n{'Results':-^80}")
    print(f"Overall Score: {overall_score:.1f}/100")
    print(f"Technical Accuracy: {metrics.technical_accuracy:.1f}/100")
    print(f"STAR Adherence: {metrics.star_adherence:.1f}/100")
    print(f"Answer Structure: {metrics.answer_structure:.1f}/100")
    print(f"Completeness: {metrics.completeness:.1f}/100")
    print(f"Relevance: {metrics.relevance:.1f}/100")

    print(f"\n{'Strengths':-^80}")
    for i, strength in enumerate(metrics.strengths, 1):
        print(f"{i}. {strength}")

    print(f"\n{'Areas for Improvement':-^80}")
    for i, improvement in enumerate(metrics.improvements, 1):
        print(f"{i}. {improvement}")

    print(f"\n{'Detailed Feedback':-^80}")
    print(metrics.detailed_feedback)


async def test_technical_question():
    """Test analyzing a technical question response."""
    print("\n" + "=" * 80)
    print("Testing TECHNICAL Question Analysis")
    print("=" * 80)

    analyzer = ContentAnalyzer()

    question = "Explain the difference between SQL and NoSQL databases."
    transcript = """
    SQL databases are relational databases that use structured query language and
    have a predefined schema. They're great for applications that need ACID transactions
    and complex joins, like banking systems. NoSQL databases like MongoDB or Cassandra
    use flexible schemas and are designed for horizontal scalability. They're better
    for handling large volumes of unstructured data and when you need high availability.
    The trade-off is that NoSQL databases often sacrifice strong consistency for
    availability and partition tolerance, following the CAP theorem.
    """

    print(f"\nQuestion: {question}")
    print(f"\nTranscript: {transcript.strip()}")
    print("\nAnalyzing...")

    metrics = await analyzer.analyze(
        question=question,
        transcript=transcript,
        question_type="technical",
    )

    overall_score = analyzer.calculate_overall_score(metrics, "technical")

    print(f"\n{'Results':-^80}")
    print(f"Overall Score: {overall_score:.1f}/100")
    print(f"Technical Accuracy: {metrics.technical_accuracy:.1f}/100")
    print(f"Answer Structure: {metrics.answer_structure:.1f}/100")
    print(f"Completeness: {metrics.completeness:.1f}/100")
    print(f"Relevance: {metrics.relevance:.1f}/100")

    print(f"\n{'Strengths':-^80}")
    for i, strength in enumerate(metrics.strengths, 1):
        print(f"{i}. {strength}")

    print(f"\n{'Areas for Improvement':-^80}")
    for i, improvement in enumerate(metrics.improvements, 1):
        print(f"{i}. {improvement}")

    print(f"\n{'Detailed Feedback':-^80}")
    print(metrics.detailed_feedback)


async def main():
    """Run all tests."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n" + "!" * 80)
        print("ERROR: ANTHROPIC_API_KEY environment variable not set!")
        print("Please set it with: export ANTHROPIC_API_KEY=your_api_key")
        print("!" * 80)
        return

    await test_behavioral_question()
    await test_technical_question()

    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
