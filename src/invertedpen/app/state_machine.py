"""Explicit lifecycle states for an application run."""

from __future__ import annotations

from enum import Enum, auto


class ApplicationState(Enum):
    """States in the deterministic application lifecycle."""

    INIT = auto()
    BALANCE = auto()
    STOP = auto()
    ERROR = auto()


class StateMachineError(RuntimeError):
    """Raised when an invalid lifecycle transition is requested."""
