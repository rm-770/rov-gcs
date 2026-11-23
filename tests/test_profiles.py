import pytest

from gcs.core.eventbus import EventBus
from gcs.core.events import ControllerConnected, ProfileChanged
from gcs.input.mapping import Mapping
from gcs.input.profiles import ProfileManager, ProfileStore


def test_save_then_load_round_trip(tmp_path):
    store = ProfileStore(tmp_path)
    store.save(Mapping(name="alpha", buttons={"button_0": "light"}))
    assert Mapping.from_dict(store.load_dict("alpha")).buttons == {"button_0": "light"}
    assert store.list_names() == ["alpha"]


def test_finds_profile_for_known_controller(tmp_path):
    store = ProfileStore(tmp_path)
    store.save(Mapping(name="alpha"))
    store.save(Mapping(name="beta", controllers=("Pad X",)))
    assert store.find_for_controller("Pad X") == "beta"
    assert store.find_for_controller("Unknown Pad") is None


def test_profile_name_cannot_escape_the_folder(tmp_path):
    with pytest.raises(ValueError):
        ProfileStore(tmp_path).path_for("../evil")


def test_manager_loads_default_then_switches_when_controller_connects(tmp_path):
    store = ProfileStore(tmp_path)
    store.save(Mapping(name="default"))
    store.save(Mapping(name="xbox", controllers=("Pad X",)))
    bus = EventBus()
    changes = bus.subscribe(ProfileChanged)
    manager = ProfileManager(bus, store, "default")
    manager.start()
    try:
        # get(timeout=...) waits for the event but fails the test instead of hanging forever.
        assert changes.get(timeout=2).name == "default"
        bus.publish(ControllerConnected(name="Pad X"))
        assert changes.get(timeout=2).name == "xbox"
    finally:
        manager.stop()
        manager.join(timeout=2)