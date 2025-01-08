from typing import Literal, Annotated, TypeAlias


from shimbboleth._model import Model, field, NonEmpty


class GitHubCommitStatusInfo(Model, extra=False):
    # somehow not required?
    context: str | None = None


class _NotifyBase(Model, extra=False):
    # @TEST: Is an empty string considered a skip?
    if_condition: str | None = field(default=None, json_alias="if")


class GitHubCommitStatusNotify(_NotifyBase):
    github_commit_status: GitHubCommitStatusInfo


class GitHubCheckNotify(Model, extra=False):
    # @TODO: See https://github.com/buildkite/pipeline-schema/pull/117#issuecomment-2537680177
    github_check: dict[str, str]


class EmailNotify(_NotifyBase):
    email: str


class BasecampCampfireNotify(_NotifyBase):
    basecamp_campfire: str


class SlackNotifyInfo(Model, extra=False):
    channels: Annotated[list[str], NonEmpty] = field()
    message: str | None = None


class SlackNotify(_NotifyBase):
    # The `slack` notification is invalid: Each channel should be defined as `#channel-name`, `team-name#channel-name`, 'team-name@user-name', '@user-name', 'U12345678', 'W12345678', or 'S12345678'
    slack: str | SlackNotifyInfo

    # @TODO: JSON conversion to SlackNotifyInfo with str -> channels: [string]


class WebhookNotify(_NotifyBase):
    webhook: str


class PagerdutyNotify(_NotifyBase):
    pagerduty_change_event: str


BuildNotifyT: TypeAlias = list[
    Literal["github_check", "github_commit_status"]
    | EmailNotify
    | BasecampCampfireNotify
    | SlackNotify
    | WebhookNotify
    | PagerdutyNotify
    | GitHubCommitStatusNotify
    | GitHubCheckNotify
]

StepNotifyT: TypeAlias = list[
    Literal["github_check", "github_commit_status"]
    | BasecampCampfireNotify
    | SlackNotify
    | GitHubCommitStatusNotify
    | GitHubCheckNotify
]
