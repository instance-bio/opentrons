"""Protocol API module implementation logic."""
from __future__ import annotations

from typing import Optional, List

from opentrons.hardware_control import SynchronousAdapter, modules as hw_modules
from opentrons.hardware_control.modules.types import (
    ModuleModel,
    TemperatureStatus,
    MagneticStatus,
    ThermocyclerStep,
    SpeedStatus,
    module_model_from_string,
)
from opentrons.drivers.types import (
    HeaterShakerLabwareLatchStatus,
    ThermocyclerLidStatus,
)
from opentrons.types import DeckSlotName
from opentrons.protocol_engine.clients import SyncClient as ProtocolEngineClient
from opentrons.protocol_engine.errors.exceptions import (
    LabwareNotLoadedOnModuleError,
    NoMagnetEngageHeightError,
)

from opentrons.protocols.api_support.types import APIVersion

from ... import validation
from ..module import (
    AbstractModuleCore,
    AbstractTemperatureModuleCore,
    AbstractMagneticModuleCore,
    AbstractThermocyclerCore,
    AbstractHeaterShakerCore,
    AbstractMagneticBlockCore,
    AbstractAbsorbanceReaderCore,
)
from .exceptions import InvalidMagnetEngageHeightError


class ModuleCore(AbstractModuleCore):
    """Module core logic implementation for Python protocols.
    Args:
        module_id: ProtocolEngine ID of the loaded modules.
    """

    def __init__(
        self,
        module_id: str,
        engine_client: ProtocolEngineClient,
        api_version: APIVersion,
        sync_module_hardware: SynchronousAdapter[hw_modules.AbstractModule],
    ) -> None:
        self._module_id = module_id
        self._engine_client = engine_client
        self._api_version = api_version
        self._sync_module_hardware = sync_module_hardware

    @property
    def api_version(self) -> APIVersion:
        """Get the api version protocol module target."""
        return self._api_version

    @property
    def module_id(self) -> str:
        """The module's unique ProtocolEngine ID."""
        return self._module_id

    def get_model(self) -> ModuleModel:
        """Get the module's model identifier."""
        return module_model_from_string(
            self._engine_client.state.modules.get_connected_model(self.module_id)
        )

    def get_serial_number(self) -> str:
        """Get the module's unique hardware serial number."""
        return self._engine_client.state.modules.get_serial_number(self.module_id)

    def get_deck_slot(self) -> DeckSlotName:
        """Get the module's deck slot."""
        return self._engine_client.state.modules.get_location(self.module_id).slotName

    def get_deck_slot_id(self) -> str:
        slot_name = self.get_deck_slot()
        return validation.internal_slot_to_public_string(
            slot_name, robot_type=self._engine_client.state.config.robot_type
        )

    def get_display_name(self) -> str:
        """Get the module's display name."""
        return self._engine_client.state.modules.get_definition(
            self.module_id
        ).displayName


class NonConnectedModuleCore(AbstractModuleCore):
    """Not connected module core logic implementation for Python protocols.

    Args:
        module_id: ProtocolEngine ID of the loaded modules.
    """

    def __init__(
        self,
        module_id: str,
        engine_client: ProtocolEngineClient,
        api_version: APIVersion,
    ) -> None:
        self._module_id = module_id
        self._engine_client = engine_client
        self._api_version = api_version

    @property
    def api_version(self) -> APIVersion:
        """Get the api version protocol module target."""
        return self._api_version

    @property
    def module_id(self) -> str:
        """The module's unique ProtocolEngine ID."""
        return self._module_id

    def get_model(self) -> ModuleModel:
        """Get the module's model identifier."""
        return module_model_from_string(
            self._engine_client.state.modules.get_connected_model(self.module_id)
        )

    def get_deck_slot(self) -> DeckSlotName:
        """Get the module's deck slot."""
        return self._engine_client.state.modules.get_location(self.module_id).slotName

    def get_display_name(self) -> str:
        """Get the module's display name."""
        return self._engine_client.state.modules.get_definition(
            self.module_id
        ).displayName

    def get_deck_slot_id(self) -> str:
        slot_name = self.get_deck_slot()
        return validation.internal_slot_to_public_string(
            slot_name, robot_type=self._engine_client.state.config.robot_type
        )


class TemperatureModuleCore(ModuleCore, AbstractTemperatureModuleCore):
    """Temperature Module core logic implementation for Python protocols."""

    _sync_module_hardware: SynchronousAdapter[hw_modules.TempDeck]

    def set_target_temperature(self, celsius: float) -> None:
        """Set the Temperature Module's target temperature in °C."""
        self._engine_client.temperature_module_set_target_temperature(
            module_id=self.module_id, celsius=celsius
        )

    def wait_for_target_temperature(self, celsius: Optional[float] = None) -> None:
        """Wait until the module's target temperature is reached.
        Specifying a value for ``celsius`` that is different than
        the module's current target temperature may behave unpredictably.
        """
        self._engine_client.temperature_module_wait_for_target_temperature(
            module_id=self.module_id, celsius=celsius
        )

    def deactivate(self) -> None:
        """Deactivate the Temperature Module."""
        self._engine_client.temperature_module_deactivate(module_id=self.module_id)

    def get_current_temperature(self) -> float:
        """Get the module's current temperature in °C."""
        return self._sync_module_hardware.temperature  # type: ignore[no-any-return]

    def get_target_temperature(self) -> Optional[float]:
        """Get the module's target temperature in °C, if set."""
        return self._sync_module_hardware.target  # type: ignore[no-any-return]

    def get_status(self) -> TemperatureStatus:
        """Get the module's current temperature status."""
        return self._sync_module_hardware.status  # type: ignore[no-any-return]


class MagneticModuleCore(ModuleCore, AbstractMagneticModuleCore):
    """Magnetic Module control interface via a ProtocolEngine."""

    _sync_module_hardware: SynchronousAdapter[hw_modules.MagDeck]

    def engage(
        self,
        height_from_base: Optional[float] = None,
        height_from_home: Optional[float] = None,
    ) -> None:
        """Raise the module's magnets.
        Only one of `height_from_base` or `height_from_home` may be specified.
        Args:
            height_from_base: Distance from labware base to raise the magnets.
            height_from_home: Distance from motor home position to raise the magnets.
        """

        # This core will only be used in apiLevels >=2.14, where
        # MagneticModuleContext.engage(height=...) is no longer available.
        # So these asserts should always pass.
        assert (
            height_from_home is None
        ), "Expected engage height to be specified from base."
        assert (
            height_from_base is not None
        ), "Expected engage height to be specified from base."

        self._engine_client.magnetic_module_engage(
            module_id=self._module_id, engage_height=height_from_base
        )

    def engage_to_labware(
        self, offset: float = 0, preserve_half_mm: bool = False
    ) -> None:
        """Raise the module's magnets up to its loaded labware.
        Args:
            offset: Offset from the labware's default engage height.
            preserve_half_mm: For labware whose definitions
                erroneously use half-mm for their defined default engage height,
                use the value directly instead of converting it to real millimeters.
        """
        try:
            default_height = (
                self._engine_client.state.labware.get_default_magnet_height(
                    module_id=self.module_id, offset=offset
                )
            )
        except LabwareNotLoadedOnModuleError:
            raise InvalidMagnetEngageHeightError(
                "There is no labware loaded on this Magnetic Module,"
                " so you must specify an engage height"
                " with the `height_from_base` parameter."
            )
        except NoMagnetEngageHeightError:
            raise InvalidMagnetEngageHeightError(
                "The labware loaded on this Magnetic Module"
                " does not have a default engage height,"
                " so you must specify an engage height"
                " with the `height_from_base` parameter."
            )

        self._engine_client.magnetic_module_engage(
            module_id=self.module_id, engage_height=default_height
        )

    def disengage(self) -> None:
        """Lower the magnets back into the module."""
        self._engine_client.magnetic_module_disengage(module_id=self.module_id)

    def get_status(self) -> MagneticStatus:
        """Get the module's current magnet status."""
        return self._sync_module_hardware.status  # type: ignore[no-any-return]


class ThermocyclerModuleCore(ModuleCore, AbstractThermocyclerCore):
    """Core control interface for an attached Thermocycler Module."""

    _sync_module_hardware: SynchronousAdapter[hw_modules.Thermocycler]
    _repetitions: Optional[int] = None
    _step_count: Optional[int] = None

    def open_lid(self) -> ThermocyclerLidStatus:
        """Open the Thermocycler's lid."""
        self._engine_client.thermocycler_open_lid(module_id=self.module_id)
        return ThermocyclerLidStatus.OPEN

    def close_lid(self) -> ThermocyclerLidStatus:
        """Close the Thermocycler's lid."""
        self._engine_client.thermocycler_close_lid(module_id=self.module_id)
        return ThermocyclerLidStatus.CLOSED

    def set_target_block_temperature(
        self,
        celsius: float,
        hold_time_seconds: Optional[float] = None,
        block_max_volume: Optional[float] = None,
    ) -> None:
        """Set the target temperature for the well block, in °C."""
        self._engine_client.thermocycler_set_target_block_temperature(
            module_id=self.module_id,
            celsius=celsius,
            block_max_volume=block_max_volume,
            hold_time_seconds=hold_time_seconds,
        )

    def wait_for_block_temperature(self) -> None:
        """Wait for target block temperature to be reached."""
        self._engine_client.thermocycler_wait_for_block_temperature(
            module_id=self.module_id
        )

    def set_target_lid_temperature(self, celsius: float) -> None:
        """Set the target temperature for the heated lid, in °C."""
        self._engine_client.thermocycler_set_target_lid_temperature(
            module_id=self.module_id, celsius=celsius
        )

    def wait_for_lid_temperature(self) -> None:
        """Wait for target lid temperature to be reached."""
        self._engine_client.thermocycler_wait_for_lid_temperature(
            module_id=self.module_id
        )

    def execute_profile(
        self,
        steps: List[ThermocyclerStep],
        repetitions: int,
        block_max_volume: Optional[float] = None,
    ) -> None:
        """Execute a Thermocycler Profile."""
        self._repetitions = repetitions
        self._step_count = len(steps)
        self._engine_client.thermocycler_run_profile(
            module_id=self.module_id,
            steps=steps * repetitions,
            block_max_volume=block_max_volume,
        )

    def deactivate_lid(self) -> None:
        """Turn off the heated lid."""
        self._engine_client.thermocycler_deactivate_lid(module_id=self.module_id)

    def deactivate_block(self) -> None:
        """Turn off the well block temperature controller"""
        self._clear_cycle_counters()
        self._engine_client.thermocycler_deactivate_block(module_id=self.module_id)

    def deactivate(self) -> None:
        """Turn off the well block temperature controller, and heated lid"""
        self.deactivate_block()
        self.deactivate_lid()

    def get_lid_position(self) -> Optional[ThermocyclerLidStatus]:
        """Get the thermocycler's lid position."""
        return self._sync_module_hardware.lid_status  # type: ignore[no-any-return]

    def get_block_temperature_status(self) -> TemperatureStatus:
        """Get the thermocycler's block temperature status."""
        return self._sync_module_hardware.status  # type: ignore[no-any-return]

    def get_lid_temperature_status(self) -> Optional[TemperatureStatus]:
        """Get the thermocycler's lid temperature status."""
        return self._sync_module_hardware.lid_temp_status  # type: ignore[no-any-return]

    def get_block_temperature(self) -> Optional[float]:
        """Get the thermocycler's current block temperature in °C."""
        return self._sync_module_hardware.temperature  # type: ignore[no-any-return]

    def get_block_target_temperature(self) -> Optional[float]:
        """Get the thermocycler's target block temperature in °C."""
        return self._sync_module_hardware.target  # type: ignore[no-any-return]

    def get_lid_temperature(self) -> Optional[float]:
        """Get the thermocycler's current lid temperature in °C."""
        return self._sync_module_hardware.lid_temp  # type: ignore[no-any-return]

    def get_lid_target_temperature(self) -> Optional[float]:
        """Get the thermocycler's target lid temperature in °C."""
        return self._sync_module_hardware.lid_target  # type: ignore[no-any-return]

    def get_ramp_rate(self) -> Optional[float]:
        """Get the thermocycler's current ramp rate in °C/sec."""
        return self._sync_module_hardware.ramp_rate  # type: ignore[no-any-return]

    def get_hold_time(self) -> Optional[float]:
        """Get the remaining hold time in seconds."""
        return self._sync_module_hardware.hold_time  # type: ignore[no-any-return]

    def get_total_cycle_count(self) -> Optional[int]:
        """Get number of repetitions for current set cycle."""
        return self._repetitions

    def get_current_cycle_index(self) -> Optional[int]:
        """Get index of the current set cycle repetition."""
        if self._repetitions is None:
            return None
        step_index = self._sync_module_hardware.current_step_index
        # TODO(jbl 2022-10-31) this is intended to work even if execute profile is non-blocking, but it is blocking so
        #   this is not guaranteed to be accurate
        return (step_index - 1) // self._step_count + 1  # type: ignore[no-any-return]

    def get_total_step_count(self) -> Optional[int]:
        """Get number of steps within the current cycle."""
        return self._step_count

    def get_current_step_index(self) -> Optional[int]:
        """Get the index of the current step within the current cycle."""
        if self._step_count is None:
            return None
        step_index = self._sync_module_hardware.current_step_index
        # TODO(jbl 2022-10-31) this is intended to work even if execute profile is non-blocking, but it is blocking so
        #   this is not guaranteed to be accurate
        return (step_index - 1) % self._step_count + 1  # type: ignore[no-any-return]

    def _clear_cycle_counters(self) -> None:
        """Clear core-tracked cycle counters."""
        self._repetitions = None
        self._step_count = None


class HeaterShakerModuleCore(ModuleCore, AbstractHeaterShakerCore):
    """Core control interface for an attached Heater-Shaker Module."""

    _sync_module_hardware: SynchronousAdapter[hw_modules.HeaterShaker]

    def set_target_temperature(self, celsius: float) -> None:
        """Set the labware plate's target temperature in °C."""
        self._engine_client.heater_shaker_set_target_temperature(
            module_id=self.module_id, celsius=celsius
        )

    def wait_for_target_temperature(self) -> None:
        """Wait for the labware plate's target temperature to be reached."""
        self._engine_client.heater_shaker_wait_for_temperature(module_id=self.module_id)

    def set_and_wait_for_shake_speed(self, rpm: int) -> None:
        """Set the shaker's target shake speed and wait for it to spin up."""
        self._engine_client.heater_shaker_set_and_wait_for_shake_speed(
            module_id=self.module_id, rpm=rpm
        )

    def open_labware_latch(self) -> None:
        """Open the labware latch."""
        self._engine_client.heater_shaker_open_labware_latch(module_id=self.module_id)

    def close_labware_latch(self) -> None:
        """Close the labware latch."""
        self._engine_client.heater_shaker_close_labware_latch(module_id=self.module_id)

    def deactivate_shaker(self) -> None:
        """Stop shaking."""
        self._engine_client.heater_shaker_deactivate_shaker(module_id=self.module_id)

    def deactivate_heater(self) -> None:
        """Stop heating."""
        self._engine_client.heater_shaker_deactivate_heater(module_id=self.module_id)

    def get_current_temperature(self) -> float:
        """Get the labware plate's current temperature in °C."""
        return self._sync_module_hardware.temperature  # type: ignore[no-any-return]

    def get_target_temperature(self) -> Optional[float]:
        """Get the labware plate's target temperature in °C, if set."""
        return self._sync_module_hardware.target_temperature  # type: ignore[no-any-return]

    def get_current_speed(self) -> int:
        """Get the shaker's current speed in RPM."""
        return self._sync_module_hardware.speed  # type: ignore[no-any-return]

    def get_target_speed(self) -> Optional[int]:
        """Get the shaker's target speed in RPM, if set."""
        return self._sync_module_hardware.target_speed  # type: ignore[no-any-return]

    def get_temperature_status(self) -> TemperatureStatus:
        """Get the module's heater status."""
        return self._sync_module_hardware.temperature_status  # type: ignore[no-any-return]

    def get_speed_status(self) -> SpeedStatus:
        """Get the module's heater status."""
        return self._sync_module_hardware.speed_status  # type: ignore[no-any-return]

    def get_labware_latch_status(self) -> HeaterShakerLabwareLatchStatus:
        """Get the module's labware latch status."""
        return self._sync_module_hardware.labware_latch_status  # type: ignore[no-any-return]


class MagneticBlockCore(NonConnectedModuleCore, AbstractMagneticBlockCore):
    """Magnetic Block control interface via a ProtocolEngine."""


class AbsorbanceReaderCore(ModuleCore, AbstractAbsorbanceReaderCore):
    """Absorbance Reader core logic implementation for Python protocols."""

    _sync_module_hardware: SynchronousAdapter[hw_modules.AbsorbanceReader]
    _initialized_value: Optional[int] = None

    def initialize(self, wavelength: int) -> None:
        """Initialize the Absorbance Reader by taking zero reading."""
        self._engine_client.absorbance_reader_initialize(
            module_id=self.module_id, wavelength=wavelength
        )
        self._initialized_value = wavelength

    def initiate_read(self) -> None:
        """Initiate read on the Absorbance Reader."""
        if self._initialized_value:
            self._engine_client.absorbance_reader_measure(
                module_id=self.module_id, wavelength=self._initialized_value
            )
