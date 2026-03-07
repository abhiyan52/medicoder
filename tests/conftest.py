import os
from pathlib import Path

import pytest

import app.graph.nodes as nodes_module


@pytest.fixture(autouse=True)
def reset_cached_services():
    nodes_module._condition_extractor = None
    nodes_module._hcc_evaluator = None
    yield
    nodes_module._condition_extractor = None
    nodes_module._hcc_evaluator = None


def pytest_collection_modifyitems(config, items):
    run_integration = os.getenv("RUN_INTEGRATION_TESTS") == "1"
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    has_creds = bool(creds_path and Path(creds_path).is_file())

    if run_integration and has_creds:
        return

    skip_reason = (
        "integration test requires RUN_INTEGRATION_TESTS=1 and a valid "
        "GOOGLE_APPLICATION_CREDENTIALS file"
    )
    skip_marker = pytest.mark.skip(reason=skip_reason)

    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)
