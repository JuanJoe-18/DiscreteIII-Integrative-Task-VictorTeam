"""Stage 1 <-> Stage 2/3 contract tests.

Stage 3 only accepts the canonical tokens of ``profiles.py``. Stage 2 can only produce them if
Stage 1 is able to extract at least one surface form of each one. This file makes that dependency
explicit: if somebody adds a skill to a profile, this test fails until Stage 1 can extract it.
"""

import pytest

from src.stage1_regex import extract_qualifications
from src.stage3_classifier.profiles import PROFILES_REGISTRY

# Stage 2 creates this symbol from the years reported by Stage 1; it is not a skill written in the text.
EXPERIENCE_SYMBOL = "EXPERIENCE_PRESENT"

# One natural way of writing each canonical token of the four profiles.
SURFACE_FORMS = {
    # languages and markup
    "JAVASCRIPT": "JavaScript", "TYPESCRIPT": "TypeScript", "HTML": "HTML5", "CSS": "CSS3",
    "PYTHON": "Python", "JAVA": "Java", "CSHARP": "C#", "GO": "Go", "R": "R", "JULIA": "Julia",
    "BASH": "Bash", "POWERSHELL": "PowerShell",
    # web frameworks
    "REACT": "React.js", "ANGULAR": "Angular", "VUE": "Vue.js", "SVELTE": "Svelte", "NEXTJS": "Next.js",
    "NODE_JS": "NodeJS", "EXPRESS": "Express.js", "DJANGO": "Django", "SPRING_BOOT": "Spring Boot",
    "FASTAPI": "FastAPI", "NESTJS": "NestJS",
    # APIs
    "REST": "REST API", "GRAPHQL": "GraphQL", "WEBSOCKET": "WebSockets",
    # databases
    "POSTGRESQL": "Postgres", "MYSQL": "MySQL", "SQL": "SQL", "SQLITE": "SQLite", "ORACLE": "Oracle",
    "MONGODB": "MongoDB", "REDIS": "Redis", "FIREBASE": "Firebase",
    # data / ML
    "PANDAS": "Pandas", "NUMPY": "NumPy", "SCIPY": "SciPy", "SCIKIT_LEARN": "Scikit-learn",
    "TENSORFLOW": "Tensor Flow", "PYTORCH": "Py Torch", "KERAS": "Keras", "XGBOOST": "XGBoost",
    "LIGHTGBM": "LightGBM", "CATBOOST": "CatBoost", "STATSMODELS": "Statsmodels",
    "MATPLOTLIB": "Matplotlib", "SEABORN": "Seaborn", "PLOTLY": "Plotly", "TABLEAU": "Tableau",
    "POWER_BI": "Power BI",
    # version control
    "GIT": "Git", "GITHUB": "GitHub", "GITLAB": "GitLab",
    # DevOps / cloud
    "DOCKER": "Docker", "KUBERNETES": "K8s", "AWS": "Amazon Web Services", "AZURE": "Azure", "GCP": "GCP",
    "LINUX": "Linux", "GITHUB_ACTIONS": "GitHub Actions", "JENKINS": "Jenkins", "GITLAB_CI": "GitLab CI",
    "ARGO_CD": "Argo CD", "PODMAN": "Podman", "HELM": "Helm", "TERRAFORM": "Terraform", "ANSIBLE": "Ansible",
}


def canonical_skills():
    tokens = set()
    for profile in PROFILES_REGISTRY.values():
        for category in profile.canonical_categories:
            tokens.update(skill for skill in category.skills if skill != EXPERIENCE_SYMBOL)
    return tokens


def test_every_canonical_skill_has_a_documented_surface_form():
    missing = canonical_skills() - set(SURFACE_FORMS)
    assert not missing, f"add a surface form for: {sorted(missing)}"


@pytest.mark.parametrize("canonical, form", sorted(SURFACE_FORMS.items()))
def test_stage1_can_extract_a_surface_form_of_every_canonical_skill(canonical, form):
    # "Technical Skills:" also enables the context-sensitive words (Go, R, Julia, Oracle ...).
    result = extract_qualifications(f"Technical Skills: {form}")
    assert result.raw_tokens == [form], f"{canonical}: expected {form!r}, got {result.raw_tokens}"