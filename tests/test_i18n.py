from __future__ import annotations

import pytest

from app.core import i18n
from app.core.pipeline_core import ZSPipeline
from config.settings import Settings


@pytest.fixture(autouse=True)
def _restore_language():
    previous = i18n.get_language()
    yield
    i18n.set_language(previous)


def test_i18n_switches_ru_en_immediately_without_restart() -> None:
    assert i18n.set_language("en") == "en"
    assert i18n.t("menu.help") == "Help"
    assert i18n.t("pipeline.stage", stage="music") == "Stage: music"

    assert i18n.set_language("ru") == "ru"
    assert i18n.t("menu.help") == "Помощь"
    assert i18n.t("pipeline.stage", stage="music") == "Стадия: music"


def test_i18n_validates_language_and_has_safe_key_fallback() -> None:
    with pytest.raises(ValueError, match="unsupported language"):
        i18n.set_language("de")
    assert i18n.t("missing.translation") == "missing.translation"
    assert i18n.t("pipeline.failed") == "Пайплайн завершился с ошибкой: {reason}"


def test_settings_loads_language_from_dotenv(tmp_path) -> None:
    env = tmp_path / ".env"
    env.write_text("ZSMM_LANGUAGE=en\n", encoding="utf-8")

    settings = Settings.load(env)

    assert settings.language == "en"
    assert settings.dump()["language"] == "en"


def test_pipeline_exposes_translated_display_status_without_changing_status(tmp_path) -> None:
    i18n.set_language("en")
    pipeline = ZSPipeline("i18n", {}, checkpoint_dir=tmp_path / "checkpoints")
    pipeline.add_stage("ready", lambda _context: {"ok": True})

    result = pipeline.run(use_checkpoints=False)

    assert result["status"] == "completed"
    assert result["display_status"] == "Pipeline completed"
