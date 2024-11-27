from typing import Literal, Annotated
from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field

from ._types import IfT


class HasContext(BaseModel):
    context: str | None = Field(default=None, description="GitHub commit status name")


class GitHubCommitStatusNotify(BaseModel, extra="forbid"):
    github_commit_status: HasContext | None = None
    if_condition: IfT | None = Field(default=None, alias="if")


class GitHubCheckNotify(BaseModel, extra="forbid"):
    github_check: HasContext | None = None
    if_condition: IfT | None = Field(default=None, alias="if")


class EmailNotify(BaseModel, extra="forbid"):
    email: str | None = None
    if_condition: IfT | None = Field(default=None, alias="if")


class BasecampCampfireNotify(BaseModel, extra="forbid"):
    basecamp_campfire: str | None = None
    if_condition: IfT | None = Field(default=None, alias="if")


class SlackChannelsNotify(BaseModel):
    channels: list[str] | None = None
    message: str | None = None


class SlackNotify(BaseModel, extra="forbid"):
    slack: str | SlackChannelsNotify | None = None
    if_condition: IfT | None = Field(default=None, alias="if")


class WebhookNotify(BaseModel, extra="forbid"):
    webhook: str | None = None
    if_condition: IfT | None = Field(default=None, alias="if")


class PagerdutyNotify(BaseModel, extra="forbid"):
    pagerduty_change_event: str | None = None
    if_condition: IfT | None = Field(default=None, alias="if")


GitHubNotify = (
    GitHubCommitStatusNotify
    | GitHubCheckNotify
    | Literal["github_check", "github_commit_status"]
)
BuildNotifyT = TypeAliasType(
    "BuildNotifyT",
    Annotated[
        list[
            Literal["github_check", "github_commit_status"]
            | EmailNotify
            | BasecampCampfireNotify
            | SlackNotify
            | WebhookNotify
            | PagerdutyNotify
            | GitHubCommitStatusNotify
            | GitHubCheckNotify
        ],
        Field(default=None, description="Array of notification options for this step"),
    ],
)

CommandNotifyT = TypeAliasType(
    "CommandNotifyT",
    Annotated[
        list[
            Literal["github_check", "github_commit_status"]
            | BasecampCampfireNotify
            | SlackNotify
            | GitHubCommitStatusNotify
            | GitHubCheckNotify
        ],
        Field(default=None, description="Array of notification options for this step"),
    ],
)
