import json
from copy import deepcopy
import pydantic.json_schema
import pydantic_core.core_schema
from pydantic import BaseModel
import pytest
import httpx
import yaml
from typing import Any, cast

from shimbboleth.buildkite.pipeline_config import (
    BuildkitePipeline,
)

import jmespath

from shimbboleth.buildkite.pipeline_config._block_step import BlockStep

SCHEMA_URL = "https://raw.githubusercontent.com/buildkite/pipeline-schema/5c58c564dd128e6144ae00c993d978b68ea247dc/schema.json"
VALID_PIPELINES_URL = "https://raw.githubusercontent.com/buildkite/pipeline-schema/5c58c564dd128e6144ae00c993d978b68ea247dc/test/valid-pipelines"

VALID_PIPELINE_NAMES = (
    "block.yml",
    "command.yml",
    "env.yml",
    "extra-properties.yml",
    "group.yml",
    "input.yml",
    "matrix.yml",
    "notify.yml",
    "trigger.yml",
    "wait.yml",
)


def _json_resurce(obj, func, *, _path=""):
    """
    `func` should have match `(*, value, parent, index, path) -> bool | None`
    """

    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{_path}.{k}"
            should_stop = func(value=v, parent=obj, index=k, path=path)
            if should_stop:
                return True
            should_stop = _json_resurce(v, func, _path=path)
            if should_stop:
                return True

    elif isinstance(obj, list):
        for idx, v in enumerate(obj):
            path = f"{_path}[{idx}]"
            should_stop = func(value=v, parent=obj, index=idx, path=path)
            if should_stop:
                return True
            should_stop = _json_resurce(v, func, _path=path)
            if should_stop:
                return True


class BKCompatGenerateJsonSchema(pydantic.json_schema.GenerateJsonSchema):
    def model_schema(
        self, schema: pydantic_core.core_schema.ModelSchema
    ) -> pydantic.json_schema.JsonSchemaValue:
        json_schema = super().model_schema(schema)
        json_schema.pop("title", None)

        # Mske the `validation_alias` aliases show up in the schema
        for fieldname, fieldschema in schema["schema"].get("fields", {}).items():
            validation_alias = fieldschema.get("validation_alias", None)
            if validation_alias:
                if isinstance(validation_alias, list):
                    for aliases in validation_alias[1:]:
                        for alias in aliases:
                            assert alias != fieldname
                            mangled_ref = self.get_cache_defs_ref_schema(schema["ref"])[
                                1
                            ]["$ref"]
                            # NB: This asumes the naming of the obj
                            clsname = mangled_ref.rsplit(".", 1)[-1].split("-", 1)[0]
                            # NB: Can't use $ref because that breaks things
                            json_schema["properties"][alias] = {
                                "$ref$": f"#/definitions/{self.normalize_name(clsname)}/{fieldname}"
                            }

        return json_schema

    def generate(
        self,
        schema: pydantic_core.core_schema.CoreSchema,
        mode: pydantic.json_schema.JsonSchemaMode = "validation",
    ) -> pydantic.json_schema.JsonSchemaValue:
        json_schema = super().generate(schema, mode)

        def replce_custom_ref(*, value, parent, index, path) -> bool | None:
            if isinstance(value, dict) and "$ref$" in value:
                value["$ref"] = value.pop("$ref$")

        _json_resurce(json_schema, replce_custom_ref)
        return json_schema

    def field_title_should_be_set(self, schema) -> bool:
        return False

    def normalize_name(self, name: str) -> str:
        return name[0].lower() + name[1:].removesuffix("T")

    def nullable_schema(self, schema):
        ret = super().nullable_schema(schema)
        if "anyOf" in ret:
            ret["anyOf"].remove({"type": "null"})
            anyOf = ret["anyOf"]
            if len(anyOf) == 1:
                ret.update(**anyOf[0])
                ret.pop("anyOf")
        # @TODO oneOf?
        return ret

    def default_schema(self, schema):
        ret = super().default_schema(schema)
        if ret["default"] is None:
            ret.pop("default")
        return ret

    def literal_schema(self, schema):
        ret = super().literal_schema(schema)
        if "const" in ret:
            ret["enum"] = [ret.pop("const")]
        return ret


@pytest.fixture
def pinned_bk_schema(pytestconfig) -> dict[str, Any]:
    cached_schema = pytestconfig.cache.get(SCHEMA_URL, None)
    if cached_schema:
        return cached_schema

    response = httpx.get(SCHEMA_URL)
    response.raise_for_status()
    schema = response.json()
    pytestconfig.cache.set(SCHEMA_URL, schema)
    return schema


def _inline(schema, *defnames):
    def inner(*, value, parent, index, path):
        if isinstance(value, dict):
            if (defname := value.get("$ref", "").rsplit("/", 1)[-1]) in defnames:
                parent[index] = schema["definitions"][defname]

    _json_resurce(schema, inner)

    for defname in defnames:
        schema["definitions"].pop(defname)


def _pop_field(schema, *fields):
    for field in fields:
        head, tail = field.rsplit(".", 1)
        jmespath.search(head, schema).pop(tail)


def _handle_alias(bk_defs, defname, alias, alias_of):
    assert (
        bk_defs[defname]["properties"][alias]
        == bk_defs[defname]["properties"][alias_of]
    )
    bk_defs[defname]["properties"][alias] = {
        "$ref": f"#/definitions/{defname}/{alias_of}"
    }


ALL_STEP_TYPES = (
    "blockStep",
    "commandStep",
    "groupStep",
    "inputStep",
    "triggerStep",
    "waitStep",
)


def test_schema_compatibility(pinned_bk_schema: dict[str, Any]):
    """Test that our Pydantic model schema matches the official Buildkite schema."""
    our_schema = BuildkitePipeline.model_json_schema(
        schema_generator=BKCompatGenerateJsonSchema,
        ref_template="#/definitions/{model}",
    )

    pinned_bk_schema.pop("$schema")
    pinned_bk_schema.pop("fileMatch")
    pinned_bk_schema.pop("title")

    our_schema["definitions"] = our_schema.pop("$defs")

    bk_defs = pinned_bk_schema["definitions"]

    # A few missing descriptions
    for defname in ALL_STEP_TYPES:
        our_schema["definitions"][defname].pop("description", None)

    # https://github.com/buildkite/pipeline-schema/pull/90
    triggerStepBuildProps = bk_defs["triggerStep"]["properties"]["build"]["properties"]
    triggerStepBuildProps.pop("label")
    triggerStepBuildProps.pop("name")
    triggerStepBuildProps.pop("trigger")
    triggerStepBuildProps.pop("type")

    # https://github.com/buildkite/pipeline-schema/pull/91
    stepsTypes = pinned_bk_schema["properties"]["steps"]["items"]["anyOf"]
    stepsTypes.insert(10, stepsTypes.pop(8))
    groupStepStepTypes = bk_defs["groupStep"]["properties"]["steps"]["items"]["anyOf"]
    groupStepStepTypes.insert(11, groupStepStepTypes.pop(9))

    # https://github.com/buildkite/pipeline-schema/pull/92
    bk_defs.pop("identifier")
    for defname in ALL_STEP_TYPES:
        bk_defs[defname]["properties"]["identifier"] = {
            "$ref": f"#/definitions/{defname}/key"
        }
        bk_defs[defname]["properties"]["id"] = {"$ref": f"#/definitions/{defname}/key"}

    # https://github.com/buildkite/pipeline-schema/issues/93
    wait_def = our_schema["definitions"]["waitStep"]["properties"].pop("wait")
    our_schema["definitions"]["waitStep"]["properties"]["wait"] = {
        "description": wait_def.pop("description"),
        "anyOf": [{"type": "null"}, wait_def],
    }

    # https://github.com/buildkite/pipeline-schema/pull/94
    bk_defs["triggerStep"]["required"] = ["trigger"]

    # https://github.com/buildkite/pipeline-schema/pull/95
    # @TODO

    # Handle aliases
    _handle_alias(bk_defs, "triggerStep", "name", "label")
    assert "description" not in bk_defs["waitStep"]["properties"]["waiter"]
    bk_defs["waitStep"]["properties"]["waiter"]["description"] = bk_defs["waitStep"][
        "properties"
    ]["wait"]["description"]
    _handle_alias(bk_defs, "waitStep", "waiter", "wait")

    # Some definitions are inlined
    _inline(
        our_schema,
        "commandStepSignature",
        "emailNotify",
        "gitHubCheckNotify",
        "gitHubCommitStatusNotify",
        "hasContext",
        "matrixAdjustment",
        "multiDimenisonalMatrix",
        "pagerdutyNotify",
        "retryConditions",
        "selectInput",
        "selectOption",
        "slackChannelsNotify",
        "slackNotify",
        "textInput",
        "triggeredBuild",
        "webhookNotify",
    )

    with open("bk_schema.json", "w") as f:
        json.dump(pinned_bk_schema, f, indent=2, sort_keys=True)

    with open("our_schema.json", "w") as f:
        json.dump(our_schema, f, indent=2, sort_keys=True)

    pathqueue = [*set([*our_schema, *pinned_bk_schema])]
    while pathqueue:
        path = pathqueue.pop()
        ours = jmespath.search(path, our_schema)
        theirs = jmespath.search(path, pinned_bk_schema)
        if ours is None or theirs is None:
            assert ours == theirs, f"At '{path=}'"
        assert type(ours) == type(theirs), f"At '{path=}'"
        if isinstance(ours, dict):
            assert sorted(ours.keys()) == sorted(theirs.keys()), f"At '{path=}'"
            pathqueue.extend(f'{path}."{key}"' for key in ours.keys())
        elif isinstance(ours, list):
            assert len(ours) == len(theirs), f"At '{path=}'"
            pathqueue.extend(f"{path}[{i}]" for i in range(len(ours)))
        else:
            assert ours == theirs, f"At '{path=}'"

    assert False
    # assert our_schema == pinned_bk_schema


@pytest.fixture(params=VALID_PIPELINE_NAMES)
def upstream_valid_schema(request: pytest.FixtureRequest, pytestconfig: pytest.Config):
    url = VALID_PIPELINES_URL + f"/{request.param}"
    cached_schema = pytestconfig.cache.get(url, None)
    if cached_schema:
        return cached_schema

    response = httpx.get(url)
    response.raise_for_status()
    schema = yaml.safe_load(response.text)
    pytestconfig.cache.set(url, schema)
    return schema


def test_upstream_valid_pipelines(upstream_valid_schema):
    BuildkitePipeline(**upstream_valid_schema)
