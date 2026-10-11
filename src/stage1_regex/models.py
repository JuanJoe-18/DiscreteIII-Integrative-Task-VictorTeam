"""Data models for Stage 1 (regular-expression extraction).

Three kinds of objects live here:

* ``RegexSpec``        - one *documented* regular expression of the catalog.
* ``ExtractedItem``    - one piece of text found in a resume by one ``RegexSpec``.
* ``ExtractionResult`` - everything Stage 1 hands over to the next stages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class Category(str, Enum):
    """Coarse kind of information found in a resume.

    The first group mirrors the list of the assignment ("Contact information",
    "Programming languages", "Frameworks and libraries", "Databases",
    "Academic qualifications", "Professional experience", "Tools and technologies").
    """

    CONTACT = "CONTACT"
    IDENTITY = "IDENTITY"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"
    PROGRAMMING_LANGUAGE = "PROGRAMMING_LANGUAGE"
    FRAMEWORK_LIBRARY = "FRAMEWORK_LIBRARY"
    DATABASE = "DATABASE"
    TOOL_TECHNOLOGY = "TOOL_TECHNOLOGY"
    OTHER = "OTHER"


#: Categories whose items are *qualifications* that travel to Stage 2.
SKILL_CATEGORIES = frozenset(
    {
        Category.PROGRAMMING_LANGUAGE,
        Category.FRAMEWORK_LIBRARY,
        Category.DATABASE,
        Category.TOOL_TECHNOLOGY,
        Category.OTHER,
    }
)

#: Categories that are known technologies (everything in SKILL_CATEGORIES but OTHER).
TECH_CATEGORIES = SKILL_CATEGORIES - {Category.OTHER}


class Scope(str, Enum):
    """Where in the resume a regex is allowed to look."""

    DOCUMENT = "DOCUMENT"
    SKILLS_SECTION = "SKILLS_SECTION"


@dataclass(frozen=True)
class RegexSpec:
    """A regular expression together with its formal documentation.

    Attributes:
        name: Unique identifier, e.g. ``"EMAIL"``.
        category: Coarse kind of information it extracts.
        pattern: The regular expression (Python ``re`` syntax).
        description: The textual language recognised, in plain words.
        accepts: Strings that belong to the language (``fullmatch`` must succeed).
        rejects: Strings that do NOT belong to the language (``fullmatch`` must fail).
        flags: ``re`` flags used to compile the pattern.
        group: Which group holds the text to keep (0 = the whole match).
        scope: Where the pattern may be searched (whole document or Skills section).
        techniques: Regex features used (for the documentation / defence).
        rationale: Why the pattern was designed this way (optional).
    """

    name: str
    category: Category
    pattern: str
    description: str
    accepts: Tuple[str, ...]
    rejects: Tuple[str, ...]
    flags: int = 0
    group: int = 0
    scope: Scope = Scope.DOCUMENT
    techniques: Tuple[str, ...] = ()
    rationale: str = ""

    @property
    def regex(self) -> "re.Pattern[str]":
        """The compiled pattern (``re`` caches compilations internally)."""
        return re.compile(self.pattern, self.flags)

    def recognises(self, text: str) -> bool:
        """True if the *whole* string belongs to the language of this spec."""
        return self.regex.fullmatch(text) is not None

    def example_failures(self) -> List[str]:
        """Documented examples that the pattern does not honour (empty = all good)."""
        failures = [f"accepts {s!r} but it does not match" for s in self.accepts if not self.recognises(s)]
        failures += [f"rejects {s!r} but it matches" for s in self.rejects if self.recognises(s)]
        return failures


@dataclass(frozen=True)
class ExtractedItem:
    """One piece of text found in the resume."""

    spec_name: str
    category: Category
    text: str
    start: int
    end: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec": self.spec_name,
            "category": self.category.value,
            "text": self.text,
            "start": self.start,
            "end": self.end,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedItem":
        return cls(
            spec_name=data["spec"],
            category=Category(data["category"]),
            text=data["text"],
            start=data["start"],
            end=data["end"],
        )


@dataclass
class ExtractionResult:
    """Output of Stage 1.

    ``raw_tokens`` is the hand-over to Stage 2: the raw qualification strings
    exactly as the candidate wrote them (``JS``, ``React.js``, ``Postgres`` ...),
    without duplicates and in order of appearance. Years of experience are NOT
    part of ``raw_tokens``; they are reported in ``years_of_experience``.
    """

    raw_tokens: List[str] = field(default_factory=list)
    years_of_experience: Optional[int] = None
    candidate_name: Optional[str] = None
    items: List[ExtractedItem] = field(default_factory=list)

    # ------------------------------------------------------------------ views
    def texts(self, *spec_names: str) -> List[str]:
        """Texts found by the given specs, in order of appearance (no duplicates)."""
        seen: Dict[str, None] = {}
        for item in self.items:
            if item.spec_name in spec_names:
                seen.setdefault(item.text, None)
        return list(seen)

    def by_category(self) -> Dict[Category, List[str]]:
        """Texts grouped by category, in order of appearance (no duplicates)."""
        grouped: Dict[Category, Dict[str, None]] = {}
        for item in self.items:
            grouped.setdefault(item.category, {}).setdefault(item.text, None)
        return {cat: list(texts) for cat, texts in grouped.items()}

    @property
    def contact(self) -> Dict[str, List[str]]:
        """Contact data: ``email``, ``phone``, ``linkedin`` and ``github`` lists."""
        return {
            "email": self.texts("EMAIL"),
            "phone": self.texts("PHONE"),
            "linkedin": self.texts("LINKEDIN_URL"),
            "github": self.texts("GITHUB_URL"),
        }

    @property
    def education(self) -> List[str]:
        """Academic qualifications and certifications."""
        return self.texts("DEGREE", "CERTIFICATION")

    @property
    def job_titles(self) -> List[str]:
        return self.texts("JOB_TITLE")

    # ------------------------------------------------------------- persistence
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "years_of_experience": self.years_of_experience,
            "contact": self.contact,
            "job_titles": self.job_titles,
            "education": self.education,
            "raw_tokens": list(self.raw_tokens),
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractionResult":
        return cls(
            raw_tokens=list(data.get("raw_tokens", [])),
            years_of_experience=data.get("years_of_experience"),
            candidate_name=data.get("candidate_name"),
            items=[ExtractedItem.from_dict(d) for d in data.get("items", [])],
        )