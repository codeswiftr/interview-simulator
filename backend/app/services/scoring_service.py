"""Scoring utilities for feedback analysis."""

from __future__ import annotations

from typing import Literal

from app.models.feedback import SkillDimension

TrendType = Literal["improving", "declining", "stable"]


class ScoringService:
    """Service for calculating scores and metrics from feedback data."""

    def calculate_overall_score(
        self,
        content_score: float,
        audio_score: float,
        content_weight: float = 0.8,
        audio_weight: float = 0.2,
    ) -> float:
        """Calculate weighted overall score from content and audio scores."""
        total_weight = content_weight + audio_weight
        if total_weight <= 0:
            return 0.0
        return round(
            (content_score * content_weight + audio_score * audio_weight) / total_weight,
            1,
        )

    def calculate_delivery_score(
        self,
        speech_rate_score: float | None,
        filler_word_score: float | None,
        confidence_score: float | None,
        volume_consistency: float | None,
    ) -> float:
        """Calculate weighted delivery score from audio metrics."""
        return round(
            (speech_rate_score or 0) * 0.25
            + (filler_word_score or 0) * 0.25
            + (confidence_score or 0) * 0.25
            + (volume_consistency or 0) * 0.25,
            1,
        )

    def calculate_behavioral_score(
        self,
        star_adherence: float | None,
        answer_structure: float | None,
        completeness: float | None,
    ) -> float:
        """Calculate weighted behavioral score."""
        return round(
            (star_adherence or 0) * 0.4
            + (answer_structure or 0) * 0.35
            + (completeness or 0) * 0.25,
            1,
        )

    def calculate_technical_score(
        self,
        technical_accuracy: float | None,
        completeness: float | None,
        relevance: float | None,
    ) -> float:
        """Calculate weighted technical score."""
        return round(
            (technical_accuracy or 0) * 0.4
            + (completeness or 0) * 0.35
            + (relevance or 0) * 0.25,
            1,
        )

    def calculate_trend(
        self,
        current_score: float,
        previous_score: float,
        threshold: float = 2.0,
    ) -> TrendType:
        """Determine trend based on score difference threshold."""
        if current_score > previous_score + threshold:
            return "improving"
        if current_score < previous_score - threshold:
            return "declining"
        return "stable"

    def evaluate_skill_dimension(
        self,
        name: str,
        recent_scores: list[float],
        previous_scores: list[float] | None,
        sessions_with_data: int,
        target_score: int,
    ) -> SkillDimension | None:
        """Generic skill dimension evaluator."""
        if not recent_scores:
            return None

        current = sum(recent_scores) / len(recent_scores)
        if previous_scores:
            previous = sum(previous_scores) / len(previous_scores)
        else:
            previous = current

        trend = self.calculate_trend(current, previous)

        return SkillDimension(
            name=name,
            current_score=round(current, 1),
            target_score=target_score,
            sessions_with_data=sessions_with_data,
            trend=trend,
        )
