from ._types import AllowDependencyFailureT, DependsOnT, IfT, LabelT
from typing_extensions import TypeAliasType
from pydantic import (
    Field,
    BaseModel as PydanticBaseModel,
    model_validator,
    AliasChoices,
    ConfigDict,
)

from typing import Any, Annotated, Unpack, ClassVar, Literal


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

# @TODO: New base class that pops Nones? (Then remove the code in _alias_heirarchy)

class BKStepBase(
    PydanticBaseModel,
    # NB: Defer building since we change the schema in `__pydantic_init_subclass__`
    defer_build=True,
):
    __shimbboleth_bk_step_alias__: ClassVar[str | None] = None

    # @TODO: support "wait"/"waiter"

    key: KeyT | None = Field(
        default=None, validation_alias=AliasChoices("key", "id", "identifier")
    )
    allow_dependency_failure: AllowDependencyFailureT = False
    depends_on: DependsOnT | None = None
    if_condition: IfT | None = Field(default=None, alias="if")
    label: LabelT | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "name",
            "label",
            # NB: If the step name field isn't being used
            #   (e.g. `command` and `trigger` are used, but `input` and `wait` aren't')
            #   then this also includes an alias of the step name.
        ),
    )
    # @TODO: Add `type` field

    # `branches` is not valid on `group` (but IS on wait, just missing from schema)

    @model_validator(mode="before")
    @classmethod
    def _alias_heirarchy(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Support mutliple `validation_alias` aliases being passed.

        (NOTE: Buildkite stops verifying the type at the first hit)
        """
        if not isinstance(data, dict):
            return

        for field_name, field_info in cls.model_fields.items():
            validation_alias = field_info.validation_alias
            if not isinstance(validation_alias, AliasChoices):
                continue
            alias_iter = iter(validation_alias.choices)
            for alias in alias_iter:
                assert isinstance(alias, str)
                if alias in data and data[alias] is None:
                    data.pop(alias)
                if alias in data:
                    for lower_prio in alias_iter:
                        assert isinstance(lower_prio, str)
                        data.pop(lower_prio, None)
                    break
        return data

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any):
        super().__pydantic_init_subclass__(**kwargs)

        # (maybe) Add the step name to the `label` alias choices
        step_type = cls.__name__.removesuffix("Step").lower()
        if step_type not in cls.model_fields:
            label_field_info = cls.model_fields["label"]
            assert isinstance(label_field_info.validation_alias, AliasChoices)
            label_field_info.validation_alias = AliasChoices(
                *label_field_info.validation_alias.choices, step_type
            )
            cls.model_rebuild()
