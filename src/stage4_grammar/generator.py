"""Deterministic DSL serialization and an adapter for the first three stages."""

import json
import re

from src.stage2_fst.aliases import all_canonical_tokens
from src.stage4_grammar.models import CandidateProfile, Contact, Education, Experience
from src.stage4_grammar.parser import parse_profile


def _text(value):
    if not isinstance(value, str):
        raise TypeError('DSL text fields must be strings.')
    return json.dumps(value, ensure_ascii=True)


def _symbol(value):
    # Never interpolate unchecked identifiers: a caller could inject DSL fields.
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', value):
        raise ValueError(f'Invalid DSL symbol: {value!r}.')
    return value


def serialize_profile(profile: CandidateProfile) -> str:
    """Produce a validated DSL, rejecting invalid or lossy model conversions."""
    if not isinstance(profile, CandidateProfile):
        raise TypeError('Expected a CandidateProfile.')
    lines = ['candidate {', '  personal {']

    def optional(key, value, indent='    '):
        if value is not None:
            lines.append(f'{indent}{key} {_text(value)};')

    for key in ('name', 'summary', 'location'):
        optional(key, getattr(profile, key))
    lines += ['  }', '  contact {']
    for entry in profile.contacts:
        lines.append(f'    {_symbol(entry.kind)} {_text(entry.value)};')
    lines += ['  }', '  experience {']
    years = profile.years_of_experience
    if years is not None:
        if type(years) is not int or years < 0:
            raise ValueError('years_of_experience must be a nonnegative integer or None.')
        lines.append(f'    total_years {years};')
    for entry in profile.experiences:
        lines.append('    entry {')
        lines.append(f'      title {_text(entry.title)};')
        for key in ('organization', 'period', 'description'):
            optional(key, getattr(entry, key), '      ')
        lines.append('    }')
    lines += ['  }', '  education {']
    for entry in profile.education:
        lines += ['    entry {', f'      qualification {_text(entry.qualification)};']
        for key in ('institution', 'period'):
            optional(key, getattr(entry, key), '      ')
        lines.append('    }')
    lines += ['  }', '  skills {']
    lines += [f'    skill {_symbol(token)};' for token in profile.skills]
    lines += [f'    unrecognized {_text(value)};' for value in profile.unrecognized_skills]
    lines += ['  }', '  classification {']
    lines += [f'    accepted {_symbol(pid)};' for pid in profile.accepted_profiles]
    lines += ['  }', '}', '']
    source = '\n'.join(lines)
    if parse_profile(source) != profile:
        raise ValueError('The profile must use the immutable tuple-based model without data loss.')
    return source


def candidate_from_results(extraction, normalization, classification, *, name=None, summary=None):
    """Preserve extracted facts; do not infer employers, periods or degree associations.

    Job titles and education mentions become separate partial records. Total years
    belong to the candidate, never to each individual job. Unknown skills retain
    their original spelling and cannot satisfy a classifier requirement.
    """
    vocabulary = set(all_canonical_tokens())
    unique = lambda values: tuple(dict.fromkeys(values))
    return CandidateProfile(
        name=name if name is not None else extraction.candidate_name,
        summary=summary,
        contacts=unique(Contact(kind, value) for kind, values in extraction.contact.items() for value in values),
        years_of_experience=extraction.years_of_experience,
        experiences=tuple(Experience(title) for title in dict.fromkeys(extraction.job_titles)),
        education=tuple(Education(value) for value in dict.fromkeys(extraction.education)),
        skills=unique(t for t in normalization.normalized_tokens if t in vocabulary),
        unrecognized_skills=unique(t.raw for t in normalization.traces if not t.recognized),
        accepted_profiles=tuple(pid for pid, result in classification.results_by_profile.items() if result.is_accepted),
    )
