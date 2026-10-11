"""Tests of the Stage 2 transducers as formal objects (7-tuples) and of their pyformlang versions."""

import itertools
import random
import string

import pytest

from src.stage2_fst.aliases import ALIAS_FAMILIES, EXPERIENCE_TOKEN, all_canonical_tokens
from src.stage2_fst.transducers import (
    CLEAN,
    END,
    EXPERIENCE,
    Transducer,
    build_alias_transducer,
    build_family_transducers,
    build_filter_transducer,
    build_full_alias_transducer,
    clean_aliases,
    clean_word,
    run_fst,
)
from src.stage3_classifier.profiles import PROFILES_REGISTRY

FULL = build_full_alias_transducer()
FULL_FST = FULL.to_fst()


def _alias_run(word: str):
    return run_fst(FULL_FST, list(word) + [END])


# --------------------------------------------------------------------------- 7-tuples
@pytest.mark.parametrize("t", [CLEAN, EXPERIENCE, FULL, *build_family_transducers().values()],
                         ids=lambda t: t.name)
def test_every_transducer_is_a_well_formed_deterministic_7_tuple(t):
    t.validate()
    assert t.q0 in t.states and set(t.finals) <= set(t.states)
    # delta and omega are functions on the same domain (determinism)
    assert set(t.delta) == set(t.omega)
    assert all(src in t.states and dst in t.states for (src, _), dst in t.delta.items())


def test_validate_rejects_a_symbol_outside_sigma():
    bad = Transducer("BAD", ("q0",), ("a",), ("a",), {("q0", "b"): "q0"}, {("q0", "b"): "a"}, "q0", ("q0",))
    with pytest.raises(AssertionError):
        bad.validate()


def test_validate_rejects_an_output_outside_gamma():
    bad = Transducer("BAD", ("q0",), ("a",), ("a",), {("q0", "a"): "q0"}, {("q0", "a"): "z"}, "q0", ("q0",))
    with pytest.raises(AssertionError):
        bad.validate()


def test_clean_transducer_has_one_state_and_the_documented_alphabets():
    assert CLEAN.states == ("q0",)
    assert set(string.ascii_uppercase) <= set(CLEAN.sigma)
    assert not set(string.ascii_uppercase) & set(CLEAN.gamma)       # the output is always lower case
    assert not set(" .-_/") & set(CLEAN.gamma)                      # separators never come out


def test_experience_transducer_definition():
    assert EXPERIENCE.states == ("q0", "q1") and EXPERIENCE.finals == ("q1",)
    assert EXPERIENCE.gamma == (EXPERIENCE_TOKEN,)


# --------------------------------------------------------------------------- CLEAN
@pytest.mark.parametrize("raw, expected", [
    ("Node.js", "nodejs"), ("NodeJS", "nodejs"), ("node-js", "nodejs"), ("NODE JS", "nodejs"),
    ("Scikit-learn", "scikitlearn"), ("scikit_learn", "scikitlearn"), ("GitLab CI/CD", "gitlabcicd"),
    ("C#", "c#"), ("C++", "c++"), ("Power BI", "powerbi"), ("R", "r"), ("HTML5", "html5"),
])
def test_clean_removes_case_and_separators_but_keeps_hash_and_plus(raw, expected):
    assert clean_word(raw) == expected


@pytest.mark.parametrize("raw", ["Café", "R&D", "node(js)", "a,b", "C!", "日本"])
def test_clean_rejects_symbols_outside_the_input_alphabet(raw):
    assert clean_word(raw) is None


def test_clean_is_idempotent_and_ignores_case():
    for raw in ["React.js", "Spring-Boot", "Tensor Flow", "C#", "GITHUB ACTIONS"]:
        once = clean_word(raw)
        assert clean_word(once) == once
        assert clean_word(raw.upper()) == clean_word(raw.lower()) == once


# --------------------------------------------------------------------------- ALIAS
def test_every_spelling_reaches_its_canonical_token():
    for family in ALIAS_FAMILIES.values():
        for canonical, spellings in family.items():
            for spelling in spellings + [canonical]:
                assert _alias_run(clean_word(spelling)) == [canonical], spelling


def test_family_transducers_agree_with_the_full_transducer():
    families = build_family_transducers()
    for name, t in families.items():
        for canonical, spellings in ALIAS_FAMILIES[name].items():
            for spelling in spellings:
                word = clean_word(spelling)
                assert t.simulate(list(word) + [END]) == [canonical]
                assert FULL.simulate(list(word) + [END]) == [canonical]


def test_pyformlang_and_the_reference_simulator_agree_on_random_inputs():
    rng = random.Random(2026)
    alphabet = sorted(set(FULL.sigma) - {END})
    words = [clean_word(s) for fam in ALIAS_FAMILIES.values() for sp in fam.values() for s in sp]
    for _ in range(300):
        word = rng.choice(words)
        mutated = list(word)
        if mutated and rng.random() < 0.7:
            mutated[rng.randrange(len(mutated))] = rng.choice(alphabet)
        if rng.random() < 0.3:
            mutated.append(rng.choice(alphabet))
        seq = mutated + [END]
        assert run_fst(FULL_FST, seq) == FULL.simulate(seq)


@pytest.mark.parametrize("word", ["", "gitx", "gi", "githubs", "nod", "pythonn", "c", "sqlserverx"])
def test_unknown_words_and_strict_prefixes_are_rejected(word):
    assert _alias_run(word) is None


def test_a_word_that_is_a_prefix_of_another_does_not_swallow_it():
    assert _alias_run("git") == ["GIT"]
    assert _alias_run("github") == ["GITHUB"]
    assert _alias_run("gitlab") == ["GITLAB"]
    assert _alias_run("gitlabci") == ["GITLAB_CI"]
    assert _alias_run("sql") == ["SQL"] and _alias_run("sqlite") == ["SQLITE"]
    assert _alias_run("java") == ["JAVA"] and _alias_run("javascript") == ["JAVASCRIPT"]


def test_end_marker_is_required():
    assert run_fst(FULL_FST, list("git")) is None


def test_ambiguous_vocabulary_is_rejected_at_build_time():
    with pytest.raises(ValueError):
        clean_aliases({"A": ["Node.js"], "B": ["nodejs"]})
    with pytest.raises(ValueError):
        clean_aliases({"A": ["bad word!"]})


def test_alias_transducer_is_a_trie():
    t = build_alias_transducer({"GIT": ["Git"], "GITHUB": ["GitHub"]})
    # prefixes: "", g, gi, git, gith, githu, github  + qf
    assert len(t.states) == 8
    assert t.number_of_transitions == len(t.delta) == 6 + 2
    assert t.finals == ("qf",)
    assert sum(1 for (_, s) in t.delta if s == END) == 2


def test_vocabulary_covers_every_skill_of_every_profile():
    produced = set(all_canonical_tokens())
    for profile in PROFILES_REGISTRY.values():
        missing = {s for s in profile.alphabet if s != EXPERIENCE_TOKEN} - produced
        assert not missing, f"{profile.profile_id}: no spelling produces {missing}"


def test_canonical_tokens_are_fixed_points_of_the_cascade():
    for token in all_canonical_tokens():
        assert _alias_run(clean_word(token)) == [token]


# --------------------------------------------------------------------------- EXPERIENCE
@pytest.mark.parametrize("digits", ["0", "1", "3", "10", "99", "2026"])
def test_experience_maps_any_number_to_one_symbol(digits):
    assert run_fst(EXPERIENCE.to_fst(), list(digits)) == [EXPERIENCE_TOKEN]


@pytest.mark.parametrize("text", ["", "a", "3a", "-3", "3.5"])
def test_experience_rejects_what_is_not_a_number(text):
    assert run_fst(EXPERIENCE.to_fst(), list(text)) is None


# --------------------------------------------------------------------------- FILTER
def test_filter_keeps_only_the_wanted_tokens_in_order():
    t = build_filter_transducer({"A", "C"}, ["A", "B", "C"])
    assert t.translate(["C", "B", "A", "B", "A"]) == ["C", "A", "A"]
    assert t.translate(["B", "B"]) == []


def test_filter_matches_its_reference_simulator():
    t = build_filter_transducer({"X", "Y"}, ["X", "Y", "Z"])
    for n in range(0, 5):
        for seq in itertools.product("XYZ", repeat=n):
            assert t.translate(list(seq)) == t.simulate(seq)


# --------------------------------------------------------------------------- reference simulator and validation
def test_reference_simulator_rejects_a_word_that_ends_in_a_non_final_state():
    assert FULL.simulate(list("git")) is None            # no end marker: state "git" is not accepting
    assert FULL.simulate(list("gi") + [END]) is None     # no edge for the marker in state "gi"
    assert FULL.simulate(list("git") + [END]) == ["GIT"]


def test_validate_rejects_delta_and_omega_with_different_domains():
    bad = Transducer("BAD", ("q0",), ("a", "b"), ("a",), {("q0", "a"): "q0", ("q0", "b"): "q0"},
                     {("q0", "a"): "a"}, "q0", ("q0",))
    with pytest.raises(AssertionError):
        bad.validate()


def test_validate_rejects_final_states_that_are_not_states():
    bad = Transducer("BAD", ("q0",), ("a",), ("a",), {("q0", "a"): "q0"}, {("q0", "a"): "a"}, "q0", ("q9",))
    with pytest.raises(AssertionError):
        bad.validate()


def test_clean_aliases_adds_the_canonical_token_as_a_spelling():
    assert clean_aliases({"NODE_JS": ["Node"]}) == {"node": "NODE_JS", "nodejs": "NODE_JS"}
