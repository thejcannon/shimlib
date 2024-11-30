from typing import Literal, Annotated, Pattern
from typing_extensions import TypeAliasType


from pydantic import BaseModel, Field


class TextInput(BaseModel, extra="forbid"):
    """
    For Input Step: https://buildkite.com/docs/pipelines/input-step#text-input-attributes
    For Block Step: https://buildkite.com/docs/pipelines/block-step#text-input-attributes
    """

    key: str = Field(
        description="The meta-data key that stores the field's input",
        pattern="^[a-zA-Z0-9-_]+$",
        examples=["release-name"],
    )

    hint: str | None = Field(
        default=None,
        description="The explanatory text that is shown after the label",
        examples=["What's the code name for this release? :name_badge:"],
    )
    required: bool = Field(
        default=True, description="Whether the field is required for form submission"
    )
    default: str | None = Field(
        default=None,
        description="The value that is pre-filled in the text field",
        examples=["Flying Dolphin"],
    )
    format: Pattern | None = Field(
        default=None,
        description="The format must be a regular expression implicitly anchored to the beginning and end of the input and is functionally equivalent to the HTML5 pattern attribute.",  # TODO: Only one with period?
        examples=["[0-9a-f]+"],
    )
    text: str | None = Field(
        default=None, description="The text input name", examples=["Release Name"]
    )


class SelectOption(BaseModel, extra="forbid"):
    label: str = Field(
        description="The text displayed on the select list item", examples=["Stable"]
    )
    value: str = Field(
        description="The value to be stored as meta-data", examples=["stable"]
    )

    hint: str | None = Field(
        default=None,
        description="The text displayed directly under the select field's label",
        examples=["Which release stream does this belong in? :fork:"],
    )
    required: bool = Field(
        default=True, description="Whether the field is required for form submission"
    )


class SelectInput(BaseModel, extra="forbid"):
    """
    For Input Step: https://buildkite.com/docs/pipelines/input-step#select-input-attributes
    For Block Step: https://buildkite.com/docs/pipelines/block-step#select-input-attributes
    """

    key: str = Field(
        description="The meta-data key that stores the field's input",
        pattern="^[a-zA-Z0-9-_]+$",
        examples=["release-stream"],
    )
    options: list[SelectOption]

    default: str | list[str] | None = Field(
        default=None,
        description="The value of the option(s) that will be pre-selected in the dropdown",
        examples=["beta", ["alpha", "beta"]],
    )
    hint: str | None = Field(
        default=None,
        description="The explanatory text that is shown after the label",
        examples=["What's the code name for this release? :name_badge:"],
    )
    multiple: bool = Field(
        default=False, description="Whether more than one option may be selected"
    )
    required: bool = Field(
        default=True, description="Whether the field is required for form submission"
    )
    select: str | None = Field(
        default=None, description="The text input name", examples=["Release Stream"]
    )


FieldsT = TypeAliasType(
    "FieldsT",
    Annotated[
        list[TextInput | SelectInput],
        Field(
            description="A list of input fields required to be filled out before unblocking the step"
        ),
    ],
)


class SoftFailByStatus(BaseModel):
    exit_status: Literal["*"] | int | None = Field(
        default=None,
        description="The exit status number that will cause this job to soft-fail",
    )


SoftFailT = TypeAliasType(
    "SoftFailT",
    Annotated[
        bool | list[SoftFailByStatus],
        Field(description="The conditions for marking the step as a soft-fail."),
    ],
)
