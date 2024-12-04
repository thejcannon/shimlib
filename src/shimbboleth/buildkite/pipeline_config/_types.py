from typing_extensions import TypeAliasType
from pydantic import BeforeValidator, Field, WithJsonSchema

from typing import Any, Annotated


# @TODO: A lot of these are only used in one place

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
# @TODO: RHS Any?
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
        str | list[str],
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
        bool | str,
        Field(
            description="Whether this step should be skipped. You can specify a reason for using a string.",
            examples=[True, False, "My reason"],
        ),
    ],
)

# NB: Most Buildkite booleans also support the strings "true" and "false"
LooseBoolT = Annotated[
    bool,
    BeforeValidator(lambda v: True if v == "true" else False if v == "false" else v),
    WithJsonSchema({"enum": [True, False, "true", "false"]}),
]
