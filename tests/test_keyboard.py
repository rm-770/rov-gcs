from gcs.input.devices import KeyboardDevice


def test_press_and_release_update_state():
    kb = KeyboardDevice()
    try:
        kb._on_press(type("K", (), {"char": "w"})())
        assert "key_w" in kb.read()["buttons"]

        kb._on_release(type("K", (), {"char": "w"})())
        assert "key_w" not in kb.read()["buttons"]
    finally:
        kb.close()

def test_press_two_keys():
    kb = KeyboardDevice()
    try:
        kb._on_press(type("K", (), {"char": "w"})())
        kb._on_press(type("K", (), {"char": "a"})())
        buttons = kb.read()["buttons"]
        assert "key_w" in buttons
        assert "key_a" in buttons

        kb._on_release(type("K", (), {"char": "w"})())
        buttons = kb.read()["buttons"]
        assert "key_w" not in buttons
        assert "key_a" in buttons
    finally:
        kb.close()

def test_special_key():
    kb = KeyboardDevice()
    try:
        kb._on_press(type("K", (), {"name": "space"})())
        assert "key_space" in kb.read()["buttons"]

        kb._on_release(type("K", (), {"name": "space"})())
        assert "key_space" not in kb.read()["buttons"]
    finally:
        kb.close()

def test_press_and_release_same_key_multiple_times():
    kb = KeyboardDevice()
    try:
        kb._on_press(type("K", (), {"char": "w"})())
        kb._on_press(type("K", (), {"char": "w"})())
        assert "key_w" in kb.read()["buttons"]

        kb._on_release(type("K", (), {"char": "w"})())
        assert "key_w" not in kb.read()["buttons"]
    finally:
        kb.close()
