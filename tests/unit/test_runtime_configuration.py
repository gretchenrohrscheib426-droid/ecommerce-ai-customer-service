import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sample = importlib.import_module("sample_demo")
mysql = importlib.import_module("configure_demo_mysql")


def test_sample_ports_reject_invalid_or_conflicting_values():
    for ports in [(True, 7476, 8012), (80, 7476, 8012), (7689, 7689, 8012), (7689, 7476, 65536)]:
        with pytest.raises(ValueError):
            sample.configure(*ports)


def test_mysql_never_initializes_unowned_existing_data(tmp_path, monkeypatch):
    monkeypatch.setattr(mysql, "LOCAL", tmp_path)
    data = tmp_path / "mysql"
    data.mkdir()
    sentinel = data / "existing.txt"
    sentinel.write_text("preserve")
    with pytest.raises(ValueError, match="Unowned"):
        mysql.configure(3310)
    assert sentinel.read_text() == "preserve"
    assert not (data / "my.ini").exists()


def test_mysql_refuses_port_change(tmp_path, monkeypatch):
    monkeypatch.setattr(mysql, "LOCAL", tmp_path)
    runtime = tmp_path / "runtime.json"
    runtime.write_text('{"mysql_port":3310}')
    with pytest.raises(ValueError, match="port differs"):
        mysql.configure(3311)
    assert runtime.read_text() == '{"mysql_port":3310}'
