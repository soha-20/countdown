"""Pure event logic: validation, countdown, urgency, sorting, editing.

Every function that depends on the current date takes `today` explicitly
so behaviour is testable and deterministic.
"""

import re
from datetime import date

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

URGENT, SOON, LATER, PAST = "URGENT", "SOON", "LATER", "PAST"


class EventError(Exception):
    """Raised for invalid user input (bad name, bad date, unknown ID)."""


def parse_date(text):
    """Parse a strict YYYY-MM-DD date (R1)."""
    if not DATE_RE.match(text):
        raise EventError(f"Invalid date '{text}': use YYYY-MM-DD, e.g. 2026-12-03.")
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise EventError(f"Invalid date '{text}': that day does not exist.") from None


def clean_name(name):
    """Trim a name and reject empty ones (R1)."""
    name = name.strip()
    if not name:
        raise EventError("Event name cannot be empty.")
    return name


def add_event(data, name, date_text):
    """Add an event and return it (R1)."""
    event = {
        "id": data["next_id"],
        "name": clean_name(name),
        "date": parse_date(date_text).isoformat(),
    }
    data["events"].append(event)
    data["next_id"] += 1
    return event


def find_event(data, event_id):
    for event in data["events"]:
        if event["id"] == event_id:
            return event
    raise EventError(f"No event with ID {event_id}.")


def remove_event(data, event_id):
    """Remove an event and return it (R4)."""
    event = find_event(data, event_id)
    data["events"].remove(event)
    return event


def edit_event(data, event_id, name=None, date_text=None):
    """Change an event's name and/or date (R4). Validates before changing anything."""
    if name is None and date_text is None:
        raise EventError("Nothing to edit: give --name and/or --date.")
    event = find_event(data, event_id)
    new_name = clean_name(name) if name is not None else event["name"]
    new_date = parse_date(date_text).isoformat() if date_text is not None else event["date"]
    event["name"], event["date"] = new_name, new_date
    return event


def days_remaining(event, today):
    """Whole calendar days from today to the event (R2). Negative if past."""
    return (date.fromisoformat(event["date"]) - today).days


def status(days):
    """Urgency tier for a number of days remaining (R3)."""
    if days < 0:
        return PAST
    if days <= 3:
        return URGENT
    if days <= 7:
        return SOON
    return LATER


def sorted_events(events, today):
    """Upcoming events soonest first, then past events most recent first (R2, R3).

    Ties on the same date keep the order they were added (by ID).
    """
    upcoming = [e for e in events if days_remaining(e, today) >= 0]
    past = [e for e in events if days_remaining(e, today) < 0]
    upcoming.sort(key=lambda e: (e["date"], e["id"]))
    past.sort(key=lambda e: (-days_remaining(e, today), e["id"]))
    return upcoming + past


def countdown_words(days):
    """Human wording for days remaining (R6)."""
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    if days == -1:
        return "yesterday"
    if days > 1:
        return f"in {days} days"
    return f"{-days} days ago"
