"""Pure-BNF model of the Stage 4 grammar, used only to generate documentation.

This module writes the grammar of ``src/stage4_grammar/candidate.tx`` a second
time, as a pure context-free grammar in BNF (no EBNF operators).
``scripts/export_stage4_artifacts.py`` uses it to

* compute NULLABLE, FIRST and FOLLOW sets and the LL(1) parsing table printed
  in ``docs/stage4_grammar.md``;
* build the leftmost derivation and the parse tree drawn in that document.

It is not a test and nothing in ``src`` or ``tests`` imports it.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

EPS = 'ε'
END = '$'
START = 'Candidate'

# Lexical token classes (terminals whose lexeme is an attribute).
TEXT, CANON, UINT = 'TEXT', 'CANONICAL_TOKEN', 'UINT'
TOKEN_CLASSES = (TEXT, CANON, UINT)

# Pure BNF. Each right-hand side is a tuple of grammar symbols; () is ε.
# Auxiliary nonterminals (…Opt, …List) are the standard expansion of EBNF:
#   [X]  ->  XOpt  -> X | ε          {X}  ->  XList -> X XList | ε
BNF: dict[str, list[tuple[str, ...]]] = {
    'Candidate': [('candidate', '{', 'Personal', 'ContactSection', 'ExperienceSection',
                   'EducationSection', 'SkillSection', 'Classification', '}')],
    'Personal': [('personal', '{', 'NameOpt', 'SummaryOpt', 'LocationOpt', '}')],
    'NameOpt': [('name', TEXT, ';'), ()],
    'SummaryOpt': [('summary', TEXT, ';'), ()],
    'LocationOpt': [('location', TEXT, ';'), ()],
    'ContactSection': [('contact', '{', 'ContactList', '}')],
    'ContactList': [('Contact', 'ContactList'), ()],
    'Contact': [('ContactKind', TEXT, ';')],
    'ContactKind': [('email',), ('phone',), ('linkedin',), ('github',)],
    'ExperienceSection': [('experience', '{', 'YearsOpt', 'ExperienceList', '}')],
    'YearsOpt': [('total_years', UINT, ';'), ()],
    'ExperienceList': [('Experience', 'ExperienceList'), ()],
    'Experience': [('entry', '{', 'title', TEXT, ';', 'OrganizationOpt',
                    'WorkPeriodOpt', 'DescriptionOpt', '}')],
    'OrganizationOpt': [('organization', TEXT, ';'), ()],
    'WorkPeriodOpt': [('period', TEXT, ';'), ()],
    'DescriptionOpt': [('description', TEXT, ';'), ()],
    'EducationSection': [('education', '{', 'EducationList', '}')],
    'EducationList': [('Education', 'EducationList'), ()],
    'Education': [('entry', '{', 'qualification', TEXT, ';', 'InstitutionOpt',
                   'StudyPeriodOpt', '}')],
    'InstitutionOpt': [('institution', TEXT, ';'), ()],
    'StudyPeriodOpt': [('period', TEXT, ';'), ()],
    'SkillSection': [('skills', '{', 'SkillList', '}')],
    'SkillList': [('Skill', 'SkillList'), ()],
    'Skill': [('KnownSkill',), ('UnrecognizedSkill',)],
    'KnownSkill': [('skill', CANON, ';')],
    'UnrecognizedSkill': [('unrecognized', TEXT, ';')],
    'Classification': [('classification', '{', 'AcceptedList', '}')],
    'AcceptedList': [('AcceptedProfile', 'AcceptedList'), ()],
    'AcceptedProfile': [('accepted', 'ProfileId', ';')],
    'ProfileId': [('full_stack',), ('machine_learning',), ('cloud_devops',), ('data_scientist',)],
}

NONTERMINALS = tuple(BNF)
# The 16 nonterminals that are rules of candidate.tx (the rest are EBNF expansions).
TEXTX_RULES = ('Candidate', 'Personal', 'ContactSection', 'Contact', 'ContactKind',
               'ExperienceSection', 'Experience', 'EducationSection', 'Education',
               'SkillSection', 'Skill', 'KnownSkill', 'UnrecognizedSkill',
               'Classification', 'AcceptedProfile', 'ProfileId')
TERMINALS = tuple(sorted({s for rhss in BNF.values() for rhs in rhss for s in rhs if s not in BNF}))
KEYWORDS = tuple(t for t in TERMINALS if re.fullmatch(r'[a-z_]+', t))
PUNCTUATION = tuple(t for t in TERMINALS if t in '{};')


def productions():
    """Numbered list of productions (A, rhs), in declaration order."""
    return [(lhs, rhs) for lhs, rhss in BNF.items() for rhs in rhss]


# --------------------------------------------------------------------------- sets

def nullable_set():
    nullable, changed = set(), True
    while changed:
        changed = False
        for lhs, rhs in productions():
            if lhs not in nullable and all(s in nullable for s in rhs):
                nullable.add(lhs)
                changed = True
    return nullable


def first_of_sequence(seq, first, nullable):
    out = set()
    for s in seq:
        if s not in BNF:
            out.add(s)
            return out
        out |= first[s]
        if s not in nullable:
            return out
    out.add(EPS)
    return out


def first_sets():
    nullable = nullable_set()
    first = {a: set() for a in BNF}
    changed = True
    while changed:
        changed = False
        for lhs, rhs in productions():
            new = first_of_sequence(rhs, first, nullable) - {EPS}
            if not new <= first[lhs]:
                first[lhs] |= new
                changed = True
    return first


def follow_sets():
    nullable, first = nullable_set(), first_sets()
    follow = {a: set() for a in BNF}
    follow[START].add(END)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in productions():
            for i, s in enumerate(rhs):
                if s not in BNF:
                    continue
                rest = first_of_sequence(rhs[i + 1:], first, nullable)
                new = (rest - {EPS}) | (follow[lhs] if EPS in rest else set())
                if not new <= follow[s]:
                    follow[s] |= new
                    changed = True
    return follow


def predict_sets():
    """PREDICT(A -> α) = FIRST(α) ∪ (FOLLOW(A) if α is nullable)."""
    nullable, first, follow = nullable_set(), first_sets(), follow_sets()
    out = []
    for lhs, rhs in productions():
        f = first_of_sequence(rhs, first, nullable)
        out.append((lhs, rhs, (f - {EPS}) | (follow[lhs] if EPS in f else set())))
    return out


def ll1_table():
    """Return (table, conflicts). table[(A, a)] = rhs."""
    table, conflicts = {}, []
    for lhs, rhs, predict in predict_sets():
        for a in predict:
            if (lhs, a) in table and table[(lhs, a)] != rhs:
                conflicts.append((lhs, a, table[(lhs, a)], rhs))
            table[(lhs, a)] = rhs
    return table, conflicts


# ------------------------------------------------------------ structural analysis

def reachable():
    seen, stack = {START}, [START]
    while stack:
        for rhs in BNF[stack.pop()]:
            for s in rhs:
                if s in BNF and s not in seen:
                    seen.add(s)
                    stack.append(s)
    return seen


def productive():
    prod, changed = set(), True
    while changed:
        changed = False
        for lhs, rhs in productions():
            if lhs not in prod and all(s not in BNF or s in prod for s in rhs):
                prod.add(lhs)
                changed = True
    return prod


def self_embedding_nonterminals():
    """Nonterminals A with A =>+ u A v where u and v are both nonempty words.

    Every nonterminal of G derives at least one nonempty word, so a symbol
    sequence can derive a nonempty word iff it is itself nonempty. Hence it
    suffices to search the graph of states (B, left nonempty, right nonempty).
    """
    result = set()
    for a in BNF:
        start = (a, False, False)
        seen, stack = {start}, [start]
        while stack:
            b, left, right = stack.pop()
            for rhs in BNF[b]:
                for i, s in enumerate(rhs):
                    if s not in BNF:
                        continue
                    state = (s, left or i > 0, right or i < len(rhs) - 1)
                    if s == a and state[1] and state[2]:
                        result.add(a)
                    if state not in seen:
                        seen.add(state)
                        stack.append(state)
    return result


def every_nonterminal_derives_a_nonempty_word():
    return all(any(rhs for rhs in BNF[a]) for a in BNF)


def recursive_nonterminals():
    """Nonterminals that can derive a sentential form containing themselves."""
    out = set()
    for a in BNF:
        seen, stack = set(), [a]
        while stack:
            b = stack.pop()
            for rhs in BNF[b]:
                for s in rhs:
                    if s == a:
                        out.add(a)
                    if s in BNF and s not in seen:
                        seen.add(s)
                        stack.append(s)
    return out


# ------------------------------------------------------------------------- lexer

@dataclass(frozen=True)
class Token:
    kind: str        # a keyword/punctuation terminal, or TEXT/CANONICAL_TOKEN/UINT
    lexeme: str
    line: int
    column: int


_TEXT_RE = r'"(?:[^"\\\x00-\x1f]|\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4}))*"'
_LEX = re.compile(r'''
    (?P<ws>[ \t\r\n]+) | (?P<comment>//[^\n\r]*) |
    (?P<text>''' + _TEXT_RE + r''') |
    (?P<word>[A-Za-z_][A-Za-z0-9_]*) | (?P<number>[0-9]+) |
    (?P<punct>[{};])
''', re.VERBOSE)


class LexicalError(ValueError):
    pass


def tokenize(source: str) -> list[Token]:
    """Context-free tokenizer equivalent to the scannerless textX recognition.

    Words are taken by maximal munch and then classified, which reproduces textX's
    keyword word-boundary rule (``autokwd``): ``skillPYTHON`` is one invalid word.
    """
    tokens, pos, line, line_start = [], 0, 1, 0
    while pos < len(source):
        m = _LEX.match(source, pos)
        if not m:
            raise LexicalError(f'unexpected character {source[pos]!r} at {line}:{pos - line_start + 1}')
        kind, lexeme = m.lastgroup, m.group()
        column = pos - line_start + 1
        if kind == 'word':
            if lexeme in KEYWORDS:
                tokens.append(Token(lexeme, lexeme, line, column))
            elif re.fullmatch(r'[A-Z][A-Z0-9_]*', lexeme):
                tokens.append(Token(CANON, lexeme, line, column))
            else:
                raise LexicalError(f'invalid word {lexeme!r} at {line}:{column}')
        elif kind == 'number':
            if not re.fullmatch(r'0|[1-9][0-9]*', lexeme):
                raise LexicalError(f'invalid number {lexeme!r} at {line}:{column}')
            tokens.append(Token(UINT, lexeme, line, column))
        elif kind == 'text':
            tokens.append(Token(TEXT, lexeme, line, column))
        elif kind == 'punct':
            tokens.append(Token(lexeme, lexeme, line, column))
        newlines = lexeme.count('\n')
        if newlines:
            line += newlines
            line_start = pos + lexeme.rfind('\n') + 1
        pos = m.end()
    return tokens


# ------------------------------------------------------------------ LL(1) parser

@dataclass
class Node:
    symbol: str
    children: list = field(default_factory=list)
    token: Token | None = None


class SyntaxRejection(ValueError):
    def __init__(self, message, token=None):
        super().__init__(message)
        self.token = token


def parse_tokens(tokens: list[Token]) -> Node:
    """Table-driven predictive (LL(1)) parse; returns the parse tree."""
    table, conflicts = ll1_table()
    assert not conflicts
    stream = list(tokens) + [Token(END, END, -1, -1)]
    root = Node(START)
    stack = [(END, None), (START, root)]
    i = 0
    while stack:
        symbol, node = stack.pop()
        look = stream[i]
        if symbol == END:
            if look.kind != END:
                raise SyntaxRejection(f'trailing input {look.lexeme!r}', look)
            return root
        if symbol not in BNF:
            if look.kind != symbol:
                raise SyntaxRejection(f'expected {symbol!r}, found {look.lexeme!r}', look)
            node.token = look
            i += 1
            continue
        rhs = table.get((symbol, look.kind))
        if rhs is None:
            raise SyntaxRejection(f'no production for {symbol} on {look.lexeme!r}', look)
        children = [Node(s) for s in rhs] or [Node(EPS)]
        node.children = children
        for s, child in reversed(list(zip(rhs, children))):
            stack.append((s, child))
    raise AssertionError('unreachable')


def recognizes(source: str) -> bool:
    try:
        parse_tokens(tokenize(source))
        return True
    except (LexicalError, SyntaxRejection):
        return False


def leftmost_derivation(tree: Node):
    """Sentential forms of the leftmost derivation encoded by a parse tree."""
    forms, frontier = [], [tree]

    def render(nodes):
        return [n.symbol if n.token is None or n.symbol in BNF else (
            n.token.lexeme if n.symbol in TOKEN_CLASSES else n.symbol) for n in nodes]

    while True:
        forms.append(render(frontier))
        for idx, n in enumerate(frontier):
            if n.symbol in BNF:
                frontier = frontier[:idx] + [c for c in n.children if c.symbol != EPS] + frontier[idx + 1:]
                break
        else:
            return forms


def tree_leaves(tree: Node):
    if not tree.children:
        return [] if tree.symbol == EPS or tree.symbol in BNF else [tree.token]
    return [t for c in tree.children for t in tree_leaves(c)]


# ----------------------------------------------------------- sentence generation

def random_sentence(rng: random.Random, lexemes, *, max_items=3, p_optional=0.5):
    """Random token sequence of L(G) obtained by a random leftmost derivation.

    ``lexemes`` maps TEXT/CANONICAL_TOKEN/UINT to a callable(rng) -> lexeme.
    A list nonterminal ``XList -> X XList | ε`` is applied k times followed by ε,
    with k uniform in 0..max_items; optional nonterminals choose X with
    probability ``p_optional``; other alternatives are chosen uniformly.
    """
    out = []

    def expand(symbol):
        if symbol not in BNF:
            out.append(lexemes[symbol](rng) if symbol in TOKEN_CLASSES else symbol)
            return
        item, empty = BNF[symbol][0], ()
        if symbol.endswith('List'):
            for _ in range(rng.randint(0, max_items)):
                expand(item[0])
            return
        if symbol.endswith('Opt'):
            choice = item if rng.random() < p_optional else empty
        else:
            choice = rng.choice(BNF[symbol])
        for s in choice:
            expand(s)

    expand(START)
    return out


def layout(tokens, rng: random.Random | None = None, *, comments=False):
    """Join tokens with random (or single-space) whitespace and optional comments."""
    if rng is None:
        return ' '.join(tokens)
    parts = []
    for tok in tokens:
        parts.append(tok)
        sep = rng.choice([' ', '\n', '  ', '\t', '\n    ', ' \n '])
        if comments and rng.random() < 0.1:
            sep = f' // note {rng.randint(0, 99)} "quoted" {{}};\n'
        parts.append(sep)
    return ''.join(parts)
