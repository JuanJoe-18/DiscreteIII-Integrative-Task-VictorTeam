"""Catalog of the regular expressions used by Stage 1.

``expressions.py`` holds the regular expressions themselves, as plain raw strings
(``EMAIL_PATTERN = r"..."``). This file wraps each one in a ``RegexSpec`` together with its
documentation: the language it recognises, strings it must accept and strings it must reject.
The extractor (``extractor.py``) is a generic engine that simply runs the whole catalog, so
adding a new type of information means adding one entry to ``DEFAULT_SPECS`` - and nothing else.

Design principles
-----------------
1. **Stage 1 does not decide equivalences.** ``React``, ``ReactJS`` and ``React.js``
   are all *recognised* (they are surface forms of one technology), but the
   unification into ``REACT`` is the job of the transducers of Stage 2.
2. **Word boundaries for technologies.** A technology is only recognised when it is
   not glued to other word characters (``JS`` is recognised in ``JS, React`` but not
   inside ``JSON``). See ``_LB`` and ``_RB`` in ``expressions.py``.
3. **Ambiguous words are context-sensitive.** Words that are also common English words
   or names (``R``, ``Go``, ``Rust``, ``Julia``, ``Node``, ``Express``, ``Next``,
   ``Spring``, ``Oracle`` ...) are only recognised inside the *Skills* section,
   where a bare ``Go`` can only mean the language. Their unambiguous forms
   (``Node.js``, ``Express.js``, ``Spring Boot``) are recognised anywhere.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple

from src.stage1_regex.expressions import (
    EMAIL_PATTERN,
    PHONE_PATTERN,
    LINKEDIN_URL_PATTERN,
    GITHUB_URL_PATTERN,
    CANDIDATE_NAME_PATTERN,
    YEARS_OF_EXPERIENCE_PATTERN,
    JOB_TITLE_PATTERN,
    DEGREE_PATTERN,
    CERTIFICATION_PATTERN,
    PROGRAMMING_LANGUAGE_PATTERN,
    PROGRAMMING_LANGUAGE_AMBIGUOUS_PATTERN,
    WEB_FRAMEWORK_PATTERN,
    WEB_FRAMEWORK_AMBIGUOUS_PATTERN,
    DATA_ML_LIBRARY_PATTERN,
    DATABASE_PATTERN,
    DATABASE_AMBIGUOUS_PATTERN,
    API_PROTOCOL_PATTERN,
    VERSION_CONTROL_PATTERN,
    DEVOPS_CLOUD_TOOL_PATTERN,
)
from src.stage1_regex.models import Category, RegexSpec, Scope

# --------------------------------------------------------------------------- #
# Contact information                                                          #
# --------------------------------------------------------------------------- #

EMAIL = RegexSpec(
    name="EMAIL",
    category=Category.CONTACT,
    pattern=EMAIL_PATTERN,
    description=(
        "A local part of word characters, dots, plus signs or hyphens, an '@', and a "
        "domain made of at least two dot-separated labels of letters, digits or hyphens."
    ),
    accepts=("wednesday.addams@example.com", "juan_perez+cv@mail.icesi.edu.co"),
    rejects=("user@localhost", "@example.com", "user@.com", "user name@example.com"),
    techniques=("character sets", "quantifiers", "non-capturing group", "negative lookbehind/lookahead"),
    rationale=(
        "At least one dot in the domain avoids matching '@' mentions such as 'user@localhost'. "
        "A trailing sentence dot is not swallowed because a label must contain a letter or digit."
    ),
)

PHONE = RegexSpec(
    name="PHONE",
    category=Category.CONTACT,
    pattern=PHONE_PATTERN,
    description=(
        "A 10-digit phone number written as 3-3-4 digits, optionally separated by spaces or "
        "hyphens, optionally with the area code in parentheses and an international prefix "
        "'+' followed by 1 to 3 digits."
    ),
    accepts=("304-555-1234", "(304) 555-1234", "+57 300 123 4567", "3001234567"),
    rejects=("12345", "2019-2023", "555-1234", "+57 300 123 45"),
    techniques=("optional groups", "bounded quantifiers {n,m}", "negative lookbehind/lookahead"),
    rationale=(
        "Requiring exactly 10 digits keeps year ranges such as '2019-2023' and short numbers out. "
        "The negative lookahead (?!\\d) prevents matching the first 10 digits of a longer number."
    ),
)

LINKEDIN_URL = RegexSpec(
    name="LINKEDIN_URL",
    category=Category.CONTACT,
    pattern=LINKEDIN_URL_PATTERN,
    flags=re.IGNORECASE,
    description=(
        "A LinkedIn profile address: optional 'http(s)://' and 'www.', the host 'linkedin.com', "
        "the path '/in/' and a user handle of word characters, '%' or hyphens, with an optional "
        "final slash."
    ),
    accepts=("linkedin.com/in/wednesday-addams", "https://www.linkedin.com/in/wadd/"),
    rejects=("linkedin.com", "linkedin.com/company/nevermore", "notlinkedin.com/in/x"),
    techniques=("optional groups", "escaping literals", "IGNORECASE flag"),
)

GITHUB_URL = RegexSpec(
    name="GITHUB_URL",
    category=Category.CONTACT,
    pattern=GITHUB_URL_PATTERN,
    flags=re.IGNORECASE,
    description=(
        "A GitHub profile or repository address: optional scheme and 'www.', the host "
        "'github.com', a user name and, optionally, a repository name."
    ),
    accepts=("github.com/wednesday", "https://github.com/wednesday/nevermore-notes"),
    rejects=("github.com", "gitlab.com/wednesday"),
    techniques=("optional groups", "escaping literals", "IGNORECASE flag"),
)

# --------------------------------------------------------------------------- #
# Identity and professional experience                                         #
# --------------------------------------------------------------------------- #


CANDIDATE_NAME = RegexSpec(
    name="CANDIDATE_NAME",
    category=Category.IDENTITY,
    pattern=CANDIDATE_NAME_PATTERN,
    group=1,
    description=(
        "The beginning of the document: two to four consecutive words on the same line, each one "
        "capitalised (or all upper case), allowing accents, apostrophes and hyphens ('Jean-Luc', "
        "\"O'Brien\"), and not being a typical heading word (Resume, Skills, Developer ...)."
    ),
    accepts=("Wednesday Addams", "Mary Jane Watson", "JUAN PÉREZ", "Jean-Luc Picard", "Conan O'Brien"),
    rejects=("wednesday addams", "Wednesday", "Curriculum Vitae", "Full Stack Developer", "Resume"),
    techniques=("anchor \\A", "capturing group", "negative lookahead", "scoped flag (?i:...)"),
    rationale=(
        "Resumes start with the candidate name; anchoring at \\A avoids guessing names elsewhere. "
        "The group keeps only the words, and the lookahead stops the name from swallowing the next "
        "heading when the whole resume is written on one line."
    ),
)


YEARS_OF_EXPERIENCE = RegexSpec(
    name="YEARS_OF_EXPERIENCE",
    category=Category.EXPERIENCE,
    pattern=YEARS_OF_EXPERIENCE_PATTERN,
    flags=re.IGNORECASE,
    group=1,
    description=(
        "A quantity of years: a number from 0 to 49 (digits) or a number word from 'one' to "
        "'twelve' (English) or 'uno' to 'doce' (Spanish), an optional '+', optional spaces or a hyphen, and the unit 'year(s)', 'yr(s)' "
        "or the Spanish 'año(s)'. Only the quantity is kept."
    ),
    accepts=("3 years", "10+ years", "5-year", "two years", "7 años", "cinco años"),
    rejects=("50 years", "years", "2020 years", "3 yearbooks"),
    techniques=("alternation for numeric range", "capturing group", "optional quantifier", "negative lookbehind"),
    rationale=(
        "The range 0-49 is built by alternation ([1-4]\\d | 0?\\d), "
        "so '10 years' is accepted but '2020 years' or '99 years' are not coherent and are "
        "rejected. Decimals ('1.5 years') are intentionally not supported."
    ),
)

JOB_TITLE = RegexSpec(
    name="JOB_TITLE",
    category=Category.EXPERIENCE,
    pattern=JOB_TITLE_PATTERN,
    flags=re.IGNORECASE,
    description=(
        "A job title: an optional seniority word (Senior, Junior, Lead, Principal), a domain "
        "(Full Stack, Front End, Back End, Web, Software, Machine Learning, Data, DevOps, Cloud, AI), "
        "an optional 'Application' and a role (Developer, Engineer, Scientist, Analyst)."
    ),
    accepts=("Web Application Developer", "Senior Full Stack Developer", "Machine Learning Engineer", "data scientist"),
    rejects=("Developer", "Web", "Teacher Assistant", "Dataset Engineer"),
    techniques=("optional groups", "alternation", "IGNORECASE flag"),
)

# --------------------------------------------------------------------------- #
# Academic qualifications                                                      #
# --------------------------------------------------------------------------- #

DEGREE = RegexSpec(
    name="DEGREE",
    category=Category.EDUCATION,
    pattern=DEGREE_PATTERN,
    description=(
        "An academic degree: 'Bachelor/Master [\\'s] [degree] of|in <Field>' (the field being 1-4 "
        "capitalised words, optionally followed by a second 'in|of <Field>'), an abbreviation or "
        "doctorate (BSc, MSc, PhD, Doctorate ...) optionally followed by its field, or the Spanish "
        "'Ingeniería|Maestría de|en <Field>'."
    ),
    accepts=(
        "Bachelor of Science in Computer Science",
        "Master's in Data Science",
        "PhD in Physics",
        "B.Sc. in Software Engineering",
        "Ingeniería de Sistemas",
        "Maestría en Ciencia de Datos",
    ),
    rejects=("Scrum Master", "Master the art", "bachelor party", "Doctor"),
    techniques=("scoped flag (?i:...)", "alternation", "optional groups", "bounded quantifier {0,3}", "negative lookbehind/lookahead"),
    rationale=(
        "Words like 'Master' are ambiguous ('Scrum Master'), so Bachelor/Master are only accepted "
        "when followed by 'of' or 'in'. Scoped flags make the keywords case-insensitive while the "
        "field of study still has to start with a capital letter."
    ),
)

CERTIFICATION = RegexSpec(
    name="CERTIFICATION",
    category=Category.EDUCATION,
    pattern=CERTIFICATION_PATTERN,
    description=(
        "A professional certification: either '<AWS|Azure|GCP|Google Cloud> Certified <Title>' or "
        "'Certified <Title>', where the title is a sequence of capitalised words on the same line."
    ),
    accepts=("AWS Certified Solutions Architect", "Certified Kubernetes Administrator"),
    rejects=("Certified", "certified developer", "Certified engineer"),
    techniques=("alternation", "bounded quantifier {n,m}", "horizontal whitespace only"),
)

# --------------------------------------------------------------------------- #
# Programming languages                                                        #
# --------------------------------------------------------------------------- #

PROGRAMMING_LANGUAGE = RegexSpec(
    name="PROGRAMMING_LANGUAGE",
    category=Category.PROGRAMMING_LANGUAGE,
    pattern=PROGRAMMING_LANGUAGE_PATTERN,
    flags=re.IGNORECASE,
    description=(
        "Unambiguous names of programming, markup and scripting languages and their usual "
        "abbreviations: JavaScript/JS, TypeScript/TS, Python, Java, C#, C++, PHP, Kotlin, HTML, CSS, "
        "Bash, PowerShell (any capitalisation, with or without the space in 'Java Script')."
    ),
    accepts=("JavaScript", "Javascript", "javascript", "Java Script", "JS", "TypeScript", "Python", "Python3", "Java", "C#", "C++", "HTML5"),
    rejects=("Javascripting", "JSON", "Pythonic", "Jazz", "TSLA"),
    techniques=("alternation (ordered)", "negative lookahead Java(?!Script)", "word boundaries via lookaround", "IGNORECASE flag"),
    rationale=(
        "'Java(?!\\s?Script)' makes Java and JavaScript mutually exclusive. The right boundary "
        "rejects 'JSON' and 'Pythonic' so abbreviations such as JS or TS are not found inside other words."
    ),
)

PROGRAMMING_LANGUAGE_AMBIGUOUS = RegexSpec(
    name="PROGRAMMING_LANGUAGE_AMBIGUOUS",
    category=Category.PROGRAMMING_LANGUAGE,
    pattern=PROGRAMMING_LANGUAGE_AMBIGUOUS_PATTERN,
    scope=Scope.SKILLS_SECTION,
    description=(
        "Language names that are also ordinary words or first names: R, Go, Rust, Julia, Ruby. "
        "They are case-sensitive and only recognised inside the Skills section."
    ),
    accepts=("R", "Go", "Rust", "Julia", "Ruby"),
    rejects=("r", "go", "Gopher", "R&D", "Python"),
    techniques=("scope restriction (Skills section)", "case-sensitive match", "word boundaries via lookaround"),
    rationale=(
        "'Go to the office' or a candidate called Julia must not produce a programming language. "
        "Inside 'Skills: Python, R, Go' there is no such ambiguity."
    ),
)

# --------------------------------------------------------------------------- #
# Frameworks and libraries                                                     #
# --------------------------------------------------------------------------- #

WEB_FRAMEWORK = RegexSpec(
    name="WEB_FRAMEWORK",
    category=Category.FRAMEWORK_LIBRARY,
    pattern=WEB_FRAMEWORK_PATTERN,
    flags=re.IGNORECASE,
    description=(
        "Web front-end and back-end frameworks written in an unambiguous way: React.js/ReactJS, "
        "Angular/AngularJS, Vue/Vue.js, Svelte, Next.js, Node.js/NodeJS, Express.js, Django, Flask, "
        "Spring Boot, FastAPI, Nest.js (dot and capitalisation optional)."
    ),
    accepts=("React.js", "ReactJS", "NodeJS", "Node.js", "Angular", "Vue.js", "Spring Boot", "Express.js", "Django", "FastAPI"),
    rejects=("React", "Node", "Express", "Reactive", "Nodes", "Spring"),
    techniques=("optional groups (?:\\.?js)", "ordered alternation", "IGNORECASE flag"),
    rationale=(
        "The optional '\\.?' captures the usual spelling variants (React.js, ReactJS) without deciding "
        "that they are the same technology; that is Stage 2's job."
    ),
)

WEB_FRAMEWORK_AMBIGUOUS = RegexSpec(
    name="WEB_FRAMEWORK_AMBIGUOUS",
    category=Category.FRAMEWORK_LIBRARY,
    pattern=WEB_FRAMEWORK_AMBIGUOUS_PATTERN,
    scope=Scope.SKILLS_SECTION,
    description=(
        "Short framework names that are also English words: React, Node, Express, Next, Spring, Nest. "
        "Case-sensitive and only recognised inside the Skills section."
    ),
    accepts=("React", "Node", "Express", "Next", "Spring", "Nest"),
    rejects=("react", "express", "Reaction", "Nodes", "Spring Boot"),
    techniques=("scope restriction (Skills section)", "case-sensitive match", "word boundaries via lookaround"),
    rationale="'We react quickly' or 'express interest' must not become frameworks.",
)

DATA_ML_LIBRARY = RegexSpec(
    name="DATA_ML_LIBRARY",
    category=Category.FRAMEWORK_LIBRARY,
    pattern=DATA_ML_LIBRARY_PATTERN,
    flags=re.IGNORECASE,
    description=(
        "Data-analysis, machine-learning and visualisation libraries and tools: Pandas, NumPy, SciPy, "
        "scikit-learn (and its variants 'scikit learn', 'sklearn'), TensorFlow ('Tensor Flow'), PyTorch "
        "('Py Torch'), Keras, XGBoost, LightGBM, CatBoost, Statsmodels, Matplotlib, Seaborn, Plotly, "
        "Tableau, Power BI."
    ),
    accepts=("Pandas", "NumPy", "Scikit-learn", "scikit learn", "sklearn", "Tensor Flow", "TensorFlow", "Py Torch", "PyTorch", "Power BI"),
    rejects=("Panda", "Tensor", "Torch", "Numeric"),
    techniques=("character sets [-_\\s]", "optional quantifier", "ordered alternation", "IGNORECASE flag"),
    rationale="Variants with hyphen, underscore, space or no separator are all surface forms of one library.",
)

# --------------------------------------------------------------------------- #
# Databases                                                                    #
# --------------------------------------------------------------------------- #

DATABASE = RegexSpec(
    name="DATABASE",
    category=Category.DATABASE,
    pattern=DATABASE_PATTERN,
    flags=re.IGNORECASE,
    description=(
        "Database systems and the SQL language: Postgres/PostgreSQL, MySQL, MariaDB, SQLite, "
        "SQL Server, Mongo/MongoDB, Redis, Firebase, Cassandra, Elasticsearch and plain SQL."
    ),
    accepts=("Postgres", "PostgreSQL", "MySQL", "SQLite", "SQL Server", "MongoDB", "Mongo", "Redis", "SQL"),
    rejects=("NoSQL", "SQLAlchemy", "Reddish", "Postgresql-based"),
    techniques=("ordered alternation (compound forms first)", "optional group", "IGNORECASE flag"),
    rationale="'SQL Server' must come before 'SQL', otherwise the shorter form would win.",
)

DATABASE_AMBIGUOUS = RegexSpec(
    name="DATABASE_AMBIGUOUS",
    category=Category.DATABASE,
    pattern=DATABASE_AMBIGUOUS_PATTERN,
    scope=Scope.SKILLS_SECTION,
    description="The word 'Oracle' (database or company). Case-sensitive, only inside the Skills section.",
    accepts=("Oracle",),
    rejects=("oracle", "Oracles"),
    techniques=("scope restriction (Skills section)", "case-sensitive match"),
    rationale="'Worked at Oracle' names a company, not a skill.",
)

# --------------------------------------------------------------------------- #
# Tools and technologies                                                       #
# --------------------------------------------------------------------------- #

API_PROTOCOL = RegexSpec(
    name="API_PROTOCOL",
    category=Category.TOOL_TECHNOLOGY,
    pattern=API_PROTOCOL_PATTERN,
    description=(
        "API styles and protocols: REST/RESTful (upper case, optionally followed by API/APIs), "
        "'Rest API' in title case, GraphQL and WebSocket(s) (any capitalisation)."
    ),
    accepts=("REST", "RESTful", "REST API", "RESTful APIs", "Rest API", "GraphQL", "graphql", "WebSockets"),
    rejects=("rest", "Rest", "Restaurant", "Rest of"),
    techniques=("case-sensitive alternation", "scoped flag (?i:...)", "optional groups"),
    rationale=(
        "'rest' is a very common English word, so REST is case-sensitive; title-case 'Rest' is only "
        "accepted when followed by API."
    ),
)

VERSION_CONTROL = RegexSpec(
    name="VERSION_CONTROL",
    category=Category.TOOL_TECHNOLOGY,
    pattern=VERSION_CONTROL_PATTERN,
    flags=re.IGNORECASE,
    description="Version-control tools and hosting services: Git, GitHub, GitLab, Bitbucket, SVN, Subversion.",
    accepts=("Git", "GitHub", "GitLab", "git", "Bitbucket", "SVN"),
    rejects=("Gitea", "Digit", "Github.com", "GitOps"),
    techniques=("optional group (?:Hub|Lab)", "word boundaries via lookaround", "IGNORECASE flag"),
    rationale="'Digit' and 'GitOps' are rejected by the left and right boundaries.",
)

DEVOPS_CLOUD_TOOL = RegexSpec(
    name="DEVOPS_CLOUD_TOOL",
    category=Category.TOOL_TECHNOLOGY,
    pattern=DEVOPS_CLOUD_TOOL_PATTERN,
    flags=re.IGNORECASE,
    description=(
        "CI/CD, container, infrastructure-as-code, cloud and operating-system tools: GitHub Actions, "
        "GitLab CI(/CD), Jenkins, Argo CD, Docker, Kubernetes/K8s, Podman, Helm, Terraform, Ansible, "
        "AWS/Amazon Web Services, Azure, GCP/Google Cloud (Platform) and Linux."
    ),
    accepts=("Docker", "Kubernetes", "K8s", "AWS", "Amazon Web Services", "Google Cloud Platform", "GitHub Actions", "GitLab CI/CD", "Terraform", "Linux"),
    rejects=("Dockerfile", "Dockers", "AWSome", "Google"),
    techniques=("ordered alternation", "optional groups", "IGNORECASE flag"),
    rationale=(
        "'GitHub Actions' is longer than the 'GitHub' match of VERSION_CONTROL; the extractor keeps the "
        "longest overlapping technology, so the CI tool wins."
    ),
)

# --------------------------------------------------------------------------- #
# The catalog                                                                  #
# --------------------------------------------------------------------------- #

DEFAULT_SPECS: Tuple[RegexSpec, ...] = (
    EMAIL,
    PHONE,
    LINKEDIN_URL,
    GITHUB_URL,
    CANDIDATE_NAME,
    YEARS_OF_EXPERIENCE,
    JOB_TITLE,
    DEGREE,
    CERTIFICATION,
    PROGRAMMING_LANGUAGE,
    PROGRAMMING_LANGUAGE_AMBIGUOUS,
    WEB_FRAMEWORK,
    WEB_FRAMEWORK_AMBIGUOUS,
    DATA_ML_LIBRARY,
    DATABASE,
    DATABASE_AMBIGUOUS,
    API_PROTOCOL,
    VERSION_CONTROL,
    DEVOPS_CLOUD_TOOL,
)

SPECS_BY_NAME: Dict[str, RegexSpec] = {spec.name: spec for spec in DEFAULT_SPECS}

assert len(SPECS_BY_NAME) == len(DEFAULT_SPECS), "RegexSpec names must be unique"