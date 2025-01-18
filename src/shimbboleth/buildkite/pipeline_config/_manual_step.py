from typing import Annotated
import re
from shimbboleth._model import MatchesRegex, field, Model, NonEmptyList
from shimbboleth._model.jsonT import JSONObject
from shimbboleth._model.validation import InvalidValueError
from ._types import bool_from_json
from ._types import list_str_from_json
from ._base import StepBase


class _OptionBaseModel(Model):
    key: Annotated[str, MatchesRegex("^[a-zA-Z0-9-_]+$")]
    """The meta-data key that stores the field's input"""

    hint: str | None = None
    """The explanatory text that is shown after the label"""

    required: bool = field(default=True, json_loader=bool_from_json)
    """Whether the field is required for form submission"""


class TextInput(_OptionBaseModel, extra=False):
    """
    For Input Step: https://buildkite.com/docs/pipelines/input-step#text-input-attributes
    For Block Step: https://buildkite.com/docs/pipelines/block-step#text-input-attributes
    """

    text: str
    """The text input name"""

    default: str | None = None
    """The value that is pre-filled in the text field"""

    format: re.Pattern | None = None
    """The format must be a regular expression implicitly anchored to the beginning and end of the input and is functionally equivalent to the HTML5 pattern attribute."""


class SelectOption(Model, extra=False):
    label: str
    """The text displayed on the select list item"""

    value: str
    """The value to be stored as meta-data"""

    hint: str | None = None
    """The text displayed directly under the select field's label"""

    required: bool = field(default=True, json_loader=bool_from_json)
    """Whether the field is required for form submission"""


class SelectInput(_OptionBaseModel, extra=False):
    """
    For Input Step: https://buildkite.com/docs/pipelines/input-step#select-input-attributes
    For Block Step: https://buildkite.com/docs/pipelines/block-step#select-input-attributes
    """

    select: str
    """The select input name"""

    options: NonEmptyList[SelectOption]
    """The list of select field options."""

    # @TODO: (upstream) strangely this doesn't validate if its a valid option
    default: str | list[str] | None = None
    """The value(s) of the option(s) that will be pre-selected in the dropdown"""

    multiple: bool = field(default=False, json_loader=bool_from_json)
    """Whether more than one option may be selected"""

    def __post_init__(self):
        if not self.multiple and isinstance(self.default, list):
            raise InvalidValueError(
                "`default` cannot be a list when `multiple` is `False`"
            )


class ManualStepBase(StepBase, extra=False):
    """
    (The base of both Input and Block steps)
    """

    branches: list[str] = field(default_factory=list, json_loader=list_str_from_json)
    """Which branches will include this step in their builds"""

    fields: list[TextInput | SelectInput] = field(default_factory=list)
    """A list of input fields required to be filled out before unblocking the step"""

    prompt: str | None = None
    """The instructional message displayed in the dialog box when the unblock step is activated"""


@ManualStepBase._json_loader_("fields")
def _load_fields(value: list[JSONObject]) -> list[TextInput | SelectInput]:
    ret = []
    for index, field_dict in enumerate(value):
        with InvalidValueError.context(prefix=f"[{index}]"):
            if "text" in field_dict:
                ret.append(TextInput.model_load(field_dict))
            elif "select" in field_dict:
                ret.append(SelectInput.model_load(field_dict))
            else:
                raise InvalidValueError("Input fields must contain `text`` or `select`")
    return ret
