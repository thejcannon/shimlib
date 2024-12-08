from typing_extensions import TypeAliasType
from typing import Literal
from pydantic import Field, BaseModel

from typing import Any, Annotated
from ._canonicalize import Canonicalizer, ListofStringCanonicalizer


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


class _LooseBoolCanonicalizer(
    Canonicalizer[Literal[True, False, "true", "false"], bool]
):
    @classmethod
    def canonicalize(
        cls,
        value: Literal[True, False, "true", "false"],
    ) -> bool:
        return True if value == "true" else False if value == "false" else value


# NB: Most Buildkite booleans also support the strings "true" and "false"
LooseBoolT = Annotated[bool, _LooseBoolCanonicalizer()]


class ExitStatus(BaseModel, extra="allow"):
    exit_status: Literal["*"] | int | None = Field(
        default=None,
        description="The exit status number that will cause this job to soft-fail",
    )


# NB: This may seem annoying (having to do `any(status == '*' for soft_fail in model.soft_fail)`)
#   however consider if we allowed `bool`. `if model.soft_fail` would be ambiguous (because a non-empty list is truthy)
# @TODO: Propvide helper method for this
class _SoftFailCanonicalizer(
    Canonicalizer[LooseBoolT | list[ExitStatus] | None, list[ExitStatus]]
):
    @classmethod
    def canonicalize(
        cls, value: LooseBoolT | list[ExitStatus] | None
    ) -> list[ExitStatus]:
        # @TODO: Does `_LooseBoolCanonicalizer` already fire?
        if value == "true" or value is True:
            return [ExitStatus(exit_status="*")]
        if value is None or value == "false" or value is False:
            return []
        return value


SoftFailT = TypeAliasType(
    "SoftFailT",
    Annotated[
        list[ExitStatus] | None,
        _SoftFailCanonicalizer(),
        Field(description="The conditions for marking the step as a soft-fail."),
    ],
)
