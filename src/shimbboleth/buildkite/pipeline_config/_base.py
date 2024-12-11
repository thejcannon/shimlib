from ._types import IfT, LooseBoolT
from ._alias import FieldAlias, FieldAliasSupport
from typing_extensions import TypeAliasType
from uuid import UUID
from pydantic import Field, AfterValidator, BaseModel
from pydantic_core import PydanticCustomError
from typing import Annotated, ClassVar


def _not_a_uuid(value: str) -> str:
    try:
        UUID(value)
    except ValueError:
        return value
    else:
        raise PydanticCustomError("not_uuid_error", "Value must not be a valid UUID")


KeyT = TypeAliasType(
    "KeyT",
    Annotated[
        str,
        Field(
            description="A unique identifier for a step, must not resemble a UUID",
            examples=["deploy-staging", "test-integration"],
            json_schema_extra={
                "not": {
                    "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
                }
            },
        ),
        AfterValidator(_not_a_uuid),
    ],
)

AllowDependencyFailureT = TypeAliasType(
    "AllowDependencyFailureT",
    Annotated[
        LooseBoolT,
        Field(
            default=False,
            description="Whether to proceed with this step and further steps if a step named in the depends_on attribute fails",
        ),
    ],
)


class DependsOnDependency(BaseModel, extra="forbid"):
    allow_failure: LooseBoolT | None = False
    step: str | None = None


DependsOnT = TypeAliasType(
    "DependsOnT",
    # @TODO: Canonicalize
    Annotated[
        None | str | list[str | DependsOnDependency],
        Field(description="The step keys for a step to depend on"),
    ],
)


class BKStepBase(FieldAliasSupport):
    key: KeyT | None = Field(default=None)
    allow_dependency_failure: AllowDependencyFailureT = False
    depends_on: DependsOnT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")

    id: ClassVar[FieldAlias] = FieldAlias("key", deprecated=True)
    identifier: ClassVar[FieldAlias] = FieldAlias("key")
