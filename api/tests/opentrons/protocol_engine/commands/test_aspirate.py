"""Test aspirate commands."""
from datetime import datetime

from opentrons_shared_data.errors.exceptions import PipetteOverpressureError
from decoy import matchers, Decoy
import pytest

from opentrons.protocol_engine.commands.pipetting_common import (
    OverpressureError,
    OverpressureErrorInternalData,
)
from opentrons.types import MountType, Point
from opentrons.protocol_engine import WellLocation, WellOrigin, WellOffset, DeckPoint

from opentrons.protocol_engine.commands.aspirate import (
    AspirateParams,
    AspirateResult,
    AspirateImplementation,
)
from opentrons.protocol_engine.commands.command import DefinedErrorData, SuccessData

from opentrons.protocol_engine.state import StateView

from opentrons.protocol_engine.execution import (
    MovementHandler,
    PipettingHandler,
)
from opentrons.protocol_engine.resources.model_utils import ModelUtils
from opentrons.protocol_engine.types import CurrentWell, LoadedPipette
from opentrons.hardware_control import HardwareControlAPI
from opentrons.protocol_engine.notes import CommandNoteAdder


@pytest.fixture
def subject(
    state_view: StateView,
    hardware_api: HardwareControlAPI,
    movement: MovementHandler,
    pipetting: PipettingHandler,
    mock_command_note_adder: CommandNoteAdder,
    model_utils: ModelUtils,
) -> AspirateImplementation:
    """Get the implementation subject."""
    return AspirateImplementation(
        pipetting=pipetting,
        state_view=state_view,
        movement=movement,
        hardware_api=hardware_api,
        command_note_adder=mock_command_note_adder,
        model_utils=model_utils,
    )


async def test_aspirate_implementation_no_prep(
    decoy: Decoy,
    state_view: StateView,
    hardware_api: HardwareControlAPI,
    movement: MovementHandler,
    pipetting: PipettingHandler,
    subject: AspirateImplementation,
    mock_command_note_adder: CommandNoteAdder,
) -> None:
    """An Aspirate should have an execution implementation without preparing to aspirate."""
    location = WellLocation(origin=WellOrigin.BOTTOM, offset=WellOffset(x=0, y=0, z=1))

    data = AspirateParams(
        pipetteId="abc",
        labwareId="123",
        wellName="A3",
        wellLocation=location,
        volume=50,
        flowRate=1.23,
    )

    decoy.when(pipetting.get_is_ready_to_aspirate(pipette_id="abc")).then_return(True)

    decoy.when(
        await movement.move_to_well(
            pipette_id="abc",
            labware_id="123",
            well_name="A3",
            well_location=location,
            current_well=None,
        ),
    ).then_return(Point(x=1, y=2, z=3))

    decoy.when(
        await pipetting.aspirate_in_place(
            pipette_id="abc",
            volume=50,
            flow_rate=1.23,
            command_note_adder=mock_command_note_adder,
        ),
    ).then_return(50)

    result = await subject.execute(data)

    assert result == SuccessData(
        public=AspirateResult(volume=50, position=DeckPoint(x=1, y=2, z=3)),
        private=None,
    )


async def test_aspirate_implementation_with_prep(
    decoy: Decoy,
    state_view: StateView,
    hardware_api: HardwareControlAPI,
    movement: MovementHandler,
    pipetting: PipettingHandler,
    mock_command_note_adder: CommandNoteAdder,
    subject: AspirateImplementation,
) -> None:
    """An Aspirate should have an execution implementation with preparing to aspirate."""
    location = WellLocation(origin=WellOrigin.BOTTOM, offset=WellOffset(x=0, y=0, z=1))

    data = AspirateParams(
        pipetteId="abc",
        labwareId="123",
        wellName="A3",
        wellLocation=location,
        volume=50,
        flowRate=1.23,
    )

    decoy.when(pipetting.get_is_ready_to_aspirate(pipette_id="abc")).then_return(False)

    decoy.when(state_view.pipettes.get(pipette_id="abc")).then_return(
        LoadedPipette.construct(  # type:ignore[call-arg]
            mount=MountType.LEFT
        )
    )
    decoy.when(
        await movement.move_to_well(
            pipette_id="abc",
            labware_id="123",
            well_name="A3",
            well_location=location,
            current_well=CurrentWell(
                pipette_id="abc",
                labware_id="123",
                well_name="A3",
            ),
        ),
    ).then_return(Point(x=1, y=2, z=3))

    decoy.when(
        await pipetting.aspirate_in_place(
            pipette_id="abc",
            volume=50,
            flow_rate=1.23,
            command_note_adder=mock_command_note_adder,
        ),
    ).then_return(50)

    result = await subject.execute(data)

    assert result == SuccessData(
        public=AspirateResult(volume=50, position=DeckPoint(x=1, y=2, z=3)),
        private=None,
    )

    decoy.verify(
        await movement.move_to_well(
            pipette_id="abc",
            labware_id="123",
            well_name="A3",
            well_location=WellLocation(origin=WellOrigin.TOP),
        ),
        await pipetting.prepare_for_aspirate(pipette_id="abc"),
    )


async def test_aspirate_raises_volume_error(
    decoy: Decoy,
    pipetting: PipettingHandler,
    mock_command_note_adder: CommandNoteAdder,
    subject: AspirateImplementation,
) -> None:
    """Should raise an assertion error for volume larger than working volume."""
    location = WellLocation(origin=WellOrigin.BOTTOM, offset=WellOffset(x=0, y=0, z=1))

    data = AspirateParams(
        pipetteId="abc",
        labwareId="123",
        wellName="A3",
        wellLocation=location,
        volume=50,
        flowRate=1.23,
    )

    decoy.when(pipetting.get_is_ready_to_aspirate(pipette_id="abc")).then_return(True)

    decoy.when(
        await pipetting.aspirate_in_place(
            pipette_id="abc",
            volume=50,
            flow_rate=1.23,
            command_note_adder=mock_command_note_adder,
        )
    ).then_raise(AssertionError("blah blah"))

    with pytest.raises(AssertionError):
        await subject.execute(data)


async def test_overpressure_error(
    decoy: Decoy,
    movement: MovementHandler,
    pipetting: PipettingHandler,
    subject: AspirateImplementation,
    model_utils: ModelUtils,
    mock_command_note_adder: CommandNoteAdder,
) -> None:
    """It should return an overpressure error if the hardware API indicates that."""
    pipette_id = "pipette-id"
    labware_id = "labware-id"
    well_name = "well-name"
    well_location = WellLocation(
        origin=WellOrigin.BOTTOM, offset=WellOffset(x=0, y=0, z=1)
    )

    position = Point(x=1, y=2, z=3)

    error_id = "error-id"
    error_timestamp = datetime(year=2020, month=1, day=2)

    data = AspirateParams(
        pipetteId=pipette_id,
        labwareId=labware_id,
        wellName=well_name,
        wellLocation=well_location,
        volume=50,
        flowRate=1.23,
    )

    decoy.when(pipetting.get_is_ready_to_aspirate(pipette_id=pipette_id)).then_return(
        True
    )

    decoy.when(
        await movement.move_to_well(
            pipette_id=pipette_id,
            labware_id=labware_id,
            well_name=well_name,
            well_location=well_location,
            current_well=None,
        ),
    ).then_return(position)

    decoy.when(
        await pipetting.aspirate_in_place(
            pipette_id=pipette_id,
            volume=50,
            flow_rate=1.23,
            command_note_adder=mock_command_note_adder,
        ),
    ).then_raise(PipetteOverpressureError())

    decoy.when(model_utils.generate_id()).then_return(error_id)
    decoy.when(model_utils.get_timestamp()).then_return(error_timestamp)

    result = await subject.execute(data)

    assert result == DefinedErrorData(
        public=OverpressureError.construct(
            id=error_id, createdAt=error_timestamp, wrappedErrors=[matchers.Anything()]
        ),
        private=OverpressureErrorInternalData(
            position=DeckPoint(x=position.x, y=position.y, z=position.z)
        ),
    )
