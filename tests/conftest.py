# -*- coding: utf-8 -*-

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_addoption(parser):
    parser.addoption(
        "--run-golden",
        action="store_true",
        default=False,
        help="run long-running golden case tests",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-golden"):
        return

    skip_golden = pytest.mark.skip(reason="need --run-golden option to run")
    for item in items:
        if "golden" in item.keywords:
            item.add_marker(skip_golden)
