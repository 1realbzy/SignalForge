from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern

from job_board_tool.detection.models import DetectionSignal

GROUP_WEIGHTS: dict[str, float] = {
    "hiring_intent": 0.50,
    "application_intent": 0.50,
    "opportunity_terminology": 0.50,
    "research_opening": 0.50,
    "actionable_contact": 0.50,
    "program_terminology": 0.20,
    "recruitment_language": 0.20,
    "engagement_type": 0.20,
    "personal_career_announcement": -0.45,
    "promotion_announcement": -0.40,
    "career_advice": -0.40,
    "job_market_discussion": -0.35,
    "historical_hiring": -0.35,
    "non_actionable_commentary": -0.30,
    "ambiguous_future_intent": -0.30,
}

POSITIVE_GROUPS = frozenset(
    {
        "hiring_intent",
        "application_intent",
        "opportunity_terminology",
        "research_opening",
        "actionable_contact",
        "program_terminology",
        "recruitment_language",
        "engagement_type",
    }
)


@dataclass(frozen=True)
class SignalSpec:
    name: str
    group: str
    pattern: str


SIGNAL_SPECS: tuple[SignalSpec, ...] = (
    SignalSpec("were_hiring", "hiring_intent", r"\bwe(?:'re| are) (?:now )?hiring\b"),
    SignalSpec("now_hiring", "hiring_intent", r"\bnow hiring\b"),
    SignalSpec("hiring_for", "hiring_intent", r"\bhiring for\b"),
    SignalSpec("open_roles", "hiring_intent", r"\bopen roles?\b"),
    SignalSpec("open_positions", "hiring_intent", r"\bopen positions?\b"),
    SignalSpec("job_opening", "hiring_intent", r"\bjob[- ]openings?\b"),
    SignalSpec("apply_now_here_via", "application_intent", r"\bapply (?:now|here|via)\b"),
    SignalSpec("applications_open", "application_intent", r"\bapplications? (?:are )?(?:now )?open\b"),
    SignalSpec("submit_application", "application_intent", r"\bsubmit (?:your )?application\b"),
    SignalSpec("send_resume", "application_intent", r"\bsend (?:in )?(?:your )?(?:resume|cv)\b"),
    SignalSpec("position_available", "opportunity_terminology", r"\bposition available\b"),
    SignalSpec("vacancy", "opportunity_terminology", r"\bvacancies?\b"),
    SignalSpec("accepting_applications", "opportunity_terminology", r"\bnow accepting applications\b"),
    SignalSpec(
        "research_assistant_opening",
        "research_opening",
        r"\bresearch assistant (?:opening|position)s?\b",
    ),
    SignalSpec("research_opening", "research_opening", r"\bresearch (?:opening|position)s?\b"),
    SignalSpec("funded_phd_postdoc", "research_opening", r"\bfunded (?:phd|postdoc(?:toral)?)\b"),
    SignalSpec("postdoc_opening", "research_opening", r"\bpostdoc(?:toral)? (?:opening|position)s?\b"),
    SignalSpec("dm_to_apply", "actionable_contact", r"\bdm (?:me|us)\b.{0,50}\bapply\b"),
    SignalSpec("email_to_apply", "actionable_contact", r"\b(?:email|e-mail) (?:us|me)\b.{0,50}\bapply\b"),
    SignalSpec("apply_by_email_or_dm", "actionable_contact", r"\bapply (?:by|via) (?:email|dm)\b"),
    SignalSpec("internship_word", "program_terminology", r"\binternships?\b"),
    SignalSpec("intern_word", "program_terminology", r"\binterns?\b"),
    SignalSpec("fellowship_word", "program_terminology", r"\bfellowships?\b"),
    SignalSpec("apprenticeship_word", "program_terminology", r"\bapprenticeships?\b"),
    SignalSpec("graduate_program_word", "program_terminology", r"\bgraduate (?:program|scheme)s?\b"),
    SignalSpec("join_our_team", "recruitment_language", r"\bjoin our team\b"),
    SignalSpec("looking_for", "recruitment_language", r"\blooking for (?:a|an|our)\b"),
    SignalSpec("seeking", "recruitment_language", r"\bseeking (?:a|an|our)\b"),
    SignalSpec("freelance_word", "engagement_type", r"\bfreelance\b"),
    SignalSpec("contractor_word", "engagement_type", r"\bcontractor\b"),
    SignalSpec("contract_role", "engagement_type", r"\bcontract (?:role|position|work|opening)\b"),
    SignalSpec("i_got_hired", "personal_career_announcement", r"\bi (?:just )?(?:got|was) hired\b"),
    SignalSpec("started_new_role", "personal_career_announcement", r"\bi (?:just )?started my new role\b"),
    SignalSpec(
        "excited_to_join",
        "personal_career_announcement",
        r"\bi(?:'m| am) (?:so )?(?:excited|thrilled) to (?:join|announce)\b",
    ),
    SignalSpec(
        "announce_i_joined",
        "personal_career_announcement",
        r"\b(?:excited|thrilled) to announce i\b",
    ),
    SignalSpec("i_have_joined", "personal_career_announcement", r"\bi(?:'ve| have) (?:accepted|joined)\b"),
    SignalSpec("i_was_promoted", "promotion_announcement", r"\bi (?:was|got) promoted\b"),
    SignalSpec("have_been_promoted", "promotion_announcement", r"\bi(?:'ve| have) been promoted\b"),
    SignalSpec("how_to_get_hired", "career_advice", r"\bhow to (?:get hired|land (?:a )?job)\b"),
    SignalSpec("resume_interview_tips", "career_advice", r"\b(?:resume|cv|interview) tips\b"),
    SignalSpec(
        "tips_for_landing",
        "career_advice",
        r"\btips (?:to|for) (?:get(?:ting)? hired|land(?:ing)? a job|landing)\b",
    ),
    SignalSpec("things_to_get_hired", "career_advice", r"\bthings you should do to get hired\b"),
    SignalSpec("job_market", "job_market_discussion", r"\bjob market\b"),
    SignalSpec("hiring_freeze", "job_market_discussion", r"\bhiring freeze\b"),
    SignalSpec("nobody_hiring", "job_market_discussion", r"\bnobody is hiring\b"),
    SignalSpec("tough_market", "job_market_discussion", r"\b(?:tough|terrible|bad) (?:job )?market\b"),
    SignalSpec("we_hired", "historical_hiring", r"\bwe hired\b"),
    SignalSpec("hired_last_year", "historical_hiring", r"\bhired \w+ last year\b"),
    SignalSpec("companies_should_hire", "non_actionable_commentary", r"\bcompanies should hire\b"),
    SignalSpec("would_you_take_job", "non_actionable_commentary", r"\bwould you take (?:a |this )?job\b"),
    SignalSpec("should_hire_more", "non_actionable_commentary", r"\bshould hire more\b"),
    SignalSpec("may_be_hiring", "ambiguous_future_intent", r"\bmay be hiring\b"),
    SignalSpec("might_hire", "ambiguous_future_intent", r"\bmight (?:be )?hir(?:e|ing)\b"),
    SignalSpec("thinking_about_hiring", "ambiguous_future_intent", r"\bthinking about hiring\b"),
    SignalSpec("planning_to_hire", "ambiguous_future_intent", r"\bplanning to hire\b"),
    SignalSpec("hiring_soon", "ambiguous_future_intent", r"\bhiring soon\b"),
)


@dataclass(frozen=True)
class CompiledSignal:
    spec: SignalSpec
    regex: Pattern[str]


def matching_view(text: str) -> str:
    normalized = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2014", " ")
        .replace("\u2013", " ")
    )
    return " ".join(normalized.split()).casefold()


def compile_signals() -> tuple[CompiledSignal, ...]:
    return tuple(CompiledSignal(spec=spec, regex=re.compile(spec.pattern)) for spec in SIGNAL_SPECS)


def group_weight(group: str, overrides: dict[str, float] | None = None) -> float:
    if overrides and group in overrides:
        return overrides[group]
    return GROUP_WEIGHTS[group]


def match_signals(
    view: str,
    compiled: tuple[CompiledSignal, ...],
    overrides: dict[str, float] | None = None,
) -> tuple[tuple[DetectionSignal, ...], tuple[DetectionSignal, ...]]:
    positive: list[DetectionSignal] = []
    negative: list[DetectionSignal] = []
    for item in compiled:
        match = item.regex.search(view)
        if match is None:
            continue
        weight = group_weight(item.spec.group, overrides)
        polarity = "positive" if item.spec.group in POSITIVE_GROUPS else "negative"
        signal = DetectionSignal(
            name=item.spec.name,
            group=item.spec.group,
            polarity=polarity,
            weight=weight,
            matched_text=match.group(0),
        )
        if polarity == "positive":
            positive.append(signal)
        else:
            negative.append(signal)
    return tuple(positive), tuple(negative)
