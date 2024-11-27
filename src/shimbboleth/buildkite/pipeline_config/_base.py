from ._types import AllowDependencyFailureT, DependsOnT, IfT, LabelT
from typing_extensions import TypeAliasType
from pydantic import (
    Field,
    BaseModel as PydanticBaseModel,
    model_validator,
    AliasChoices,
    ConfigDict
)

from typing import Any, Annotated, Unpack


KeyT = TypeAliasType(
    "KeyT",
    Annotated[
        str,
        Field(
            # TODO: UUID validation
            description="A unique identifier for a step, must not resemble a UUID",
            examples=["deploy-staging", "test-integration"],
        ),
    ],
)


class BKStepBase(PydanticBaseModel):
    key: KeyT | None = Field(
        default=None, validation_alias=AliasChoices("key", "id", "identifier")
    )
    allow_dependency_failure: AllowDependencyFailureT = False
    depends_on: DependsOnT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")
    # @TODO: precedence is name > label > <other one>
    label: LabelT | None = Field(
       default=None, validation_alias=AliasChoices("label", "name")
    )

    # `branches` is not valid on `group` (but IS on wait, just missing from schema)

    @model_validator(mode="before")
    @staticmethod
    def _key_heirarchy(data: dict[str, Any]) -> dict[str, Any]:
        """
        Buildkite has a "heirarchy" of aliases for `key`/`id`/`identifier`.
        """
        if not isinstance(data, dict):
            return
        # NB: Buildkite doesn't validate the type of the field(s) not being used,
        #   so `pop` is the right thing to do.
        if "key" in data:
            data.pop("id", None)
            data.pop("identifier", None)
        if "id" in data:
            data.pop("identifier", None)
        return data

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any):
        super().__pydantic_init_subclass__(**kwargs)
        step_type = cls.__name__.removesuffix("Step").lower()
        if step_type not in cls.model_fields:
            label_field_info = cls.model_fields["label"]
            assert isinstance(label_field_info.validation_alias, AliasChoices)
            label_field_info.validation_alias = AliasChoices(*label_field_info.validation_alias.choices, step_type)
            delattr(cls, '__pydantic_core_schema__')
