# Countdown — Specification

A command-line tool that shows students how many days are left until their
events (finals, breaks, deadlines), and flags the ones that are close.

## Decisions from clarification

- R1 means an event has a **name** and a **date**.
- `problem.md` lists R5 twice. The second one (readability) is treated as **R6**.
- Dates are typed as `YYYY-MM-DD` only.
- Urgency has three tiers (see R3).
- Past events are kept and shown as `PAST` until the user removes them.
- The interface is subcommands: `add`, `list`, `edit`, `remove`.

## Interface

```
py countdown.py add "<name>" <YYYY-MM-DD>
py countdown.py list
py countdown.py edit <id> [--name "<new name>"] [--date <YYYY-MM-DD>]
py countdown.py remove <id>
```

Running with no subcommand behaves like `list`.

Every event gets a numeric **ID** when it is added. IDs are shown in `list` and
are used by `edit` and `remove`, so two events can share a name. IDs are never
reused after removal.

Errors (bad date, unknown ID, empty name, nothing to edit) print a message to
stderr and exit with status 1. Successful commands exit with status 0.

## Requirements

### R1 — Add an event with a name and a date

- `add "<name>" <YYYY-MM-DD>` stores a new event and prints
  `Added #<id>: <name> (<date>)`.
- The name must not be empty or only whitespace; surrounding spaces are trimmed.
- The date must be a real calendar date in `YYYY-MM-DD` form
  (`2026-02-30` and `12/03/2026` are rejected).
- Dates in the past are allowed (they will show as PAST).

### R2 — See all events with days remaining, soonest first

- `list` prints one line per event with: ID, name, date, and days remaining.
- Days remaining = event date − today, in whole calendar days.
- Events are sorted by date, soonest first. Events on the same date keep the
  order they were added (by ID).
- Past events appear at the bottom, most recent past first (see R3).
- With no events, `list` prints `No events yet. Add one with: py countdown.py add "<name>" <YYYY-MM-DD>`.

### R3 — Tell at a glance which events are urgent

Each event gets a status label based on days remaining:

| Days remaining | Label    | Color  |
|----------------|----------|--------|
| 0 – 3          | `URGENT` | red    |
| 4 – 7          | `SOON`   | yellow |
| 8 or more      | `LATER`  | green  |
| below 0        | `PAST`   | grey   |

- The label is always printed as text, so urgency is visible even without color.
- Upcoming events (URGENT/SOON/LATER) are listed first by date; PAST events
  follow, most recent first.

### R4 — Remove or edit an event

- `remove <id>` deletes the event and prints `Removed #<id>: <name>`.
- `edit <id> --name "<name>"` and/or `--date <YYYY-MM-DD>` changes the given
  fields and prints `Updated #<id>: <name> (<date>)`.
- `edit` with neither option is an error.
- Name and date in `edit` follow the same validation as R1.
- An unknown ID is an error and nothing is changed.

### R5 — Keep events saved between sessions

- Events are stored in a JSON file, by default `~/.countdown.json`.
- The environment variable `COUNTDOWN_FILE` overrides the path (used by tests).
- Each command loads the file, applies its change, and writes it back. A missing
  file means "no events". The file stores events and the next ID to assign.
- Writes go to a temporary file which is then renamed over the old one, so a
  crash mid-write does not corrupt existing data.
- A corrupt/unreadable file produces a clear error instead of being overwritten.

### R6 — Easy to read and understand

- Days remaining are written in words: `today`, `tomorrow`, `in 5 days`,
  `yesterday`, `3 days ago`.
- Columns are aligned so names, dates and countdowns line up.
- Colors are used only when output is a terminal and the `NO_COLOR` environment
  variable is not set; `--no-color` turns them off explicitly.
- A one-line summary is printed under the list, e.g.
  `2 urgent, 1 soon, 4 later, 1 past`.

## Design

- Language: Python 3 (standard library only; pytest for tests).
- `countdown.py` — CLI entry point (argparse) and output formatting.
- `events.py` — pure logic (parse date, add/edit/remove, days remaining,
  status label, sort, wording). Functions take `today` as a parameter so
  tests can fix the date.
- `storage.py` — load/save the JSON file.
- `tests/` — pytest tests; every test name or docstring names the requirement
  ID it checks (e.g. `test_r3_three_days_is_urgent`).
