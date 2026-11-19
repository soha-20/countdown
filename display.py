"""Rendering: banner, urgent alert, boxed table, summary (R3, R6, R8)."""

import os
import unicodedata
from datetime import date

import events

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[1;36m"
RED = "\033[1;31m"
GREEN_OK = "\033[1;32m"
TIER_COLORS = {
    events.URGENT: "\033[1;31m",  # bold red
    events.SOON: "\033[33m",      # yellow
    events.LATER: "\033[32m",     # green
    events.PAST: "\033[90m",      # grey
}
TIER_ORDER = [events.URGENT, events.SOON, events.LATER, events.PAST]

EMPTY_HINT_CLI = 'No events yet. Add one with: py countdown.py add "<name>" <YYYY-MM-DD>'


def use_color(no_color_flag, stream):
    """Color only on a real terminal, unless NO_COLOR or --no-color is set (R6)."""
    if no_color_flag or os.environ.get("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def enable_windows_ansi():
    """Older Windows consoles need this before ANSI color codes work."""
    if os.name == "nt":
        os.system("")


def paint(text, code, color):
    return f"{code}{text}{RESET}" if color else text


def width(text):
    """Columns the text takes on screen; wide chars (emoji, CJK) take two (R8)."""
    total = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        total += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return total


def pad(text, w):
    return text + " " * (w - width(text))


def banner(today):
    """Double-line title box with today's date (R8)."""
    lines = ["COUNTDOWN", f"{today:%A}, {today.day} {today:%B %Y}"]
    inner = max(36, max(width(l) for l in lines) + 4)
    out = ["╔" + "═" * inner + "╗"]
    out += ["║  " + pad(l, inner - 2) + "║" for l in lines]
    out.append("╚" + "═" * inner + "╝")
    return out


def alert(evts, today, color):
    """One line flagging urgent events, or reassurance if there are none (R8)."""
    if not evts:
        return None
    urgent = [e for e in events.sorted_events(evts, today)
              if events.status(events.days_remaining(e, today)) == events.URGENT]
    if not urgent:
        return paint("✓ Nothing urgent in the next 3 days.", GREEN_OK, color)
    noun = "event" if len(urgent) == 1 else "events"
    items = ", ".join(
        f"{e['name']} ({events.countdown_words(events.days_remaining(e, today))})"
        for e in urgent)
    return paint(f"⚠ {len(urgent)} {noun} in the next 3 days: {items}", RED, color)


def table(evts, today, color):
    """Box-drawn table, each row colored by urgency tier (R2, R3, R8)."""
    headers = ["ID", "STATUS", "EVENT", "DATE", "WHEN"]
    rows = []
    for e in events.sorted_events(evts, today):
        days = events.days_remaining(e, today)
        d = date.fromisoformat(e["date"])
        rows.append(([f"#{e['id']}", events.status(days), e["name"],
                      f"{d:%a} {e['date']}", events.countdown_words(days)],
                     events.status(days)))
    widths = [max(width(h), *(width(r[0][i]) for r in rows)) for i, h in enumerate(headers)]

    def border(left, mid, right):
        return left + mid.join("─" * (w + 2) for w in widths) + right

    def line(cells, code):
        return "│" + "│".join(" " + paint(pad(c, w), code, color) + " "
                              for c, w in zip(cells, widths)) + "│"

    out = [border("┌", "┬", "┐"), line(headers, BOLD), border("├", "┼", "┤")]
    out += [line(cells, TIER_COLORS[tier]) for cells, tier in rows]
    out.append(border("└", "┴", "┘"))
    return out, [tier for _, tier in rows]


def summary(tiers, color):
    """Count of events per tier, each in its color (R6, R8)."""
    return ", ".join(paint(f"{tiers.count(t)} {t.lower()}", TIER_COLORS[t], color)
                     for t in TIER_ORDER)


def dashboard(evts, today, color=False, empty_hint=EMPTY_HINT_CLI):
    """Full screen: banner, alert, table, summary."""
    out = [paint(l, CYAN, color) for l in banner(today)]
    out.append("")
    if not evts:
        out.append(empty_hint)
        return "\n".join(out)
    out += [alert(evts, today, color), ""]
    rows, tiers = table(evts, today, color)
    out += rows
    out += ["", summary(tiers, color)]
    return "\n".join(out)
