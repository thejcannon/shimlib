from typing import (
    TypeVar,
    Any,
    Iterable,
    ClassVar,
    Mapping,
)
from types import MemberDescriptorType, GenericAlias, UnionType
import dataclasses
import uuid
from shimbboleth._model._types import AnnotationType, GenericUnionType
from shimbboleth._model.validation import (
    ValidationError,
    _NotGenericAlias,
    MatchesRegex,
    Not,
    Ge,
    Le,
    NonEmpty,
    Validator,
)
from functools import singledispatch

K = TypeVar("K")
V = TypeVar("V")


@dataclasses.dataclass(slots=True, frozen=True)
class ListElementsValidator:
    element_validators: tuple[Validator, ...]

    def __call__(self, value: list):
        # @TODO: Add note on exception
        for element in value:
            for validator in self.element_validators:
                try:
                    validator(element)
                except ValidationError as e:
                    e.add_context("Where: value is a list element")
                    raise


@dataclasses.dataclass(slots=True, frozen=True)
class DictValidator:
    keys_validators: tuple[Validator, ...]
    values_validators: tuple[Validator, ...]

    def __call__(self, value: dict[K, Any]):
        for validator in self.keys_validators:
            for key in value.keys():
                try:
                    validator(key)
                except ValidationError as e:
                    e.add_context("Where: value is a dict key")
                    raise
        for validator in self.values_validators:
            for value in value.values():
                try:
                    validator(value)
                except ValidationError as e:
                    e.add_context("Where: value is a dict value")
                    raise


@dataclasses.dataclass(slots=True, frozen=True)
class UUIDValidator:
    description: ClassVar[str] = "be a valid UUID"

    def __call__(self, value: str):
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValidationError(value, self.description) from None


@dataclasses.dataclass(slots=True, frozen=True)
class UnionValidator:
    # NB: This is an incomplete map, only types with validators will be included.
    validators_by_type: Mapping[type, tuple[Validator]]

    # @TODO: Description
    description = "@TODO"

    def __call__(self, value: str):
        # NB: Remember, we assume data type-correctness
        # @TODO: This doesn't handle subtyping, but IDK if we want to support that
        validators = self.validators_by_type.get(type(value), [])
        for validator in validators:
            validator(value)


@singledispatch
def get_validators(field_type: type) -> Iterable[Validator]:
    return ()


@get_validators.register
def get_generic_alias_validators(field_type: GenericAlias) -> Iterable[Validator]:
    container_t = field_type.__origin__
    argTs = field_type.__args__
    if container_t is list:
        element_validators = tuple(get_validators(argTs[0]))
        if element_validators:
            yield ListElementsValidator(element_validators)
    elif container_t is dict:
        key_validators = tuple(get_validators(argTs[0]))
        value_validators = tuple(get_validators(argTs[1]))
        if key_validators or value_validators:
            yield DictValidator(key_validators, value_validators)


@get_validators.register
def get_union_type_validators(field_type: UnionType) -> Iterable[Validator]:
    validators_by_type = {}
    for argT in field_type.__args__:
        rawtype = argT
        while hasattr(rawtype, "__origin__"):
            rawtype = rawtype.__origin__

        if rawtype in validators_by_type:
            raise TypeError(
                f"Overlapping outer types in Union is unsupported: found multiple '{rawtype}' types."
            )
        validators_by_type[rawtype] = list(get_validators(argT))

    validators_by_type = {
        key: tuple(value) for key, value in validators_by_type.items() if value
    }
    if validators_by_type:
        yield UnionValidator(validators_by_type)


@get_validators.register
def _get_generic_union_type_validators(
    field_type: GenericUnionType,
) -> Iterable[Validator]:
    yield from get_union_type_validators(field_type)


def _get_annotation_arg_validators(argT) -> Iterable[Validator]:
    if argT is NonEmpty or isinstance(argT, (MatchesRegex, Ge, Le)):
        yield argT
    elif isinstance(argT, _NotGenericAlias):
        yield Not(list(_get_annotation_arg_validators(argT.inner)))
    elif argT is uuid.UUID:
        yield UUIDValidator()
    else:
        yield from get_validators(argT)


@get_validators.register
def get_annotation_validators(field_type: AnnotationType) -> Iterable[Validator]:
    originT = field_type.__origin__
    yield from get_validators(originT)
    for annotation in field_type.__metadata__:
        annotation_validators = list(_get_annotation_arg_validators(annotation))
        if annotation_validators and isinstance(originT, (UnionType, GenericUnionType)):
            raise TypeError(
                f"Valiating union types is unsupported. (For type '{originT}')"
            )

        yield from annotation_validators


class ValidationDescriptor:
    def __init__(
        self, field_descriptor: MemberDescriptorType, validators: tuple[Validator, ...]
    ):
        self.field_descriptor = field_descriptor
        assert validators
        self.validators = validators

    def __get__(self, instance, owner):
        return self.field_descriptor.__get__(instance, owner)

    def __set__(self, instance, value):
        for validator in self.validators:
            try:
                validator(value)
            except ValidationError as e:
                e.add_context(f"Field: {self.field_descriptor.__name__}")
                raise
        self.field_descriptor.__set__(instance, value)
