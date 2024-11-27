from typing import Literal, Annotated

from pydantic import BaseModel, Field, AliasChoices

from ._types import (
    AllowDependencyFailureT,
    IfT,
    DependsOnT,
    IdentifierT,
    KeyT,
    SkipT,
)
from ._block_step import BlockStep, NestedBlockStep, StringBlockStep
from ._input_step import InputStep, NestedInputStep, StringInputStep
from ._wait_step import WaitStep, NestedWaitStep, StringWaitStep
from ._trigger_step import TriggerStep, NestedTriggerStep
from ._command_step import CommandStep, NestedCommandStep
from ._notify import BuildNotifyT


class GroupStep(BaseModel, extra="forbid"):
    """
    A group step can contain various sub-steps, and display them in a single logical group on the Build page.

    https://buildkite.com/docs/pipelines/group-step
    """

    allow_dependency_failure: AllowDependencyFailureT = False
    depends_on: DependsOnT | None = None
    group: str | None = Field(
        default=None,
        description="The name to give to this group of steps",
        examples=["Tests"],
        validation_alias=AliasChoices("group", "label", "name"),
    )

    if_condition: IfT | None = Field(default=None, alias="if")
    key: KeyT | None = Field(
        default=None, validation_alias=AliasChoices("key", "id", "identifier")
    )
    notify: BuildNotifyT | None = None
    skip: SkipT | None = None
    steps: Annotated[
        list[
            BlockStep
            | NestedBlockStep
            | StringBlockStep
            | InputStep
            | NestedInputStep
            | StringInputStep
            | CommandStep
            | NestedCommandStep
            | WaitStep
            | NestedWaitStep
            | StringWaitStep
            | TriggerStep
            | NestedTriggerStep
        ]
        | None,
        Field(description="A list of steps", min_length=1),
    ]
    type: Literal["group"] | None = None
