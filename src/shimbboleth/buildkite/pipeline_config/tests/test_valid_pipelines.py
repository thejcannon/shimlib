"""
# Pipeline Config Tests

This test loads files from `./valid-pipelines` to check:

1. Pipeline Validation: These pipelines should be valid and be loadable.
    Additionally, we can (eventually) upload them to Buildkite (via a planned smoke-test)
    to verify they are valid upstream.

2. Round-Trip Testing: We verify that pipeline configurations maintain their integrity when:
   - Parsed from YAML into our internal representation
   - Converted back to YAML

This way we can ensure we're parsing the config correctly, and that we're "canonicalizing" correctly as well.

(I would love to also put Buildkite's representation in here, but the API responds with
data thats ambiguous and missing fields.)
"""

from shimbboleth.buildkite.pipeline_config import BuildkitePipeline
from shimbboleth.buildkite.pipeline_config.group_step import GroupStep
from pathlib import Path
import copy
from typing import Iterable, Any, Callable
from dataclasses import dataclass
from shimbboleth.buildkite.pipeline_config.tests.conftest import STEP_TYPE_PARAMS

import yaml


@dataclass(slots=True, frozen=True)
class ValidPipeline:
    name: str
    pipeline: dict[str, Any]
    expected: dict[str, Any]

    @classmethod
    def _replaced_type(
        cls, docs: list[dict[str, Any]], replacer: Callable[[dict[str, Any]], None]
    ) -> list[dict[str, Any]]:
        docs = copy.deepcopy(docs)
        for doc in docs:
            for step in doc["steps"]:
                assert step.pop("type") is None
                replacer(step)
        return docs

    @classmethod
    def load_all(cls) -> "Iterable[ValidPipeline]":
        """
        Load all the valid pipelines from the `valid-pipelines` directory,
        special-casing:
            - all-*.yaml: Yields a pipeline per step type
            - manual-*.yaml: Yields a pipeline for both Block and Input steps
            - substep-*.yaml: Yields a pipeline for all step types except Group steps
            - (Non-group): Yields a pipeline with the same definition but as a group step
        """
        paths = (Path(__file__).parent / "valid-pipelines").glob("*.yaml")
        for path in paths:
            name = path.stem
            yaml_docs = list(yaml.safe_load_all(path.read_text()))
            # @TODO: all/manual/substep, but as Group steps too
            if name.startswith("all-"):
                for step_type_param in STEP_TYPE_PARAMS:
                    docs = cls._replaced_type(
                        yaml_docs,
                        lambda step: step.update(step_type_param.dumped_default),
                    )
                    yield ValidPipeline(
                        f"*{step_type_param.lowercase}-{name.removeprefix('all-')}",
                        docs[0],
                        docs[-1],
                    )
            elif name.startswith("manual-"):
                for step_type in ("block", "input"):
                    docs = cls._replaced_type(
                        yaml_docs, lambda step: step.__setitem__("type", step_type)
                    )
                    yield ValidPipeline(
                        f"*{step_type}-{name.removeprefix('manual-')}",
                        docs[0],
                        docs[-1],
                    )
            elif name.startswith("substep-"):
                for step_type_param in STEP_TYPE_PARAMS:
                    if step_type_param.cls is GroupStep:
                        continue
                    docs = cls._replaced_type(
                        yaml_docs,
                        lambda step: step.update(step_type_param.dumped_default),
                    )
                    yield ValidPipeline(
                        f"*{step_type_param.lowercase}-{name.removeprefix('substep-')}",
                        docs[0],
                        docs[-1],
                    )
            else:
                yield ValidPipeline(name, yaml_docs[0], yaml_docs[-1])
                if not name.startswith(("pipeline-", "group-")):
                    pipeline = {"steps": [{"group": "group", **yaml_docs[0]}]}
                    expected = {"steps": [{"group": "group", **yaml_docs[-1]}]}
                    yield ValidPipeline(f"*group-{name}", pipeline, expected)


def pytest_generate_tests(metafunc):
    if "pipeline_info" in metafunc.fixturenames:
        metafunc.parametrize(
            "pipeline_info", list(ValidPipeline.load_all()), ids=lambda info: info.name
        )


# @TODO: "manual" and "all" pipelines
def test_valid_pipeline(pipeline_info: ValidPipeline):
    """
    This test loads the YAML, and ensures that loading the first document
    and then dumping it matches the second document
    (with them possibly being the same document).
    """
    pipeline = BuildkitePipeline.model_load(pipeline_info.pipeline)
    assert pipeline.model_dump() == pipeline_info.expected


# @BUG: an empty pipeline is valid using the UI (`null` steps)
# @LINT: no duplicate pipelines/ duplicate steps
# @LINT: all files use "yaml" suffix
# @LINT: All steps in the result have `type: ` of the first part of the filename
# @TEST: test that every one of the test cases are equivalent (if not identical)
# @LINT/TEST: Keep the block-* pipelines in sync withe the input ones (where relevant)
# @LINT(+fixer): That if there's 2 documents, they dont equal
# FEAT: Make it so the second document can use null (no change), + or - keys to indicate a change, as a form of brevity

# @TODO: Test all our pipelines pass validating against upstream schema
