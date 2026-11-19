# Countdown

A command-line countdown for students. Calendars show dates; this shows **how
many days are left** until finals, breaks and deadlines, and flags the ones
that are close.

- Add events with a name and a date, edit or remove them later.
- List every event with the days remaining, soonest first.
- Each event is labelled `URGENT` (0–3 days), `SOON` (4–7), `LATER` (8+) or
  `PAST`, colored on a terminal.
- Events are saved to `~/.countdown.json`, so they are there next time.

## Run it

Requires Python 3 (no extra packages).

```
py countdown.py add "Math final" 2026-12-10
py countdown.py list
py countdown.py edit 1 --name "Calc final" --date 2026-12-11
py countdown.py remove 1
```

Example `list` output:

```
ID  STATUS  NAME          DATE        WHEN
--  ------  ------------  ----------  -----------
#2  URGENT  Physics quiz  2026-11-20  in 2 days
#3  SOON    Essay due     2026-11-24  in 6 days
#1  LATER   Math final    2026-12-10  in 22 days
#4  PAST    Midterm       2026-11-01  17 days ago

1 urgent, 1 soon, 1 later, 1 past
```

Options: `--no-color` (or set `NO_COLOR`) turns off colors; set
`COUNTDOWN_FILE` to store events in a different file.

## Run the tests

Requires pytest (`py -m pip install pytest`).

```
py -m pytest
```

Each test's name starts with the requirement it checks (`test_r1_…` to
`test_r6_…`); see `spec.md` for what each requirement means.
