"""Self-contained HTML output, available only after complete DSL validation."""

from dataclasses import asdict, dataclass
from html import escape

from src.stage3_classifier.profiles import PROFILES_REGISTRY
from src.stage4_grammar.generator import serialize_profile
from src.stage4_grammar.models import CandidateProfile
from src.stage4_grammar.parser import parse_profile


@dataclass(frozen=True)
class ProfileDocument:
    profile: CandidateProfile
    dsl: str
    html: str

    def to_dict(self):
        return {'validated': True, 'dsl': self.dsl, 'html': self.html, 'profile': asdict(self.profile)}


def validate_document(source: str, *, filename: str | None = None) -> ProfileDocument:
    """Validate syntax and domain rules before invoking the private HTML renderer."""
    profile = parse_profile(source, filename=filename)
    return ProfileDocument(profile, source, _render(profile))


def generate_document(profile: CandidateProfile) -> ProfileDocument:
    return validate_document(serialize_profile(profile))


def render_profile_html(source: str) -> str:
    return validate_document(source).html


def _render(profile):
    esc = lambda value: escape(str(value), quote=True)
    sections = []

    def section(title, content):
        sections.append(f'<section><h2>{esc(title)}</h2>{content}</section>')

    def listing(values):
        return '<ul>' + ''.join(f'<li>{esc(v)}</li>' for v in values) + '</ul>'

    if profile.contacts:
        # Contact values are text, not user-controlled HTML or URL attributes.
        section('Contact', listing(f'{c.kind.title()}: {c.value}' for c in profile.contacts))
    experience = ''
    if profile.years_of_experience is not None:
        experience += f'<p>Total reported experience: <strong>{profile.years_of_experience} years</strong></p>'
    for entry in profile.experiences:
        experience += f'<article><h3>{esc(entry.title)}</h3>'
        experience += ''.join(f'<p>{esc(v)}</p>' for v in (entry.organization, entry.period, entry.description) if v is not None)
        experience += '</article>'
    if experience:
        section('Experience', experience)
    if profile.education:
        content = ''
        for entry in profile.education:
            content += f'<article><h3>{esc(entry.qualification)}</h3>'
            content += ''.join(f'<p>{esc(v)}</p>' for v in (entry.institution, entry.period) if v is not None)
            content += '</article>'
        section('Education and certifications', content)
    if profile.skills:
        section('Canonical skills', listing(profile.skills))
    if profile.unrecognized_skills:
        section('Other reported skills', '<p>Outside the classification vocabulary.</p>' + listing(profile.unrecognized_skills))
    titles = [PROFILES_REGISTRY[pid].title for pid in profile.accepted_profiles]
    section('Declared accepted profiles', listing(titles) if titles else '<p>No accepted profiles declared.</p>')
    name = esc(profile.name or 'Candidate profile')
    intro = ''.join(f'<p>{esc(v)}</p>' for v in (profile.summary, profile.location) if v is not None)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{name} | ResumeLens</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f1f5f7;color:#152c3a;font:16px/1.6 system-ui,sans-serif}}
main{{max-width:900px;margin:32px auto;background:white;padding:40px;border-top:8px solid #007d78}}
header{{border-bottom:1px solid #cbd5df;padding-bottom:20px}}h1{{font-size:2.3rem;margin:8px 0}}
h2{{font-size:1.25rem;color:#006f6b;margin-top:28px}}h3{{font-size:1rem;margin:12px 0 2px}}
p{{margin:6px 0;white-space:pre-wrap}}ul{{padding-left:24px}}li,h1,h3,p{{overflow-wrap:anywhere}}
article{{break-inside:avoid}}footer{{font-size:.85rem;color:#506575;border-top:1px solid #cbd5df;margin-top:28px;padding-top:16px}}
.brand{{letter-spacing:.15em;font-weight:700;font-size:.8rem;color:#006f6b}}
@media(max-width:600px){{main{{margin:0;padding:22px}}h1{{font-size:1.8rem}}}}
@media print{{body{{background:white}}main{{margin:0;padding:16px;max-width:none}}}}
</style></head><body><main><header><div class="brand">RESUMELENS / VALIDATED DSL</div>
<h1>{name}</h1>{intro}</header>{''.join(sections)}
<footer>Generated after textX syntax and domain validation. Validation does not verify personal facts
or independently rerun classification. In pipeline output, accepted profiles come from the four DFAs;
in an edited DSL, they are declarations. Missing information is omitted.</footer></main></body></html>'''
