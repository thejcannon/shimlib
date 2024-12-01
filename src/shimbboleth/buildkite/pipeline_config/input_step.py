from typing import Literal, Annotated
from typing_extensions import ClassVar, TypeAliasType

from pydantic import BaseModel, Field

from ._alias import FieldAlias
from ._base import BKStepBase
from ._types import (
    BranchesT,
    PromptT,
)
from ._fields import FieldsT


class InputStep(BKStepBase, extra="forbid"):
    """
    An input step is used to collect information from a user.

    https://buildkite.com/docs/pipelines/input-step
    """

    branches: BranchesT | None = None
    fields: FieldsT | None = None
    prompt: PromptT | None = None
    input: str | None = Field(default=None, description="The label of the input step")
    type: Literal["input"] | None = None

    label: ClassVar = FieldAlias("input", mode="prepend")
    name: ClassVar = FieldAlias("input", mode="prepend")


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
