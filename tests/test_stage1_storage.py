"""Stage 1 - tests of result persistence (JSON)."""

import json
from pathlib import Path

from src.stage1_regex import extract_qualifications, load_result, save_result

RICH = Path(__file__).parent / "data" / "resumes" / "rich_resume.txt"


def test_save_and_load_roundtrip(tmp_path):
    original = extract_qualifications(RICH.read_text(encoding="utf-8"))
    path = save_result(original, tmp_path / "nested" / "result.json")
    assert path.exists()

    loaded = load_result(path)
    assert loaded.raw_tokens == original.raw_tokens
    assert loaded.years_of_experience == original.years_of_experience
    assert loaded.candidate_name == original.candidate_name
    assert loaded.items == original.items


def test_json_file_is_human_readable_utf8(tmp_path):
    result = extract_qualifications("Juan Pérez\nHabilidades: Python, Git")
    path = save_result(result, tmp_path / "r.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["candidate_name"] == "Juan Pérez"
    assert data["raw_tokens"] == ["Python", "Git"]
    assert "Pérez" in path.read_text(encoding="utf-8")  # not escaped as é