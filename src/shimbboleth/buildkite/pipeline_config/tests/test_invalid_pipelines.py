"""
@TODO: ...


@TODO: Implement (and then use/test errors printing the field (jmes)path)
"""

from shimbboleth.buildkite.pipeline_config import BuildkitePipeline
from shimbboleth.buildkite.pipeline_config.tests.conftest import STEP_TYPE_PARAMS

import pytest


class _TestBase:
    def invalid_pipeline(self, pipeline_config, error, path=None):
        with pytest.raises(Exception) as e:
            BuildkitePipeline.model_load(pipeline_config)
        assert error in str(e.value)
        if path:
            assert f"Path: {path}" in str(e.value)

    # @TODO: Eventually, compare this against the generated schema
    #   and also against the upstream schema
    #   and also against the API
    def invalid_step(self, step, steptype_param=None, error=None, path=None):
        if steptype_param is not None:
            step = {**step, **steptype_param.dumped_default}

        if path:
            path = f"[0].{path}"

        self.invalid_pipeline([step], error=error, path=path)
        self.invalid_pipeline(
            {"steps": [step]}, error=error, path=f"steps.{path}" if path else path
        )
        if isinstance(step, dict) and "group" not in step:
            self.invalid_pipeline(
                {"group": "group", "steps": [step]},
                error=error,
                path=f"steps.{path}" if path else path,
            )
        # @TODO: Also do the other versions (steps: and group)


class Test_Pipeline(_TestBase):
    def test_bad_steps(self):
        self.invalid_pipeline(["unknown"], error="Unrecognizable step: `'unknown'`")
        self.invalid_pipeline([None], error="Unrecognizable step: `None`")
        self.invalid_step(
            {"type": "unknown"}, error="Unrecognizable step: `{'type': 'unknown'}`"
        )

    def test_env_list(self):
        self.invalid_pipeline(
            {"steps": [], "env": ["key"]},
            error="Expected `dict`, got `['key']` of type `list`",
            path="env",
        )

    def test_notify_invalid(self):
        self.invalid_pipeline(
            {"steps": [], "notify": ["unknown"]},
            error="Unrecognizable notification: `unknown`",
        )
        self.invalid_pipeline(
            {"steps": [], "notify": [{"unknown": ""}]},
            error="Unrecognizable notification: `unknown`",
        )


@pytest.mark.parametrize(
    "steptype_param",
    [
        pytest.param(steptype_param, id=steptype_param.stepname)
        for steptype_param in STEP_TYPE_PARAMS.values()
    ],
)
class Test_AnyStepType(_TestBase):
    def test_key_uuid(self, steptype_param):
        self.invalid_step(
            {"key": "2cb75f85-79ab-43a0-b666-91dbcb64321a"},
            steptype_param=steptype_param,
            error="Expected `'2cb75f85-79ab-43a0-b666-91dbcb64321a'` to not be a valid UUID",
            path="key",
        )

    def test_depends_on_missing_step(self, steptype_param):
        self.invalid_step(
            {"depends_on": [{}]},
            steptype_param=steptype_param,
            # @TODO: "Dependency" isn't an obvious typename
            error="`Dependency` missing 1 required fields: `step`",
        )


@pytest.mark.parametrize("step_type", ["block", "input"])
class Test_ManualStep(_TestBase):
    def test_field_missing_required_key(self, step_type):
        self.invalid_step(
            {"fields": [{}]},
            steptype_param=STEP_TYPE_PARAMS[step_type],
            error="Input fields must contain `text`` or `select`",
        )

    def test_single_select_list_default(self, step_type):
        self.invalid_step(
            {
                "fields": [
                    {
                        "select": "select",
                        "key": "key",
                        "options": [{"label": "label", "value": "value"}],
                        "multiple": False,
                        "default": ["value"],
                    }
                ]
            },
            steptype_param=STEP_TYPE_PARAMS[step_type],
            error="`default` cannot be a list when `multiple` is `False`",
        )

    # @TODO: both text and select
    def test_bad_key(self, step_type):
        self.invalid_step(
            {"fields": [{"text": "text", "key": "has:a:colon"}]},
            steptype_param=STEP_TYPE_PARAMS[step_type],
            error="Expected `'has:a:colon'` to match regex `^[a-zA-Z0-9-_]+$`",
        )
        self.invalid_step(
            {"fields": [{"text": "text", "key": "has a space"}]},
            steptype_param=STEP_TYPE_PARAMS[step_type],
            error="Expected `'has a space'` to match regex `^[a-zA-Z0-9-_]+$`",
        )

    # @TODO: missing key field
    # @TODO: select missing options

    def test_text_format_not_valid_regex(self, step_type):
        pass  # @TODO: implement


class Test_CommandStep(_TestBase):
    def invalid_step(self, step, steptype_param=None, error=None, path=None):
        super().invalid_step({**step, "type": "command"}, error=error, path=path)

    def test_notify_unsupported(self):
        self.invalid_step(
            {"notify": ["unknown"]},
            error="Unrecognizable notification: `unknown`",
            path="notify",
        )
        self.invalid_step(
            {"notify": [{"email": "hello@example.com"}]},
            error="`email` is not a valid step notification",
            path="notify",
        )


class Test_TriggerStep(_TestBase):
    def invalid_step(self, step, steptype_param=None, error=None, path=None):
        super().invalid_step({**step, "type": "trigger"}, error=error, path=path)

    def test_missing_trigger(self):
        self.invalid_step(
            {}, error="`TriggerStep` missing 1 required fields: `trigger`"
        )


class Test_GroupStep(_TestBase):
    def test_no_steps(self):
        self.invalid_step(
            {"group": "group", "steps": []},
            error="Expected `[]` to be non-empty",
            path="steps",
        )
        self.invalid_step(
            {"group": "group"}, error="`GroupStep` missing 1 required fields: `steps`"
        )

    # (unsupported) notify types
    # group step of group step
