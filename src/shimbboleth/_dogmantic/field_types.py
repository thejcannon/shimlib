from dataclasses import dataclass

NonEmpty = object()


@dataclass(frozen=True, slots=True)
class Description:
    description: str


@dataclass(frozen=True, slots=True)
class Examples:
    examples: list

    def __init__(self, *examples):
        object.__setattr__(self, "examples", list(examples))


@dataclass(frozen=True, slots=True)
class MatchesRegex:
    regex: str
