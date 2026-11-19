import io
import json
from datetime import date

import pytest

import countdown
import menu

TODAY = date(2026, 11, 18)


@pytest.fixture
def store(tmp_path, monkeypatch):
    path = tmp_path / "events.json"
    monkeypatch.setenv("COUNTDOWN_FILE", str(path))
    monkeypatch.delenv("NO_COLOR", raising=False)
    return path


def session(*answers, color=False, clear=False):
    """Run the menu with scripted answers; returns (exit code, output)."""
    it = iter(answers)

    def fake_input(prompt):
        try:
            return next(it)
        except StopIteration:
            raise EOFError from None

    out = io.StringIO()
    code = menu.run_menu(TODAY, input_fn=fake_input, out=out, color=color, clear=clear)
    return code, out.getvalue()


def saved(store):
    return json.loads(store.read_text(encoding="utf-8"))["events"]


def last_screen(out):
    """Text of the final redraw (from the last banner onward)."""
    return out[out.rindex("╔"):]


# --- R7: menu basics ------------------------------------------------------------

def test_r7_menu_shows_dashboard_and_options(store):
    _, out = session("4")
    assert "COUNTDOWN" in out
    assert "[1] Add event" in out and "[4] Quit" in out
    assert "No events yet. Choose [1]" in out


@pytest.mark.parametrize("word", ["4", "q", "quit", "Q"])
def test_r7_quit_choices(store, word):
    code, out = session(word)
    assert code == 0
    assert "Goodbye" in out


def test_r7_end_of_input_quits_cleanly(store):
    code, out = session()
    assert code == 0
    assert "Goodbye" in out


def test_r7_ctrl_c_quits_cleanly(store):
    def interrupt(prompt):
        raise KeyboardInterrupt
    out = io.StringIO()
    assert menu.run_menu(TODAY, input_fn=interrupt, out=out) == 0
    assert "Goodbye" in out.getvalue()


def test_r7_unknown_choice_shows_hint(store):
    _, out = session("9", "4")
    assert "Please choose 1, 2, 3 or 4." in out


# --- R7: add ---------------------------------------------------------------------

def test_r7_add_event(store):
    _, out = session("1", "Math final", "2026-12-10", "4")
    assert saved(store) == [{"id": 1, "name": "Math final", "date": "2026-12-10"}]
    screen = last_screen(out)
    assert "✓ Added #1: Math final (2026-12-10)" in screen
    assert "Math final" in screen and "in 22 days" in screen


def test_r7_add_bad_date_asks_again(store):
    _, out = session("1", "Quiz", "12/01/2026", "2026-02-30", "2026-12-01", "4")
    assert "YYYY-MM-DD" in out
    assert "does not exist" in out
    assert saved(store)[0]["date"] == "2026-12-01"


def test_r7_add_blank_name_cancels(store):
    _, out = session("1", "", "4")
    assert "Cancelled." in out
    assert not store.exists()


def test_r7_add_blank_date_cancels(store):
    _, out = session("1", "Quiz", "", "4")
    assert "Cancelled." in out
    assert not store.exists()


# --- R7: edit ---------------------------------------------------------------------

def test_r7_edit_name_keeps_date(store):
    session("1", "Quiz", "2026-12-01", "4")
    _, out = session("2", "1", "Big quiz", "", "4")
    assert saved(store) == [{"id": 1, "name": "Big quiz", "date": "2026-12-01"}]
    assert "✓ Updated #1: Big quiz (2026-12-01)" in out


def test_r7_edit_date_keeps_name_and_accepts_hash_id(store):
    session("1", "Quiz", "2026-12-01", "4")
    session("2", "#1", "", "bad", "2026-12-05", "4")
    assert saved(store) == [{"id": 1, "name": "Quiz", "date": "2026-12-05"}]


def test_r7_edit_prompt_shows_current_values(store):
    session("1", "Quiz", "2026-12-01", "4")
    prompts = []
    answers = iter(["2", "1", "", "", "4"])
    menu.run_menu(TODAY, input_fn=lambda p: (prompts.append(p), next(answers))[1],
                  out=io.StringIO())
    assert any("[Quiz]" in p for p in prompts)
    assert any("[2026-12-01]" in p for p in prompts)


def test_r7_edit_nothing_changed(store):
    session("1", "Quiz", "2026-12-01", "4")
    _, out = session("2", "1", "", "", "4")
    assert "No changes made." in out


def test_r7_edit_unknown_id_is_error(store):
    session("1", "Quiz", "2026-12-01", "4")
    _, out = session("2", "7", "4")
    assert "No event with ID 7." in out


def test_r7_edit_non_number_id_is_error(store):
    session("1", "Quiz", "2026-12-01", "4")
    _, out = session("2", "abc", "4")
    assert "is not an event ID" in out


def test_r7_edit_with_no_events(store):
    _, out = session("2", "4")
    assert "no events to edit" in out


# --- R7: remove ---------------------------------------------------------------------

def test_r7_remove_with_confirmation(store):
    session("1", "Quiz", "2026-12-01", "4")
    _, out = session("3", "1", "y", "4")
    assert saved(store) == []
    assert "✓ Removed #1: Quiz" in out


def test_r7_remove_declined_keeps_event(store):
    session("1", "Quiz", "2026-12-01", "4")
    _, out = session("3", "1", "n", "4")
    assert len(saved(store)) == 1
    assert "nothing removed" in out


def test_r7_remove_default_answer_is_no(store):
    session("1", "Quiz", "2026-12-01", "4")
    session("3", "1", "", "4")
    assert len(saved(store)) == 1


def test_r7_remove_with_no_events(store):
    _, out = session("3", "4")
    assert "no events to remove" in out


# --- R7: screen behaviour -----------------------------------------------------------

def test_r7_clears_screen_only_when_asked(store):
    _, out = session("4", clear=True)
    assert menu.CLEAR in out
    _, out = session("4", clear=False)
    assert menu.CLEAR not in out


def test_r7_messages_colored_when_color_on(store):
    _, out = session("1", "Quiz", "2026-12-01", "9", "4", color=True)
    assert "\033[1;32m✓ Added" in out
    assert "\033[1;31m✗ Please choose" in out


def test_r7_corrupt_file_reports_error(store):
    store.write_text("garbage", encoding="utf-8")
    code, out = session("4")
    assert code == 1
    assert "Could not read events file" in out


# --- R7: how the program starts ---------------------------------------------------

def run_main(argv, interactive, answers=()):
    it = iter(answers)
    out, err = io.StringIO(), io.StringIO()
    code = countdown.main(argv, today=TODAY, out=out, err=err,
                          input_fn=lambda p: next(it), interactive=interactive)
    return code, out.getvalue()


def test_r7_no_arguments_from_terminal_opens_menu(store):
    code, out = run_main([], interactive=True, answers=["4"])
    assert code == 0
    assert "[1] Add event" in out and "Goodbye" in out


def test_r7_no_arguments_when_piped_just_lists(store):
    code, out = run_main([], interactive=False)
    assert code == 0
    assert "[1] Add event" not in out
    assert "No events yet" in out


def test_r7_menu_subcommand_opens_menu(store):
    _, out = run_main(["menu"], interactive=False, answers=["4"])
    assert "[1] Add event" in out
