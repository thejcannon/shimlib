from shimbboleth._model import Model, field, FieldAlias
from ._types import bool_from_json
from uuid import UUID
from typing import ClassVar, Any, final


# @TODO: Belongs in _model validation
def _ensure_not_uuid(value: str) -> str:
    try:
        UUID(value)
    except ValueError:
        return value
    else:
        raise ValueError("not_uuid_error", "Value must not be a valid UUID")


class Dependency(Model, extra=False):
    allow_failure: bool = field(default=False, json_converter=bool_from_json)
    step: str | None = None


class StepBase(Model):
    # @TODO: Annotate `Not[UUID]`
    key: str | None = field(default=None)
    """A unique identifier for a step, must not resemble a UUID"""

    allow_dependency_failure: bool = field(default=False, json_converter=bool_from_json)
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

    # def __post_init__(self):
    #     super().__post_init__()
    #     if self.key:
    #         _ensure_not_uuid(self.key)

    @Model._json_converter_(depends_on)
    @classmethod
    def _convert_depends_on(
        cls, value: str | list[str | Dependency]
    ) -> list[Dependency]:
        if isinstance(value, str):
            return [Dependency(step=value)]
        return [
            Dependency(step=elem) if isinstance(elem, str) else elem for elem in value
        ]
