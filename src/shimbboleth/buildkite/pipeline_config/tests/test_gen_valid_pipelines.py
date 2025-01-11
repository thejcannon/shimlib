"""
@TODO: ...
"""
from pathlib import Path

from shimbboleth.buildkite.pipeline_config import BuildkitePipeline

from shimbboleth.buildkite.pipeline_config.tests.conftest import STEP_TYPE_PARAMS

import pytest
from pytest import param

GENERATION_PATH = Path(__file__).parent /  "valid-pipelines" / "generated"


BOOLVALS = ("true", "false", True, False)


# @TODO: Test the pipeline is valid
#   and then dump it to file (with the canonicalized version)?


@pytest.mark.parametrize(
    "pipeline_step",
    [
        *(
            param({
                **step_param.values[0],  # type: ignore
                **step_type_param.dumped_default,
            }, id=f"{step_type_param.stepname}-{step_param.id}")
            for step_type_param in STEP_TYPE_PARAMS.values()
            for step_param in (
                # allow_dependency_failure
                *(param({"allow_dependency_failure": value}, id="all-allow_dependency_failure") for value in BOOLVALS),
                # depends_on
                param({"depends_on": "scalar"}, id="depends_on"),
                param({"depends_on": ["string"]}, id="depends_on"),
                param({"depends_on": [{"step": "step_id"}]}, id="depends_on"),
                *(param({"depends_on": [{"step": "step_id", "allow_failure": value}]}, id="depends_on-allow_failure") for value in BOOLVALS),
                param({"depends_on": ["string", {"step": "step_id", "allow_failure": True}]}, id="depends_on-mixed"),
                # if
                param({"if": "string"}, id="if"),
                # key-id-identifier
                param({"key": "key1"}, id="key"),
                param({"id": "id1"}, id="id"),
                param({"identifier": "identifier1"}, id="identifier"),
                param({"key": "key2", "id": "id2"}, id="key-id"),
                param({"key": "key3", "identifier": "identifier2"}, id="key-identifier"),
                param({"id": "id3", "identifier": "identifier3"}, id="id-identifier"),
                param({"key": "key4", "id": "id4", "identifier": "identifier4"}, id="key-id-identifier"),
                # @TODO: Also the cases where the value is null (techincally, but also bleh)

            )
        ),
        # All but group
        *(
            param({
                **step_param.values[0],  # type: ignore
                **step_type_param.dumped_default,
            }, id=f"{step_type_param.stepname}-{step_param.id}")
            for steptype, step_type_param in STEP_TYPE_PARAMS.items()
            if steptype != "group"
            for step_param in (
                # stepname-label-name
                param({"type": step_type_param.type}, id="type"),
                param({"type": step_type_param.type, "label": "label"}, id="type-label"),
                param({"type": step_type_param.type, "label": "label", "name": "name"}, id="type-label-name"),
                param({step_type_param.stepname: step_type_param.stepname}, id="stepname"),
                param({step_type_param.stepname: step_type_param.stepname, "label": "label"}, id="stepname-label"),
                param({step_type_param.stepname: step_type_param.stepname, "name": "name"}, id="stepname-name"),
                param({step_type_param.stepname: step_type_param.stepname, "label": "label", "name": "name"}, id="stepname-label-name"),
                # branches
                param({"branches": "master"}, id="branches-string"),
                param({"branches": ["master"]}, id="branches-list"),
            )
        ),
        # nested
        # @TODO: test the aliases too (manueal, waiter)
        *(
            param({step_type_param.stepname: step_type_param.ctor_defaults}, id=f"{step_type_param.stepname}-nested")
            for steptype, step_type_param in STEP_TYPE_PARAMS.items()
            if steptype != "group"
        ),
        {"block": None},
        {"input": None},
        {"wait": None},
        *("block", "manual", "input", "wait", "waiter"),
        # BlockStep
        *(
            param({"type": "block", "blocked_state": state}, id="blocked-state")
            for state in ("passed", 'failed', "running")
        ),
        # Command Step


        # Wait Step
        *(param({"type": "wait", "continue_on_failure": value}, id="wait-continue_on_failure") for value in BOOLVALS),
    ]
)
def test_valid_pipeline_steps(pipeline_step: dict, request: pytest.FixtureRequest):
    #param_id = request.node.name.removeprefix(request.node.originalname)[1:-1]
    # @TODO: make sure the directory has the same set of files as the param
    # (GENERATION_PATH / f"{param_id}.yaml").write_text(yaml.safe_dump({"steps": [pipeline_step]}))
    pipeline = BuildkitePipeline.model_load([pipeline_step])
    pipeline.model_dump()
