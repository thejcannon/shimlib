from shimbboleth.buildkite.pipeline_config import BuildkitePipeline
from pathlib import Path

import yaml
import pytest


@pytest.mark.parametrize(
    "pipeline_path",
    (Path(__file__).parent / "valid-pipelines").glob("*.yaml"),
    ids=lambda path: path.stem,
)
def test_valid_pipeline(pipeline_path: Path):
    test_case = list(yaml.safe_load_all(pipeline_path.read_text()))
    pipeline = BuildkitePipeline.model_load(test_case[0])
    assert pipeline.model_dump() == test_case[0:2][-1]


# @BUG: an empty pipeline is valid using the UI
# @LINT: pipelines are canonically formatted
# @LINT: no duplicate pipelines
# @TEST: test that every one of the test cases are equivalent (if not identical)
