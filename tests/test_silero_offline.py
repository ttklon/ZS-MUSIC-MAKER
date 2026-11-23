"""Offline package loading must not call torch.hub or download a repository."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from modules import silero_loader as loader


@pytest.fixture
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "ROOT", tmp_path)
    monkeypatch.delenv("ZSMM_SILERO_MODEL", raising=False)
    monkeypatch.setattr("app.core.net_policy.network_allowed", lambda: False)
    calls = []
    model = SimpleNamespace(apply_tts=lambda **kw: None, to=lambda device: calls.append(("to", device)))

    class Importer:
        def __init__(self, path):
            calls.append(("package", path))

        def load_pickle(self, module, name):
            calls.append(("pickle", module, name))
            return model

    def no_download(**kwargs):
        pytest.fail("offline loader attempted torch.hub download")

    torch = SimpleNamespace(
        hub=SimpleNamespace(get_dir=lambda: str(tmp_path / "hub"), load=no_download),
        package=SimpleNamespace(PackageImporter=Importer),
    )
    monkeypatch.setitem(sys.modules, "torch", torch)
    return tmp_path, calls, model, torch


def package(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"trusted package stand-in; loader calls are mocked")
    return path


def test_offline_reuses_official_hub_cache(environment):
    root, calls, model, torch = environment
    path = package(root / "hub/snakers4_silero-models_master/src/silero/model/v3_1_ru.pt")
    assert loader.load_silero() is model
    assert ("package", str(path)) in calls
    assert ("pickle", "tts_models", "model") in calls
    assert ("to", "cpu") in calls


def test_project_package_takes_precedence_over_cache(environment):
    root, calls, model, torch = environment
    path = package(root / "models/silero/v3_1_ru.pt")
    package(root / "hub/snakers4_silero-models_master/src/silero/model/v3_1_ru.pt")
    assert loader.load_silero() is model
    assert ("package", str(path)) in calls


def test_explicit_trusted_path_is_supported_offline(environment, monkeypatch):
    root, calls, model, torch = environment
    path = package(root / "my-weights/model.pt")
    monkeypatch.setenv("ZSMM_SILERO_MODEL", str(path))
    assert loader.load_silero() is model
    assert ("package", str(path)) in calls


def test_explicit_missing_model_does_not_silently_switch_or_download(environment, monkeypatch):
    root, calls, model, torch = environment
    monkeypatch.setenv("ZSMM_SILERO_MODEL", str(root / "missing.pt"))
    monkeypatch.setattr("app.core.net_policy.network_allowed", lambda: True)
    with pytest.raises(FileNotFoundError, match="configured Silero model"):
        loader.load_silero()


def test_missing_offline_weights_explain_next_step_without_network(environment):
    with pytest.raises(FileNotFoundError, match="weights unavailable offline"):
        loader.load_silero()


def test_online_opt_in_allows_official_hub_download(environment, monkeypatch):
    root, calls, model, torch = environment
    monkeypatch.setattr("app.core.net_policy.network_allowed", lambda: True)
    torch.hub.load = lambda **kw: (calls.append(("hub", kw)), (model, None))[1]
    assert loader.load_silero() is model
    assert next(call[1] for call in calls if call[0] == "hub")["speaker"] == "v3_1_ru"


def test_female_silero_uses_its_own_cached_version(environment):
    root, calls, model, torch = environment
    path = package(root / "models/silero/v4_ru.pt")
    assert loader.load_silero("v4_ru") is model
    assert ("package", str(path)) in calls


def test_invalid_local_package_is_not_redownloaded(environment, monkeypatch):
    root, calls, model, torch = environment
    package(root / "models/silero/v3_1_ru.pt")
    monkeypatch.setattr("app.core.net_policy.network_allowed", lambda: True)

    def broken(path):
        raise RuntimeError("corrupt package")

    torch.package.PackageImporter = broken
    with pytest.raises(RuntimeError, match="corrupt"):
        loader.load_silero()


def test_unknown_model_id_is_rejected_before_import_or_network(environment):
    with pytest.raises(ValueError, match="unsupported"):
        loader.load_silero("../../unknown")


def test_online_loader_pins_upstream_code_revision(environment, monkeypatch):
    root, calls, model, torch = environment
    monkeypatch.setattr('app.core.net_policy.network_allowed', lambda: True)
    torch.hub.load = lambda **kw: (calls.append(('hub', kw)), (model, None))[1]
    loader.load_silero()
    assert next(kw for kind, kw in calls if kind == 'hub')['repo_or_dir'] == 'snakers4/silero-models:' + loader.UPSTREAM_REVISION
    assert len(loader.UPSTREAM_REVISION) == 40
