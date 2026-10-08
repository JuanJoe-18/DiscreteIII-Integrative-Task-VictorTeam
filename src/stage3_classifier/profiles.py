"""Definition of professional profiles, canonical categories, and alphabets for ResumeLens.

This module defines the 4 supported profiles (2 reference profiles and 2 custom profiles),
the categories of qualifications required for each profile, their canonical sequence,
and the authorized technical skills (alphabet symbols).
"""

from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass(frozen=True)
class Category:
    """Represents a qualification category within a professional profile."""
    name: str
    description: str
    skills: Set[str]


@dataclass(frozen=True)
class ProfileDefinition:
    """Represents a professional profile specification."""
    profile_id: str
    title: str
    domain: str
    canonical_categories: List[Category]

    @property
    def alphabet(self) -> Set[str]:
        """Returns the complete input alphabet Sigma for this profile."""
        all_skills: Set[str] = set()
        for cat in self.canonical_categories:
            all_skills.update(cat.skills)
        return all_skills

    def get_category_for_skill(self, skill: str) -> str | None:
        """Finds the category name that contains the given skill."""
        for cat in self.canonical_categories:
            if skill in cat.skills:
                return cat.name
        return None


# ============================================================================
# Profile 1: Full Stack Developer (Reference Profile 1 - Software Engineering)
# Canonical Order: Frontend -> Backend -> Database -> Version Control
# ============================================================================
FULL_STACK_PROFILE = ProfileDefinition(
    profile_id="full_stack",
    title="Full Stack Developer",
    domain="Software Engineering",
    canonical_categories=[
        Category(
            name="EXPERIENCE",
            description="Años de experiencia profesional o rango numérico (\\d)",
            skills={"\\d", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
        ),
        Category(
            name="FE_LANGUAGE",
            description="Lenguajes de programación del lado del cliente",
            skills={"JAVASCRIPT", "TYPESCRIPT", "HTML", "CSS"},
        ),
        Category(
            name="FE_FRAMEWORK",
            description="Frameworks y librerías de interfaz de usuario",
            skills={"REACT", "ANGULAR", "VUE", "SVELTE", "NEXTJS"},
        ),
        Category(
            name="BE_LANGUAGE",
            description="Lenguajes y entornos de ejecución del backend",
            skills={"NODE_JS", "PYTHON", "JAVA", "CSHARP", "GO"},
        ),
        Category(
            name="BE_FRAMEWORK",
            description="Frameworks del lado del servidor",
            skills={"EXPRESS", "DJANGO", "SPRING_BOOT", "FASTAPI", "NESTJS"},
        ),
        Category(
            name="API_COMMUNICATION",
            description="Protocolos y arquitectura de APIs",
            skills={"REST", "GRAPHQL", "WEBSOCKET"},
        ),
        Category(
            name="DATABASE_SQL",
            description="Bases de datos relacionales SQL",
            skills={"POSTGRESQL", "MYSQL", "SQL", "SQLITE", "ORACLE"},
        ),
        Category(
            name="DATABASE_NOSQL",
            description="Bases de datos NoSQL y almacenamiento en memoria",
            skills={"MONGODB", "REDIS", "FIREBASE"},
        ),
        Category(
            name="DEVOPS_CLOUD",
            description="Contenedores y despliegue en la nube",
            skills={"DOCKER", "KUBERNETES", "AWS"},
        ),
        Category(
            name="VERSION_CONTROL",
            description="Control de versiones y repositorios colaborativos",
            skills={"GIT", "GITHUB", "GITLAB"},
        ),
    ],
)

# ============================================================================
# Profile 2: Machine Learning Engineer (Reference Profile 2 - AI / Data)
# Canonical Order: Language -> Data Processing -> ML Framework -> Database -> Version Control
# ============================================================================
MACHINE_LEARNING_PROFILE = ProfileDefinition(
    profile_id="machine_learning",
    title="Machine Learning Engineer",
    domain="AI / Data",
    canonical_categories=[
        Category(
            name="CORE_LANGUAGE",
            description="Primary data science and scientific programming language",
            skills={"PYTHON", "R", "JULIA"},
        ),
        Category(
            name="DATA_PROCESSING",
            description="Numerical computing and tabular data manipulation",
            skills={"PANDAS", "NUMPY", "SCIPY"},
        ),
        Category(
            name="ML_FRAMEWORKS",
            description="Machine learning and deep learning modeling frameworks",
            skills={"SCIKIT_LEARN", "TENSORFLOW", "PYTORCH", "KERAS", "XGBOOST"},
        ),
        Category(
            name="DATABASE",
            description="Relational data querying and extraction",
            skills={"SQL", "POSTGRESQL", "MYSQL"},
        ),
        Category(
            name="VERSION_CONTROL",
            description="Version control and collaboration systems",
            skills={"GIT", "GITHUB", "GITLAB"},
        ),
    ],
)

# ============================================================================
# Profile 3: Cloud & DevOps Engineer (Custom Profile 1 - Software Engineering)
# Canonical Order: Scripting -> CI/CD -> Containers -> Cloud/IaC -> Version Control
# ============================================================================
DEVOPS_PROFILE = ProfileDefinition(
    profile_id="cloud_devops",
    title="Cloud & DevOps Engineer",
    domain="Software Engineering",
    canonical_categories=[
        Category(
            name="SCRIPTING_OS",
            description="Automation scripting and OS administration",
            skills={"BASH", "LINUX", "PYTHON", "POWERSHELL"},
        ),
        Category(
            name="CICD",
            description="Continuous integration and continuous deployment pipelines",
            skills={"GITHUB_ACTIONS", "JENKINS", "GITLAB_CI", "ARGO_CD"},
        ),
        Category(
            name="CONTAINERS_ORCHESTRATION",
            description="Containerization and cluster orchestration engines",
            skills={"DOCKER", "KUBERNETES", "PODMAN", "HELM"},
        ),
        Category(
            name="CLOUD_IAC",
            description="Cloud providers and Infrastructure as Code",
            skills={"AWS", "AZURE", "GCP", "TERRAFORM", "ANSIBLE"},
        ),
        Category(
            name="VERSION_CONTROL",
            description="Version control systems and repository collaboration",
            skills={"GIT", "GITHUB", "GITLAB"},
        ),
    ],
)

# ============================================================================
# Profile 4: Data Scientist (Custom Profile 2 - AI / Data)
# Canonical Order: Language -> Data Analysis/Stats -> Data Visualization -> Machine Learning -> Version Control
# ============================================================================
DATA_SCIENTIST_PROFILE = ProfileDefinition(
    profile_id="data_scientist",
    title="Data Scientist",
    domain="AI / Data",
    canonical_categories=[
        Category(
            name="DATA_LANGUAGE",
            description="Statistical and analytical programming languages",
            skills={"PYTHON", "R", "SQL", "JULIA"},
        ),
        Category(
            name="DATA_ANALYSIS_STATS",
            description="Exploratory data analysis, numerical computing, and statistics",
            skills={"PANDAS", "NUMPY", "SCIPY", "STATSMODELS"},
        ),
        Category(
            name="DATA_VISUALIZATION",
            description="Data visualization, storytelling, and business intelligence",
            skills={"MATPLOTLIB", "SEABORN", "PLOTLY", "TABLEAU", "POWER_BI"},
        ),
        Category(
            name="MACHINE_LEARNING",
            description="Applied predictive modeling and machine learning algorithms",
            skills={"SCIKIT_LEARN", "XGBOOST", "LIGHTGBM", "CATBOOST"},
        ),
        Category(
            name="VERSION_CONTROL",
            description="Source versioning, experiment tracking, and collaboration",
            skills={"GIT", "GITHUB", "GITLAB"},
        ),
    ],
)

# Registry of all 4 profiles
PROFILES_REGISTRY: Dict[str, ProfileDefinition] = {
    FULL_STACK_PROFILE.profile_id: FULL_STACK_PROFILE,
    MACHINE_LEARNING_PROFILE.profile_id: MACHINE_LEARNING_PROFILE,
    DEVOPS_PROFILE.profile_id: DEVOPS_PROFILE,
    DATA_SCIENTIST_PROFILE.profile_id: DATA_SCIENTIST_PROFILE,
}
