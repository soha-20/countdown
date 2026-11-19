import io
import re
from datetime import date

import display

TODAY = date(2026, 11, 18)
ANSI = re.compile(r"\033\[[0-9;]*m")


def ev(id_, date_text, name="E"):
    return {"id": id_, "name": name, "date": date_text}


SAMPLE = [ev(1, "2026-12-10", "Math final"), ev(2, "2026-11-20", "Physics quiz"),
          ev(3, "2026-11-24", "Essay due"), ev(4, "2026-11-01", "Midterm")]


# --- R3 / R6: color only where it helps ---------------------------------------

class Tty(io.StringIO):
    def isatty(self):
        return True


def test_r6_color_on_terminal_and_disabled_by_flag_or_env(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert display.use_color(False, Tty()) is True
    assert display.use_color(True, Tty()) is False
    assert display.use_color(False, io.StringIO()) is False
    monkeypatch.setenv("NO_COLOR", "1")
    assert display.use_color(False, Tty()) is False


def test_r3_rows_colored_by_tier():
    text = display.dashboard(SAMPLE, TODAY, color=True)
    lines = text.splitlines()
    def line_for(name):
        return next(l for l in lines if l.startswith("│") and name in l)
    assert display.TIER_COLORS["URGENT"] in line_for("Physics quiz")
    assert display.TIER_COLORS["SOON"] in line_for("Essay due")
    assert display.TIER_COLORS["LATER"] in line_for("Math final")
    assert display.TIER_COLORS["PAST"] in line_for("Midterm")


def test_r8_no_color_codes_when_color_off():
    assert "\033[" not in display.dashboard(SAMPLE, TODAY, color=False)


def test_r8_colored_output_matches_plain_once_codes_removed():
    colored = display.dashboard(SAMPLE, TODAY, color=True)
    assert ANSI.sub("", colored) == display.dashboard(SAMPLE, TODAY, color=False)


# --- R8: banner ------------------------------------------------------------------

def test_r8_banner_shows_title_and_full_date():
    lines = display.banner(TODAY)
    assert lines[0].startswith("╔") and lines[-1].startswith("╚")
    assert "COUNTDOWN" in lines[1]
    assert "Wednesday, 18 November 2026" in lines[2]
    assert len({display.width(l) for l in lines}) == 1


# --- R8: alert line ----------------------------------------------------------------

def test_r8_alert_lists_urgent_events():
    evts = [ev(1, "2026-11-20", "Quiz"), ev(2, "2026-11-19", "Essay"), ev(3, "2026-12-30", "Break")]
    assert display.alert(evts, TODAY, color=False) == \
        "⚠ 2 events in the next 3 days: Essay (tomorrow), Quiz (in 2 days)"


def test_r8_alert_singular_wording():
    assert display.alert([ev(1, "2026-11-18", "Quiz")], TODAY, color=False) == \
        "⚠ 1 event in the next 3 days: Quiz (today)"


def test_r8_alert_reassures_when_nothing_urgent():
    assert display.alert([ev(1, "2026-12-30")], TODAY, color=False) == \
        "✓ Nothing urgent in the next 3 days."


def test_r8_alert_red_when_urgent():
    assert display.alert([ev(1, "2026-11-18")], TODAY, color=True).startswith(display.RED)


def test_r8_no_alert_or_table_without_events():
    text = display.dashboard([], TODAY, empty_hint="Nothing here")
    assert "Nothing here" in text
    assert "⚠" not in text and "✓" not in text and "┌" not in text


# --- R8: boxed table ---------------------------------------------------------------

def test_r8_table_is_boxed_and_every_line_same_width():
    rows, _ = display.table(SAMPLE, TODAY, color=False)
    assert rows[0].startswith("┌") and rows[-1].startswith("└")
    assert len({display.width(r) for r in rows}) == 1


def test_r8_table_shows_weekday_with_date():
    rows, _ = display.table([ev(1, "2026-12-10", "Finals")], TODAY, color=False)
    assert "Thu 2026-12-10" in rows[3]


def test_r8_table_aligned_with_wide_characters():
    evts = [ev(1, "2026-12-10", "Party 🎉"), ev(2, "2026-12-11", "Plain")]
    rows, _ = display.table(evts, TODAY, color=False)
    assert len({display.width(r) for r in rows}) == 1


def test_r8_width_counts_wide_characters_as_two():
    assert display.width("abc") == 3
    assert display.width("🎉") == 2


# --- R6 / R8: summary ----------------------------------------------------------------

def test_r8_summary_counts_colored_by_tier():
    text = display.summary(["URGENT", "URGENT", "PAST"], color=True)
    assert display.TIER_COLORS["URGENT"] + "2 urgent" in text
    assert ANSI.sub("", text) == "2 urgent, 0 soon, 0 later, 1 past"
