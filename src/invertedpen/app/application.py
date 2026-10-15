"""Deterministic simulation application orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from .state_machine import ApplicationState, StateMachineError
from ..simulation_logging import SimulationLogger

Controller = Callable[[np.ndarray], np.ndarray]


class ContinuousPlant(Protocol):
    """Minimal continuous-time plant contract used by the application loop."""

    state_size: int
    input_size: int

    def dynamics(self, state: np.ndarray, control: np.ndarray) -> object:
        """Return the continuous-time state derivative."""

    def normalize_state(self, state: np.ndarray) -> np.ndarray:
        """Return a canonical representation of the state."""


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
        logger: SimulationLogger | None = None,
    ) -> None:
        self.model = model
        self.config = config
        self.current_state = model.normalize_state(
            np.asarray(config.initial_state, dtype=float).copy()
        )
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
        self.logger = logger

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
            for step in range(self.config.steps + 1):
                if step == self.config.steps:
                    if self.config.steps == 0:
                        control = np.zeros(self.model.input_size, dtype=float)
                    else:
                        control = previous_control
                    if self.logger is not None:
                        self._log_sample(step, control)
                    break
                control = np.asarray(
                    self.controller(self.current_state), dtype=float
                ).reshape(self.model.input_size)
                if self.logger is not None:
                    self._log_sample(step, control)
                previous_control = control
                self.current_state = _rk4_step(
                    self.model, self.current_state, control, self.config.dt
                )
                self.current_state = self.model.normalize_state(self.current_state)
                self.trajectory.append(self.current_state.copy())
            self.transition_to(ApplicationState.STOP)
            if self.logger is not None:
                self.logger.finalize()
        except Exception as exception:
            self.state = ApplicationState.ERROR
            if self.logger is not None and self.logger.run_path is None:
                self.logger.finalize(status="incomplete", error=exception)
            raise
        return np.asarray(self.trajectory)

    def _log_sample(self, step: int, control: np.ndarray) -> None:
        signals: dict[str, object] = {
            "time": step * self.config.dt,
            "state": self.current_state,
            "input": control,
        }
        output = getattr(self.model, "output", None)
        if output is not None:
            signals["output"] = output(self.current_state)
        energy = getattr(self.model, "energy", None)
        if energy is not None:
            signals["energy.total"] = energy(self.current_state)
        self.logger.log(step, **signals)
