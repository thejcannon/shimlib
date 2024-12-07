from typing import Literal, Annotated
from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field

from ._types import IfT


class _EmptyModel(BaseModel, extra="forbid"):
    pass

class HasContext(BaseModel):
    context: str | None = Field(default=None, description="GitHub commit status name")


class _NotifyBase(BaseModel, extra="forbid"):
    if_condition: IfT | None = Field(default=None, alias="if")

class GitHubCommitStatusNotify(_NotifyBase):
    github_commit_status: HasContext | None = None


class GitHubCheckNotify(BaseModel, extra="forbid"):
    github_check: _EmptyModel | None = None


class EmailNotify(_NotifyBase):
    email: str | None = None


class BasecampCampfireNotify(_NotifyBase):
    basecamp_campfire: str | None = None


class SlackChannels(BaseModel):
    channels: list[str] | None = None
    message: str | None = None


class SlackNotify(_NotifyBase):
    slack: str | SlackChannels | None = None


class WebhookNotify(_NotifyBase):
    webhook: str | None = None


class PagerdutyNotify(_NotifyBase):
    pagerduty_change_event: str | None = None


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
