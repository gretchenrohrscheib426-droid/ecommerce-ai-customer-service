import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "boundary", Path(__file__).resolve().parents[2] / "scripts/check_public_boundary.py"
)
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)


def test_sensitive_payloads_and_paths():
    assert boundary.inspect_blob("materials_private/course.json", b"{}")
    assert boundary.inspect_blob(".env", b"")
    assert boundary.inspect_blob("models/model.safetensors", b"weights")
    key = ("sk-" + "A" * 32).encode()
    assert boundary.inspect_blob("README.md", key)[0]["rule"] == "provider_key"
    assert boundary.inspect_blob("large.txt", b"x" * (boundary.MAX_BYTES + 1))
    assert not boundary.inspect_blob("data/sample/products.json", b'{"source": "Synthetic Demo Data"}')
    assert not boundary.inspect_blob("materials_private/.gitkeep", b"")


def test_blank_secret_does_not_consume_next_line():
    assert not boundary.inspect_blob(".env.example", b"MYSQL_PASSWORD=\nMYSQL_DATABASE=example_database\n")


def test_database_environment_and_personal_directory_excluded():
    for name in ["cache.db", "app.sqlite", ".venv-new/pyvenv.cfg", "models/arbitrary.json"]:
        assert boundary.inspect_blob(name, b"{}")
    private_path = ("E:" + "/Projects/" + "private-name").encode()
    assert boundary.inspect_blob("guide.md", private_path)
