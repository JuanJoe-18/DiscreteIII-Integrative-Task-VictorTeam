"""Immutable structured output of the candidate-profile parser.

Missing scalar values are None; repeated elements are tuples. In particular,
unknown experience is different from an explicit zero years of experience.
These records describe a profile; they do not make classification decisions.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    kind: str
    value: str


@dataclass(frozen=True)
class Experience:
    title: str
    organization: str | None = None
    period: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class Education:
    qualification: str
    institution: str | None = None
    period: str | None = None


@dataclass(frozen=True)
class CandidateProfile:
    name: str | None = None
    summary: str | None = None
    location: str | None = None
    contacts: tuple[Contact, ...] = ()
    years_of_experience: int | None = None
    experiences: tuple[Experience, ...] = ()
    education: tuple[Education, ...] = ()
    skills: tuple[str, ...] = ()
    unrecognized_skills: tuple[str, ...] = ()
    accepted_profiles: tuple[str, ...] = ()
