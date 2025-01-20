from typing import ClassVar, Literal


from shimbboleth.internal.clay import field, FieldAlias, NonEmptyList
from shimbboleth.internal.clay.jsonT import JSONArray, JSONObject
from shimbboleth.buildkite.pipeline_config._types import skip_from_json

from shimbboleth.buildkite.pipeline_config._nested_steps import (
    NestedWaitStep,
    NestedInputStep,
    NestedBlockStep,
    NestedCommandStep,
    NestedTriggerStep,
)
from shimbboleth.buildkite.pipeline_config.block_step import BlockStep
from shimbboleth.buildkite.pipeline_config.input_step import InputStep
from shimbboleth.buildkite.pipeline_config.wait_step import WaitStep
from shimbboleth.buildkite.pipeline_config.trigger_step import TriggerStep
from shimbboleth.buildkite.pipeline_config.command_step import CommandStep
from shimbboleth.buildkite.pipeline_config._notify import StepNotifyT
from shimbboleth.buildkite.pipeline_config._base import StepBase


class GroupStep(StepBase, extra=False):
    """
    A group step can contain various sub-steps, and display them in a single logical group on the Build page.

    https://buildkite.com/docs/pipelines/group-step
    """

    # NB: `group` is required, but can be null.
    # (e.g. BK complains about `steps: [{"steps": ["wait"]}]` not having a type)
    group: str | None
    """The name to give to this group of steps"""

    notify: StepNotifyT = field(default_factory=list)

    # NB: Passing an empty string is equivalent to false.
    skip: bool | str = field(default=False, json_loader=skip_from_json)
    "Whether this step should be skipped. Passing a string provides a reason for skipping this command"

    steps: NonEmptyList[
        BlockStep | InputStep | CommandStep | WaitStep | TriggerStep
    ] = field()
    """A list of steps"""

    name: ClassVar = FieldAlias("group", json_mode="append")
    label: ClassVar = FieldAlias("group", json_mode="append")


@GroupStep._json_loader_(
    "steps",
    json_schema_type=NonEmptyList[
        BlockStep
        | InputStep
        | CommandStep
        | WaitStep
        | TriggerStep
        | NestedWaitStep
        | NestedInputStep
        | NestedBlockStep
        | NestedCommandStep
        | NestedTriggerStep
        | Literal[
            "block",
            "manual",
            "input",
            "command",
            "commands",
            "script",
            "wait",
            "waiter",
        ]
    ],
)
@staticmethod
def _load_steps(
    value: list[str | JSONObject],
) -> NonEmptyList[BlockStep | InputStep | CommandStep | WaitStep | TriggerStep]:
    # NB: Nested to avoid circular import
    from ._parse_steps import parse_steps

    # @TODO: Don't allow group steps in here
    return parse_steps(value)  # type: ignore


@GroupStep._json_loader_("notify", json_schema_type=StepNotifyT)
def _load_notify(value: JSONArray) -> StepNotifyT:
    from shimbboleth.buildkite.pipeline_config._notify import parse_step_notify

    return parse_step_notify(value)
