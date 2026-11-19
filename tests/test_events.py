from datetime import date

import pytest

import events
from events import EventError
from storage import empty_data

TODAY = date(2026, 11, 18)


def ev(id_, date_text, name="E"):
    return {"id": id_, "name": name, "date": date_text}


# --- R1: add an event with a name and a date ---------------------------------

def test_r1_add_event_stores_name_and_date():
    data = empty_data()
    e = events.add_event(data, "Finals", "2026-12-10")
    assert e == {"id": 1, "name": "Finals", "date": "2026-12-10"}
    assert data["events"] == [e]


def test_r1_ids_increase_and_are_not_reused():
    data = empty_data()
    events.add_event(data, "A", "2026-12-01")
    events.remove_event(data, 1)
    e = events.add_event(data, "B", "2026-12-02")
    assert e["id"] == 2


def test_r1_name_is_trimmed():
    data = empty_data()
    assert events.add_event(data, "  Finals  ", "2026-12-10")["name"] == "Finals"


@pytest.mark.parametrize("name", ["", "   "])
def test_r1_empty_name_rejected(name):
    with pytest.raises(EventError):
        events.add_event(empty_data(), name, "2026-12-10")


@pytest.mark.parametrize("bad", ["12/03/2026", "2026-2-3", "Dec 3", "2026-02-30", "2026-13-01", ""])
def test_r1_invalid_dates_rejected(bad):
    with pytest.raises(EventError):
        events.add_event(empty_data(), "X", bad)


def test_r1_past_date_allowed():
    e = events.add_event(empty_data(), "Old", "2020-01-01")
    assert e["date"] == "2020-01-01"


# --- R2: days remaining, soonest first ----------------------------------------

def test_r2_days_remaining_counts_calendar_days():
    assert events.days_remaining(ev(1, "2026-11-18"), TODAY) == 0
    assert events.days_remaining(ev(1, "2026-11-19"), TODAY) == 1
    assert events.days_remaining(ev(1, "2026-12-03"), TODAY) == 15
    assert events.days_remaining(ev(1, "2026-11-15"), TODAY) == -3


def test_r2_sorted_soonest_first():
    es = [ev(1, "2026-12-20"), ev(2, "2026-11-20"), ev(3, "2026-12-01")]
    assert [e["id"] for e in events.sorted_events(es, TODAY)] == [2, 3, 1]


def test_r2_same_date_keeps_added_order():
    es = [ev(3, "2026-12-01"), ev(1, "2026-12-01"), ev(2, "2026-12-01")]
    assert [e["id"] for e in events.sorted_events(es, TODAY)] == [1, 2, 3]


# --- R3: urgency tiers ----------------------------------------------------------

@pytest.mark.parametrize("days, label", [
    (0, "URGENT"), (3, "URGENT"),
    (4, "SOON"), (7, "SOON"),
    (8, "LATER"), (100, "LATER"),
    (-1, "PAST"), (-30, "PAST"),
])
def test_r3_status_tiers(days, label):
    assert events.status(days) == label


def test_r3_past_events_listed_after_upcoming_most_recent_first():
    es = [ev(1, "2026-11-01"), ev(2, "2026-12-25"), ev(3, "2026-11-17"), ev(4, "2026-11-18")]
    assert [e["id"] for e in events.sorted_events(es, TODAY)] == [4, 2, 3, 1]


# --- R4: remove or edit -----------------------------------------------------------

def test_r4_remove_event():
    data = empty_data()
    events.add_event(data, "A", "2026-12-01")
    events.add_event(data, "B", "2026-12-02")
    removed = events.remove_event(data, 1)
    assert removed["name"] == "A"
    assert [e["id"] for e in data["events"]] == [2]


def test_r4_remove_unknown_id_is_error():
    with pytest.raises(EventError):
        events.remove_event(empty_data(), 99)


def test_r4_edit_name_only():
    data = empty_data()
    events.add_event(data, "A", "2026-12-01")
    e = events.edit_event(data, 1, name="Finals")
    assert e == {"id": 1, "name": "Finals", "date": "2026-12-01"}


def test_r4_edit_date_only():
    data = empty_data()
    events.add_event(data, "A", "2026-12-01")
    e = events.edit_event(data, 1, date_text="2026-12-05")
    assert e == {"id": 1, "name": "A", "date": "2026-12-05"}


def test_r4_edit_with_nothing_is_error():
    data = empty_data()
    events.add_event(data, "A", "2026-12-01")
    with pytest.raises(EventError):
        events.edit_event(data, 1)


def test_r4_edit_unknown_id_is_error():
    with pytest.raises(EventError):
        events.edit_event(empty_data(), 5, name="X")


def test_r4_edit_with_bad_date_changes_nothing():
    data = empty_data()
    events.add_event(data, "A", "2026-12-01")
    with pytest.raises(EventError):
        events.edit_event(data, 1, name="New", date_text="bad")
    assert data["events"][0] == {"id": 1, "name": "A", "date": "2026-12-01"}


# --- R6: readable wording -----------------------------------------------------------

@pytest.mark.parametrize("days, words", [
    (0, "today"), (1, "tomorrow"), (5, "in 5 days"),
    (-1, "yesterday"), (-3, "3 days ago"),
])
def test_r6_countdown_in_words(days, words):
    assert events.countdown_words(days) == words
