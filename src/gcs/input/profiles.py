"""Saving, loading, auto-selecting and live-reloading mapping profiles (R8)."""

import json
import logging
import queue
import threading
from pathlib import Path

from gcs.core.events import ControllerConnected, LoadProfileRequest, ProfileChanged
from gcs.input.mapping import Mapping

log = logging.getLogger(__name__)


class ProfileStore:
    """Reads and writes profiles as JSON files in one directory."""

    def __init__(self, directory):
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, name):
        """File path for a profile name. Rejects names like '../evil' (path traversal)."""
        if not name or Path(name).name != name:
            raise ValueError(f"invalid profile name: {name!r}")
        return self._dir / f"{name}.json"

    def list_names(self):
        """Names of all profiles on disk, alphabetically."""
        return sorted(p.stem for p in self._dir.glob("*.json"))

    def load_dict(self, name):
        """Read a profile as plain data. Raises OSError (missing) or ValueError (bad JSON)."""
        # utf-8-sig also accepts files with a BOM, which Windows Notepad and PowerShell
        # often add and which plain "utf-8" would reject.
        with open(self.path_for(name), encoding="utf-8-sig") as f:
            return json.load(f)

    def save(self, mapping):
        """Write a Mapping to disk atomically."""
        path = self.path_for(mapping.name)
        # Write to a temp file first, then rename. The rename is atomic, so the live
        # reloader can never see a half-written file.
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(mapping.to_dict(), indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)

    def find_for_controller(self, controller_name):
        """Name of the first profile that lists this controller, or None."""
        for name in self.list_names():
            try:
                data = self.load_dict(name)
            except (OSError, ValueError):
                continue  # skip unreadable profiles instead of failing the whole search
            if isinstance(data, dict) and controller_name in data.get("controllers", []):
                return name
        return None


class ProfileManager(threading.Thread):
    """Decides which profile is active and announces changes on the bus.

    It reacts to three things: startup (load the default), a controller connecting
    (load its profile), and a LoadProfileRequest. It also re-publishes the active profile
    whenever its file changes on disk, so edits apply without restarting.
    """

    POLL_SECONDS = 0.2

    def __init__(self, bus, store, default_name):
        super().__init__(name="ProfileManager", daemon=True)
        self._bus = bus
        self._store = store
        self._default = default_name
        # Subscribe in the constructor (main thread) so no event published later is missed.
        self._connected_q = bus.subscribe(ControllerConnected)
        self._request_q = bus.subscribe(LoadProfileRequest)
        self._stop_event = threading.Event()
        self._active_name = None
        self._seen_mtime = None   # last modification time we reacted to

    def stop(self):
        self._stop_event.set()

    def _mtime(self, name):
        """Modification time of a profile file, or None if it does not exist."""
        try:
            return self._store.path_for(name).stat().st_mtime
        except OSError:
            return None

    def _activate(self, name):
        """Load, validate and announce a profile. On any problem, keep the current one."""
        # Record the mtime BEFORE loading. If the file is broken we report it once,
        # and only retry after the file changes again, instead of every 0.2 s.
        self._seen_mtime = self._mtime(name)
        try:
            data = self._store.load_dict(name)
            Mapping.from_dict(data)  # validation only; raises ValueError if the profile is bad
        except (OSError, ValueError) as exc:
            log.error("Could not load profile %r (%s); keeping the current one", name, exc)
            return
        self._active_name = name
        self._bus.publish(ProfileChanged(name=name, data=data))
        log.info("Profile %r is now active", name)

    def _handle_connections(self):
        """Switch to the profile registered for a newly connected controller."""
        while True:
            try:
                event = self._connected_q.get_nowait()
            except queue.Empty:
                return
            name = self._store.find_for_controller(event.name)
            if name is None:
                log.info("No profile registered for %r; keeping %r", event.name, self._active_name)
            else:
                self._activate(name)

    def _handle_requests(self):
        """Switch profile when someone asks for one by name."""
        while True:
            try:
                event = self._request_q.get_nowait()
            except queue.Empty:
                return
            self._activate(event.name)

    def _check_for_file_changes(self):
        """Reload the active profile if its file was edited or replaced."""
        if self._active_name is None:
            return
        if self._mtime(self._active_name) != self._seen_mtime:
            log.info("Profile file %r changed on disk; reloading", self._active_name)
            self._activate(self._active_name)

    def run(self):
        log.info("Profile manager started")
        self._activate(self._default)
        # wait() returns True as soon as stop() is called, so shutdown is immediate.
        while not self._stop_event.wait(self.POLL_SECONDS):
            self._handle_connections()
            self._handle_requests()
            self._check_for_file_changes()
        log.info("Profile manager stopped")