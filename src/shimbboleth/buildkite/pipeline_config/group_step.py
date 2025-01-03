from typing import Annotated, ClassVar, TypeAlias, Literal, Any


from shimbboleth._model import Model, field, FieldAlias, NonEmptyList

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


class GroupStep(StepBase, extra=False):
    """
    A group step can contain various sub-steps, and display them in a single logical group on the Build page.

    https://buildkite.com/docs/pipelines/group-step
    """

    group: str | None = None
    """The name to give to this group of steps"""

    notify: BuildNotifyT = field(default_factory=list)

    # NB: Passing an empty string is equivalent to false.
    skip: bool | str = field(default=False)
    "Whether this step should be skipped. Passing a string provides a reason for skipping this command"

    steps: NonEmptyList[
        BlockStep | InputStep | CommandStep | WaitStep | TriggerStep
    ] = field()
    """A list of steps"""

    name: ClassVar = FieldAlias("group")
    label: ClassVar = FieldAlias("group")

    @Model._json_converter_(steps)
    @classmethod
    def __steps__from_json(
        cls,
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
            | Literal["block", "wait", "waiter", "input"]
        ],
        data: Any,
    ) -> NonEmptyList[BlockStep | InputStep | CommandStep | WaitStep | TriggerStep]:
        return []
