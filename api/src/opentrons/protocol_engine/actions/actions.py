"""State store actions.

Actions can be passed to the ActionDispatcher, where they will trigger
reactions in objects that subscribe to the pipeline, like the StateStore.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from opentrons.protocols.models import LabwareDefinition

from ..commands import Command, CommandCreate
from ..errors import ProtocolEngineError
from ..types import LabwareOffsetCreate


@dataclass(frozen=True)
class PlayAction:
    """Start or resume processing commands in the engine."""


@dataclass(frozen=True)
class PauseAction:
    """Pause processing commands in the engine."""


@dataclass(frozen=True)
class StopAction:
    """Stop the current engine execution.

    After a StopAction, the engine status will be marked as stopped.
    """


@dataclass(frozen=True)
class FinishErrorDetails:
    """Error details for the payload of a FinishAction."""

    error: Exception
    error_id: str
    created_at: datetime


@dataclass(frozen=True)
class FinishAction:
    """Gracefully stop processing commands in the engine.

    After a FinishAction, the engine status will be marked as succeeded or failed.
    """

    error_details: Optional[FinishErrorDetails] = None


@dataclass(frozen=True)
class HardwareStoppedAction:
    """An action dispatched after hardware has successfully been stopped."""


@dataclass(frozen=True)
class QueueCommandAction:
    """Add a command request to the queue."""

    command_id: str
    created_at: datetime
    request: CommandCreate


@dataclass(frozen=True)
class UpdateCommandAction:
    """Update a given command."""

    command: Command


@dataclass(frozen=True)
class FailCommandAction:
    """Mark a given command as failed."""

    # TODO(mc, 2021-11-12): we'll likely need to add the command params
    # to this payload for state reaction purposes
    command_id: str
    error_id: str
    failed_at: datetime
    error: ProtocolEngineError


@dataclass(frozen=True)
class AddLabwareOffsetAction:
    """Add a labware offset, to apply to subsequent `LoadLabwareCommand`s."""

    labware_offset_id: str
    created_at: datetime
    request: LabwareOffsetCreate


@dataclass(frozen=True)
class AddLabwareDefinitionAction:
    """Add a labware definition, to apply to subsequent `LoadLabwareCommand`s."""

    definition: LabwareDefinition


Action = Union[
    PlayAction,
    PauseAction,
    StopAction,
    FinishAction,
    HardwareStoppedAction,
    QueueCommandAction,
    UpdateCommandAction,
    FailCommandAction,
    AddLabwareOffsetAction,
    AddLabwareDefinitionAction,
]
