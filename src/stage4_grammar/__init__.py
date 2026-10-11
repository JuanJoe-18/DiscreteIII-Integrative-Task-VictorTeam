"""Stage 4: structured candidate-profile language, parsed and validated with textX."""

from src.stage4_grammar.models import CandidateProfile, Contact, Education, Experience
from src.stage4_grammar.parser import ProfileValidationError, parse_profile, parse_profile_file
from src.stage4_grammar.generator import candidate_from_results, serialize_profile
from src.stage4_grammar.renderer import (
    ProfileDocument, generate_document, render_profile_html, validate_document,
)

__all__ = [
    'CandidateProfile', 'Contact', 'Education', 'Experience',
    'ProfileValidationError', 'parse_profile', 'parse_profile_file',
    'candidate_from_results', 'serialize_profile', 'ProfileDocument',
    'generate_document', 'render_profile_html', 'validate_document',
]
