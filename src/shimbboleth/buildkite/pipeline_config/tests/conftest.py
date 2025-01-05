import pytest
from dataclasses import dataclass
from typing import TypeVar, Generic, Any

from shimbboleth.buildkite.pipeline_config import (
    BlockStep,
    InputStep,
    CommandStep,
    WaitStep,
    TriggerStep,
    GroupStep,
)
from shimbboleth._model import Model

T = TypeVar("T", bound=Model)


@dataclass(slots=True, frozen=True)
class StepTypeParam(Generic[T]):
    cls: type[T]
    ctor_defaults: dict[str, Any]

    @property
    def lowercase(self) -> str:
        return self.cls.__name__.lower().removesuffix("step")

    def ctor(self, **kwargs) -> T:
        return self.cls(**{**kwargs, **self.ctor_defaults})

    @property
    def dumped_default(self) -> dict[str, Any]:
        return self.ctor().model_dump()

STEP_TYPE_PARAMS = [
    StepTypeParam(BlockStep, {}),
    StepTypeParam(CommandStep, {}),
    StepTypeParam(InputStep, {}),
    StepTypeParam(WaitStep, {}),
    StepTypeParam(TriggerStep, {"trigger": "trigger"}),
    StepTypeParam(GroupStep, {"group": "group", "steps": [WaitStep()]}),
]

@pytest.fixture(params=[
    pytest.param(step_type_param, id=step_type_param.cls.__name__)
    for step_type_param in STEP_TYPE_PARAMS
])
def all_step_types(request) -> StepTypeParam:
    return request.param
