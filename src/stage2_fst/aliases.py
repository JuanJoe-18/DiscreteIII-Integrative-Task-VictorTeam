"""Vocabulary of Stage 2: every spelling of a skill that must be turned into one canonical token.

The table is organised in *families* (languages, web, data, databases, ...). Each family is
compiled into its own transducer and the family transducers are merged into the alias
transducer used by the pipeline (see ``transducers.build_alias_transducer``).

A spelling is written the way a person would write it ("Node.js", "Power BI", "scikit learn").
Capitalisation, dots, hyphens, underscores, slashes and spaces are removed by the cleaning
transducer before the alias transducer reads the word, so it is enough to list one spelling for
each *different sequence of letters*: "Node.js", "NodeJS" and "node js" are the same entry.
"""

from typing import Dict, List

#: family name -> canonical token -> spellings that must be mapped to it.
ALIAS_FAMILIES: Dict[str, Dict[str, List[str]]] = {
    "LANGUAGES": {
        "JAVASCRIPT": ["JavaScript", "JS", "Java Script"],
        "TYPESCRIPT": ["TypeScript", "TS", "Type Script"],
        "PYTHON": ["Python", "Python3", "Py"],
        "JAVA": ["Java"],
        "CSHARP": ["C#", "CSharp", "C Sharp"],
        "CPP": ["C++", "CPP"],
        "GO": ["Go", "Golang"],
        "RUST": ["Rust"],
        "RUBY": ["Ruby"],
        "JULIA": ["Julia"],
        "R": ["R"],
        "PHP": ["PHP"],
        "KOTLIN": ["Kotlin"],
        "HTML": ["HTML", "HTML5"],
        "CSS": ["CSS", "CSS3"],
        "BASH": ["Bash"],
        "POWERSHELL": ["PowerShell", "Power Shell"],
    },
    "WEB": {
        "REACT": ["React", "React.js", "ReactJS"],
        "ANGULAR": ["Angular", "Angular.js", "AngularJS"],
        "VUE": ["Vue", "Vue.js", "VueJS"],
        "SVELTE": ["Svelte"],
        "NEXTJS": ["Next", "Next.js", "NextJS"],
        "NODE_JS": ["Node", "Node.js", "NodeJS"],
        "EXPRESS": ["Express", "Express.js", "ExpressJS"],
        "NESTJS": ["Nest", "Nest.js", "NestJS"],
        "DJANGO": ["Django"],
        "FLASK": ["Flask"],
        "FASTAPI": ["FastAPI", "Fast API"],
        "SPRING_BOOT": ["Spring", "Spring Boot", "SpringBoot", "Spring-Boot"],
        "REST": ["REST", "RESTful", "REST API", "REST APIs", "RESTful API", "RESTful APIs", "Rest API"],
        "GRAPHQL": ["GraphQL", "Graph QL"],
        "WEBSOCKET": ["WebSocket", "WebSockets", "Web Socket", "Web Sockets"],
    },
    "DATA": {
        "PANDAS": ["Pandas"],
        "NUMPY": ["NumPy"],
        "SCIPY": ["SciPy"],
        "SCIKIT_LEARN": ["Scikit-learn", "scikit learn", "scikit_learn", "sklearn", "sk-learn"],
        "TENSORFLOW": ["TensorFlow", "Tensor Flow", "TF"],
        "PYTORCH": ["PyTorch", "Py Torch"],
        "KERAS": ["Keras"],
        "XGBOOST": ["XGBoost"],
        "LIGHTGBM": ["LightGBM"],
        "CATBOOST": ["CatBoost"],
        "STATSMODELS": ["Statsmodels"],
        "MATPLOTLIB": ["Matplotlib"],
        "SEABORN": ["Seaborn"],
        "PLOTLY": ["Plotly"],
        "TABLEAU": ["Tableau"],
        "POWER_BI": ["Power BI", "PowerBI"],
    },
    "DATABASES": {
        "POSTGRESQL": ["Postgres", "PostgreSQL", "Postgre"],
        "MYSQL": ["MySQL"],
        "MARIADB": ["MariaDB"],
        "SQLITE": ["SQLite"],
        "SQL_SERVER": ["SQL Server", "SQLServer", "MS SQL Server"],
        "SQL": ["SQL"],
        "ORACLE": ["Oracle"],
        "MONGODB": ["Mongo", "MongoDB"],
        "REDIS": ["Redis"],
        "FIREBASE": ["Firebase"],
        "CASSANDRA": ["Cassandra"],
        "ELASTICSEARCH": ["Elasticsearch", "Elastic Search"],
    },
    "VERSION_CONTROL": {
        "GIT": ["Git"],
        "GITHUB": ["GitHub"],
        "GITLAB": ["GitLab"],
        "BITBUCKET": ["Bitbucket"],
        "SVN": ["SVN", "Subversion"],
    },
    "DEVOPS_CLOUD": {
        "DOCKER": ["Docker"],
        "KUBERNETES": ["Kubernetes", "K8s"],
        "PODMAN": ["Podman"],
        "HELM": ["Helm"],
        "AWS": ["AWS", "Amazon Web Services"],
        "AZURE": ["Azure"],
        "GCP": ["GCP", "Google Cloud", "Google Cloud Platform"],
        "TERRAFORM": ["Terraform"],
        "ANSIBLE": ["Ansible"],
        "JENKINS": ["Jenkins"],
        "GITHUB_ACTIONS": ["GitHub Actions", "GitHubActions"],
        "GITLAB_CI": ["GitLab CI", "GitLab CI/CD", "GitLabCI"],
        "ARGO_CD": ["Argo", "Argo CD", "ArgoCD"],
        "LINUX": ["Linux"],
    },
}

#: Canonical token produced for the experience of the candidate.
EXPERIENCE_TOKEN = "EXPERIENCE_PRESENT"


def all_canonical_tokens() -> List[str]:
    """Every canonical token that the alias transducer can produce."""
    return [token for family in ALIAS_FAMILIES.values() for token in family]
