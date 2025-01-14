"""
Contains the base class for all steps: StepBase.
"""

from shimbboleth._model import Model, field, FieldAlias, Not
from ._types import bool_from_json
from uuid import UUID
from typing import ClassVar, Any, final, Annotated


class Dependency(Model, extra=False):
    # @TODO: Make a PR upstream, this isn't required upstream?
    step: str

    allow_failure: bool = field(default=False, json_loader=bool_from_json)


class StepBase(Model):
    key: Annotated[str, Not[UUID]] | None = field(default=None)
    """A unique identifier for a step, must not resemble a UUID"""

    allow_dependency_failure: bool = field(default=False, json_loader=bool_from_json)
    """Whether to proceed with this step and further steps if a step named in the depends_on attribute fails"""

    depends_on: list[Dependency] = field(default_factory=list)
    """The step keys for a step to depend on"""

    # @TEST: Is an empty string considered a skip?
    if_condition: str | None = field(default=None, json_alias="if")
    """A boolean expression that omits the step when false"""

    id: ClassVar = FieldAlias("key", deprecated=True)
    identifier: ClassVar = FieldAlias("key")

    @final
    @classmethod
    def _get_canonical_type(cls) -> str | None:
        type_field = cls.__dataclass_fields__.get("type")
        if type_field is not None:
            return type_field.default
        return None  # GroupStep :|

    def model_dump(self) -> dict[str, Any]:
        val = super().model_dump()

        type_tag = self._get_canonical_type()
        if type_tag is not None:
            val["type"] = type_tag

        return val

    @Model._json_loader_(depends_on)
    @staticmethod
    def _convert_depends_on(
        value: str | list[str | dict[str, Any]],
    ) -> list[Dependency]:
        if isinstance(value, str):
            return [Dependency(step=value)]
        return [
            Dependency(step=elem)
            if isinstance(elem, str)
            else Dependency.model_load(elem)
            for elem in value
        ]
