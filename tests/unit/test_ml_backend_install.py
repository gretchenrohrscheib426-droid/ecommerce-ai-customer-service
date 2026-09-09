"""The isolated backend must install the shared validation package before pip check."""

import importlib.util
from pathlib import Path


def test_isolated_install_includes_project_and_checks_dependencies(monkeypatch):
    path = Path(__file__).resolve().parents[2] / "scripts/install_ml_backend.py"
    spec = importlib.util.spec_from_file_location("ml_install", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.sys, "prefix", str(path.parent / "ml-sdk"))
    calls = []
    monkeypatch.setattr(module.subprocess, "run", lambda argv, **kw: calls.append((argv, kw)))
    module.main()
    commands = [args for args, _ in calls]
    assert [module.sys.executable, "-m", "pip", "install", "-e", str(module.ROOT)] in commands
    assert commands[-1] == [module.sys.executable, "-m", "pip", "check"]
    assert all(options == {"check": True} for _, options in calls)
