"""
Pytest config for all of shimbboleth testing.

Currently configures:
    - Integration test support
"""
# @TODO: It'd be nice if this was just some kind of "meta" plugin and we got to configure each
#   plugin in its own little box.

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests",
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration (run with `--integration`)"
    )

def pytest_runtest_setup(item):
    if not item.config.getoption("--integration") and item.get_closest_marker("integration"):
        pytest.skip("Integration test; use `-m integration` to run")
