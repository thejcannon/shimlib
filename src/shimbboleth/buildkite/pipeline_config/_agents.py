from typing import Annotated
from typing_extensions import TypeAliasType

from shimbboleth._model import Description, Examples


AgentsListT = TypeAliasType(
    "AgentsListT",
    Annotated[
        list[str],
        Description("Query rules to target specific agents in k=v format"),
        Examples("queue=default", "xcode=true"),
    ],
)

AgentsObjectT = TypeAliasType(
    "AgentsObjectT",
    Annotated[
        # @TODO: Any? (agent query rules cant be an object or an array)
        dict[str, str],
        Description("Query rules to target specific agents"),
        Examples({"queue": "deploy"}, {"ruby": "2*"}),
    ],
)


def agents_from_json(value: AgentsObjectT | AgentsListT) -> dict[str, str]:
    if isinstance(value, list):
        # @TODO: probably more validation (e.g. malformed strings)
        value = dict(elem.split("=") for elem in value)
    return value
