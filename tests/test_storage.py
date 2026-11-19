import pytest

import storage


def test_r5_missing_file_means_no_events(tmp_path):
    data = storage.load(tmp_path / "none.json")
    assert data == {"next_id": 1, "events": []}


def test_r5_saved_events_load_back(tmp_path):
    path = tmp_path / "events.json"
    data = {"next_id": 2, "events": [{"id": 1, "name": "Finals", "date": "2026-12-10"}]}
    storage.save(data, path)
    assert storage.load(path) == data


def test_r5_save_leaves_no_temp_file(tmp_path):
    path = tmp_path / "events.json"
    storage.save(storage.empty_data(), path)
    assert [p.name for p in tmp_path.iterdir()] == ["events.json"]


def test_r5_corrupt_file_raises_clear_error_and_is_not_overwritten(tmp_path):
    path = tmp_path / "events.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load(path)
    assert path.read_text(encoding="utf-8") == "{not json"


def test_r5_wrong_shape_file_raises_error(tmp_path):
    path = tmp_path / "events.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load(path)


def test_r5_countdown_file_env_overrides_path(tmp_path, monkeypatch):
    path = tmp_path / "custom.json"
    monkeypatch.setenv("COUNTDOWN_FILE", str(path))
    assert storage.data_path() == path
