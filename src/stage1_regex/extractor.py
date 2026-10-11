"""Stage 1: Resume information extraction using regular expressions.

``ResumeExtractor`` is a generic engine: it runs every ``RegexSpec`` of the catalog
(``patterns.py``) over the resume and collects what they find. It does not decide whether two
expressions are equivalent (that is Stage 2) and it does not decide whether the candidate
satisfies a profile (that is Stage 3).

Pipeline of one extraction
--------------------------
1. Normalise line endings and find the Skills section(s) (``sections.py``).
2. Run each ``RegexSpec`` over its scope (whole document or Skills section only).
3. Resolve overlaps among technologies: technologies inside a contact item (e.g. an e-mail) are
   dropped and, between overlapping technologies, the longest wins (``GitHub Actions`` beats
   ``GitHub``).
4. Items of the Skills section that no technology pattern explains become category ``OTHER``
   (e.g. ``Figma``); Stage 2 decides whether it knows them.
5. Build the result: ``raw_tokens`` (hand-over to Stage 2), years of experience, name, items.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

from src.stage1_regex.models import (
    SKILL_CATEGORIES,
    TECH_CATEGORIES,
    Category,
    ExtractedItem,
    ExtractionResult,
    RegexSpec,
    Scope,
)
from src.stage1_regex.patterns import DEFAULT_SPECS
from src.stage1_regex.sections import section_spans, split_skill_items

_NUMBER_WORDS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve".split()
    )
}
_NUMBER_WORDS.update(
    {
        word: value
        for value, word in enumerate(
            "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce".split()
        )
    }
)

# What an unknown skill (category OTHER) may look like: 1 to 3 "words" of technology-like
# characters, starting with a letter, at most 30 characters (no sentences).
_PLAUSIBLE_SKILL = re.compile(r"[A-Za-z][\w.+#/-]*(?:[ ][\w.+#/-]+){0,2}")
_PARENTHETICAL = re.compile(r"\s*\(.*?\)")  # non-greedy: "React (3 years)" -> "React"


class ResumeExtractor:
    """Runs a catalog of ``RegexSpec`` over resumes."""

    def __init__(self, specs: Sequence[RegexSpec] = DEFAULT_SPECS):
        self.specs: Tuple[RegexSpec, ...] = tuple(specs)

    # ------------------------------------------------------------------ public
    def extract(self, cv_text: str) -> ExtractionResult:
        """Extract every kind of information from the text of a resume."""
        if not cv_text or not cv_text.strip():
            return ExtractionResult()

        text = cv_text.replace("\r\n", "\n").replace("\r", "\n")
        skills_spans = section_spans(text, "skills")

        items = self._run_specs(text, skills_spans)
        items = self._resolve_overlaps(items)
        items += self._unknown_skills(text, skills_spans, items)
        items.sort(key=lambda item: (item.start, item.end))

        return ExtractionResult(
            raw_tokens=self._raw_tokens(items),
            years_of_experience=self._years(items),
            candidate_name=next((i.text for i in items if i.spec_name == "CANDIDATE_NAME"), None),
            items=items,
        )

    # ----------------------------------------------------------------- internals
    def _run_specs(self, text: str, skills_spans: List[Tuple[int, int]]) -> List[ExtractedItem]:
        found: List[ExtractedItem] = []
        for spec in self.specs:
            regions = [(0, len(text))] if spec.scope is Scope.DOCUMENT else skills_spans
            regex = spec.regex
            for region_start, region_end in regions:
                # pos/endpos (instead of slicing) keep the look-behinds able to see the context.
                for match in regex.finditer(text, region_start, region_end):
                    if match.group(spec.group) is None:
                        continue
                    start, end = match.span(spec.group)
                    found.append(
                        ExtractedItem(
                            spec_name=spec.name,
                            category=spec.category,
                            text=" ".join(match.group(spec.group).split()),
                            start=start,
                            end=end,
                        )
                    )
        return found

    @staticmethod
    def _resolve_overlaps(items: List[ExtractedItem]) -> List[ExtractedItem]:
        contact_spans = [(i.start, i.end) for i in items if i.category is Category.CONTACT]

        def inside_contact(item: ExtractedItem) -> bool:
            return any(item.start < c_end and c_start < item.end for c_start, c_end in contact_spans)

        technologies = [i for i in items if i.category in TECH_CATEGORIES and not inside_contact(i)]
        others = [i for i in items if i.category not in TECH_CATEGORIES]

        # Longest first among items that start at the same place, then greedy left-to-right.
        technologies.sort(key=lambda i: (i.start, -(i.end - i.start)))
        kept: List[ExtractedItem] = []
        last_end = -1
        for item in technologies:
            if item.start >= last_end:
                kept.append(item)
                last_end = item.end
        return others + kept

    @staticmethod
    def _unknown_skills(
        text: str,
        skills_spans: List[Tuple[int, int]],
        items: List[ExtractedItem],
    ) -> List[ExtractedItem]:
        """Items of a Skills list that no technology pattern explains -> category OTHER."""
        known_spans = [(i.start, i.end) for i in items if i.category in TECH_CATEGORIES]
        unknown: List[ExtractedItem] = []
        for span_start, span_end in skills_spans:
            for raw, start, end in split_skill_items(text, span_start, span_end):
                if any(start < k_end and k_start < end for k_start, k_end in known_spans):
                    continue
                cleaned = _PARENTHETICAL.sub("", raw).strip()
                if not cleaned or len(cleaned) > 30 or not _PLAUSIBLE_SKILL.fullmatch(cleaned):
                    continue
                unknown.append(
                    ExtractedItem(
                        spec_name="UNKNOWN_SKILL",
                        category=Category.OTHER,
                        text=" ".join(cleaned.split()),
                        start=start,
                        end=start + len(cleaned),
                    )
                )
        return unknown

    @staticmethod
    def _raw_tokens(items: List[ExtractedItem]) -> List[str]:
        """Qualification strings in order of appearance, without duplicates."""
        seen: Dict[str, None] = {}
        for item in sorted(items, key=lambda i: i.start):
            if item.category in SKILL_CATEGORIES:
                seen.setdefault(item.text, None)
        # Case-insensitive de-duplication that keeps the first spelling.
        unique: Dict[str, str] = {}
        for token in seen:
            unique.setdefault(token.casefold(), token)
        return list(unique.values())

    @staticmethod
    def _years(items: List[ExtractedItem]) -> Optional[int]:
        values: List[int] = []
        for item in items:
            if item.spec_name != "YEARS_OF_EXPERIENCE":
                continue
            word = item.text.lower()
            values.append(int(word) if word.isdigit() else _NUMBER_WORDS[word])
        return max(values) if values else None


_DEFAULT_EXTRACTOR = ResumeExtractor()


def extract_qualifications(cv_text: str) -> ExtractionResult:
    """STAGE 1 entry point.

    Extracts contact data, name, experience, education and qualifications from the text of a
    resume using regular expressions.

    Example:
        'Wednesday Addams 3 years of experience ... Technical Skills: JS, React.js, NodeJS, Postgres, Git.'
        -> raw_tokens: ['JS', 'React.js', 'NodeJS', 'Postgres', 'Git'], years_of_experience: 3
    """
    return _DEFAULT_EXTRACTOR.extract(cv_text)