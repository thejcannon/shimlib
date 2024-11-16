from textwrap import dedent
from dataclasses import dataclass
from pathlib import Path
import os
from typing import Any
from unittest.mock import call, _Call

import pytest

from shimbboleth.buildkite.agent import (
    BuildkiteAgent,
    AsyncioBuildkiteAgent,
    TrioBuildkiteAgent,
)


@dataclass
class FakeBKAgent:
    path: Path
    argsfile: Path
    stdoutfile: Path
    stderrfile: Path
    returncodefile: Path

    def __init__(self, path: Path):
        self.path = path.absolute()
        self.argsfile = self.path / "args"
        self.stdoutfile = self.path / "stdout"
        self.stderrfile = self.path / "stderr"
        self.returncodefile = self.path / "returncode"
        self.__post_init__()

    def __post_init__(self):
        self.path.mkdir()
        agent_path = self.path / "buildkite-agent"
        agent_path.write_text(
            dedent(f"""\
                #!/bin/bash

                cat "{self.stdoutfile}" 2>/dev/null || true
                if [ -f "{self.stderrfile}" ]; then
                    cat "{self.stderrfile}" >&2
                fi

                for arg in "$@"; do
                    echo "$arg" >> "{self.argsfile}"
                done

                exit $(cat "{self.returncodefile}" 2>/dev/null || echo 0)
            """).strip()
        )
        agent_path.chmod(0o755)

    @property
    def args(self) -> list[str]:
        return self.argsfile.read_text().splitlines()

    @property
    def stdout(self):
        return self.stdoutfile.read_text()

    @stdout.setter
    def stdout(self, value: str) -> None:
        self.stdoutfile.write_text(value)

    @property
    def stderr(self):
        return self.stderrfile.read_text()

    @stderr.setter
    def stderr(self, value: str) -> None:
        self.stderrfile.write_text(value)

    @property
    def returncode(self):
        return int(self.returncodefile.read_text())

    @returncode.setter
    def returncode(self, value: int) -> None:
        self.returncodefile.write_text(str(value))


@pytest.fixture
def fake_agent(tmp_path: Path, monkeypatch) -> FakeBKAgent:
    ret = FakeBKAgent(tmp_path / "fake-agent")
    monkeypatch.setenv("PATH", f"{ret.path}:{os.environ.get('PATH', '')}")
    return ret


@dataclass
class ClientAgent:
    obj: Any

    def __getattr__(self, attr):
        async def wrapped(*args, **kwargs):
            result = getattr(self.obj, attr)(*args, **kwargs)
            if hasattr(result, "__await__"):
                return await result
            return result

        return wrapped


@pytest.fixture(
    params=[
        pytest.param(BuildkiteAgent, marks=pytest.mark.asyncio),
        pytest.param(TrioBuildkiteAgent, marks=pytest.mark.trio),
        pytest.param(AsyncioBuildkiteAgent, marks=pytest.mark.asyncio),
    ]
)
def client_agent(request) -> ClientAgent:
    return ClientAgent(request.param())


@pytest.mark.parametrize(
    ["methodname", "argspec", "expected"],
    [
        ("annotate", call("body"), ["annotate", "body"]),
        (
            "annotate",
            call("body with space"),
            ["annotate", "body with space"],
        ),
        (
            "annotate",
            call("body", context="foo"),
            ["annotate", "body", "--context", "foo"],
        ),
        (
            "annotate",
            call("body", style="foo"),
            ["annotate", "body", "--style", "foo"],
        ),
        (
            "annotate",
            call("body", append=True),
            ["annotate", "body", "--append"],
        ),
        (
            "annotate",
            call("body", append=False),
            ["annotate", "body"],
        ),
        (
            "annotate",
            call("body", priority=1),
            ["annotate", "body", "--priority", "1"],
        ),
        (
            "upload_artifact",
            call("path"),
            ["artifact", "upload", "path"],
        ),
        ("download_artifact", call(), ["artifact", "download"]),
        (
            "download_artifact",
            call("query"),
            ["artifact", "download", "query"],
        ),
        (
            "download_artifact",
            call("query", "dest"),
            ["artifact", "download", "query", "dest"],
        ),
        (
            "download_artifact",
            call("query", "dest", step="step"),
            ["artifact", "download", "query", "dest", "--step", "step"],
        ),
        (
            "get_meta_data",
            call("key"),
            ["meta-data", "get", "key"],
        ),
        (
            "set_meta_data",
            call("key", "value"),
            ["meta-data", "set", "key", "value"],
        ),
        (
            "meta_data_exists",
            call("key"),
            ["meta-data", "exists", "key"],
        ),
        ("meta_data_keys", call(), ["meta-data", "keys"]),
        ("upload_pipeline", call(), ["pipeline", "upload"]),
        (
            "upload_pipeline",
            call("path.yml"),
            ["pipeline", "upload", "path.yml"],
        ),
        (
            "upload_pipeline",
            call(replace=True),
            ["pipeline", "upload", "--replace"],
        ),
        (
            "upload_pipeline",
            call(dry_run=True),
            ["pipeline", "upload", "--dry-run"],
        ),
        (
            "upload_pipeline",
            call("path.yml", replace=True, dry_run=True),
            ["pipeline", "upload", "path.yml", "--replace", "--dry-run"],
        ),
    ],
    ids=lambda val: "",
)
async def test_arg_passthrough(
    methodname: str,
    argspec: _Call,
    expected: list[str],
    fake_agent: FakeBKAgent,
    client_agent: ClientAgent,
    capfd: pytest.CaptureFixture,
):
    fake_agent.stderr = "Stood Error"
    fake_agent.stdout = "Stood Out"
    await getattr(client_agent, methodname)(*argspec.args, **argspec.kwargs)
    assert fake_agent.args == expected

    # Also test our usage of stdout/stderr
    stdout, stderr = capfd.readouterr()
    assert stdout == ""
    assert stderr == "Stood Error"


async def test_get_meta_data(fake_agent: FakeBKAgent, client_agent: ClientAgent):
    fake_agent.stdout = "value"
    assert await client_agent.get_meta_data("key") == "value"


async def test_meta_data_exists(fake_agent: FakeBKAgent, client_agent: ClientAgent):
    assert BuildkiteAgent().meta_data_exists("key")
    fake_agent.returncode = 100
    assert not (await client_agent.meta_data_exists("key"))

    fake_agent.returncode = 1
    with pytest.raises(BuildkiteAgent.CalledProcessError, match=r"exit status 1"):
        await client_agent.meta_data_exists("key")


async def test_meta_data_keys(fake_agent: FakeBKAgent, client_agent: ClientAgent):
    fake_agent.stdout = "key1\nkey2\n"
    assert BuildkiteAgent().meta_data_keys() == ["key1", "key2"]
