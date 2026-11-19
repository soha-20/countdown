"""Interactive numbered menu (R7).

`input_fn` is injected so tests can script a whole session.
"""

import sys

import display
import events
import storage

CLEAR = "\033[2J\033[H"
EMPTY_HINT = "No events yet. Choose [1] to add your first one."
MENU_LINE = "  [1] Add event   [2] Edit event   [3] Remove event   [4] Quit"
QUIT_WORDS = {"4", "q", "quit", "exit"}
OK, INFO, ERROR = "ok", "info", "error"


class _Quit(Exception):
    """User pressed Ctrl+C or input ended."""


def run_menu(today, input_fn=input, out=None, color=False, clear=False):
    out = out or sys.stdout

    def show(text=""):
        print(text, file=out)

    def styled(kind, text):
        if kind == OK:
            return display.paint("✓ " + text, display.GREEN_OK, color)
        if kind == ERROR:
            return display.paint("✗ " + text, display.RED, color)
        return text

    def ask(prompt):
        try:
            return input_fn(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            raise _Quit from None

    def ask_date(prompt):
        """Ask until a valid date is typed. Returns '' if left blank."""
        while True:
            text = ask(prompt)
            if not text:
                return ""
            try:
                events.parse_date(text)
                return text
            except events.EventError as ex:
                show(styled(ERROR, str(ex)))

    def ask_event(data, verb):
        """Ask for an event ID. Returns the event, or None if left blank."""
        text = ask(f"ID of the event to {verb} (e.g. 2): ").lstrip("#")
        if not text:
            return None
        if not text.isdigit():
            raise events.EventError(
                f"'{text}' is not an event ID. Use the number in the ID column.")
        return events.find_event(data, int(text))

    def do_add(data):
        name = ask("Event name (Enter to cancel): ")
        if not name:
            return INFO, "Cancelled."
        date_text = ask_date("Date as YYYY-MM-DD (Enter to cancel): ")
        if not date_text:
            return INFO, "Cancelled."
        e = events.add_event(data, name, date_text)
        storage.save(data)
        return OK, f"Added #{e['id']}: {e['name']} ({e['date']})"

    def do_edit(data):
        if not data["events"]:
            return ERROR, "There are no events to edit yet."
        e = ask_event(data, "edit")
        if e is None:
            return INFO, "Cancelled."
        name = ask(f"New name [{e['name']}] (Enter to keep): ")
        date_text = ask_date(f"New date [{e['date']}] (Enter to keep): ")
        if not name and not date_text:
            return INFO, "No changes made."
        e = events.edit_event(data, e["id"], name=name or None, date_text=date_text or None)
        storage.save(data)
        return OK, f"Updated #{e['id']}: {e['name']} ({e['date']})"

    def do_remove(data):
        if not data["events"]:
            return ERROR, "There are no events to remove."
        e = ask_event(data, "remove")
        if e is None:
            return INFO, "Cancelled."
        if ask(f"Remove #{e['id']} {e['name']}? (y/N): ").lower() not in ("y", "yes"):
            return INFO, "Kept it, nothing removed."
        events.remove_event(data, e["id"])
        storage.save(data)
        return OK, f"Removed #{e['id']}: {e['name']}"

    actions = {"1": do_add, "2": do_edit, "3": do_remove}
    message = ""
    try:
        while True:
            try:
                data = storage.load()
            except storage.StorageError as ex:
                show(styled(ERROR, str(ex)))
                return 1
            if clear:
                out.write(CLEAR)
            show(display.dashboard(data["events"], today, color, empty_hint=EMPTY_HINT))
            show()
            if message:
                show(message)
                show()
            show(display.paint(MENU_LINE, display.BOLD, color))
            choice = ask("\nChoose an option: ").lower()
            if choice in QUIT_WORDS:
                break
            if choice not in actions:
                message = styled(ERROR, "Please choose 1, 2, 3 or 4.")
                continue
            try:
                message = styled(*actions[choice](data))
            except events.EventError as ex:
                message = styled(ERROR, str(ex))
    except _Quit:
        show()
    show("Goodbye! Good luck with your events.")
    return 0
