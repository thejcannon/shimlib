"""
Validation of model fields.

NOTE: This only handles Annotated validations (E.g. `Annotated[int, Ge(10)]`)
"""

from typing import (
    TypeVar,
    TypeAlias,
    Callable,
    Any,
    Iterable,
    ClassVar,
    Annotated,
)
from types import MemberDescriptorType, GenericAlias, UnionType
import dataclasses
import uuid
import re
from shimbboleth._model._types import AnnotationType, GenericUnionType
from functools import singledispatch

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
Validator: TypeAlias = Callable[[T], None]
Validators: TypeAlias = list[Validator]


class ValidationError(ValueError):
    # @TODO: Improve this, with more info
    def __init__(self, value, expectation: str):
        super().__init__(value, expectation)

    # @TODO: Add type in here?
    #   E.g. Expected `dict` to not be empty, or expected dict key to not be empty
    def __str__(self):
        return f"ValidationError: Expected '{self.args[0]}' to {self.args[1]}"

    def __repr__(self):
        return f"ValidationError(value={self.args[0]!r}, expectation={self.args[1]!r})"

    @property
    def value(self):
        return self.args[0]

    @property
    def expectation(self) -> str:
        return self.args[1]


class _NonEmptyT:
    description: ClassVar[str] = "not be empty"

    def __call__(self, value: str | dict | list):
        if len(value) == 0:
            raise ValidationError(value, "to be non-empty")

    def __repr__(self) -> str:
        return "NonEmpty"


NonEmpty = _NonEmptyT()


@dataclasses.dataclass(frozen=True, slots=True)
class MatchesRegex:
    regex: re.Pattern

    def __init__(self, regex: str):
        object.__setattr__(self, "regex", re.compile(regex))

    def __call__(self, value: str):
        if not self.regex.fullmatch(value):
            raise ValidationError(value, self.description)

    @property
    def description(self) -> str:
        return f"match regex '{self.regex.pattern}'"


@dataclasses.dataclass(slots=True, frozen=True)
class ListElementsValidator:
    element_validators: Iterable[Validator]

    def __call__(self, value: list):
        # @TODO: Add note on exception
        for element in value:
            for validator in self.element_validators:
                validator(element)


@dataclasses.dataclass(slots=True, frozen=True)
class DictValidator:
    keys_validators: list[Validator]
    values_validators: list[Validator]

    def __call__(self, value: dict[T, Any]):
        # @TODO: Add note on exception
        for validator in self.keys_validators:
            for key in value.keys():
                validator(key)
        for validator in self.values_validators:
            for value in value.values():
                validator(value)


@dataclasses.dataclass(slots=True, frozen=True)
class UUIDValidator:
    description: ClassVar[str] = "be a valid UUID"

    def __call__(self, value: str):
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValidationError(value, self.description) from None


NonEmptyList = Annotated[list[T], NonEmpty]
NonEmptyString = Annotated[str, NonEmpty]


@dataclasses.dataclass(frozen=True, slots=True)
class _NotGenericAlias:
    inner: type

    def __repr__(self):
        return f"Not[{self.inner!r}]"


@dataclasses.dataclass(frozen=True, slots=True)
class Not:
    validators: list[Validator]

    def __class_getitem__(cls, inner: type):
        return _NotGenericAlias(inner)

    def __call__(self, value):
        for validator in self.validators:
            try:
                validator(value)
            except ValidationError:
                pass
            else:
                raise ValidationError(value, f"not {validator.description}")


@dataclasses.dataclass(frozen=True, slots=True)
class Ge:
    bound: int

    def __call__(self, value: int):
        if value < self.bound:
            raise ValidationError(value, self.description)

    @property
    def description(self) -> str:
        return f"be greater than or equal to {self.bound}"


@dataclasses.dataclass(frozen=True, slots=True)
class Le:
    bound: int

    def __call__(self, value: int):
        if value > self.bound:
            raise ValidationError(value, self.description)

    @property
    def description(self) -> str:
        return f"be less than or equal to {self.bound}"


# ====


@singledispatch
def get_validators(field_type: type[T]) -> Validators:
    return []


@get_validators.register
def get_generic_alias_validators(field_type: GenericAlias) -> Validators:
    container_t = field_type.__origin__
    argTs = field_type.__args__
    if container_t is list:
        element_validators = get_validators(argTs[0])
        if element_validators:
            return [ListElementsValidator(element_validators)]
    elif container_t is dict:
        key_validators = get_validators(argTs[0])
        value_validators = get_validators(argTs[1])
        if key_validators or value_validators:
            return [DictValidator(key_validators, value_validators)]
    return []


@get_validators.register
def get_union_type_validators(field_type: UnionType) -> Validators:
    # @TODO: Assert that there's no dupes of types (e.g. list[str] | list[int] must be illegal)
    validators = []
    for argT in field_type.__args__:
        arg_validators = get_validators(argT)
        if arg_validators:
            validators.extend(
                [
                    None  # @TODO: a validator that first checks "isinstance"
                    for validator in arg_validators
                ]
            )

    return validators


@get_validators.register
def _get_generic_union_type_validators(field_type: GenericUnionType) -> Validators:
    return get_union_type_validators(field_type)


def _get_annotation_arg_validators(argT) -> Validators:
    if argT is NonEmpty or isinstance(argT, (MatchesRegex, Ge, Le)):
        return [argT]
    elif isinstance(argT, _NotGenericAlias):
        return [Not(_get_annotation_arg_validators(argT.inner))]
    elif argT is uuid.UUID:
        return [UUIDValidator()]
    else:
        return get_validators(argT)


@get_validators.register
def get_annotation_validators(field_type: AnnotationType) -> Validators:
    validators = get_validators(field_type.__origin__)
    for annotation in field_type.__metadata__:
        validators.extend(_get_annotation_arg_validators(annotation))
    return validators


class ValidationDescriptor:
    # @TODO: I think this should hold a list of validator funcs
    def __init__(self, field_descriptor: MemberDescriptorType, field_type):
        self.field_descriptor = field_descriptor
        self.field_type = field_type

    def __get__(self, instance, owner):
        return self.field_descriptor.__get__(instance, owner)

    def __set__(self, instance, value):
        # @TODO: Validate, along with nice error message
        self.field_descriptor.__set__(instance, value)
