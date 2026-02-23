"""Pure unit tests for preparation models and helpers.

Tests PreparationStage, AnswerPreparation, PreparationQnA, DeliveryAttempt models.
No database required.
"""

from uuid import uuid4

from app.models.preparation import (
    AnswerPreparation,
    DeliveryAttempt,
    PreparationQnA,
    PreparationStage,
)


class TestPreparationStage:
    def test_detective_value(self):
        assert PreparationStage.DETECTIVE == "detective"

    def test_draft_value(self):
        assert PreparationStage.DRAFT == "draft"

    def test_practice_value(self):
        assert PreparationStage.PRACTICE == "practice"

    def test_complete_value(self):
        assert PreparationStage.COMPLETE == "complete"

    def test_stage_is_string_enum(self):
        assert isinstance(PreparationStage.DETECTIVE, str)


class TestAnswerPreparation:
    def test_default_stage_is_detective(self):
        prep = AnswerPreparation(
            user_id=uuid4(),
            question_id=uuid4(),
        )
        assert prep.stage == PreparationStage.DETECTIVE

    def test_draft_answer_defaults_to_none(self):
        prep = AnswerPreparation(
            user_id=uuid4(),
            question_id=uuid4(),
        )
        assert prep.draft_answer is None

    def test_set_draft_answer(self):
        prep = AnswerPreparation(
            user_id=uuid4(),
            question_id=uuid4(),
            draft_answer="My prepared answer using STAR method.",
        )
        assert "STAR" in prep.draft_answer


class TestPreparationQnA:
    def test_fields_set_correctly(self):
        prep_id = uuid4()
        qna = PreparationQnA(
            preparation_id=prep_id,
            question="What was the outcome?",
            answer="We improved performance by 40%.",
            order=2,
        )
        assert qna.preparation_id == prep_id
        assert qna.question == "What was the outcome?"
        assert qna.order == 2


class TestDeliveryAttempt:
    def test_defaults_to_none(self):
        attempt = DeliveryAttempt(
            preparation_id=uuid4(),
        )
        assert attempt.audio_url is None
        assert attempt.transcript is None
        assert attempt.delivery_score is None
        assert attempt.comparison_feedback is None
        assert attempt.comparison_details is None

    def test_set_delivery_score(self):
        attempt = DeliveryAttempt(
            preparation_id=uuid4(),
            delivery_score=78.5,
            comparison_feedback="Good pacing but needs more examples.",
        )
        assert attempt.delivery_score == 78.5
        assert "pacing" in attempt.comparison_feedback
