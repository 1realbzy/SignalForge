"""Unit tests for opportunity detection. No live services or Twikit."""

from __future__ import annotations

from typing import Any

from job_board_tool.detection import DetectionConfig, OpportunityCategory, OpportunityDetector
from job_board_tool.ingestion.models import RawPost

STRONG_WEIGHT = 0.50
SUPPORTING_WEIGHT = 0.20
DEFAULT_THRESHOLD = 0.45


def make_raw_post(text: str, **kwargs: Any) -> RawPost:
    values: dict[str, Any] = {"source": "test", "source_id": "1", "text": text}
    values.update(kwargs)
    return RawPost(**values)


def detect(text: str, **kwargs: Any):
    config = kwargs.pop("config", None)
    post = make_raw_post(text, **kwargs)
    detector = OpportunityDetector(config)
    return detector.detect(post)


def groups(signals) -> set[str]:
    return {signal.group for signal in signals}


def test_single_strong_hiring_signal_passes_alone() -> None:
    result = detect("We're hiring software engineers.")

    assert result.is_opportunity is True
    assert result.opportunity_score == STRONG_WEIGHT
    assert result.threshold == DEFAULT_THRESHOLD
    assert groups(result.positive_signals) == {"hiring_intent"}
    assert result.negative_signals == ()
    assert "opportunity" in result.decision_reasons
    assert result.category is None
    assert result.raw_post.text == "We're hiring software engineers."


def test_single_supporting_signal_does_not_pass_alone() -> None:
    result = detect("Join our team.")

    assert result.is_opportunity is False
    assert result.opportunity_score == SUPPORTING_WEIGHT
    assert groups(result.positive_signals) == {"recruitment_language"}
    assert "insufficient_opportunity_evidence" in result.decision_reasons
    assert result.category is None


def test_overlapping_hiring_phrases_do_not_inflate_score() -> None:
    result = detect("We're hiring. Now hiring. Open roles available.")

    assert result.is_opportunity is True
    assert result.opportunity_score == STRONG_WEIGHT
    assert groups(result.positive_signals) == {"hiring_intent"}
    hiring_matches = [s for s in result.positive_signals if s.group == "hiring_intent"]
    assert len(hiring_matches) >= 2
    assert all(s.weight == STRONG_WEIGHT for s in hiring_matches)


def test_distinct_groups_still_stack() -> None:
    result = detect("We're hiring. Apply here.")

    assert result.is_opportunity is True
    assert result.opportunity_score == 1.0
    assert groups(result.positive_signals) == {"hiring_intent", "application_intent"}
    assert result.category is None


def test_hiring_interns_with_apply_sets_internship_category() -> None:
    result = detect("We're hiring summer interns. Apply here.")

    assert result.is_opportunity is True
    assert result.category == OpportunityCategory.INTERNSHIP


def test_career_advice_internship_is_not_an_opportunity() -> None:
    result = detect("Five tips for landing an internship.")

    assert result.is_opportunity is False
    assert result.category is None


def test_empty_text_is_no_opportunity_evidence() -> None:
    result = detect("")

    assert result.is_opportunity is False
    assert result.opportunity_score == 0.0
    assert result.category is None
    assert "insufficient_text" in result.decision_reasons
    assert "no_opportunity_evidence" in result.decision_reasons


def test_whitespace_text_is_no_opportunity_evidence() -> None:
    result = detect("   \n\t  ")

    assert result.is_opportunity is False
    assert "insufficient_text" in result.decision_reasons
    assert "no_opportunity_evidence" in result.decision_reasons


def test_personal_hiring_success_is_confirmed_non_opportunity() -> None:
    result = detect("I just got hired at a great company!")

    assert result.is_opportunity is False
    assert groups(result.negative_signals) == {"personal_career_announcement"}
    assert "confirmed_non_opportunity" in result.decision_reasons
    assert "no_opportunity_evidence" not in result.decision_reasons


def test_unrelated_text_is_no_opportunity_evidence() -> None:
    result = detect("The weather is nice today and I walked the dog.")

    assert result.is_opportunity is False
    assert result.positive_signals == ()
    assert result.negative_signals == ()
    assert result.decision_reasons == ("no_opportunity_evidence",)


def test_raising_threshold_flips_a_single_strong_signal() -> None:
    text = "We're hiring software engineers."
    default = detect(text)
    raised = detect(text, config=DetectionConfig(threshold=0.8))

    assert default.is_opportunity is True
    assert raised.is_opportunity is False
    assert raised.opportunity_score == STRONG_WEIGHT
    assert "insufficient_opportunity_evidence" in raised.decision_reasons


def test_author_bio_is_not_used_for_detection() -> None:
    result = detect(
        "Nice weather today, heading to the park.",
        author_bio="We post roles and we are hiring engineers",
    )

    assert result.is_opportunity is False
    assert "no_opportunity_evidence" in result.decision_reasons


def test_discovered_via_is_not_used_for_detection() -> None:
    result = detect(
        "Nice weather today, heading to the park.",
        discovered_via="hiring intern apply now",
    )

    assert result.is_opportunity is False
    assert "no_opportunity_evidence" in result.decision_reasons


def test_source_does_not_change_the_decision() -> None:
    text = "We're hiring software engineers."
    from_x = detect(text, source="x")
    from_newsletter = detect(text, source="newsletter")

    assert from_x.is_opportunity == from_newsletter.is_opportunity
    assert from_x.opportunity_score == from_newsletter.opportunity_score
    assert from_x.decision_reasons == from_newsletter.decision_reasons


def test_mixed_personal_and_hiring_without_second_positive_fails() -> None:
    result = detect("I just got hired. We're hiring though.")

    assert result.is_opportunity is False
    assert "hiring_intent" in groups(result.positive_signals)
    assert "personal_career_announcement" in groups(result.negative_signals)
    assert "insufficient_opportunity_evidence" in result.decision_reasons


def test_mixed_personal_hiring_and_apply_can_pass() -> None:
    result = detect("I got hired last month. We're now hiring interns — apply here.")

    assert result.is_opportunity is True
    assert "opportunity" in result.decision_reasons
    assert result.category == OpportunityCategory.INTERNSHIP


def test_punctuation_and_casing_still_detect_hiring() -> None:
    result = detect("WE'RE HIRING!!!")

    assert result.is_opportunity is True
    assert groups(result.positive_signals) == {"hiring_intent"}
    assert result.raw_post.text == "WE'RE HIRING!!!"


def test_original_text_is_not_rewritten() -> None:
    text = "We're Hiring  Engineers."
    result = detect(text)
    assert result.raw_post.text is text or result.raw_post.text == text


def test_fellowship_program_announcement() -> None:
    result = detect(
        "Applications are now open for our 2026 community fellowship. Details on the site."
    )

    assert result.is_opportunity is True
    assert "application_intent" in groups(result.positive_signals)
    assert result.category == OpportunityCategory.FELLOWSHIP


def test_contract_freelance_opportunity() -> None:
    result = detect(
        "We need a freelance designer for a three-month contract role. Apply here."
    )

    assert result.is_opportunity is True
    assert "application_intent" in groups(result.positive_signals)


def test_promotion_is_not_an_opportunity() -> None:
    result = detect("I was promoted to senior engineer today.")

    assert result.is_opportunity is False
    assert "confirmed_non_opportunity" in result.decision_reasons
    assert "promotion_announcement" in groups(result.negative_signals)


def test_job_market_discussion_is_not_an_opportunity() -> None:
    result = detect("The tech job market is terrible right now.")

    assert result.is_opportunity is False
    assert "confirmed_non_opportunity" in result.decision_reasons
    assert "job_market_discussion" in groups(result.negative_signals)


def test_historical_hiring_is_not_an_opportunity() -> None:
    result = detect("We hired three engineers last year.")

    assert result.is_opportunity is False
    assert "confirmed_non_opportunity" in result.decision_reasons
    assert "historical_hiring" in groups(result.negative_signals)


def test_ambiguous_future_hiring_is_not_an_opportunity() -> None:
    result = detect("We may be hiring soon, nothing is posted yet.")

    assert result.is_opportunity is False
    assert "confirmed_non_opportunity" in result.decision_reasons
    assert "ambiguous_future_intent" in groups(result.negative_signals)
    assert "hiring_intent" not in groups(result.positive_signals)


def test_missing_optional_raw_post_fields() -> None:
    post = RawPost(source="test", source_id="99", text="We're hiring analysts.")
    result = OpportunityDetector().detect(post)

    assert result.is_opportunity is True
    assert result.raw_post.author_username is None
    assert result.raw_post.url is None


def test_two_supporting_groups_still_below_threshold() -> None:
    result = detect("Looking for an intern to join our team next summer.")

    assert result.is_opportunity is False
    assert result.opportunity_score == 0.40
    assert "insufficient_opportunity_evidence" in result.decision_reasons
    assert result.category is None


def test_weight_override_changes_group_score() -> None:
    result = detect(
        "We're hiring software engineers.",
        config=DetectionConfig(weight_overrides={"hiring_intent": 0.2}),
    )

    assert result.opportunity_score == 0.2
    assert result.is_opportunity is False
