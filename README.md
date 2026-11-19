# Countdown

A command-line countdown for students. Calendars show dates; this shows **how
many days are left** until finals, breaks and deadlines, and flags the ones
that are close.

- An interactive menu to add, edit and remove events, with no commands to remember.
- A colored dashboard: title banner, an alert for anything due in the next 3
  days, and a boxed table sorted soonest first.
- Each event is labelled `URGENT` (0–3 days, red), `SOON` (4–7, yellow),
  `LATER` (8+, green) or `PAST` (grey).
- Events are saved to `~/.countdown.json`, so they are there next time.

## Run it

Requires Python 3 (no extra packages). From this folder:

```
py countdown.py
```

This opens the menu:

```
╔════════════════════════════════════╗
║  COUNTDOWN                         ║
║  Wednesday, 18 November 2026       ║
╚════════════════════════════════════╝

⚠ 1 event in the next 3 days: Physics quiz (in 2 days)

┌────┬────────┬──────────────┬────────────────┬─────────────┐
│ ID │ STATUS │ EVENT        │ DATE           │ WHEN        │
├────┼────────┼──────────────┼────────────────┼─────────────┤
│ #2 │ URGENT │ Physics quiz │ Fri 2026-11-20 │ in 2 days   │
│ #3 │ SOON   │ Essay due    │ Tue 2026-11-24 │ in 6 days   │
│ #1 │ LATER  │ Math final   │ Thu 2026-12-10 │ in 22 days  │
│ #4 │ PAST   │ Midterm      │ Sun 2026-11-01 │ 17 days ago │
└────┴────────┴──────────────┴────────────────┴─────────────┘

1 urgent, 1 soon, 1 later, 1 past

  [1] Add event   [2] Edit event   [3] Remove event   [4] Quit

Choose an option:
```

Type a number and answer the prompts. Press Enter on an empty answer to
cancel (or, when editing, to keep the current value). Colors appear in
PowerShell or Windows Terminal.

### Quick commands

The same actions also work as one-line commands:

```
py countdown.py add "Math final" 2026-12-10
py countdown.py list
py countdown.py edit 1 --name "Calc final" --date 2026-12-11
py countdown.py remove 1
```

Options: `--no-color` (or set `NO_COLOR`) turns off colors; set
`COUNTDOWN_FILE` to store events in a different file. If input is piped
rather than typed, `py countdown.py` just prints the list; use
`py countdown.py menu` to force the menu.

## Run the tests

Requires pytest (`py -m pip install pytest`).

```
py -m pytest
```

Each test's name starts with the requirement it checks (`test_r1_…` to
`test_r8_…`); see `spec.md` for what each requirement means.
