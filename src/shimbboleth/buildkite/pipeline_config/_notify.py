from typing import Literal
from typing_extensions import TypeAliasType


from shimbboleth._model import Model, field
from ._types import IfT


class GitHubCommitStatusInfo(Model, extra=False):
    context: str | None = None


class _NotifyBase(Model, extra=False):
    if_condition: IfT | None = field(default=None, json_alias="if")


class GitHubCommitStatusNotify(_NotifyBase):
    github_commit_status: GitHubCommitStatusInfo | None = None


class GitHubCheckNotify(Model, extra=False):
    # @TODO: See https://github.com/buildkite/pipeline-schema/pull/117#issuecomment-2537680177
    github_check: dict[str, str]


class EmailNotify(_NotifyBase):
    email: str | None = None


class BasecampCampfireNotify(_NotifyBase):
    basecamp_campfire: str | None = None


class SlackNotifyInfo(Model, extra=False):
    channels: list[str] | None = None
    message: str | None = None


class SlackNotify(_NotifyBase):
    slack: str | SlackNotifyInfo | None = None


class WebhookNotify(_NotifyBase):
    webhook: str | None = None


class PagerdutyNotify(_NotifyBase):
    pagerduty_change_event: str | None = None


BuildNotifyT = TypeAliasType(
    "BuildNotifyT",
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
)
