"""Deterministic simulation application orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from .state_machine import ApplicationState, StateMachineError

Controller = Callable[[np.ndarray], np.ndarray]


class ContinuousPlant(Protocol):
    """Minimal continuous-time plant contract used by the application loop."""

    state_size: int
    input_size: int

    def dynamics(self, state: np.ndarray, control: np.ndarray) -> object:
        """Return the continuous-time state derivative."""


@dataclass(frozen=True)
class SimulationConfig:
    """Bounds and timing for one deterministic simulation run."""

    initial_state: np.ndarray = field(
        default_factory=lambda: np.zeros(4, dtype=float)
    )
    dt: float = 0.01
    steps: int = 100

    def __post_init__(self) -> None:
        if self.dt <= 0:
            raise ValueError(f"dt must be positive, got {self.dt!r}")
        if self.steps < 0:
            raise ValueError(f"steps must be non-negative, got {self.steps!r}")


def _rk4_step(
    model: ContinuousPlant,
    state: np.ndarray,
    control: np.ndarray,
    dt: float,
) -> np.ndarray:
    def dynamics(value: np.ndarray) -> np.ndarray:
        return np.asarray(model.dynamics(value, control), dtype=float).reshape(
            model.state_size
        )

    k1 = dynamics(state)
    k2 = dynamics(state + 0.5 * dt * k1)
    k3 = dynamics(state + 0.5 * dt * k2)
    k4 = dynamics(state + dt * k3)
    return state + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6


class SimulationApplication:
    """Coordinate a plant, controller, and deterministic simulation loop."""

    def __init__(
        self,
        model: ContinuousPlant,
        config: SimulationConfig,
        controller: Controller | None = None,
    ) -> None:
        self.model = model
        self.config = config
        self.current_state = np.asarray(config.initial_state, dtype=float).copy()
        if self.current_state.shape != (model.state_size,):
            raise ValueError(
                f"initial_state must have shape ({model.state_size},), "
                f"got {self.current_state.shape}"
            )
        self.controller = controller or (
            lambda _state: np.zeros(model.input_size, dtype=float)
        )
        self.state = ApplicationState.INIT
        self.trajectory: list[np.ndarray] = []

    def transition_to(self, target: ApplicationState) -> None:
        allowed = {
            ApplicationState.INIT: {ApplicationState.BALANCE, ApplicationState.ERROR},
            ApplicationState.BALANCE: {ApplicationState.STOP, ApplicationState.ERROR},
            ApplicationState.STOP: set(),
            ApplicationState.ERROR: set(),
        }
        if target not in allowed[self.state]:
            raise StateMachineError(
                f"cannot transition from {self.state.name} to {target.name}"
            )
        self.state = target

    def run(self) -> np.ndarray:
        """Run the configured number of steps and return the state trajectory."""

        if self.state is not ApplicationState.INIT:
            raise StateMachineError("a simulation can only be run from INIT")
        self.trajectory = [self.current_state.copy()]
        try:
            self.transition_to(ApplicationState.BALANCE)
            for _ in range(self.config.steps):
                control = np.asarray(
                    self.controller(self.current_state), dtype=float
                ).reshape(self.model.input_size)
                self.current_state = _rk4_step(
                    self.model, self.current_state, control, self.config.dt
                )
                self.trajectory.append(self.current_state.copy())
            self.transition_to(ApplicationState.STOP)
        except Exception:
            self.state = ApplicationState.ERROR
            raise
        return np.asarray(self.trajectory)
