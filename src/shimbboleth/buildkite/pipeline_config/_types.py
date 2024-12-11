from typing_extensions import TypeAliasType
from typing import Literal, Any, Annotated
from pydantic import Field, BaseModel
from ._canonicalize import Canonicalizer, ListofStringCanonicalizer
from shimbboleth._dogmantic.field import Description, Examples

IfT = TypeAliasType(
    "IfT",
    Annotated[
        str,
        Description("A boolean expression that omits the step when false"),
        Examples("build.message != 'skip me'", "build.branch == 'master'"),
    ],
)

# @TODO: RHS shouldn't be `Any`, but it kinda is upstream
# But there's a twist!
#   `env` at the pipeline level enforces RHS `str | int | bool` (with bools coerced to `true` ro `False`)
#   `env` at the command level just silently ignores non-int/str/bool
# (what gives?!)
# @TODO: Coerce RHS from strings? E.g. `"1"` -> `1` and `"true"` -> `True`
EnvT = TypeAliasType(
    "EnvT",
    Annotated[
        dict[str, Any],
        Description("Environment variables for this step"),
        Examples({"NODE_ENV": "test"}),
    ],
)

BranchesT = TypeAliasType(
    "BranchesT",
    Annotated[
        list[str],
        ListofStringCanonicalizer(),
        Description("Which branches will include this step in their builds"),
        Examples("master", ["feature/*", "chore/*"]),
    ],
)

LabelT = TypeAliasType(
    "LabelT",
    Annotated[
        str,
        Description("The label that will be displayed in the pipeline visualisation in Buildkite. Supports emoji."),
        Examples(":docker: Build"),
    ],
)

PromptT = TypeAliasType(
    "PromptT",
    Annotated[
        str,
        Description("The instructional message displayed in the dialog box when the unblock step is activated"),
        Examples("Release to production?"),
    ],
)


SkipT = TypeAliasType(
    "SkipT",
    Annotated[
        # NB: Passing an empty string is equivalent to false.
        bool | str,
        Description("Whether this step should be skipped. Passing a string provides a reason for skipping this command"),
        Examples(True, False, "My reason"),
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
# @TODO: Provide helper method for this
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
        Description("The conditions for marking the step as a soft-fail."),
    ],
)
