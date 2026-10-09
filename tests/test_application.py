import numpy as np
import pytest

from invertedpen.app import (
    ApplicationState,
    SimulationApplication,
    SimulationConfig,
    StateMachineError,
)
from invertedpen.models.cartpole import CartPoleModel, CartPoleParameters


def make_application(steps: int = 2) -> SimulationApplication:
    model = CartPoleModel(CartPoleParameters(1.0, 0.2, 0.5))
    return SimulationApplication(model, SimulationConfig(steps=steps))


def test_run_transitions_through_balance_to_stop() -> None:
    application = make_application(steps=2)

    trajectory = application.run()

    assert application.state is ApplicationState.STOP
    assert trajectory.shape == (3, 4)
    np.testing.assert_allclose(trajectory, np.zeros((3, 4)))


def test_run_is_bounded_by_configured_step_count() -> None:
    application = make_application(steps=0)

    trajectory = application.run()

    assert trajectory.shape == (1, 4)


def test_initial_and_recorded_states_use_normalized_theta() -> None:
    model = CartPoleModel(CartPoleParameters(1.0, 0.2, 0.5))
    application = SimulationApplication(
        model,
        SimulationConfig(initial_state=np.array([0.0, 3 * np.pi, 0.0, 0.0]), steps=1),
    )

    trajectory = application.run()

    assert np.all((-np.pi <= trajectory[:, 1]) & (trajectory[:, 1] < np.pi))


def test_invalid_transition_is_rejected() -> None:
    application = make_application()

    with pytest.raises(StateMachineError):
        application.transition_to(ApplicationState.STOP)


def test_controller_is_called_once_per_step() -> None:
    calls = []
    application = make_application(steps=3)
    application.controller = lambda state: calls.append(state.copy()) or np.zeros(1)

    application.run()

    assert len(calls) == 3


def test_run_enters_error_state_when_a_step_fails() -> None:
    application = make_application(steps=1)

    def failing_controller(_state: np.ndarray) -> np.ndarray:
        raise RuntimeError("controller failure")

    application.controller = failing_controller

    with pytest.raises(RuntimeError, match="controller failure"):
        application.run()

    assert application.state is ApplicationState.ERROR
