from typing import Annotated, ClassVar, TypeAlias, Literal, Any


from shimbboleth.buildkite.pipeline_config._types import bool_from_json
from shimbboleth._model import Model, field, FieldAlias, NonEmpty, Description

from .block_step import BlockStep
from .input_step import InputStep
from .wait_step import WaitStep
from .trigger_step import TriggerStep
from .command_step import CommandStep
from ._notify import BuildNotifyT
from ._base import BKStepBase
from ._nested_steps import (
    NestedWaitStep,
    NestedInputStep,
    NestedBlockStep,
    NestedCommandStep,
    NestedTriggerStep,
)


GROUP_STEP_INPUT_TYPES: TypeAlias = (
    BlockStep
    | NestedBlockStep
    | InputStep
    | NestedInputStep
    | CommandStep
    | NestedCommandStep
    | WaitStep
    | NestedWaitStep
    | TriggerStep
    | Literal["block", "wait", "waiter", "input"]
)


class GroupStep(BKStepBase, extra=False):
    """
    A group step can contain various sub-steps, and display them in a single logical group on the Build page.

    https://buildkite.com/docs/pipelines/group-step
    """

    group: str | None = None
    """The name to give to this group of steps"""

    notify: BuildNotifyT | None = None

    # NB: Passing an empty string is equivalent to false.
    skip: bool | str = field(default=False, json_converter=bool_from_json)
    "Whether this step should be skipped. Passing a string provides a reason for skipping this command"

    steps: Annotated[
        list[BlockStep | InputStep | CommandStep | WaitStep | TriggerStep], NonEmpty
    ] = field()
    """A list of steps"""

    name: ClassVar = FieldAlias("group")
    label: ClassVar = FieldAlias("group")

    @Model._json_converter_(steps)
    @classmethod
    def __steps__from_json(
        cls,
        value: Annotated[
            list[
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
                | Literal["block", "wait", "waiter", "input"]
            ],
            Description("A list of steps"),
        ],
        data: Any,
    ) -> list[BlockStep | InputStep | CommandStep | WaitStep | TriggerStep]:
        return []
