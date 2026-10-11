"""Stage 1: Resume Information Extraction using Regular Expressions."""

from src.stage1_regex.extractor import ResumeExtractor, extract_qualifications
from src.stage1_regex.models import Category, ExtractedItem, ExtractionResult, RegexSpec, Scope
from src.stage1_regex.patterns import DEFAULT_SPECS, SPECS_BY_NAME
from src.stage1_regex.storage import load_result, save_result

__all__ = [
    "Category",
    "DEFAULT_SPECS",
    "ExtractedItem",
    "ExtractionResult",
    "RegexSpec",
    "ResumeExtractor",
    "SPECS_BY_NAME",
    "Scope",
    "extract_qualifications",
    "load_result",
    "save_result",
]