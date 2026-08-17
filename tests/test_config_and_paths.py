import json
import os

import pytest

from src.core import config as config_module
from src.core import paths
from src.core import platform as platform_module


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Point ConfigManager at a temp file and hand back a fresh instance."""
    cfg_path = os.path.join(str(tmp_path), "cfg", "config.json")
    monkeypatch.setattr(config_module, "CONFIG_FILE", cfg_path)
    config_module.ConfigManager._instance = None
    manager = config_module.ConfigManager()
    yield manager, cfg_path
    config_module.ConfigManager._instance = None


# ------------------------------------------------------------------- config


def test_config_round_trips(isolated_config):
    manager, _ = isolated_config
    assert manager.set("custom_save_path", "/tmp/saves") is True
    config_module.ConfigManager._instance = None
    reloaded = config_module.ConfigManager()
    assert reloaded.get("custom_save_path") == "/tmp/saves"


def test_config_creates_missing_directory(isolated_config):
    manager, cfg_path = isolated_config
    assert not os.path.exists(os.path.dirname(cfg_path))
    assert manager.set("k", "v") is True
    assert os.path.isfile(cfg_path)


def test_corrupt_config_falls_back_to_defaults(isolated_config):
    manager, cfg_path = isolated_config
    os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
    with open(cfg_path, "w") as f:
        f.write('{"truncated": ')
    manager.load_config()
    assert manager.config == {}


def test_save_leaves_no_temp_files_behind(isolated_config):
    manager, cfg_path = isolated_config
    manager.set("a", 1)
    manager.set("b", 2)
    leftovers = [n for n in os.listdir(os.path.dirname(cfg_path)) if n.endswith(".tmp")]
    assert leftovers == []


def test_save_returns_false_when_write_fails(isolated_config, monkeypatch):
    """The dialog relies on this to avoid closing as though it saved."""
    manager, _ = isolated_config

    def boom(*a, **k):
        raise OSError("read-only filesystem")

    monkeypatch.setattr(config_module.os, "makedirs", boom)
    assert manager.set("k", "v") is False


def test_existing_config_survives_a_failed_write(isolated_config, monkeypatch):
    """Atomic replace means a failed write cannot truncate the good file."""
    manager, cfg_path = isolated_config
    manager.set("keep", "me")
    with open(cfg_path) as f:
        original = f.read()

    import tempfile as _tempfile

    def boom(*a, **k):
        raise OSError("no space left on device")

    monkeypatch.setattr(_tempfile, "mkstemp", boom)
    assert manager.set("new", "value") is False
    with open(cfg_path) as f:
        assert f.read() == original
    assert json.loads(original) == {"keep": "me"}


# -------------------------------------------------------------------- paths


def test_get_asset_finds_the_icon_in_a_source_checkout():
    path = paths.get_asset("icon-256.png")
    assert os.path.isfile(path), f"ikon bulunamadı: {path}"
    assert path.endswith(os.path.join("assets", "icon-256.png"))


def test_get_asset_follows_pyinstallers_unpack_directory(monkeypatch, tmp_path):
    """A frozen one-file build unpacks elsewhere and points sys._MEIPASS at it.

    Getting this wrong is silent: the icon simply never appears in the released
    binary, while it works fine from a source checkout.
    """
    monkeypatch.setattr(paths.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert paths.get_asset("icon-256.png") == os.path.join(
        str(tmp_path), "assets", "icon-256.png"
    )


def test_config_and_log_dirs_are_app_scoped():
    assert paths.get_config_dir().endswith(paths.APP_NAME)
    assert paths.get_log_dir().endswith(paths.APP_NAME)


def test_config_dir_uses_appdata_on_windows(monkeypatch):
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", r"C:\Users\u\AppData\Roaming")
    assert paths.get_config_dir() == os.path.join(
        r"C:\Users\u\AppData\Roaming", paths.APP_NAME
    )


def test_config_dir_honours_xdg_on_linux(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert paths.get_config_dir() == os.path.join(str(tmp_path), paths.APP_NAME)


# ----------------------------------------------------------------- platform


@pytest.mark.parametrize(
    "system,expected",
    [("Windows", "windows"), ("Darwin", "macos"), ("Linux", "linux"), ("Plan9", "unknown")],
)
def test_get_os_type(monkeypatch, system, expected):
    monkeypatch.setattr(platform_module.platform, "system", lambda: system)
    assert platform_module.get_os_type() == expected


@pytest.mark.parametrize(
    "system,fragment",
    [
        ("Windows", "7DaysToDie"),
        ("Darwin", os.path.join("Application Support", "7DaysToDie", "Saves")),
        ("Linux", os.path.join(".local", "share", "7DaysToDie", "Saves")),
        ("Plan9", os.path.join(".local", "share", "7DaysToDie", "Saves")),
    ],
)
def test_default_saves_path_per_os(monkeypatch, system, fragment):
    monkeypatch.setattr(platform_module.platform, "system", lambda: system)
    assert fragment in platform_module.get_default_saves_path()


def test_custom_save_path_wins_when_valid(monkeypatch, tmp_path):
    monkeypatch.setattr(
        platform_module.config, "get", lambda k, d=None: str(tmp_path)
    )
    assert platform_module.get_saves_path() == str(tmp_path)


def test_custom_save_path_ignored_when_missing(monkeypatch, tmp_path):
    missing = os.path.join(str(tmp_path), "does-not-exist")
    monkeypatch.setattr(platform_module.config, "get", lambda k, d=None: missing)
    assert platform_module.get_saves_path() != missing


def test_custom_save_path_ignored_when_empty(monkeypatch):
    monkeypatch.setattr(platform_module.config, "get", lambda k, d=None: "")
    assert platform_module.get_saves_path() == platform_module.get_default_saves_path()


def test_saves_path_is_not_frozen_at_import(monkeypatch, tmp_path):
    """Regression: SAVES_PATH used to cache this at import and go stale."""
    assert not hasattr(platform_module, "SAVES_PATH")
    first = os.path.join(str(tmp_path), "one")
    second = os.path.join(str(tmp_path), "two")
    os.makedirs(first)
    os.makedirs(second)
    monkeypatch.setattr(platform_module.config, "get", lambda k, d=None: first)
    assert platform_module.get_saves_path() == first
    monkeypatch.setattr(platform_module.config, "get", lambda k, d=None: second)
    assert platform_module.get_saves_path() == second
