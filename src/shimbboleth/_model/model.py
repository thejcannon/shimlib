# @TODO: DO I really need to use a base class here?
# class SupportsConverterMixin:or we could continue to decorate a la dataclasses?

from typing import Any
import dataclasses

from shimbboleth._model.validation import ValidationVisitor
from shimbboleth._model.model_meta import ModelMeta

# NB: This is just a heirarchical Model helper, with kw_only=True and slots=True.
#   (@TODO: Ideally we ensure none of the other nonsense is there? But also meh?)


class Model(metaclass=ModelMeta):
    _extra: dict[str, Any] = dataclasses.field(
        default_factory=dict, init=False, repr=False, compare=False, hash=False
    )
    """
    If `extra` is `True`, then this contains any extra fields provided when loading.
    """

    def __post_init__(self):
        ValidationVisitor().visit(type(self), obj=self)

    @classmethod
    def model_load(cls, value: dict[str, Any]):
        pass

    def model_dump(self) -> dict[str, Any]:
        # @TODO: asdict(self)?!
        raise NotImplementedError
