from typing import Literal, TypeAlias, Any
import dataclasses

from shimbboleth._model import Model, field, NonEmptyList
from shimbboleth._model.json_load import JSONLoadError


class GitHubCommitStatusInfo(Model, extra=False):
    context: str | None = None


class _NotifyBase(Model, extra=False):
    # @TEST: Is an empty string considered a skip?
    if_condition: str | None = field(default=None, json_alias="if")


class GitHubCommitStatusNotify(_NotifyBase):
    github_commit_status: GitHubCommitStatusInfo


class GitHubCheckNotify(Model, extra=False):
    # NB: See https://github.com/buildkite/pipeline-schema/pull/117#issuecomment-2537680177
    github_check: dict[str, str]


class EmailNotify(_NotifyBase):
    email: str


class BasecampCampfireNotify(_NotifyBase):
    basecamp_campfire: str


class SlackNotifyInfo(Model, extra=False):
    channels: NonEmptyList[str]
    message: str | None = None


# @TODO When loading `notify`, convert this to just `SlackNotifyInfo`
class SlackNotify(_NotifyBase):
    # @VALIDATE: The `slack` notification is invalid: Each channel should be defined as `#channel-name`, `team-name#channel-name`, 'team-name@user-name', '@user-name', 'U12345678', 'W12345678', or 'S12345678'
    slack: SlackNotifyInfo


@SlackNotify._json_loader_("slack")
def _load_slack(value: str | SlackNotifyInfo) -> SlackNotifyInfo:
    if isinstance(value, str):
        return SlackNotifyInfo(channels=[value], message=None)
    return value


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


# @TODO: Not return Any, but I'm lazy
def _parse_notification(value: Any) -> Any:
    if value in ("github_check", "github_commit_status"):
        return value
    elif isinstance(value, dict):
        keys = set(value.keys())
        keys.discard("if")
        if len(keys) == 1:
            key = keys.pop()
            notify_type = {
                "email": EmailNotify,
                "basecamp_campfire": BasecampCampfireNotify,
                "slack": SlackNotify,
                "webhook": WebhookNotify,
                "pagerduty_change_event": PagerdutyNotify,
                "github_commit_status": GitHubCommitStatusNotify,
                "github_check": GitHubCheckNotify,
            }.get(key, None)
            if notify_type is None:
                raise JSONLoadError(f"Unrecognizable notification: `{key}`")
            return notify_type.model_load(value)

    raise JSONLoadError(f"Unrecognizable notification: `{value}`")


def parse_build_notify(
    value: list[Any],
) -> BuildNotifyT:
    # NB: Every notification option has one required key
    #   and they don't overlap.
    ret = []
    for index, elem in enumerate(value):
        with JSONLoadError.context(index=index):
            ret.append(_parse_notification(elem))
    return ret


def parse_step_notify(
    value: list[Any],
) -> StepNotifyT:
    parsed = parse_build_notify(value)
    for index, elem in enumerate(parsed):
        if isinstance(elem, (EmailNotify, WebhookNotify, PagerdutyNotify)):
            keyname = dataclasses.fields(elem)[1].name
            # NB: It IS a valid _build_ notification though
            raise JSONLoadError(
                f"`{keyname}` is not a valid step notification", index=index
            )
    return parsed
