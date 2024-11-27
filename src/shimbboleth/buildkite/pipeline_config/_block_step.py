from typing import Literal, Annotated
from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field, AliasChoices

from ._types import (
    AllowDependencyFailureT,
    BranchesT,
    IfT,
    DependsOnT,
    IdentifierT,
    KeyT,
    LabelT,
    PromptT,
)
from ._fields import TextInput, SelectInput, FieldsT


class BlockStep(BaseModel, extra="forbid"):
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
    depends_on: DependsOnT | None = None
    fields: FieldsT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")
    key: KeyT | None = Field(
        default=None, validation_alias=AliasChoices("key", "identifier", "id")
    )
    # @TODO: precedence is name > label > block
    label: LabelT | None = Field(
        default=None, validation_alias=AliasChoices("label", "name", "block")
    )
    prompt: PromptT | None = None
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
