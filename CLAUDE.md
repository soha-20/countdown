# CLAUDE.md

Standing rules for this project.

## Language
- Python 3 (3.13 on this machine), standard library only for the program.
- pytest is the only dev dependency.

## Run the program
```
py countdown.py add "Finals" 2026-12-10
py countdown.py list
py countdown.py edit 1 --date 2026-12-11
py countdown.py remove 1
```
Events are saved to `~/.countdown.json`; set `COUNTDOWN_FILE` to use another file.

## Run the tests
```
py -m pytest
```

## Rules
- Requirements live in `problem.md` (R1–R6; the second "R5" is R6). How each is met is in `spec.md` — keep code and spec in sync.
- Every test names the requirement ID it checks, in the test function name (e.g. `test_r3_three_days_is_urgent`).
- Tests must never touch the real `~/.countdown.json`: use `COUNTDOWN_FILE` pointing at a pytest `tmp_path`.
- Tests must not depend on the real current date: pass a fixed `today` into the logic.
- Commit in small steps; messages say what changed and why.
- Do not commit CLAUDE.md.
