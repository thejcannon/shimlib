from typing import Literal, Annotated
from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field
from pydantic.aliases import AliasChoices

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


class InputStep(BaseModel, extra="forbid"):
    """
    An input step is used to collect information from a user.

    https://buildkite.com/docs/pipelines/input-step
    """

    allow_dependency_failure: AllowDependencyFailureT = False
    branches: BranchesT | None = None
    depends_on: DependsOnT | None = None
    fields: FieldsT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")
    key: KeyT | None = Field(
        default=None, validation_alias=AliasChoices("key", "id", "identifier")
    )
    # @TODO: precedence is name > label > input
    label: LabelT | None = Field(
        default=None, validation_alias=AliasChoices("label", "name", "input")
    )
    prompt: PromptT | None = None
    type: Literal["input"] | None = None


class NestedInputStep(BaseModel, extra="forbid"):
    input: InputStep | None = None


StringInputStep = TypeAliasType(
    "StringInputStep",
    Annotated[
        Literal["input"],
        Field(
            description="Pauses the execution of a build and waits on a user to unblock it"
        ),
    ],
)
