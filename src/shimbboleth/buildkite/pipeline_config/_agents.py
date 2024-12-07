from typing_extensions import TypeAliasType
from pydantic import (
    Field,
)
import pydantic_core
from ._canonicalize import Canonicalizer

from typing import Any, Annotated

AgentsListT = TypeAliasType(
    "AgentsListT",
    Annotated[
        list[str],
        Field(
            description="Query rules to target specific agents in k=v format",
            examples=["queue=default", "xcode=true"],
        ),
    ],
)
AgentsObjectT = TypeAliasType(
    "AgentsObjectT",
    Annotated[
        # @TODO: Any? (agent query rules cant be an object or an array)
        dict[str, Any],
        Field(
            description="Query rules to target specific agents",
            examples=[{"queue": "deploy"}, {"ruby": "2*"}],
        ),
    ],
)


class AgentsCanonicalizer(Canonicalizer[AgentsObjectT | AgentsListT, dict[str, str]]):
    @classmethod
    def canonicalize(
        cls,
        value: AgentsObjectT | AgentsListT,
    ) -> dict[str, str]:
        if isinstance(value, list):
            # @TODO: probably more validation (e.g. malformed strings)
            value = dict(elem.split("=") for elem in value)
        return value


AgentsT = TypeAliasType("AgentsT", Annotated[dict[str, Any], AgentsCanonicalizer()])
