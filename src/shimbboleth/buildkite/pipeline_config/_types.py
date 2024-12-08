from typing_extensions import TypeAliasType
from typing import Literal
from pydantic import Field, BaseModel

from typing import Any, Annotated
from ._canonicalize import ListofStringCanonicalizer, LooseBoolValidator


IfT = TypeAliasType(
    "IfT",
    Annotated[
        str,
        Field(
            description="A boolean expression that omits the step when false",
            examples=["build.message != 'skip me'", "build.branch == 'master'"],
        ),
    ],
)

# @TODO: RHS Should be "any JSON type": https://docs.pydantic.dev/latest/api/types/#pydantic.types.Json maybe?
# @TODO: Find out what happens to `true`/`false`/`null`/`dict`/`list` BK-side (likely to be stringified)
EnvT = TypeAliasType(
    "EnvT",
    Annotated[
        dict[str, Any],
        Field(
            description="Environment variables for this step",
            examples=[{"NODE_ENV": "test"}],
        ),
    ],
)

BranchesT = TypeAliasType(
    "BranchesT",
    Annotated[
        list[str],
        ListofStringCanonicalizer(),
        Field(
            description="Which branches will include this step in their builds",
            examples=["master", ["feature/*", "chore/*"]],
        ),
    ],
)

LabelT = TypeAliasType(
    "LabelT",
    Annotated[
        str,
        Field(
            description="The label that will be displayed in the pipeline visualisation in Buildkite. Supports emoji.",
            examples=[":docker: Build"],
        ),
    ],
)

PromptT = TypeAliasType(
    "PromptT",
    Annotated[
        str,
        Field(
            description="The instructional message displayed in the dialog box when the unblock step is activated",
            examples=["Release to production?"],
        ),
    ],
)


SkipT = TypeAliasType(
    "SkipT",
    Annotated[
        # NB: Passing an empty string is equivalent to false.
        bool | str,
        Field(
            description="Whether this step should be skipped. Passing a string provides a reason for skipping this command",
            examples=[True, False, "My reason"],
        ),
    ],
)

# NB: Most Buildkite booleans also support the strings "true" and "false"
LooseBoolT = Annotated[bool, LooseBoolValidator()]


class SoftFailConditions(BaseModel, extra="allow"):
    exit_status: Literal["*"] | int | None = Field(
        default=None,
        description="The exit status number that will cause this job to soft-fail",
    )


# @TODO: Canonicalize
#   (IDK if we should flatten '*' exit statuses or convert 'true' to '*')
SoftFailT = TypeAliasType(
    "SoftFailT",
    Annotated[
        LooseBoolT | list[SoftFailConditions],
        Field(description="The conditions for marking the step as a soft-fail."),
    ],
)
