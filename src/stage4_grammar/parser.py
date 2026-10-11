"""Parse the Stage 4 DSL with textX and report syntax/domain errors.

The grammar defines structure. Model processors additionally check nonblank
text, contact formats, vocabulary membership and duplicate set entries. They
do not rerun the DFA or certify that an accepted profile is supported by skills.
"""

import json
from functools import lru_cache
from pathlib import Path

from textx import TextXError, TextXSemanticError, get_location, metamodel_from_file

from src.stage1_regex.patterns import SPECS_BY_NAME
from src.stage2_fst.aliases import all_canonical_tokens
from src.stage4_grammar.models import CandidateProfile, Contact, Education, Experience

GRAMMAR_PATH = Path(__file__).with_name('candidate.tx')
_CONTACT_SPECS = {
    'email': 'EMAIL', 'phone': 'PHONE',
    'linkedin': 'LINKEDIN_URL', 'github': 'GITHUB_URL',
}


class ProfileValidationError(ValueError):
    """A DSL error with a stable category and optional source location."""

    def __init__(self, message, *, kind, line=None, column=None, filename=None):
        self.message = message
        self.kind = kind
        self.line = line
        self.column = column
        self.filename = filename
        location = f'{filename}:' if filename else ''
        if line is not None:
            location += f'{line}:{column}: '
        super().__init__(f'{location}{kind}: {message}')


def _reject(obj, message):
    raise TextXSemanticError(message, **get_location(obj))


def _check_text_fields(obj, *fields):
    for field in fields:
        value = getattr(obj, field)
        if value is not None and not value.strip():
            _reject(obj, f'{field} must not be blank; omit an unknown optional field.')


def _check_unique(entries, key, label):
    seen = set()
    for entry in entries:
        value = key(entry)
        if value in seen:
            _reject(entry, f'Duplicate {label}: {value!r}.')
        seen.add(value)


def _validate_model(model, _metamodel):
    _check_text_fields(model.personal, 'name', 'summary', 'location')
    for entry in model.contact.entries:
        if not SPECS_BY_NAME[_CONTACT_SPECS[entry.kind]].recognises(entry.value):
            _reject(entry, f'Invalid {entry.kind} format: {entry.value!r}.')
    _check_unique(model.contact.entries, lambda e: (e.kind, e.value), 'contact')

    for entry in model.experience.entries:
        _check_text_fields(entry, 'title', 'organization', 'period', 'description')
    for entry in model.education.entries:
        _check_text_fields(entry, 'qualification', 'institution', 'period')

    vocabulary = set(all_canonical_tokens())
    known = [e for e in model.skills.entries if e.__class__.__name__ == 'KnownSkill']
    unknown = [e for e in model.skills.entries if e.__class__.__name__ == 'UnrecognizedSkill']
    for entry in known:
        if entry.token not in vocabulary:
            _reject(entry, f'Unknown canonical skill {entry.token!r}; use unrecognized for unknown skills.')
    for entry in unknown:
        _check_text_fields(entry, 'value')
    _check_unique(known, lambda e: e.token, 'skill')
    _check_unique(unknown, lambda e: e.value, 'unrecognized skill')
    _check_unique(model.classification.entries, lambda e: e.profile, 'accepted profile')


@lru_cache(maxsize=1)
def _metamodel():
    # Disabling automatic defaults preserves absent years (None) versus zero.
    metamodel = metamodel_from_file(
        str(GRAMMAR_PATH), auto_init_attributes=False, autokwd=True,
    )
    metamodel.register_obj_processors({'Text': json.loads, 'NonNegativeInt': int})
    metamodel.register_model_processor(_validate_model)
    return metamodel


def parse_profile(source: str, *, filename: str | None = None) -> CandidateProfile:
    """Validate the entire DSL document and return its structured information.

    Raise ProfileValidationError for malformed DSL or failed domain checks;
    lexical errors are reported as syntax errors by the textX parser.
    """
    if not isinstance(source, str):
        raise TypeError('The candidate profile source must be a string.')
    metamodel = _metamodel()
    try:
        model = metamodel.model_from_str(source, file_name=filename)
    except TextXError as error:
        raise ProfileValidationError(
            error.message,
            kind='semantic' if isinstance(error, TextXSemanticError) else 'syntax',
            line=error.line, column=error.col, filename=error.filename or filename,
        ) from error

    return CandidateProfile(
        name=model.personal.name,
        summary=model.personal.summary,
        location=model.personal.location,
        contacts=tuple(Contact(e.kind, e.value) for e in model.contact.entries),
        years_of_experience=model.experience.total_years,
        experiences=tuple(Experience(e.title, e.organization, e.period, e.description)
                          for e in model.experience.entries),
        education=tuple(Education(e.qualification, e.institution, e.period)
                        for e in model.education.entries),
        skills=tuple(e.token for e in model.skills.entries if e.__class__.__name__ == 'KnownSkill'),
        unrecognized_skills=tuple(e.value for e in model.skills.entries
                                 if e.__class__.__name__ == 'UnrecognizedSkill'),
        accepted_profiles=tuple(e.profile for e in model.classification.entries),
    )


def parse_profile_file(path: str | Path) -> CandidateProfile:
    """Read and validate a UTF-8 .resume document, retaining its error location."""
    path = Path(path)
    return parse_profile(path.read_text(encoding='utf-8'), filename=str(path))
