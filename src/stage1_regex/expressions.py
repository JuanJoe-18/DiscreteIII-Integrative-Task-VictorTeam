r"""The regular expressions of Stage 1, written as plain Python raw strings.

Each regular expression is a module-level constant called ``<NAME>_PATTERN`` that can be used
directly with the ``re`` module::

    import re
    from src.stage1_regex.expressions import EMAIL_PATTERN, YEARS_OF_EXPERIENCE_PATTERN

    re.findall(EMAIL_PATTERN, "write to wednesday.addams@example.com")                 # ['wednesday.addams@example.com']
    re.findall(YEARS_OF_EXPERIENCE_PATTERN, "3 years and 10+ years", re.IGNORECASE)   # ['3', '10']

The comment above each constant says what the expression recognises and which ``re`` flags it
needs. ``patterns.py`` wraps every constant in a ``RegexSpec`` (flags, scope, examples that must be
accepted / rejected, documentation) and ``extractor.py`` runs them over the resumes.
"""

# --------------------------------------------------------------------------- #
# Building blocks used to compose the longer expressions                       #
# --------------------------------------------------------------------------- #

# Left boundary (negative lookbehind): the technology must not be glued to a previous word
# character, dot, plus, hash or ampersand (so ``JS`` is not found in ``main.js`` or ``R`` in ``R&D``).
_LB = r"(?<![\w.+#&])"

# Right boundary (negative lookahead): the technology must not continue as a longer word
# (``JSON``), a hyphenated word (``Python-based``) or a dotted name (``Node.jsx``).
# A plain trailing dot (end of a sentence, ``Git.``) is allowed.
_RB = r"(?![\w+#&]|-\w|\.\w)"

# A capitalised word on the same line, horizontal whitespace (never crosses a line break) and
# 1 to 4 capitalised words, optionally linked by a lower-case connector ("Ciencia de Datos").
_CAP = r"[A-ZÁÉÍÓÚÑ][\w&-]*"
_SP = r"[ \t]+"
_CAPS = rf"{_CAP}(?:{_SP}(?:(?:de|del|of|and|y|&){_SP})?{_CAP}){{0,3}}"

# A word of a person name (Wednesday, Jean-Luc, O'Brien, PÉREZ) and the words that must NOT be
# taken as part of a name (headings and job words).
_NAME_WORD = r"(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+(?:['’-][A-ZÁÉÍÓÚÑ]?[a-záéíóúñü]+)*|[A-ZÁÉÍÓÚÑ]{2,})"
_NOT_NAME = (
    r"(?!(?i:technical|skills|experience|education|summary|profile|contact|resume|curriculum|cv|"
    r"software|web|full|senior|junior|data|machine|cloud|developer|engineer)\b)"
)

# Number words accepted as an amount of years (English and Spanish).
_NUMBER_WORDS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
    "|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce"
)


def _tech(*alternatives: str) -> str:
    """Wrap a list of surface forms in an alternation with word boundaries.

    Order matters: longer / compound forms must come before their prefixes
    (``SQL[\\s-]?Server`` before ``SQL``), because the first alternative whose
    boundary check succeeds wins.
    """
    return rf"{_LB}(?:{'|'.join(alternatives)}){_RB}"


# --------------------------------------------------------------------------- #
# Contact information                                                        #
# --------------------------------------------------------------------------- #

# EMAIL: A local part of word characters, dots, plus signs or hyphens, an '@', and a domain made
# of at least two dot-separated labels of letters, digits or hyphens.
EMAIL_PATTERN = r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+(?![\w@-])"

# PHONE: A 10-digit phone number written as 3-3-4 digits, optionally separated by spaces or
# hyphens, optionally with the area code in parentheses and an international prefix '+' followed
# by 1 to 3 digits.
PHONE_PATTERN = r"(?<![\w+])(?:\+\d{1,3}[ -]?)?(?:\(\d{3}\)[ -]?|\d{3}[ -]?)\d{3}[ -]?\d{4}(?!\d)"

# LINKEDIN_URL: A LinkedIn profile address: optional 'http(s)://' and 'www.', the host
# 'linkedin.com', the path '/in/' and a user handle of word characters, '%' or hyphens, with an
# optional final slash.
# flags: re.IGNORECASE
LINKEDIN_URL_PATTERN = r"(?<![\w.])(?:https?://)?(?:www\.)?linkedin\.com/in/[\w%-]+/?"

# GITHUB_URL: A GitHub profile or repository address: optional scheme and 'www.', the host
# 'github.com', a user name and, optionally, a repository name.
# flags: re.IGNORECASE
GITHUB_URL_PATTERN = r"(?<![\w.])(?:https?://)?(?:www\.)?github\.com/[\w-]+(?:/[\w-]+(?:\.[\w-]+)*)?/?"

# --------------------------------------------------------------------------- #
# Identity and professional experience                                       #
# --------------------------------------------------------------------------- #

# CANDIDATE_NAME: The beginning of the document: two to four consecutive words on the same line,
# each one capitalised (or all upper case), allowing accents, apostrophes and hyphens ('Jean-Luc',
# "O'Brien"), and not being a typical heading word (Resume, Skills, Developer ...).
CANDIDATE_NAME_PATTERN = rf"\A\s*({_NOT_NAME}{_NAME_WORD}(?:[ \t]+{_NOT_NAME}{_NAME_WORD}){{1,3}})(?=\s|$)"

# YEARS_OF_EXPERIENCE: A quantity of years: a number from 0 to 49 (digits) or a number word from
# 'one' to 'twelve' (English) or 'uno' to 'doce' (Spanish), an optional '+', optional spaces or a
# hyphen, and the unit 'year(s)', 'yr(s)' or the Spanish 'año(s)'. Only the quantity is kept.
# flags: re.IGNORECASE
YEARS_OF_EXPERIENCE_PATTERN = rf"(?<![\d.])((?:[1-4]\d|0?\d)|{_NUMBER_WORDS})\+?[\s-]*(?:years?|yrs?|a[ñn]os?)\b"

# JOB_TITLE: A job title: an optional seniority word (Senior, Junior, Lead, Principal), a domain
# (Full Stack, Front End, Back End, Web, Software, Machine Learning, Data, DevOps, Cloud, AI), an
# optional 'Application' and a role (Developer, Engineer, Scientist, Analyst).
# flags: re.IGNORECASE
JOB_TITLE_PATTERN = (
    r"(?<!\w)(?:(?:Senior|Junior|Lead|Principal)\s+)?"
    r"(?:Full[\s-]?Stack|Front[\s-]?End|Back[\s-]?End|Web|Software|Machine\s+Learning|Data|DevOps|Cloud|AI)"
    r"\s+(?:Application\s+)?(?:Developer|Engineer|Scientist|Analyst)(?!\w)"
)

# --------------------------------------------------------------------------- #
# Academic qualifications                                                    #
# --------------------------------------------------------------------------- #

# DEGREE: An academic degree: 'Bachelor/Master [\'s] [degree] of|in <Field>' (the field being 1-4
# capitalised words, optionally followed by a second 'in|of <Field>'), an abbreviation or
# doctorate (BSc, MSc, PhD, Doctorate ...) optionally followed by its field, or the Spanish
# 'Ingeniería|Maestría de|en <Field>'.
DEGREE_PATTERN = (
    r"(?<!\w)(?:"
    # Bachelor / Master must be followed by 'of' or 'in': this keeps out "Scrum Master".
    rf"(?i:Bachelor|Master)(?:['’]s)?(?:{_SP}degree)?{_SP}(?i:of|in){_SP}{_CAPS}"
    rf"(?:{_SP}(?i:in|of){_SP}{_CAPS})?"
    # Abbreviations and doctorates, optionally followed by the field of study.
    rf"|(?i:B\.?Sc\.?|M\.?Sc\.?|PhD|Ph\.D\.?|Doctorate|Doctorado|Pregrado)(?:{_SP}(?i:in|of|en){_SP}{_CAPS})?"
    # Spanish engineering / master degrees.
    rf"|(?i:Ingenier[ií]a|Maestr[ií]a){_SP}(?i:de|en){_SP}{_CAPS}"
    r")(?!\w)"
)

# CERTIFICATION: A professional certification: either '<AWS|Azure|GCP|Google Cloud> Certified
# <Title>' or 'Certified <Title>', where the title is a sequence of capitalised words on the same
# line.
CERTIFICATION_PATTERN = (
    rf"(?<!\w)(?:(?:AWS|Azure|GCP|Google{_SP}Cloud){_SP}Certified{_SP}{_CAPS}"
    rf"|Certified{_SP}{_CAP}(?:{_SP}{_CAP}){{1,3}})(?!\w)"
)

# --------------------------------------------------------------------------- #
# Programming languages                                                      #
# --------------------------------------------------------------------------- #

# PROGRAMMING_LANGUAGE: Unambiguous names of programming, markup and scripting languages and their
# usual abbreviations: JavaScript/JS, TypeScript/TS, Python, Java, C#, C++, PHP, Kotlin, HTML,
# CSS, Bash, PowerShell (any capitalisation, with or without the space in 'Java Script').
# flags: re.IGNORECASE
PROGRAMMING_LANGUAGE_PATTERN = _tech(
    r"Java[\s]?Script",
    r"JS",
    r"Type[\s]?Script",
    r"TS",
    r"Python3?",
    r"Java(?!\s?Script)",
    r"C#",
    r"C\+\+",
    r"PHP",
    r"Kotlin",
    r"HTML5?",
    r"CSS3?",
    r"Bash",
    r"PowerShell",
)

# PROGRAMMING_LANGUAGE_AMBIGUOUS: Language names that are also ordinary words or first names: R,
# Go, Rust, Julia, Ruby. They are case-sensitive and only recognised inside the Skills section.
PROGRAMMING_LANGUAGE_AMBIGUOUS_PATTERN = _tech(r"R", r"Go", r"Rust", r"Julia", r"Ruby")

# --------------------------------------------------------------------------- #
# Frameworks and libraries                                                   #
# --------------------------------------------------------------------------- #

# WEB_FRAMEWORK: Web front-end and back-end frameworks written in an unambiguous way:
# React.js/ReactJS, Angular/AngularJS, Vue/Vue.js, Svelte, Next.js, Node.js/NodeJS, Express.js,
# Django, Flask, Spring Boot, FastAPI, Nest.js (dot and capitalisation optional).
# flags: re.IGNORECASE
WEB_FRAMEWORK_PATTERN = _tech(
    r"React\.?js",
    r"Angular(?:\.?js)?",
    r"Vue(?:\.?js)?",
    r"Svelte",
    r"Next\.?js",
    r"Node\.?js",
    r"Express\.?js",
    r"Django",
    r"Flask",
    r"Spring[\s-]?Boot",
    r"FastAPI",
    r"Nest\.?js",
)

# WEB_FRAMEWORK_AMBIGUOUS: Short framework names that are also English words: React, Node,
# Express, Next, Spring, Nest. Case-sensitive and only recognised inside the Skills section.
WEB_FRAMEWORK_AMBIGUOUS_PATTERN = _tech(r"React", r"Node", r"Express", r"Next", r"Spring", r"Nest")

# DATA_ML_LIBRARY: Data-analysis, machine-learning and visualisation libraries and tools: Pandas,
# NumPy, SciPy, scikit-learn (and its variants 'scikit learn', 'sklearn'), TensorFlow ('Tensor
# Flow'), PyTorch ('Py Torch'), Keras, XGBoost, LightGBM, CatBoost, Statsmodels, Matplotlib,
# Seaborn, Plotly, Tableau, Power BI.
# flags: re.IGNORECASE
DATA_ML_LIBRARY_PATTERN = _tech(
    r"Pandas",
    r"NumPy",
    r"SciPy",
    r"Scikit[-_\s]?learn",
    r"sk[-_\s]?learn",
    r"Tensor[\s-]?Flow",
    r"Py[\s-]?Torch",
    r"Keras",
    r"XGBoost",
    r"LightGBM",
    r"CatBoost",
    r"Statsmodels",
    r"Matplotlib",
    r"Seaborn",
    r"Plotly",
    r"Tableau",
    r"Power[\s-]?BI",
)

# --------------------------------------------------------------------------- #
# Databases                                                                  #
# --------------------------------------------------------------------------- #

# DATABASE: Database systems and the SQL language: Postgres/PostgreSQL, MySQL, MariaDB, SQLite,
# SQL Server, Mongo/MongoDB, Redis, Firebase, Cassandra, Elasticsearch and plain SQL.
# flags: re.IGNORECASE
DATABASE_PATTERN = _tech(
    r"Postgre(?:s|SQL)?",
    r"MySQL",
    r"MariaDB",
    r"SQLite",
    r"SQL[\s-]?Server",
    r"Mongo(?:DB)?",
    r"Redis",
    r"Firebase",
    r"Cassandra",
    r"Elasticsearch",
    r"SQL",
)

# DATABASE_AMBIGUOUS: The word 'Oracle' (database or company). Case-sensitive, only inside the
# Skills section.
DATABASE_AMBIGUOUS_PATTERN = _tech(r"Oracle")

# --------------------------------------------------------------------------- #
# Tools and technologies                                                     #
# --------------------------------------------------------------------------- #

# API_PROTOCOL: API styles and protocols: REST/RESTful (upper case, optionally followed by
# API/APIs), 'Rest API' in title case, GraphQL and WebSocket(s) (any capitalisation).
API_PROTOCOL_PATTERN = rf"{_LB}(?:REST(?:ful)?(?:\s?APIs?)?|Rest(?:ful)?\s?APIs?|(?i:GraphQL|Web[\s-]?Sockets?)){_RB}"

# VERSION_CONTROL: Version-control tools and hosting services: Git, GitHub, GitLab, Bitbucket,
# SVN, Subversion.
# flags: re.IGNORECASE
VERSION_CONTROL_PATTERN = _tech(r"Git(?:Hub|Lab)?", r"Bitbucket", r"SVN", r"Subversion")

# DEVOPS_CLOUD_TOOL: CI/CD, container, infrastructure-as-code, cloud and operating-system tools:
# GitHub Actions, GitLab CI(/CD), Jenkins, Argo CD, Docker, Kubernetes/K8s, Podman, Helm,
# Terraform, Ansible, AWS/Amazon Web Services, Azure, GCP/Google Cloud (Platform) and Linux.
# flags: re.IGNORECASE
DEVOPS_CLOUD_TOOL_PATTERN = _tech(
    r"GitHub[\s-]?Actions",
    r"GitLab[\s-]?CI(?:/CD)?",
    r"Jenkins",
    r"Argo[\s-]?CD",
    r"Docker",
    r"Kubernetes",
    r"K8s",
    r"Podman",
    r"Helm",
    r"Terraform",
    r"Ansible",
    r"AWS",
    r"Amazon\s+Web\s+Services",
    r"Azure",
    r"GCP",
    r"Google\s+Cloud(?:\s+Platform)?",
    r"Linux",
)