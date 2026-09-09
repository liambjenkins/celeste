import importlib

import pytest


@pytest.fixture
def storage(tmp_path, monkeypatch):
    """Fresh flashcards.storage module pointed at a throwaway DB per
    test, so tests never touch the real flashcards/data/flashcards.db."""

    import flashcards.storage as storage_module

    monkeypatch.setattr(storage_module, "DB_PATH", tmp_path / "test_flashcards.db")
    importlib.reload(storage_module)
    monkeypatch.setattr(storage_module, "DB_PATH", tmp_path / "test_flashcards.db")
    storage_module.init_db()
    return storage_module


def test_card_index_roundtrip(storage):
    for planet in storage.PLANETS:
        for house in storage.HOUSES:
            index = storage.card_index(planet, house)
            assert storage.card_at_index(index) == (planet, house)


def test_total_cards_is_84(storage):
    assert storage.total_cards() == 84


def test_get_card_defaults_to_draft_with_no_fragments(storage):
    card = storage.get_card("mars", 6)
    assert card == {"planet": "mars", "house": 6, "fragments": [], "status": "draft"}


def test_save_and_get_card_roundtrip(storage):
    storage.save_card("venus", 5, ["Fragment one.", "Fragment two.", "  "], "reviewed")
    card = storage.get_card("venus", 5)
    assert card["fragments"] == ["Fragment one.", "Fragment two."]
    assert card["status"] == "reviewed"


def test_save_card_rejects_unknown_status(storage):
    with pytest.raises(ValueError):
        storage.save_card("venus", 5, ["x"], "not_a_real_status")


def test_progress_summary_counts_fragments_and_locked(storage):
    storage.save_card("sun", 1, ["a"], "draft")
    storage.save_card("moon", 3, [], "draft")  # no fragments -- shouldn't count
    storage.save_card("mars", 6, ["b"], "locked")

    progress = storage.progress_summary()
    assert progress["total"] == 84
    assert progress["with_fragments"] == 2
    assert progress["locked"] == 1


def test_adjacent_planet_card_wraps_house_12_to_1(storage):
    storage.save_card("sun", 1, ["seed fragment"], "draft")
    reference = storage.adjacent_planet_card("sun", 12)
    assert reference["house"] == 1
    assert reference["fragments"] == ["seed fragment"]
