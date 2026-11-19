import io
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

import countdown

TODAY = date(2026, 11, 18)
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def store(tmp_path, monkeypatch):
    path = tmp_path / "events.json"
    monkeypatch.setenv("COUNTDOWN_FILE", str(path))
    monkeypatch.delenv("NO_COLOR", raising=False)
    return path


def row(out, name):
    """The table row for an event (rows start with a box border)."""
    return next(l for l in out.splitlines() if l.startswith("│") and name in l)


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    code = countdown.main(list(argv), today=TODAY, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


# --- R1 --------------------------------------------------------------------------

def test_r1_cli_add_prints_confirmation(store):
    code, out, _ = run("add", "Math final", "2026-12-10")
    assert code == 0
    assert out.strip() == "Added #1: Math final (2026-12-10)"


def test_r1_cli_add_bad_date_errors_and_saves_nothing(store):
    code, out, err = run("add", "X", "12/10/2026")
    assert code == 1
    assert "YYYY-MM-DD" in err
    assert not store.exists()


# --- R2 --------------------------------------------------------------------------

def test_r2_cli_list_shows_days_remaining_soonest_first(store):
    run("add", "Winter break", "2026-12-19")
    run("add", "Finals", "2026-12-10")
    _, out, _ = run("list")
    lines = out.splitlines()
    assert lines.index(row(out, "Finals")) < lines.index(row(out, "Winter break"))
    assert "in 22 days" in row(out, "Finals")
    assert "in 31 days" in row(out, "Winter break")


def test_r2_cli_list_shows_id_name_and_date(store):
    run("add", "Finals", "2026-12-10")
    _, out, _ = run("list")
    r = row(out, "Finals")
    assert "#1" in r and "2026-12-10" in r


def test_r2_cli_list_empty_message(store):
    code, out, _ = run("list")
    assert code == 0
    assert "No events yet" in out


def test_r2_cli_no_subcommand_lists(store):
    run("add", "Finals", "2026-12-10")
    _, out, _ = run()
    assert "Finals" in out


# --- R3 --------------------------------------------------------------------------

def test_r3_cli_list_labels_each_tier(store):
    run("add", "Quiz", "2026-11-20")       # 2 days
    run("add", "Essay", "2026-11-24")      # 6 days
    run("add", "Finals", "2026-12-10")     # 22 days
    run("add", "Midterm", "2026-11-01")    # past
    _, out, _ = run("--no-color", "list")
    rows = {name: row(out, name) for name in ["Quiz", "Essay", "Finals", "Midterm"]}
    assert "URGENT" in rows["Quiz"]
    assert "SOON" in rows["Essay"]
    assert "LATER" in rows["Finals"]
    assert "PAST" in rows["Midterm"]


def test_r3_cli_past_events_listed_last(store):
    run("add", "Midterm", "2026-11-01")
    run("add", "Finals", "2026-12-10")
    _, out, _ = run("list")
    lines = out.splitlines()
    assert lines.index(row(out, "Finals")) < lines.index(row(out, "Midterm"))


# --- R4 --------------------------------------------------------------------------

def test_r4_cli_remove(store):
    run("add", "Finals", "2026-12-10")
    code, out, _ = run("remove", "1")
    assert code == 0
    assert out.strip() == "Removed #1: Finals"
    _, out, _ = run("list")
    assert "Finals" not in out


def test_r4_cli_edit_name_and_date(store):
    run("add", "Finals", "2026-12-10")
    code, out, _ = run("edit", "1", "--name", "Math final", "--date", "2026-12-11")
    assert code == 0
    assert out.strip() == "Updated #1: Math final (2026-12-11)"
    _, out, _ = run("list")
    assert "Math final" in out and "2026-12-11" in out


def test_r4_cli_unknown_id_errors(store):
    code, _, err = run("remove", "7")
    assert code == 1
    assert "No event with ID 7" in err


def test_r4_cli_edit_without_changes_errors(store):
    run("add", "Finals", "2026-12-10")
    code, _, err = run("edit", "1")
    assert code == 1
    assert "Nothing to edit" in err


# --- R5 --------------------------------------------------------------------------

def test_r5_cli_events_persist_to_file(store):
    run("add", "Finals", "2026-12-10")
    saved = json.loads(store.read_text(encoding="utf-8"))
    assert saved["events"] == [{"id": 1, "name": "Finals", "date": "2026-12-10"}]


def test_r5_separate_processes_share_saved_events(store):
    """Two real program runs: the second sees what the first added."""
    env = {**__import__("os").environ, "COUNTDOWN_FILE": str(store), "NO_COLOR": "1"}
    script = str(ROOT / "countdown.py")
    subprocess.run([sys.executable, script, "add", "Finals", "2099-01-01"],
                   env=env, check=True, capture_output=True)
    result = subprocess.run([sys.executable, script, "list"],
                            env=env, check=True, capture_output=True,
                            text=True, encoding="utf-8")
    assert "Finals" in result.stdout


def test_r5_cli_corrupt_file_reports_error(store):
    store.write_text("garbage", encoding="utf-8")
    code, _, err = run("add", "X", "2026-12-10")
    assert code == 1
    assert "Could not read events file" in err
    assert store.read_text(encoding="utf-8") == "garbage"


# --- R6 --------------------------------------------------------------------------

def test_r6_cli_countdown_words(store):
    run("add", "Today thing", "2026-11-18")
    run("add", "Tomorrow thing", "2026-11-19")
    run("add", "Old thing", "2026-11-17")
    _, out, _ = run("list")
    assert "today" in row(out, "Today thing")
    assert "tomorrow" in row(out, "Tomorrow thing")
    assert "yesterday" in row(out, "Old thing")


def test_r6_cli_columns_aligned(store):
    run("add", "A", "2026-12-10")
    run("add", "A much longer name", "2026-12-11")
    _, out, _ = run("list")
    rows = [l for l in out.splitlines() if "2026-12-1" in l]
    assert len({l.index("2026-12-1") for l in rows}) == 1


def test_r6_cli_summary_line(store):
    run("add", "Quiz", "2026-11-20")
    run("add", "Quiz 2", "2026-11-21")
    run("add", "Finals", "2026-12-10")
    run("add", "Midterm", "2026-11-01")
    _, out, _ = run("list")
    assert out.strip().splitlines()[-1] == "2 urgent, 0 soon, 1 later, 1 past"


def test_r6_no_color_when_not_a_terminal(store):
    run("add", "Quiz", "2026-11-20")
    _, out, _ = run("list")
    assert "\033[" not in out
