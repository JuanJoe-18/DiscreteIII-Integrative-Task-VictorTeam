"""Stage 1: Resume Information Extraction module using Regular Expressions.

This module defines the interface contract for Integrante 1.
It extracts relevant technical skills, experience, and qualification tokens
from raw textual resumes using regular expressions.
"""

from dataclasses import dataclass
import re
from typing import List


@dataclass
class ExtractionResult:
    """Represents the output of Stage 1 extraction."""
    raw_tokens: List[str]
    years_of_experience: str | None = None
    candidate_name: str | None = None


# Known patterns for technical skills in resume text (Mock / Reference patterns)
_DEFAULT_SKILL_PATTERNS = [
    r"\b[A-Za-z0-9\.\+#_-]+(?:\.js)?\b",
]


def extract_qualifications(cv_text: str) -> ExtractionResult:
    """ETAPA 1 (A cargo de Integrante 1):
    
    Extrae fragmentos de calificaciones crudas del texto de una hoja de vida
    utilizando expresiones regulares (módulo re de Python).
    
    Args:
        cv_text: Texto plano extraído del currículum vitae.
        
    Returns:
        ExtractionResult con la lista de tokens crudos identificados y metadatos.
        
    Ejemplo:
        'Wednesday Addams 3 years ... JS, React.js, NodeJS, Postgres, Git'
        -> raw_tokens: ['3', 'JS', 'React.js', 'NodeJS', 'Postgres', 'Git']
    """
    if not cv_text or not cv_text.strip():
        return ExtractionResult(raw_tokens=[])

    # 1. Extract years of experience (e.g. '3 years', '2 years of experience')
    years_match = re.search(r"(\d+)\s*(?:years|años)", cv_text, re.IGNORECASE)
    years_exp = years_match.group(1) if years_match else None

    # 2. Extract technical skill fragments (simulated regex extractor)
    # Looks for phrases like 'Technical Skills: ...' or scans tokens
    skills_section_match = re.search(
        r"(?:Technical Skills|Skills|Habilidades|Tecnolog[ií]as)[:\s]+([^\n]+)",
        cv_text,
        re.IGNORECASE,
    )

    extracted_skills: List[str] = []
    if skills_section_match:
        raw_section = skills_section_match.group(1)
        # Split by comma or semicolon
        items = [item.strip() for item in re.split(r"[,;]+", raw_section) if item.strip()]
        cleaned_items = []
        for item in items:
            if item.endswith(".") and not item.lower().endswith(".js"):
                item = item.rstrip(".").strip()
            if item:
                cleaned_items.append(item)
        extracted_skills = cleaned_items
    else:
        # Fallback: tokenize words looking like skills
        tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9\.\+#_-]*\b", cv_text)
        extracted_skills = tokens

    final_tokens: List[str] = []
    if years_exp:
        final_tokens.append(years_exp)
    final_tokens.extend(extracted_skills)

    return ExtractionResult(
        raw_tokens=final_tokens,
        years_of_experience=years_exp,
    )
