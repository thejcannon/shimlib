"""
Shims around the `buildkite-agent` CLI.

https://buildkite.com/docs/agent/v3/cli-reference

Each command is mapped to the corresponding buildkite-agent CLI command and handles
argument formatting and execution.
"""

import functools
from dataclasses import dataclass
import itertools
from typing import (
    Callable,
    ParamSpec,
    TypeVar,
    overload,
    Coroutine,
    Iterable,
    Any,
    Container,
)
import subprocess


def _make_flags(kwargs: dict[str, Any]) -> Iterable[str]:
    return itertools.chain.from_iterable(
        [
            f"--{k.replace('_', '-')}",
            *([str(v)] if not isinstance(v, bool) else []),
        ]
        for k, v in kwargs.items()
        if v is not None and v is not False
    )


P = ParamSpec("P")
T = TypeVar("T")


@overload
def _command(
    *names: str, allowed_exit_codes: Container[int] = (0,), post: None = None
) -> Callable[[Callable[P, None]], Callable[P, None]]: ...


@overload
def _command(
    *names: str,
    allowed_exit_codes: Container[int] = (0,),
    post: Callable[[subprocess.CompletedProcess], T],
) -> Callable[[Callable[P, T]], Callable[P, T]]: ...
def _command(
    *names: str,
    allowed_exit_codes: Container[int] = (0,),
    post: Callable[[subprocess.CompletedProcess], T] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            nonlocal names

            bkagent: "_BuildkiteAgentBase" = args[0]  # type: ignore
            result = subprocess.run(
                [
                    bkagent.agent_path,
                    *names,
                    *map(str, args[1:]),
                    *_make_flags(kwargs),
                ],
                check=False,
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
            )
            if result.returncode not in allowed_exit_codes:
                raise bkagent.CalledProcessError(
                    result.returncode, result.args, result.stdout, result.stderr
                )

            if post:
                return post(result)
            return None  # type: ignore

        return wrapper

    return decorator


@dataclass(frozen=True)
class _BuildkiteAgentBase:
    class CalledProcessError(subprocess.CalledProcessError):
        pass

    agent_path: str = "buildkite-agent"

    @_command("annotate")
    def _annotate(
        self,
        body: str,
        *,
        context: str | None = None,
        style: str | None = None,
        append: bool = False,
        priority: int | None = None,
    ) -> None:
        """
        Annotate the build page within the Buildkite UI with text from within a Buildkite job.

        :param context: The context of the annotation used to differentiate this annotation from others
        :param style: The style of the annotation ('success', 'info', 'warning' or 'error')
        :param append: Append to the body of an existing annotation
        :param priority: The priority of the annotation ('1' to '10').
            Annotations with a priority of '10' are shown first, while annotations with a priority of '1' are shown last.
        :param job: Which job should the annotation come from
        """
        raise AssertionError

    @_command("artifact", "upload")
    def _upload_artifact(self, path: str) -> None:
        """
        Uploads files to a job as artifacts.

        :param path: Path to file(s) to upload
        """
        raise AssertionError

    @_command("artifact", "download")
    def _download_artifact(
        self,
        query: str | None = None,
        destination: str | None = None,
        *,
        step: str | None = None,
        build: str | None = None,
        include_retried_jobs: bool = False,
    ) -> None:
        """
        Downloads artifacts from Buildkite to the local machine.

        :param query: Pattern of files to download
        :param destination: Destination path to download artifacts to
        :param step: Scope the search to a particular step. Can be the step's key or label, or a Job ID
        :param build: The build that the artifacts were uploaded to
        :param include_retried_jobs: Include artifacts from retried jobs in the search
        """
        raise AssertionError

    @_command("meta-data", "get", post=lambda result: result.stdout.strip())
    def _get_meta_data(self, key: str) -> str:
        """
        Get data from a build.

        :param key: Key to retrieve metadata for
        :return: Value stored for key
        """
        raise AssertionError

    @_command("meta-data", "set")
    def _set_meta_data(self, key: str, value: str) -> None:
        """
        Set data from a build.

        :param key: Key to set metadata for
        :param value: Value to store. The value must be a non-empty string,
            and strings containing only whitespace characters are not allowed.
        """
        raise AssertionError

    @_command(
        "meta-data",
        "exists",
        allowed_exit_codes=(0, 100),
        post=lambda result: result.returncode == 0,
    )
    def _meta_data_exists(self, key: str) -> bool:
        """
        Check to see if the meta data key exists for a build.

        :param key: Key to check metadata for
        :return: Whether the key has been set
        """
        raise AssertionError

    @_command(
        "meta-data", "keys", post=lambda result: result.stdout.strip().splitlines()
    )
    def _meta_data_keys(self) -> list[str]:
        """
        Lists all meta-data keys that have been previously set.
        """
        raise AssertionError

    @_command("pipeline", "upload")
    def _upload_pipeline(
        self,
        pipeline_path: str | None = None,
        *,
        replace: bool = False,
        dry_run: bool = False,
    ):
        """
        Uploads a description of a build pipeline adds it to the currently running build after the current job.

        :param pipeline_path: Path to pipeline yaml/json file. If not provided, reads from stdin
        :param replace: Replace existing pipeline with uploaded steps
        :param dry_run: Print pipeline instead of uploading
        """
        raise AssertionError


@dataclass(frozen=True)
class BuildkiteAgent(_BuildkiteAgentBase):
    @staticmethod
    def _make(func: "Callable[P, T]") -> "Callable[P, T]":
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return func(*args, **kwargs)

        return wrapper

    annotate = _make(_BuildkiteAgentBase._annotate)
    upload_artifact = _make(_BuildkiteAgentBase._upload_artifact)
    download_artifact = _make(_BuildkiteAgentBase._download_artifact)
    get_meta_data = _make(_BuildkiteAgentBase._get_meta_data)
    set_meta_data = _make(_BuildkiteAgentBase._set_meta_data)
    meta_data_exists = _make(_BuildkiteAgentBase._meta_data_exists)
    meta_data_keys = _make(_BuildkiteAgentBase._meta_data_keys)
    upload_pipeline = _make(_BuildkiteAgentBase._upload_pipeline)


@dataclass(frozen=True)
class AsyncioBuildkiteAgent(_BuildkiteAgentBase):
    @staticmethod
    def _make_async(func: Callable[P, T]) -> Callable[P, Coroutine[None, None, T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            import asyncio

            return await asyncio.to_thread(func, *args, **kwargs)

        return wrapper

    annotate = _make_async(_BuildkiteAgentBase._annotate)
    upload_artifact = _make_async(_BuildkiteAgentBase._upload_artifact)
    download_artifact = _make_async(_BuildkiteAgentBase._download_artifact)
    get_meta_data = _make_async(_BuildkiteAgentBase._get_meta_data)
    set_meta_data = _make_async(_BuildkiteAgentBase._set_meta_data)
    meta_data_exists = _make_async(_BuildkiteAgentBase._meta_data_exists)
    meta_data_keys = _make_async(_BuildkiteAgentBase._meta_data_keys)
    upload_pipeline = _make_async(_BuildkiteAgentBase._upload_pipeline)


@dataclass(frozen=True)
class TrioBuildkiteAgent(_BuildkiteAgentBase):
    @staticmethod
    def _make_async(func: Callable[P, T]) -> Callable[P, Coroutine[None, None, T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            import trio  # type: ignore

            return await trio.to_thread.run_sync(lambda: func(*args, **kwargs))

        return wrapper

    annotate = _make_async(_BuildkiteAgentBase._annotate)
    upload_artifact = _make_async(_BuildkiteAgentBase._upload_artifact)
    download_artifact = _make_async(_BuildkiteAgentBase._download_artifact)
    get_meta_data = _make_async(_BuildkiteAgentBase._get_meta_data)
    set_meta_data = _make_async(_BuildkiteAgentBase._set_meta_data)
    meta_data_exists = _make_async(_BuildkiteAgentBase._meta_data_exists)
    meta_data_keys = _make_async(_BuildkiteAgentBase._meta_data_keys)
    upload_pipeline = _make_async(_BuildkiteAgentBase._upload_pipeline)
