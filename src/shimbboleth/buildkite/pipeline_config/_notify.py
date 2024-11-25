from typing import Literal, Annotated
from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field

from ._types import IfT


class HasContext(BaseModel):
    context: str | None = Field(default=None, description="GitHub commit status name")
    if_condition: IfT | None = None


class GitHubCommitStatusNotify(BaseModel, extra="forbid"):
    github_commit_status: HasContext | None = None
    if_condition: IfT | None = None


class GitHubCheckNotify(BaseModel, extra="forbid"):
    github_check: HasContext | None = None
    if_condition: IfT | None = None


class EmailNotify(BaseModel, extra="forbid"):
    email: str | None = None
    if_condition: IfT | None = None


class BasecampCampfireNotify(BaseModel, extra="forbid"):
    basecamp_campfire: str | None = None
    if_condition: IfT | None = None


class SlackChannelsNotify(BaseModel, extra="forbid"):
    channels: list[str] | None = None
    message: str | None = None


class SlackNotify(BaseModel, extra="forbid"):
    slack: str | SlackChannelsNotify
    if_condition: IfT | None = None


class WebhookNotify(BaseModel, extra="forbid"):
    webhook: str | None = None
    if_condition: IfT | None = None


class PagerdutyNotify(BaseModel, extra="forbid"):
    pagerduty_change_event: str | None = None
    if_condition: IfT | None = None


GitHubNotify = (
    GitHubCommitStatusNotify
    | GitHubCheckNotify
    | Literal["github_check", "github_commit_status"]
)
BuildNotifyT = TypeAliasType(
    "BuildNotifyT",
    Annotated[
        list[
            GitHubNotify | EmailNotify | SlackNotify | WebhookNotify | PagerdutyNotify
        ],
        Field(default=None, description="Array of notification options for this step"),
    ],
)
