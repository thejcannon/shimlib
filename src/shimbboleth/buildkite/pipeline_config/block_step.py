from typing import Literal, Annotated, ClassVar
from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field

from shimbboleth.buildkite.pipeline_config._alias import FieldAlias

from ._types import (
    AllowDependencyFailureT,
    BranchesT,
    LabelT,
    PromptT,
)
from ._fields import FieldsT
from ._base import BKStepBase


class BlockStep(BKStepBase, extra="forbid"):
    """
    A block step is used to pause the execution of a build and wait on a team member to unblock it using the web or the API.

    https://buildkite.com/docs/pipelines/block-step
    """

    allow_dependency_failure: AllowDependencyFailureT = False
    blocked_state: Literal["passed", "failed", "running"] | None = Field(
        default=None,
        description="The state that the build is set to when the build is blocked by this block step",
    )
    branches: BranchesT | None = None
    fields: FieldsT | None = None
    prompt: PromptT | None = None
    name: ClassVar = FieldAlias("label")
    label: LabelT | None = Field(default=None)
    block: ClassVar = FieldAlias("label")
    type: Literal["block"] | None = None


class NestedBlockStep(BaseModel, extra="forbid"):
    block: BlockStep | None = None


StringBlockStep = TypeAliasType(
    "StringBlockStep",
    Annotated[
        Literal["block"],
        Field(
            description="Pauses the execution of a build and waits on a user to unblock it"
        ),
    ],
)
