"""Test Heater Shaker await temperature command implementation."""
import pytest
from decoy import Decoy

from opentrons.protocol_engine import execution
from opentrons.protocol_engine.commands import heater_shaker
from opentrons.protocol_engine.commands.heater_shaker.await_temperature import (
    AwaitTemperatureImpl,
)


@pytest.fixture()
def subject(
    equipment: execution.EquipmentHandler,
    movement: execution.MovementHandler,
    pipetting: execution.PipettingHandler,
    run_control: execution.RunControlHandler,
) -> AwaitTemperatureImpl:
    """Get the command implementation with mocked out dependencies."""
    return AwaitTemperatureImpl(
        equipment=equipment,
        movement=movement,
        pipetting=pipetting,
        run_control=run_control,
    )


# TODO(mc, 2022-02-25): verify hardware interaction
@pytest.mark.xfail(raises=NotImplementedError, strict=True)
async def test_await_temperature(decoy: Decoy, subject: AwaitTemperatureImpl) -> None:
    """It should be able to wait for the module's target temperature."""
    data = heater_shaker.AwaitTemperatureParams(moduleId="heater-shaker-id")

    result = await subject.execute(data)

    assert result == heater_shaker.AwaitTemperatureResult()
