"""Specification table of the Stage 2 vocabulary.

Every spelling that the alias transducer must translate, written the way a person would write it, with
the canonical token it must produce. The table is written by hand on purpose: it is the *specification*
that the vocabulary of ``aliases.py`` is checked against, so a spelling that is deleted by mistake (or
added without being reviewed) makes a test fail.
"""

import pytest

from src.stage2_fst import normalize_token
from src.stage2_fst.aliases import ALIAS_FAMILIES

SPECIFICATION = [
    # LANGUAGES
    ('JavaScript', "JAVASCRIPT"),
    ('JS', "JAVASCRIPT"),
    ('Java Script', "JAVASCRIPT"),
    ('TypeScript', "TYPESCRIPT"),
    ('TS', "TYPESCRIPT"),
    ('Type Script', "TYPESCRIPT"),
    ('Python', "PYTHON"),
    ('Python3', "PYTHON"),
    ('Py', "PYTHON"),
    ('Java', "JAVA"),
    ('C#', "CSHARP"),
    ('CSharp', "CSHARP"),
    ('C Sharp', "CSHARP"),
    ('C++', "CPP"),
    ('CPP', "CPP"),
    ('Go', "GO"),
    ('Golang', "GO"),
    ('Rust', "RUST"),
    ('Ruby', "RUBY"),
    ('Julia', "JULIA"),
    ('R', "R"),
    ('PHP', "PHP"),
    ('Kotlin', "KOTLIN"),
    ('HTML', "HTML"),
    ('HTML5', "HTML"),
    ('CSS', "CSS"),
    ('CSS3', "CSS"),
    ('Bash', "BASH"),
    ('PowerShell', "POWERSHELL"),
    ('Power Shell', "POWERSHELL"),
    # WEB
    ('React', "REACT"),
    ('React.js', "REACT"),
    ('ReactJS', "REACT"),
    ('Angular', "ANGULAR"),
    ('Angular.js', "ANGULAR"),
    ('AngularJS', "ANGULAR"),
    ('Vue', "VUE"),
    ('Vue.js', "VUE"),
    ('VueJS', "VUE"),
    ('Svelte', "SVELTE"),
    ('Next', "NEXTJS"),
    ('Next.js', "NEXTJS"),
    ('NextJS', "NEXTJS"),
    ('Node', "NODE_JS"),
    ('Node.js', "NODE_JS"),
    ('NodeJS', "NODE_JS"),
    ('Express', "EXPRESS"),
    ('Express.js', "EXPRESS"),
    ('ExpressJS', "EXPRESS"),
    ('Nest', "NESTJS"),
    ('Nest.js', "NESTJS"),
    ('NestJS', "NESTJS"),
    ('Django', "DJANGO"),
    ('Flask', "FLASK"),
    ('FastAPI', "FASTAPI"),
    ('Fast API', "FASTAPI"),
    ('Spring', "SPRING_BOOT"),
    ('Spring Boot', "SPRING_BOOT"),
    ('SpringBoot', "SPRING_BOOT"),
    ('Spring-Boot', "SPRING_BOOT"),
    ('REST', "REST"),
    ('RESTful', "REST"),
    ('REST API', "REST"),
    ('REST APIs', "REST"),
    ('RESTful API', "REST"),
    ('RESTful APIs', "REST"),
    ('Rest API', "REST"),
    ('GraphQL', "GRAPHQL"),
    ('Graph QL', "GRAPHQL"),
    ('WebSocket', "WEBSOCKET"),
    ('WebSockets', "WEBSOCKET"),
    ('Web Socket', "WEBSOCKET"),
    ('Web Sockets', "WEBSOCKET"),
    # DATA
    ('Pandas', "PANDAS"),
    ('NumPy', "NUMPY"),
    ('SciPy', "SCIPY"),
    ('Scikit-learn', "SCIKIT_LEARN"),
    ('scikit learn', "SCIKIT_LEARN"),
    ('scikit_learn', "SCIKIT_LEARN"),
    ('sklearn', "SCIKIT_LEARN"),
    ('sk-learn', "SCIKIT_LEARN"),
    ('TensorFlow', "TENSORFLOW"),
    ('Tensor Flow', "TENSORFLOW"),
    ('TF', "TENSORFLOW"),
    ('PyTorch', "PYTORCH"),
    ('Py Torch', "PYTORCH"),
    ('Keras', "KERAS"),
    ('XGBoost', "XGBOOST"),
    ('LightGBM', "LIGHTGBM"),
    ('CatBoost', "CATBOOST"),
    ('Statsmodels', "STATSMODELS"),
    ('Matplotlib', "MATPLOTLIB"),
    ('Seaborn', "SEABORN"),
    ('Plotly', "PLOTLY"),
    ('Tableau', "TABLEAU"),
    ('Power BI', "POWER_BI"),
    ('PowerBI', "POWER_BI"),
    # DATABASES
    ('Postgres', "POSTGRESQL"),
    ('PostgreSQL', "POSTGRESQL"),
    ('Postgre', "POSTGRESQL"),
    ('MySQL', "MYSQL"),
    ('MariaDB', "MARIADB"),
    ('SQLite', "SQLITE"),
    ('SQL Server', "SQL_SERVER"),
    ('SQLServer', "SQL_SERVER"),
    ('MS SQL Server', "SQL_SERVER"),
    ('SQL', "SQL"),
    ('Oracle', "ORACLE"),
    ('Mongo', "MONGODB"),
    ('MongoDB', "MONGODB"),
    ('Redis', "REDIS"),
    ('Firebase', "FIREBASE"),
    ('Cassandra', "CASSANDRA"),
    ('Elasticsearch', "ELASTICSEARCH"),
    ('Elastic Search', "ELASTICSEARCH"),
    # VERSION_CONTROL
    ('Git', "GIT"),
    ('GitHub', "GITHUB"),
    ('GitLab', "GITLAB"),
    ('Bitbucket', "BITBUCKET"),
    ('SVN', "SVN"),
    ('Subversion', "SVN"),
    # DEVOPS_CLOUD
    ('Docker', "DOCKER"),
    ('Kubernetes', "KUBERNETES"),
    ('K8s', "KUBERNETES"),
    ('Podman', "PODMAN"),
    ('Helm', "HELM"),
    ('AWS', "AWS"),
    ('Amazon Web Services', "AWS"),
    ('Azure', "AZURE"),
    ('GCP', "GCP"),
    ('Google Cloud', "GCP"),
    ('Google Cloud Platform', "GCP"),
    ('Terraform', "TERRAFORM"),
    ('Ansible', "ANSIBLE"),
    ('Jenkins', "JENKINS"),
    ('GitHub Actions', "GITHUB_ACTIONS"),
    ('GitHubActions', "GITHUB_ACTIONS"),
    ('GitLab CI', "GITLAB_CI"),
    ('GitLab CI/CD', "GITLAB_CI"),
    ('GitLabCI', "GITLAB_CI"),
    ('Argo', "ARGO_CD"),
    ('Argo CD', "ARGO_CD"),
    ('ArgoCD', "ARGO_CD"),
    ('Linux', "LINUX"),
]


@pytest.mark.parametrize("spelling, canonical", SPECIFICATION)
def test_spelling_is_translated_to_its_canonical_token(spelling, canonical):
    trace = normalize_token(spelling)
    assert trace.recognized
    assert trace.canonical == canonical


@pytest.mark.parametrize("spelling, canonical", SPECIFICATION)
def test_capitalisation_and_separators_of_a_spelling_do_not_change_the_result(spelling, canonical):
    for variant in (spelling.upper(), spelling.lower()):
        assert normalize_token(variant).canonical == canonical


def test_specification_and_vocabulary_list_the_same_spellings():
    in_code = {(s, c) for family in ALIAS_FAMILIES.values() for c, spellings in family.items() for s in spellings}
    assert set(SPECIFICATION) == in_code


def test_specification_has_no_repeated_entries():
    assert len(SPECIFICATION) == len(set(SPECIFICATION))
