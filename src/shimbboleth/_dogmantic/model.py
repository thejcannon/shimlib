# @TODO: DO I really need to use a base class here?
# class SupportsConverterMixin:or we could continue to decorate a la dataclasses?

from typing import dataclass_transform, Any
import dataclasses

# NB: This is just a heirarchical Model helper, with kw_only=True and slots=True.
#   (@TODO: Ideally we ensure none of the other nonsense is there? But also meh?)


@dataclass_transform(kw_only_default=True, field_specifiers=(dataclasses.field,))
class ModelMeta(type):
    __allow_extra_properties__: bool

    def __new__(mcls, name, bases, namespace, *, extra: bool | None = None):
        cls = super().__new__(
            mcls,
            name,
            bases,
            namespace,
        )
        # NB: Because you get a new type when adding `__slots__`,
        #   `dataclass` actualy returns a new type when using `slots=True`.
        #   That means this constructor will run again, but this time we
        #   already have the slotted dataclass.
        #   We can tell if it's a dataclass if it has the magic attribute.
        if "__dataclass_fields__" in cls.__dict__:
            return cls
        return dataclasses.dataclass(slots=True)(cls)

    def __init__(cls, name, bases, namespace, *, extra: bool | None = None):
        cls.__allow_extra_properties__ = bool(extra)


class Model(metaclass=ModelMeta):
    @classmethod
    def model_load(cls, value: dict[str, Any]):
        raise NotImplementedError

    def model_dump(self) -> dict[str, Any]:
        # @TODO: asdict(self)?!
        raise NotImplementedError
