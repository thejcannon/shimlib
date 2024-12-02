import json
import os
import pydantic.json_schema
import pydantic_core.core_schema
import pytest
import httpx
import yaml
from typing import Any

from shimbboleth.buildkite.pipeline_config import BuildkitePipeline, ALL_STEP_TYPES
from shimbboleth.buildkite.pipeline_config._alias import GenerateJsonSchemaWithAliases

import jmespath


SCHEMA_URL = "https://raw.githubusercontent.com/buildkite/pipeline-schema/354f67f64f37456641cc39670c122d0b8e27e4e5/schema.json"
VALID_PIPELINES_URL = "https://raw.githubusercontent.com/buildkite/pipeline-schema/354f67f64f37456641cc39670c122d0b8e27e4e5/test/valid-pipelines"

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


def _json_resurse(obj, func, *, _path=""):
    """
    `func` should have match `(*, value, parent, index, path)`
    """

    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{_path}.{k}"
            func(value=v, parent=obj, index=k, path=path)
            _json_resurse(v, func, _path=path)

    elif isinstance(obj, list):
        for idx, v in enumerate(obj):
            path = f"{_path}[{idx}]"
            func(value=v, parent=obj, index=idx, path=path)
            _json_resurse(v, func, _path=path)


class BKCompatGenerateJsonSchema(GenerateJsonSchemaWithAliases):
    def model_schema(
        self, schema: pydantic_core.core_schema.ModelSchema
    ) -> pydantic.json_schema.JsonSchemaValue:
        json_schema = super().model_schema(schema)
        json_schema.pop("title", None)
        return json_schema

    def generate(
        self,
        schema: pydantic_core.core_schema.CoreSchema,
        mode: pydantic.json_schema.JsonSchemaMode = "validation",
    ) -> pydantic.json_schema.JsonSchemaValue:
        json_schema = super().generate(schema, mode)
        json_schema["definitions"] = json_schema.pop("$defs")
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
        if (ref := ret.get("$ref", None)) and "AllowDependencyFailure" in ref:
            ret.pop("default")
        return ret

    def literal_schema(self, schema):
        ret = super().literal_schema(schema)
        if "const" in ret:
            ret["enum"] = [ret.pop("const")]
        return ret

    def dict_schema(
        self, schema: pydantic_core.core_schema.DictSchema
    ) -> pydantic.json_schema.JsonSchemaValue:
        json_schema = super().dict_schema(schema)
        # pydantic doesn't leverage `patternProperties`
        pattern_props: dict[str, dict] = json_schema.pop("patternProperties", None)
        if pattern_props:
            pattern, addt_props = pattern_props.popitem()
            json_schema["additionalProperties"] = addt_props
            json_schema["propertyNames"]["pattern"] = pattern

        return json_schema


@pytest.fixture
def pinned_bk_schema(pytestconfig) -> dict[str, Any]:
    cached_schema = pytestconfig.cache.get(SCHEMA_URL, None)
    if cached_schema:
        return cached_schema

    response = httpx.get(SCHEMA_URL)
    response.raise_for_status()
    schema_text = response.text.replace("’", "'")
    schema = json.loads(schema_text)
    pytestconfig.cache.set(SCHEMA_URL, schema)
    return schema


def _inline(schema, *defnames):
    def inner(*, value, parent, index, path):
        if isinstance(value, dict):
            if (defname := value.get("$ref", "").rsplit("/", 1)[-1]) in defnames:
                parent[index] = schema["definitions"][defname]

    _json_resurse(schema, inner)

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
        "$ref": f"#/definitions/{defname}/properties/{alias_of}"
    }


def _replace_oneOf(schema, path):
    obj = jmespath.search(path, schema)
    obj["anyOf"] = obj.pop("oneOf")


def test_schema_compatibility(pinned_bk_schema: dict[str, Any]):
    """Test that our Pydantic model schema matches the official Buildkite schema."""
    our_schema = BuildkitePipeline.model_json_schema(
        schema_generator=BKCompatGenerateJsonSchema,
        ref_template="#/definitions/{model}",
    )

    pinned_bk_schema.pop("$schema")
    pinned_bk_schema.pop("fileMatch")
    pinned_bk_schema.pop("title")

    bk_defs = pinned_bk_schema["definitions"]

    # A few missing descriptions
    for step_type in ALL_STEP_TYPES:
        defname = step_type.__name__[0].lower() + step_type.__name__[1:]
        our_schema["definitions"][defname].pop("description", None)
    our_schema["definitions"]["textInput"].pop("description", None)
    our_schema["definitions"]["selectInput"].pop("description", None)

    # https://github.com/buildkite/pipeline-schema/pull/103
    bk_defs["groupStep"]["properties"].pop("type")

    # https://github.com/buildkite/pipeline-schema/pull/104
    bk_defs["groupStep"]["required"].insert(0, "group")

    # https://github.com/buildkite/pipeline-schema/pull/105
    bk_defs["waitStep"]["properties"].pop("waiter")
    bk_defs["nestedWaitStep"]["properties"].pop("waiter")

    # https://github.com/buildkite/pipeline-schema/issues/93
    bk_defs["groupStep"]["properties"]["group"]["type"] = "string"
    bk_defs["dependsOn"]["anyOf"].pop(0)
    assert bk_defs["waitStep"]["properties"]["wait"]["type"] == ["string", "null"]
    bk_defs["waitStep"]["properties"]["wait"]["type"] = "string"

    # Handle (other) aliases
    _handle_alias(bk_defs, "nestedCommandStep", "commands", "command")
    _handle_alias(bk_defs, "nestedCommandStep", "script", "command")

    # Some definitions are inlined
    _inline(
        our_schema,
        "basecampCampfireNotify",
        "cacheMap",
        "commandNotify",
        "commandStepSignature",
        "dependsOnDependency",
        "emailNotify",
        "gitHubCheckNotify",
        "gitHubCommitStatusNotify",
        "hasContext",
        "manualRetryConditions",
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
        "softFailByStatus",
    )

    # anyOf/oneOf (Should probably open an issue/PR)
    _replace_oneOf(bk_defs, "matrixElement")
    _replace_oneOf(bk_defs, "fields.items")
    _replace_oneOf(bk_defs, "fields.items.anyOf[1].properties.default")
    _replace_oneOf(bk_defs, "commandStep.properties.plugins.anyOf[0].items")
    _replace_oneOf(bk_defs, "commandStep.properties.notify.items")
    _replace_oneOf(
        bk_defs, "commandStep.properties.notify.items.anyOf[2].properties.slack"
    )
    _replace_oneOf(bk_defs, "commandStep.properties.matrix")
    _replace_oneOf(
        bk_defs,
        "commandStep.properties.matrix.anyOf[1].properties.adjustments.items.properties.with",
    )
    _replace_oneOf(bk_defs, "commandStep.properties.matrix.anyOf[1].properties.setup")
    _replace_oneOf(bk_defs, "buildNotify.items")
    _replace_oneOf(bk_defs, "buildNotify.items.anyOf[3].properties.slack")
    _replace_oneOf(bk_defs, "agents")

    # @TOD: Annoying, the non-required fields have `None` in the example object
    auto_retry_default = jmespath.search(
        "definitions.commandStep.properties.retry.properties.automatic.default[0]",
        our_schema,
    )
    auto_retry_default.pop("signal")
    auto_retry_default.pop("signal_reason")
    jmespath.search(
        "definitions.commandStep.properties.matrix.anyOf[1].properties.adjustments.items.properties.with.anyOf[1].propertyNames",
        our_schema,
    )["type"] = "string"
    jmespath.search(
        "definitions.commandStep.properties.matrix.anyOf[1].properties.setup.anyOf[1].propertyNames",
        our_schema,
    )["type"] = "string"
    # DONE!

    if os.getenv("DUMP_SCHEMAS"):
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
        assert type(ours) is type(theirs), f"At '{path=}'"
        if isinstance(ours, dict):
            assert set(ours.keys()) == set(theirs.keys()), f"At '{path=}'"
            pathqueue.extend(f'{path}."{key}"' for key in ours.keys())
        elif isinstance(ours, list):
            assert len(ours) == len(theirs), f"At '{path=}'"
            pathqueue.extend(f"{path}[{i}]" for i in range(len(ours)))
        else:
            assert ours == theirs, f"At '{path=}'"

    assert our_schema == pinned_bk_schema


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


@pytest.mark.skip(reason="PR #103 and #105 must be merged first")
def test_upstream_valid_pipelines(upstream_valid_schema):
    BuildkitePipeline(**upstream_valid_schema)
