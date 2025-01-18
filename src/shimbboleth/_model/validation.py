"""
Validation of model fields.

NOTE: This only handles Annotated validations (E.g. `Annotated[int, Ge(10)]`)
"""

from typing import TypeVar, ClassVar, Annotated, Protocol
import dataclasses
from contextlib import contextmanager
import re

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Validator(Protocol):
    def __call__(self, value) -> None: ...


# TODO: Does this belong in another module?
class InvalidValueError(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.path = []

    def __str__(self):
        return super().__str__() + "\n" + f"Path: {''.join(self.path)}"

    def add_prefix(self, prefix: str):
        self.path.insert(0, prefix)

    # @TODO: instead of "prefix" use either `index`, `key` or `attrname`
    @contextmanager
    @staticmethod
    def context(prefix: str):
        try:
            yield
        except InvalidValueError as e:
            e.add_prefix(prefix)
            raise


class ValidationError(InvalidValueError, ValueError):
    def __init__(self, value, expectation: str):
        super().__init__()
        self.value = value
        self.expectation = expectation

    def __str__(self):
        return f"Expected `{self.value!r}` to {self.expectation}" + super().__str__()


class _NonEmptyT(Validator):
    description: ClassVar[str] = "not be empty"

    def __call__(self, value: str | dict | list):
        if len(value) == 0:
            raise ValidationError(value, "be non-empty")

    def __repr__(self) -> str:
        return "NonEmpty"


NonEmpty = _NonEmptyT()


@dataclasses.dataclass(frozen=True, slots=True)
class MatchesRegex(Validator):
    regex: re.Pattern

    def __init__(self, regex: str):
        object.__setattr__(self, "regex", re.compile(regex))

    def __call__(self, value: str):
        if not self.regex.fullmatch(value):
            raise ValidationError(value, self.description)

    @property
    def description(self) -> str:
        return f"match regex `{self.regex.pattern}`"


NonEmptyString = Annotated[str, NonEmpty]
NonEmptyList = Annotated[list[T], NonEmpty]
NonEmptyDict = Annotated[dict[K, V], NonEmpty]


@dataclasses.dataclass(frozen=True, slots=True)
class _NotGenericAlias:
    inner: type

    def __repr__(self):
        return f"Not[{self.inner!r}]"


@dataclasses.dataclass(frozen=True, slots=True)
class Not(Validator):
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
class Ge(Validator):
    bound: int

    def __call__(self, value: int):
        if value < self.bound:
            raise ValidationError(value, self.description)

    @property
    def description(self) -> str:
        return f"be >= {self.bound}"


@dataclasses.dataclass(frozen=True, slots=True)
class Le(Validator):
    bound: int

    def __call__(self, value: int):
        if value > self.bound:
            raise ValidationError(value, self.description)

    @property
    def description(self) -> str:
        return f"be <= {self.bound}"
