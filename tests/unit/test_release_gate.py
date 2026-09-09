import importlib
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
gate = importlib.import_module("validate_release")


def test_skipped_only_and_empty_reports_are_never_passed():
    for xml in ['<testsuites/>', '<testsuite tests="2" skipped="2"/>']:
        assert gate.junit_status(ET.fromstring(xml))["status"] == "NOT_RUN"
    assert gate.junit_status(ET.fromstring('<testsuite tests="2" failures="1"/>'))["status"] == "FAIL"
    assert gate.junit_status(ET.fromstring('<testsuites><testsuite tests="2" skipped="1"/></testsuites>')) == {
        "status": "PASS", "tests": 2, "passed": 1, "skipped": 1, "failures": 0}
