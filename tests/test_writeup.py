"""The submission part of docs/WRITEUP_DRAFT.md stays inside the competition limits."""

import re
from pathlib import Path

DRAFT = Path(__file__).resolve().parents[1] / "docs" / "WRITEUP_DRAFT.md"
START = "<!-- SUBMISSION START -->"
END = "<!-- SUBMISSION END -->"


def _submission() -> str:
    text = DRAFT.read_text(encoding="utf-8")
    assert text.count(START) == 1
    assert text.count(END) == 1
    return text.split(START, 1)[1].split(END, 1)[0]


def test_submission_is_at_most_2000_words() -> None:
    # Counts every whitespace-separated token, table cells included, to stay conservative.
    words = [token for token in _submission().split() if re.search(r"[A-Za-z0-9]", token)]
    assert len(words) <= 2000


def test_submission_has_fewer_than_10_tables_and_figures() -> None:
    body = _submission()
    tables = re.findall(r"^\*\*Table \d+\.", body, flags=re.MULTILINE)
    figures = re.findall(r"^\*\*Figure \d+\.", body, flags=re.MULTILINE)
    separators = re.findall(r"^\| ?-{3}", body, flags=re.MULTILINE)
    assert len(separators) == len(tables)
    assert len(tables) + len(figures) < 10
