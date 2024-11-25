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
from ._fields import TextInput, SelectInput


class InputStep(BaseModel, extra="forbid"):
    """
    An input step is used to collect information from a user.

    https://buildkite.com/docs/pipelines/input-step
    """

    allow_dependency_failure: AllowDependencyFailureT = False
    branches: BranchesT | None = None
    depends_on: DependsOnT | None = None
    fields: list[TextInput | SelectInput] | None = None
    if_condition: IfT | None = Field(default=None, alias="if")
    label: str | None = Field(default=None, description="The label of the input step")
    key: KeyT | None = Field(
        default=None, validation_alias=AliasChoices("key", "id", "identifier")
    )
    label: LabelT | None = Field(
        default=None, validation_alias=AliasChoices("label", "name")
    )
    prompt: PromptT | None = None
    type: Literal["input"] | None = None


class NestedInputStep(BaseModel, extra="forbid"):
    block: InputStep | None = None


StringInputStep = TypeAliasType(
    "StringInputStep",
    Annotated[
        Literal["input"],
        Field(
            description="Pauses the execution of a build and waits on a user to unblock it"
        ),
    ],
)
