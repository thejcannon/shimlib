from ._types import AllowDependencyFailureT, DependsOnT, IfT
from ._alias import FieldAlias, FieldAliasSupport
from typing_extensions import TypeAliasType
import re
from pydantic import BaseModel, Field

from typing import Annotated, ClassVar


KeyT = TypeAliasType(
    "KeyT",
    Annotated[
        str,
        Field(
            description="A unique identifier for a step, must not resemble a UUID",
            examples=["deploy-staging", "test-integration"],
            pattern=re.compile(
                r"^(?!^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$).*$"
            ),
        ),
    ],
)

# @TODO: New base class that pops Nones? (Then remove the code in _alias_heirarchy)


class BKStepBase(FieldAliasSupport):
    key: KeyT | None = Field(default=None)
    id: ClassVar[FieldAlias] = FieldAlias("key", deprecated=True)
    identifier: ClassVar[FieldAlias] = FieldAlias("key")

    allow_dependency_failure: AllowDependencyFailureT = False
    depends_on: DependsOnT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")

    # `branches` is not valid on `group` (but IS on wait, just missing from schema)
