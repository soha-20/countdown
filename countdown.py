"""Countdown: see how many days are left until your events.

Usage:
    py countdown.py add "<name>" <YYYY-MM-DD>
    py countdown.py list
    py countdown.py edit <id> [--name "<name>"] [--date <YYYY-MM-DD>]
    py countdown.py remove <id>
"""

import argparse
import sys
from datetime import date

import display
import events
import storage


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
            color = display.use_color(args.no_color, out)
            if color:
                display.enable_windows_ansi()
            print(display.dashboard(data["events"], today, color=color), file=out)
    except (events.EventError, storage.StorageError) as ex:
        print(f"Error: {ex}", file=err)
        return 1
    return 0


if __name__ == "__main__":
    # Box-drawing characters need UTF-8 when output is redirected to a file/pipe (R8).
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main())
