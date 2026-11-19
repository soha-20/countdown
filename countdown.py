"""Countdown: see how many days are left until your events.

Usage:
    py countdown.py add "<name>" <YYYY-MM-DD>
    py countdown.py list
    py countdown.py edit <id> [--name "<name>"] [--date <YYYY-MM-DD>]
    py countdown.py remove <id>
"""

import argparse
import os
import sys
from datetime import date

import events
import storage

COLORS = {
    events.URGENT: "\033[1;31m",  # bold red
    events.SOON: "\033[33m",      # yellow
    events.LATER: "\033[32m",     # green
    events.PAST: "\033[90m",      # grey
}
RESET = "\033[0m"
TIER_ORDER = [events.URGENT, events.SOON, events.LATER, events.PAST]

EMPTY_MESSAGE = 'No events yet. Add one with: py countdown.py add "<name>" <YYYY-MM-DD>'


def use_color(no_color_flag, stream):
    """Color only on a real terminal, unless NO_COLOR or --no-color is set (R6)."""
    if no_color_flag or os.environ.get("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def format_list(evts, today, color=False):
    """Render the event table plus a summary line (R2, R3, R6)."""
    if not evts:
        return EMPTY_MESSAGE
    rows = []
    for e in events.sorted_events(evts, today):
        days = events.days_remaining(e, today)
        rows.append((f"#{e['id']}", events.status(days), e["name"], e["date"],
                     events.countdown_words(days)))

    headers = ("ID", "STATUS", "NAME", "DATE", "WHEN")
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]

    def line(cells, tier=None):
        padded = [c.ljust(w) for c, w in zip(cells, widths)]
        if color and tier:
            padded[1] = COLORS[tier] + padded[1] + RESET
        return "  ".join(padded).rstrip()

    out = [line(headers), line(["-" * w for w in widths])]
    out += [line(r, tier=r[1]) for r in rows]

    counts = {t: sum(1 for r in rows if r[1] == t) for t in TIER_ORDER}
    out.append("")
    out.append(", ".join(f"{counts[t]} {t.lower()}" for t in TIER_ORDER))
    return "\n".join(out)


def build_parser():
    p = argparse.ArgumentParser(
        prog="countdown",
        description="See how many days are left until your events.",
    )
    p.add_argument("--no-color", action="store_true", help="turn off colored output")
    sub = p.add_subparsers(dest="command")

    a = sub.add_parser("add", help="add an event")
    a.add_argument("name", help='event name, e.g. "Math final"')
    a.add_argument("date", help="event date as YYYY-MM-DD")

    sub.add_parser("list", help="list events, soonest first")

    e = sub.add_parser("edit", help="change an event's name and/or date")
    e.add_argument("id", type=int, help="event ID shown in list")
    e.add_argument("--name", help="new name")
    e.add_argument("--date", help="new date as YYYY-MM-DD")

    r = sub.add_parser("remove", help="remove an event")
    r.add_argument("id", type=int, help="event ID shown in list")
    return p


def main(argv=None, today=None, out=None, err=None):
    out = out or sys.stdout
    err = err or sys.stderr
    today = today or date.today()
    args = build_parser().parse_args(argv)
    command = args.command or "list"

    try:
        data = storage.load()
        if command == "add":
            e = events.add_event(data, args.name, args.date)
            storage.save(data)
            print(f"Added #{e['id']}: {e['name']} ({e['date']})", file=out)
        elif command == "edit":
            e = events.edit_event(data, args.id, name=args.name, date_text=args.date)
            storage.save(data)
            print(f"Updated #{e['id']}: {e['name']} ({e['date']})", file=out)
        elif command == "remove":
            e = events.remove_event(data, args.id)
            storage.save(data)
            print(f"Removed #{e['id']}: {e['name']}", file=out)
        else:
            color = use_color(args.no_color, out)
            if color and os.name == "nt":
                os.system("")  # enables ANSI escape codes in older Windows consoles
            print(format_list(data["events"], today, color=color), file=out)
    except (events.EventError, storage.StorageError) as ex:
        print(f"Error: {ex}", file=err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
