"""Compatibility command for the current boundary and manifest format."""

from check_public_boundary import main as boundary_main
from verify_manifest import verify

if __name__ == "__main__":
    result = boundary_main()
    raise SystemExit(result or verify())
