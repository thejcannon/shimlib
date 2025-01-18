"""
@TODO: ...


@TODO: Implement (and then use/test errors printing the field (jmes)path)
"""

from shimbboleth.buildkite.pipeline_config import BuildkitePipeline
from shimbboleth.buildkite.pipeline_config.tests.conftest import STEP_TYPE_PARAMS

import pytest

# @TODO: Tests for extra keys

# @TODO: Infra, I think parameterize would help (instead of test-per-use-case)


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
            path = f"[0]{path}"

        self.invalid_pipeline([step], error=error, path=path)
        self.invalid_pipeline(
            {"steps": [step]}, error=error, path=f".steps{path}" if path else path
        )
        if isinstance(step, dict) and "group" not in step:
            self.invalid_pipeline(
                {"group": "group", "steps": [step]},
                error=error,
                path=f".steps{path}" if path else path,
            )


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
            path=".env",
        )

    def test_notify_invalid(self):
        self.invalid_pipeline(
            {"steps": [], "notify": ["unknown"]},
            error="Unrecognizable notification: `unknown`",
            path=".notify",
        )
        self.invalid_pipeline(
            {"steps": [], "notify": [{"unknown": ""}]},
            error="Unrecognizable notification: `unknown`",
            path=".notify",
        )

    def test_notify__slack__empty_channels(self):
        self.invalid_pipeline(
            {"steps": [], "notify": [{"slack": {"channels": []}}]},
            error="Expected `[]` to be non-empty",
            path=".notify.slack.channels",
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
            path=".key",
        )

    def test_depends_on_missing_step(self, steptype_param):
        self.invalid_step(
            {"depends_on": [{}]},
            steptype_param=steptype_param,
            # @TODO: "Dependency" isn't an obvious typename
            error="`Dependency` missing 1 required fields: `step`",
            # path=".depends_on"
        )


# @TODO: Add paths
@pytest.mark.parametrize("step_type", ["block", "input"])
class Test_ManualStep(_TestBase):
    def _invalid_field(self, field, *, step_type, error, path=None):
        self.invalid_step(
            {"fields": [field]},
            steptype_param=STEP_TYPE_PARAMS[step_type],
            error=error,
            path=path,
        )

    def _invalid_select_field(self, field, *, step_type, error, path=None):
        self._invalid_field(
            {
                **{
                    "select": "select",
                    "key": "key",
                    "options": [{"label": "label", "value": "value"}],
                },
                **field,
            },
            step_type=step_type,
            error=error,
            path=path,
        )

    def test_field_missing_required_key(self, step_type):
        self._invalid_field(
            {},
            step_type=step_type,
            error="Input fields must contain `text`` or `select`",
            path=".fields[0]",
        )

    # @TODO: This isn't schema-invalid, but it could be with some TLC
    #   (e.g. make two types in the schema where `multiple` is `enum: [true]`)
    def test_single_select_list_default(self, step_type):
        self._invalid_select_field(
            {"multiple": False, "default": ["value"]},
            step_type=step_type,
            error="`default` cannot be a list when `multiple` is `False`",
        )

    def test_bad_key(self, step_type):
        self._invalid_field(
            {"text": "text", "key": "has:a:colon"},
            step_type=step_type,
            error="Expected `'has:a:colon'` to match regex `^[a-zA-Z0-9-_]+$`",
        )
        self._invalid_field(
            {"text": "text", "key": "has a space"},
            step_type=step_type,
            error="Expected `'has a space'` to match regex `^[a-zA-Z0-9-_]+$`",
        )
        self._invalid_select_field(
            {"key": "has:a:colon"},
            step_type=step_type,
            error="Expected `'has:a:colon'` to match regex `^[a-zA-Z0-9-_]+$`",
        )
        self._invalid_select_field(
            {"key": "has a space"},
            step_type=step_type,
            error="Expected `'has a space'` to match regex `^[a-zA-Z0-9-_]+$`",
        )

    def test_missing_key(self, step_type):
        self._invalid_field(
            {"text": "text"},
            step_type=step_type,
            error="`TextInput` missing 1 required fields: `key`",
        )
        self._invalid_field(
            {"select": "select", "options": []},
            step_type=step_type,
            error="`SelectInput` missing 1 required fields: `key`",
        )

    def test_missing_options(self, step_type):
        self._invalid_field(
            {"select": "select", "key": "key"},
            step_type=step_type,
            error="`SelectInput` missing 1 required fields: `options`",
        )

    def test_empty_options(self, step_type):
        self._invalid_field(
            {"select": "select", "key": "key", "options": []},
            step_type=step_type,
            error="Expected `[]` to be non-empty",
        )

    def test_text_format_not_valid_regex(self, step_type):
        self._invalid_field(
            {"text": "text", "key": "key", "format": "'[a-zA-Z++++'"},
            step_type=step_type,
            error="Expected a valid regex pattern, got `\"'[a-zA-Z++++'\"",
        )


class Test_BlockStep(_TestBase):
    # Nothing yet!
    pass


class Test_InputStep(_TestBase):
    # Nothing yet!
    pass


class Test_CommandStep(_TestBase):
    def invalid_step(self, step, steptype_param=None, error=None, path=None):
        super().invalid_step({**step, "type": "command"}, error=error, path=path)

    def test_notify_unsupported(self):
        self.invalid_step(
            {"notify": ["unknown"]},
            error="Unrecognizable notification: `unknown`",
            path=".notify",
        )
        self.invalid_step(
            {"notify": [{"email": "hello@example.com"}]},
            error="`email` is not a valid step notification",
            path=".notify",
        )
        self.invalid_step(
            {"notify": [{"webhook": "https://example.com"}]},
            error="`webhook` is not a valid step notification",
            path=".notify",
        )
        self.invalid_step(
            {"notify": [{"pagerduty_change_event": "pagerduty_change_event"}]},
            error="`pagerduty_change_event` is not a valid step notification",
            path=".notify",
        )

    def test_notify__slack__empty_channels(self):
        self.invalid_step(
            {"notify": [{"slack": {"channels": []}}]},
            error="Expected `[]` to be non-empty",
            path=".notify.slack.channels",
        )

    def test_matrix_steup_empty_list(self):
        self.invalid_step(
            {"matrix": {"setup": []}},
            error="Expected `[]` to be non-empty",
            path=".matrix",
        )

    def test_matrix__single_dimension__mismatched_adjustments(self):
        self.invalid_step(
            {"matrix": {"setup": [""], "adjustments": [{"with": {"": ""}}]}},
            error="Expected `str`, got `{'': ''}` of type `dict`",
            path=".matrix.adjustments[0].with_value",
        )

    def test_matrix__multi_dimension__mismatched_adjustments(self):
        self.invalid_step(
            {"matrix": {"setup": {"": []}, "adjustments": [{"with": []}]}},
            error="Expected `dict`, got `[]` of type `list`",
            path=".matrix.adjustments[0].with_value",
        )

    def test_matrix__multi_dimension__setup_empty_dict(self):
        self.invalid_step(
            {"matrix": {"setup": {}}},
            error="Expected `{}` to be non-empty",
            path=".matrix.setup",
        )

    def test_matrix__single_dimension__adjustment_empty_dict(self):
        self.invalid_step(
            {"matrix": {"setup": [""], "adjustments": [{}]}},
            error="`ScalarAdjustment` missing 1 required fields: `with_value`",
            path=".matrix.adjustments[0]",
        )

    def test_multi_dimension__adjustment_empty_dict(self):
        self.invalid_step(
            {"matrix": {"setup": {"a": ["b"]}, "adjustments": [{}]}},
            error="`MultiDimensionMatrixAdjustment` missing 1 required fields: `with_value`",
            path=".matrix.adjustments[0]",
        )

    def test_matrix__multi_dimension__bad_key(self):
        self.invalid_step(
            {"matrix": {"setup": {"": []}}},
            error="Expected `''` to match regex `^[a-zA-Z0-9_]+$",
            path=".matrix.setup (key '')",
        )

    def test_plugins__multiple_properties(self):
        self.invalid_step(
            {"plugins": [{"key1": {}, "key2": {}}]},
            error="...",
            path=".plugins[0]",
        )

    def test_cache__missing_paths(self):
        self.invalid_step(
            {"cache": {}},
            error="`CommandCache` missing 1 required fields: `paths`",
            path=".cache",
        )

    def test_cache__bad_size(self):
        self.invalid_step(
            {"cache": {"paths": [], "size": "1"}},
            error="Expected `'1'` to match regex `^\\d+g$`",
            path=".cache.size",
        )

    def test_retry__automated__big_limit(self):
        self.invalid_step(
            {"retry": {"automatic": [{"limit": 11}]}},
            error="Expected `11` to be <= 10",
            path=".retry.automatic[0].limit",
        )


class Test_TriggerStep(_TestBase):
    def invalid_step(self, step, steptype_param=None, error=None, path=None):
        super().invalid_step({**step, "type": "trigger"}, error=error, path=path)

    def test_missing_trigger(self):
        self.invalid_step(
            {}, error="`TriggerStep` missing 1 required fields: `trigger`"
        )


class Test_GroupStep(_TestBase):
    def invalid_step(self, step, steptype_param=None, error=None, path=None):
        super().invalid_step({**step, "group": "group"}, error=error, path=path)

    def test_missing_steps(self):
        self.invalid_step({}, error="`GroupStep` missing 1 required fields: `steps`")

    def test_empty_steps(self):
        self.invalid_step(
            {"steps": []}, error="Expected `[]` to be non-empty", path=".steps"
        )

    def test_notify_unsupported(self):
        self.invalid_step(
            {"notify": ["unknown"]},
            error="Unrecognizable notification: `unknown`",
            path=".notify",
        )
        self.invalid_step(
            {"notify": [{"email": "hello@example.com"}]},
            error="`email` is not a valid step notification",
            path=".notify",
        )
        self.invalid_step(
            {"notify": [{"webhook": "https://example.com"}]},
            error="`webhook` is not a valid step notification",
            path=".notify",
        )
        self.invalid_step(
            {"notify": [{"pagerduty_change_event": "pagerduty_change_event"}]},
            error="`pagerduty_change_event` is not a valid step notification",
            path=".notify",
        )

    def test_slack_notify_empty_channels(self):
        self.invalid_step(
            {"notify": [{"slack": {"channels": []}}]},
            error="Expected `[]` to be non-empty",
            path=".notify.slack.channels",
        )

    # @TODO: group step of group step


class Test_WaitStep(_TestBase):
    # Nothing yet!
    pass
