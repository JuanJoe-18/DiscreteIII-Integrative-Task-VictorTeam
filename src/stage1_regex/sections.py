"""Resume section detection.

Résumés are semi-structured: headings such as ``Technical Skills:`` or ``Education`` tell
where each kind of information lives. This module finds those headings with regular
expressions and returns the span of text that belongs to each section. Stage 1 uses it to
restrict ambiguous patterns (``Go``, ``R``, ``Node`` ...) to the Skills section and to find
skills that the catalog does not know (category ``OTHER``).

Two heading shapes are supported:

* a heading alone on its line (``Skills`` / ``Skills:``), and
* an inline heading followed by a colon (``... applications. Technical Skills: JS, React``),
  which is how a resume written on a single line looks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Heading names -> alternation of the words that introduce them (English and Spanish).
_HEADINGS = {
    "skills": (
        r"(?<!soft\s)(?:technical\s+skills|skills|tech(?:nical)?\s+stack|technologies"
        r"|habilidades(?:\s+t[eé]cnicas)?|tecnolog[ií]as)"
    ),
    "education": (
        r"education|academic\s+(?:background|qualifications)|educaci[oó]n|formaci[oó]n(?:\s+acad[eé]mica)?"
    ),
    "experience": r"(?:work\s+|professional\s+)?experience|experiencia(?:\s+(?:laboral|profesional))?",
    "projects": r"projects|proyectos",
    "summary": r"(?:professional\s+)?(?:summary|profile)|about\s+me|perfil(?:\s+profesional)?",
    "certifications": r"certifications?|certificaciones",
    "languages": r"languages|idiomas",
    "contact": r"contact(?:\s+(?:info(?:rmation)?|details))?|contacto",
}

_ALTERNATION = "|".join(f"(?P<{name}>{pattern})" for name, pattern in _HEADINGS.items())

# A heading alone on its line: "Skills", "Technical Skills:" ...
_LINE_HEADING = re.compile(rf"^[ \t]*(?:{_ALTERNATION})[ \t]*:?[ \t]*$", re.IGNORECASE | re.MULTILINE)
# An inline heading, which must end with a colon: "... Technical Skills: JS, React".
_INLINE_HEADING = re.compile(rf"\b(?:{_ALTERNATION})[ \t]*:", re.IGNORECASE)

# A blank line (possibly with spaces) ends a skills list.
_BLANK_LINE = re.compile(r"\n[ \t]*\n")

# Items of a skills list: separated by commas, semicolons, bullets, pipes or line breaks.
_ITEM = re.compile(r"[^,;•·|\n]+")
_LEADING_BULLET = re.compile(r"^[\s\-*•·▪>]+")
_LABEL = re.compile(r"^[A-Za-z][A-Za-z &/]{1,30}:\s*")  # "Frontend: React" -> "React"


@dataclass(frozen=True)
class Section:
    """A section of the resume: ``text[start:end]`` is its body (without the heading)."""

    name: str
    start: int
    end: int

    def body(self, text: str) -> str:
        return text[self.start : self.end]


def split_sections(text: str) -> List[Section]:
    """Find the headings of ``text`` and return one ``Section`` per heading, in order."""
    headings: List[Tuple[int, int, str]] = []
    for regex in (_LINE_HEADING, _INLINE_HEADING):
        for match in regex.finditer(text):
            headings.append((match.start(), match.end(), match.lastgroup or ""))
    headings.sort()

    # Keep the first of any overlapping headings (a line heading is also an inline one).
    unique: List[Tuple[int, int, str]] = []
    for start, end, name in headings:
        if unique and start < unique[-1][1]:
            continue
        unique.append((start, end, name))

    sections: List[Section] = []
    for index, (_, heading_end, name) in enumerate(unique):
        next_start = unique[index + 1][0] if index + 1 < len(unique) else len(text)
        end = next_start
        if name == "skills":
            end = _cut_at_blank_line(text, heading_end, next_start)
        sections.append(Section(name=name, start=heading_end, end=end))
    return sections


def section_spans(text: str, name: str) -> List[Tuple[int, int]]:
    """(start, end) of every section called ``name`` (e.g. ``"skills"``)."""
    return [(s.start, s.end) for s in split_sections(text) if s.name == name]


def find_section(text: str, name: str) -> Optional[Section]:
    """The first section called ``name`` or ``None``."""
    for section in split_sections(text):
        if section.name == name:
            return section
    return None


def split_skill_items(text: str, start: int, end: int) -> List[Tuple[str, int, int]]:
    """Split ``text[start:end]`` into skill items.

    Returns ``(item_text, item_start, item_end)`` triples with positions in ``text``. Leading
    bullets, category labels (``Frontend:``) and trailing dots are removed.
    """
    items: List[Tuple[str, int, int]] = []
    for match in _ITEM.finditer(text, start, end):
        raw = match.group()
        item_start = match.start()

        bullet = _LEADING_BULLET.match(raw)
        if bullet:
            raw = raw[bullet.end() :]
            item_start += bullet.end()
        label = _LABEL.match(raw)
        if label:
            raw = raw[label.end() :]
            item_start += label.end()

        raw = raw.rstrip().rstrip(".").rstrip()
        if raw:
            items.append((raw, item_start, item_start + len(raw)))
    return items


def _cut_at_blank_line(text: str, start: int, limit: int) -> int:
    """End of a skills list: the first blank line after its content, or ``limit``."""
    content_start = start
    while content_start < limit and text[content_start].isspace():
        content_start += 1
    blank = _BLANK_LINE.search(text, content_start, limit)
    return blank.start() if blank else limit