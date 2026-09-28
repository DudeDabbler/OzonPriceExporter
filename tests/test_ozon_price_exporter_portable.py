from __future__ import annotations

from pathlib import Path

from tools.ozon_price_exporter import __version__
from tools.ozon_price_exporter.state import RuntimeState
from tools.ozon_price_exporter.storage import default_storage_root


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "ozon_price_exporter"


def test_portable_version_is_single_runtime_contract() -> None:
    assert __version__ == "0.1.2"
    assert RuntimeState().snapshot()["version"] == __version__


def test_portable_distribution_files_are_versioned() -> None:
    required = (
        ROOT / "build_ozon_price_exporter_portable.bat",
        TOOL / "build_portable.ps1",
        TOOL / "ozon_price_exporter_portable.spec",
        TOOL / "portable_build_requirements.txt",
        TOOL / "portable_entry.py",
        TOOL / "portable_smoke.py",
        TOOL / "PORTABLE_README.txt",
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    assert not missing, f"missing portable files: {missing}"


def test_portable_spec_bundles_playwright_and_static_ui() -> None:
    spec = (TOOL / "ozon_price_exporter_portable.spec").read_text(encoding="utf-8")
    assert 'collect_all("playwright")' in spec
    assert '"tools/ozon_price_exporter/static"' in spec
    assert 'name="OzonPriceExporter"' in spec
    assert "console=False" in spec


def test_portable_readme_has_no_python_install_step() -> None:
    text = (TOOL / "PORTABLE_README.txt").read_text(encoding="utf-8")
    assert "Python, pip и виртуальное окружение пользователю не требуются" in text
    assert "Google Chrome или Microsoft Edge" in text
    assert "%LOCALAPPDATA%\\IFOAM\\OzonPriceExporter" in text
    assert "DudeDabbler" in text


def test_static_ui_uses_dudedabbler_brand() -> None:
    html = (TOOL / "static" / "index.html").read_text(encoding="utf-8")
    assert "DudeDabbler · локальный инструмент" in html
    assert "IFOAM · локальный инструмент" not in html


def test_new_storage_env_has_priority_and_legacy_alias_remains(monkeypatch, tmp_path: Path) -> None:
    new_root = tmp_path / "new"
    legacy_root = tmp_path / "legacy"
    monkeypatch.setenv("DUDEDABBLER_OZON_PRICE_EXPORTER_HOME", str(new_root))
    monkeypatch.setenv("IFOAM_OZON_PRICE_EXPORTER_HOME", str(legacy_root))
    assert default_storage_root() == new_root.resolve()

    monkeypatch.delenv("DUDEDABBLER_OZON_PRICE_EXPORTER_HOME")
    assert default_storage_root() == legacy_root.resolve()


def test_standalone_docs_and_workflows_exist() -> None:
    required = (
        ROOT / "docs" / "PROJECT_STATE.md",
        ROOT / "docs" / "MIGRATION_FROM_ANALYTICS_V2.md",
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / ".github" / "workflows" / "release-portable.yml",
    )
    assert all(path.is_file() for path in required)


def test_portable_smoke_bypasses_loopback_proxies_and_surfaces_startup_errors() -> None:
    smoke = (TOOL / "portable_smoke.py").read_text(encoding="utf-8")
    entry = (TOOL / "portable_entry.py").read_text(encoding="utf-8")

    assert "ProxyHandler({})" in smoke
    assert 'env["NO_PROXY"] = "127.0.0.1,localhost"' in smoke
    assert 'env["DUDEDABBLER_OZON_PRICE_EXPORTER_NO_DIALOG"] = "1"' in smoke
    assert "startup_error.log" in smoke
    assert "DUDEDABBLER_OZON_PRICE_EXPORTER_NO_DIALOG" in entry


def test_windowed_portable_normalizes_stdout_and_stderr_to_utf8() -> None:
    entry = (TOOL / "portable_entry.py").read_text(encoding="utf-8")

    assert 'stream.reconfigure(encoding="utf-8", errors="backslashreplace")' in entry
    assert "sys.stdout = _utf8_stream(sys.stdout)" in entry
    assert "sys.stderr = _utf8_stream(sys.stderr)" in entry
