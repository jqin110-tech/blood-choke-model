"""README.md and EXPLAIN.md may only state numbers that the scripts printed into results/."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NUMBER = re.compile(r"(?<![A-Za-z0-9.])\d+(?:\.\d+)?(?![A-Za-z0-9])")

# Numbers in the write-ups that are not results. Each needs a reason.
NOT_RESULTS = {
    "README.md": {"15": "count of assumptions in ASSUMPTIONS.md (checked below)"},
    "EXPLAIN.md": {"32": "32-bit numbers, in the note about a bug", "64": "64-bit numbers, in the same note"},
}
WRITE_UPS = sorted(NOT_RESULTS)


def prose(text: str) -> str:
    """A write-up without code, formulas, links' targets and image lines."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"^#+\s+\d+\.", " ", text, flags=re.M)          # numbered headings
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    return re.sub(r"\]\([^)]*\)", "]", text)


def printed_numbers() -> set[str]:
    """Every number that appears in a results file."""
    found: set[str] = set()
    for path in sorted((ROOT / "results").glob("*.txt")):
        found.update(NUMBER.findall(path.read_text()))
    return found


@pytest.mark.parametrize("name", WRITE_UPS)
def test_every_number_in_the_write_up_was_printed_by_a_script(name: str) -> None:
    printed = printed_numbers()
    stated = set(NUMBER.findall(prose((ROOT / name).read_text())))
    unexplained = sorted(n for n in stated if n not in printed and n not in NOT_RESULTS[name])
    assert not unexplained, f"{name} states numbers no script printed: {unexplained}"


@pytest.mark.parametrize("name", WRITE_UPS)
def test_the_exceptions_are_still_needed_and_true(name: str) -> None:
    stated = set(NUMBER.findall(prose((ROOT / name).read_text())))
    assert set(NOT_RESULTS[name]) <= stated, "remove exceptions the write-up no longer uses"
    assert not set(NOT_RESULTS[name]) & printed_numbers(), "remove exceptions that a script now prints"
    assumptions = re.findall(r"^\*\*A(\d+)\.", (ROOT / "ASSUMPTIONS.md").read_text(), flags=re.M)
    assert len(assumptions) == 15 and assumptions[-1] == "15"


@pytest.mark.parametrize("name", WRITE_UPS)
def test_linked_files_and_figures_exist(name: str) -> None:
    text = (ROOT / name).read_text()
    for target in re.findall(r"\]\(([^)#]+)\)", text):
        if not target.startswith("http"):
            assert (ROOT / target).exists(), f"{name} links to a missing file: {target}"


def test_readme_carries_the_required_notice_and_sections() -> None:
    text = (ROOT / "README.md").read_text()
    assert "not medical advice" in text.lower()
    for heading in ("## The question", "## The model", "## Results", "## Limitations", "## Sources"):
        assert heading in text
