"""Stage 2: Qualification Normalization and Canonical Sorting using FST.

This module defines the interface contract for Integrante 1.
It transforms raw extracted qualification variations (e.g. 'React.js', 'JS', 'Postgres')
into canonical uppercase tokens (e.g. 'REACT', 'JAVASCRIPT', 'POSTGRESQL')
and sorts them into the canonical order required by the target professional profile.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.stage3_classifier.profiles import PROFILES_REGISTRY


@dataclass
class NormalizationResult:
    """Represents the output of Stage 2 normalization."""
    normalized_tokens: List[str]
    transformations_applied: Dict[str, str] = field(default_factory=dict)
    unrecognized_tokens: List[str] = field(default_factory=list)


# Reference dictionary for qualification aliases (Mock FST transducer mapping)
# Integrante 1 will replace/augment this with pyformlang FiniteStateTransducer models
_SYNONYM_DICTIONARY: Dict[str, str] = {
    # Full Stack & Web
    "JS": "JAVASCRIPT",
    "JAVASCRIPT": "JAVASCRIPT",
    "TS": "TYPESCRIPT",
    "TYPESCRIPT": "TYPESCRIPT",
    "HTML": "HTML",
    "HTML5": "HTML",
    "CSS": "CSS",
    "CSS3": "CSS",
    "REACT": "REACT",
    "REACT.JS": "REACT",
    "REACTJS": "REACT",
    "ANGULAR": "ANGULAR",
    "ANGULAR.JS": "ANGULAR",
    "ANGULARJS": "ANGULAR",
    "VUE": "VUE",
    "VUE.JS": "VUE",
    "VUEJS": "VUE",
    "NEXT": "NEXTJS",
    "NEXT.JS": "NEXTJS",
    "NEXTJS": "NEXTJS",
    "SVELTE": "SVELTE",
    "NODE": "NODE_JS",
    "NODEJS": "NODE_JS",
    "NODE.JS": "NODE_JS",
    "EXPRESS": "EXPRESS",
    "EXPRESS.JS": "EXPRESS",
    "EXPRESSJS": "EXPRESS",
    "SPRING": "SPRING_BOOT",
    "SPRINGBOOT": "SPRING_BOOT",
    "SPRING BOOT": "SPRING_BOOT",
    "SPRING_BOOT": "SPRING_BOOT",
    "DJANGO": "DJANGO",
    "FASTAPI": "FASTAPI",
    "NEST": "NESTJS",
    "NESTJS": "NESTJS",
    "POSTGRES": "POSTGRESQL",
    "POSTGRESQL": "POSTGRESQL",
    "MONGO": "MONGODB",
    "MONGODB": "MONGODB",
    "MYSQL": "MYSQL",
    "REDIS": "REDIS",
    "SQLITE": "SQLITE",
    "SQL": "SQL",
    "REST": "REST",
    "REST API": "REST",
    "GRAPHQL": "GRAPHQL",
    "WEBSOCKET": "WEBSOCKET",
    "WEBSOCKETS": "WEBSOCKET",
    "GIT": "GIT",
    "GITHUB": "GITHUB",
    "GITLAB": "GITLAB",
    "DOCKER": "DOCKER",
    "K8S": "KUBERNETES",
    "KUBERNETES": "KUBERNETES",
    "AWS": "AWS",
    "AMAZON WEB SERVICES": "AWS",
    # Machine Learning & Data Science
    "PYTHON": "PYTHON",
    "PY": "PYTHON",
    "R": "R",
    "JULIA": "JULIA",
    "PANDAS": "PANDAS",
    "NUMPY": "NUMPY",
    "SCIPY": "SCIPY",
    "SKLEARN": "SCIKIT_LEARN",
    "SCIKIT-LEARN": "SCIKIT_LEARN",
    "SCIKIT LEARN": "SCIKIT_LEARN",
    "SCIKIT_LEARN": "SCIKIT_LEARN",
    "TENSOR FLOW": "TENSORFLOW",
    "TENSORFLOW": "TENSORFLOW",
    "TF": "TENSORFLOW",
    "PY TORCH": "PYTORCH",
    "PYTORCH": "PYTORCH",
    "KERAS": "KERAS",
    "XGBOOST": "XGBOOST",
    "LIGHTGBM": "LIGHTGBM",
    "CATBOOST": "CATBOOST",
    "STATSMODELS": "STATSMODELS",
    "MATPLOTLIB": "MATPLOTLIB",
    "SEABORN": "SEABORN",
    "PLOTLY": "PLOTLY",
    "TABLEAU": "TABLEAU",
    "POWERBI": "POWER_BI",
    "POWER BI": "POWER_BI",
    "POWER_BI": "POWER_BI",
    # DevOps
    "BASH": "BASH",
    "LINUX": "LINUX",
    "POWERSHELL": "POWERSHELL",
    "JENKINS": "JENKINS",
    "GITLAB CI": "GITLAB_CI",
    "GITLAB_CI": "GITLAB_CI",
    "GITHUB ACTIONS": "GITHUB_ACTIONS",
    "GITHUB_ACTIONS": "GITHUB_ACTIONS",
    "ARGO": "ARGO_CD",
    "ARGO CD": "ARGO_CD",
    "ARGO_CD": "ARGO_CD",
    "TERRAFORM": "TERRAFORM",
    "ANSIBLE": "ANSIBLE",
    "AZURE": "AZURE",
    "GCP": "GCP",
    "GOOGLE CLOUD": "GCP",
    "PODMAN": "PODMAN",
    "HELM": "HELM",
}


def normalize_qualifications(raw_tokens: List[str]) -> NormalizationResult:
    """ETAPA 2A (A cargo de Integrante 1):
    
    Transforma representaciones textuales equivalentes hacia su forma canónica
    en mayúsculas utilizando el modelo FST (Transductor de Estados Finitos).
    """
    normalized: List[str] = []
    transformations: Dict[str, str] = {}
    unrecognized: List[str] = []

    for token in raw_tokens:
        clean = token.strip()
        if not clean:
            continue

        # Keep raw numeric experience digits directly (e.g. '1'..'9')
        if clean.isdigit():
            normalized.append(clean)
            continue

        key = clean.upper()
        if key in _SYNONYM_DICTIONARY:
            canonical = _SYNONYM_DICTIONARY[key]
            normalized.append(canonical)
            if clean != canonical:
                transformations[clean] = canonical
        else:
            # Fallback: uppercase string
            canonical = key.replace("-", "_").replace(" ", "_")
            normalized.append(canonical)
            unrecognized.append(clean)

    return NormalizationResult(
        normalized_tokens=normalized,
        transformations_applied=transformations,
        unrecognized_tokens=unrecognized,
    )


def sort_to_canonical_order(
    normalized_tokens: List[str],
    profile_id: str = "full_stack",
) -> List[str]:
    """ETAPA 2B (A cargo de Integrante 1):
    
    Ordena las calificaciones normalizadas en el orden canónico estricto requerido
    por el autómata de clasificación (Etapa 3) del perfil seleccionado.
    
    Por ejemplo, para Full Stack Developer:
    Experience -> Frontend -> Backend -> Database -> DevOps -> Version Control
    """
    if profile_id not in PROFILES_REGISTRY:
        return normalized_tokens

    profile = PROFILES_REGISTRY[profile_id]

    # Filter out numeric experience tokens if this profile does not support an EXPERIENCE category
    has_experience_cat = any(cat.name == "EXPERIENCE" for cat in profile.canonical_categories)
    if not has_experience_cat:
        normalized_tokens = [t for t in normalized_tokens if not t.isdigit() and t != r"\d"]

    # Build category rank mapping
    category_order = {cat.name: idx for idx, cat in enumerate(profile.canonical_categories)}
    skill_to_cat = {
        skill: cat.name
        for cat in profile.canonical_categories
        for skill in cat.skills
    }

    def token_sort_key(token: str) -> tuple[int, int]:
        # Experience digits get lowest rank (-1)
        if token.isdigit() or token == r"\d":
            return (-1, 0)
        cat_name = skill_to_cat.get(token)
        if cat_name and cat_name in category_order:
            return (category_order[cat_name], 0)
        return (999, 0)  # Unrecognized tokens sent to the end

    # Stable sort according to profile canonical hierarchy
    return sorted(normalized_tokens, key=token_sort_key)


def normalize_and_sort(
    raw_tokens: List[str],
    profile_id: str = "full_stack",
) -> NormalizationResult:
    """ETAPA 2 COMPLETA (A cargo de Integrante 1):
    
    Pipeline de transducción FST: normaliza las variaciones y ordena canónicamente
    los tokens resultantes para que sean válidos en el autómata de la Etapa 3.
    """
    result = normalize_qualifications(raw_tokens)
    sorted_tokens = sort_to_canonical_order(result.normalized_tokens, profile_id)
    result.normalized_tokens = sorted_tokens
    return result
