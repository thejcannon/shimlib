"""
Validation of model fields.

NOTE: This only handles Annotated validations (E.g. `Annotated[int, Ge(10)]`)
"""

from typing import TypeVar, ClassVar, Annotated, Protocol
import dataclasses
import re

T = TypeVar("T")


class Validator(Protocol):
    def __call__(self, value) -> None: ...


class ValidationError(ValueError):
    def __init__(self, value, expectation: str):
        super().__init__(value, expectation)
        self.context = []

    def __str__(self):
        context = "".join(f"\n{note}" for note in self.context)
        return f"Expected '{self.args[0]}' to {self.args[1]}{context}"

    def __repr__(self):
        return f"ValidationError(value={self.args[0]!r}, expectation={self.args[1]!r})"

    @property
    def value(self):
        return self.args[0]

    @property
    def expectation(self) -> str:
        return self.args[1]

    def add_context(self, context: str):
        self.context.append(context)


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
        return f"match regex '{self.regex.pattern}'"


NonEmptyList = Annotated[list[T], NonEmpty]
NonEmptyString = Annotated[str, NonEmpty]


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
