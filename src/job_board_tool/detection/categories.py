from __future__ import annotations

import re
from typing import Optional

from job_board_tool.detection.models import OpportunityCategory

# Contextual type rules. These never affect opportunity_score.
_CATEGORY_PATTERNS: tuple[tuple[OpportunityCategory, tuple[str, ...]], ...] = (
    (
        OpportunityCategory.INTERNSHIP,
        (
            r"hiring(?:\s+\w+){0,5}\s+interns?\b",
            r"\binternship applications?\b",
            r"\binternships? (?:are )?(?:now )?(?:open|available)\b",
        ),
    ),
    (
        OpportunityCategory.FELLOWSHIP,
        (
            r"hiring(?:\s+\w+){0,5}\s+fellows?\b",
            r"\bfellowship applications?\b",
            r"applications? (?:are )?(?:now )?open.{0,80}\bfellowships?\b",
            r"\bfellowship (?:program|opening)s?\b",
        ),
    ),
    (
        OpportunityCategory.APPRENTICESHIP,
        (
            r"hiring(?:\s+\w+){0,5}\s+apprentices?\b",
            r"\bapprenticeship (?:applications?|program|opening)s?\b",
        ),
    ),
    (
        OpportunityCategory.GRADUATE_PROGRAM,
        (
            r"\bgraduate (?:program|scheme)s? (?:are )?(?:now )?(?:open|accepting)\b",
            r"applications? (?:are )?(?:now )?open.{0,80}\bgraduate (?:program|scheme)s?\b",
        ),
    ),
    (
        OpportunityCategory.RESEARCH,
        (
            r"\bresearch (?:assistant )?(?:opening|position)s?\b",
            r"\b(?:phd|postdoc(?:toral)?) (?:opening|position)s?\b",
        ),
    ),
    (
        OpportunityCategory.FREELANCE,
        (
            r"hiring(?:\s+\w+){0,5}\s+(?:a |an )?freelance\b",
            r"\bfreelance (?:role|position|opening|contract)\b",
        ),
    ),
    (
        OpportunityCategory.CONTRACT,
        (
            r"hiring(?:\s+\w+){0,5}\s+(?:a |an )?contract(?:or)?s?\b",
            r"\bcontract(?:or)? (?:role|position|opening)\b",
        ),
    ),
    (
        OpportunityCategory.EMPLOYMENT,
        (r"\bfull[- ]time (?:role|position|opening)\b",),
    ),
)

_SPECIFICITY = (
    OpportunityCategory.INTERNSHIP,
    OpportunityCategory.FELLOWSHIP,
    OpportunityCategory.APPRENTICESHIP,
    OpportunityCategory.GRADUATE_PROGRAM,
    OpportunityCategory.RESEARCH,
    OpportunityCategory.FREELANCE,
    OpportunityCategory.CONTRACT,
    OpportunityCategory.EMPLOYMENT,
)

_COMPILED = tuple(
    (category, tuple(re.compile(pattern) for pattern in patterns))
    for category, patterns in _CATEGORY_PATTERNS
)


def assign_category(view: str) -> Optional[OpportunityCategory]:
    matched: list[OpportunityCategory] = []
    for category, regexes in _COMPILED:
        if any(regex.search(view) for regex in regexes):
            matched.append(category)
    if not matched:
        return None
    unique = []
    for category in matched:
        if category not in unique:
            unique.append(category)
    if len(unique) == 1:
        return unique[0]
    for category in _SPECIFICITY:
        if category in unique:
            return category
    return None
