from typing import ClassVar, Literal


from shimbboleth._model import Model, field, FieldAlias, NonEmptyList
from shimbboleth.buildkite.pipeline_config._types import skip_from_json

from .block_step import BlockStep
from .input_step import InputStep
from .wait_step import WaitStep
from .trigger_step import TriggerStep
from .command_step import CommandStep
from ._notify import BuildNotifyT
from ._base import StepBase
from ._nested_steps import (
    NestedWaitStep,
    NestedInputStep,
    NestedBlockStep,
    NestedCommandStep,
    NestedTriggerStep,
)


class GroupStep(StepBase, extra=False):
    """
    A group step can contain various sub-steps, and display them in a single logical group on the Build page.

    https://buildkite.com/docs/pipelines/group-step
    """

    # NB: `group` is required, but can be null.
    # (e.g. BK complains about `steps: [{"steps": ["wait"]}]` not having a type)
    group: str | None
    """The name to give to this group of steps"""

    notify: BuildNotifyT = field(default_factory=list)

    # NB: Passing an empty string is equivalent to false.
    skip: bool | str = field(default=False, json_converter=skip_from_json)
    "Whether this step should be skipped. Passing a string provides a reason for skipping this command"

    steps: NonEmptyList[
        BlockStep | InputStep | CommandStep | WaitStep | TriggerStep
    ] = field()
    """A list of steps"""

    name: ClassVar = FieldAlias("group", json_mode="append")
    label: ClassVar = FieldAlias("group", json_mode="append")

    @Model._json_converter_(steps)
    @staticmethod
    def __steps__from_json(
        value: list[
            BlockStep
            | InputStep
            | CommandStep
            | WaitStep
            | TriggerStep
            | NestedBlockStep
            | NestedInputStep
            | NestedCommandStep
            | NestedWaitStep
            | NestedTriggerStep
            | Literal["block", "manual"]
            | Literal["input"]
            | Literal["command", "commands", "script"]
            | Literal["wait", "waiter"]
        ],
    ) -> NonEmptyList[BlockStep | InputStep | CommandStep | WaitStep | TriggerStep]:
        from ._parse_steps import parse_steps

        # NB: Because `GroupStep` is not a valid type of value`, we know this will never return
        #    a `GroupStep` instance.
        return parse_steps(value)  # type: ignore
