from pydantic.functional_validators import AfterValidator
from ._types import AllowDependencyFailureT, DependsOnT, IfT
from ._alias import FieldAlias, FieldAliasSupport
from typing_extensions import TypeAliasType
from uuid import UUID
import re
from pydantic import BaseModel, Field, AfterValidator, ValidationError
from pydantic_core import PydanticCustomError
from typing import Annotated, ClassVar, Any

def not_(value: str):
    try:
        UUID(value)
    except ValueError:
        return value
    else:
        raise PydanticCustomError(
            "not_uuid_error",
            'Value must not be a valid UUID'
        )


KeyT = TypeAliasType(
    "KeyT",
    Annotated[
        str,
        Field(
            description="A unique identifier for a step, must not resemble a UUID",
            examples=["deploy-staging", "test-integration"],
            json_schema_extra={
                "not": {"format": "uuid"}
            }
        ),
        AfterValidator(not_),
    ],
)


class BKStepBase(FieldAliasSupport):
    key: KeyT | None = Field(default=None)
    allow_dependency_failure: AllowDependencyFailureT = False
    depends_on: DependsOnT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")

    id: ClassVar[FieldAlias] = FieldAlias("key", deprecated=True)
    identifier: ClassVar[FieldAlias] = FieldAlias("key")

    # `branches` is not valid on `group` (but IS on wait, just missing from schema)
