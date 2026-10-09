import numpy as np
import pytest
import sympy as sp

from invertedpen.models.cartpole import CartPoleModel, CartPoleParameters


def make_model() -> CartPoleModel:
    return CartPoleModel(
        CartPoleParameters(
            cart_mass=1.0,
            pendulum_mass=0.2,
            pendulum_length=0.5,
        )
    )


def test_parameters_reject_nonphysical_values() -> None:
    with np.testing.assert_raises(ValueError):
        CartPoleParameters(0.0, 0.2, 0.5)


def test_upright_unforced_state_is_equilibrium() -> None:
    model = make_model()
    derivative = np.asarray(model.dynamics([0, 0, 0, 0], [0])).reshape(-1)
    np.testing.assert_allclose(derivative, np.zeros(4))


def test_output_is_full_state() -> None:
    model = make_model()
    state = np.array([0.1, -0.2, 0.3, -0.4])
    np.testing.assert_allclose(np.asarray(model.output(state)).reshape(-1), state)


@pytest.mark.parametrize(
    ("angle", "expected"),
    [
        (-3 * np.pi, -np.pi),
        (-np.pi, -np.pi),
        (np.pi, -np.pi),
        (3 * np.pi, -np.pi),
        (0.25, 0.25),
    ],
)
def test_normalize_state_wraps_theta_to_negative_pi_inclusive_interval(
    angle: float, expected: float
) -> None:
    model = make_model()
    state = np.array([1.0, angle, 2.0, 3.0])

    normalized = model.normalize_state(state)

    np.testing.assert_allclose(normalized, [1.0, expected, 2.0, 3.0])
    assert -np.pi <= normalized[1] < np.pi


def test_euler_lagrange_derivation_has_expected_force_balance() -> None:
    model = make_model()
    residuals = model.euler_lagrange_equations
    x_ddot, theta_ddot = model.q_ddot
    x, theta = model.q
    x_dot, theta_dot = model.q_dot
    force = model.force
    m = sp.Float(model.parameters.pendulum_mass)
    M = sp.Float(model.parameters.cart_mass)
    l = sp.Float(model.parameters.pendulum_length)
    g = sp.Float(model.parameters.gravity)

    expected = sp.Matrix(
        [
            (M + m) * x_ddot + m * l * sp.cos(theta) * theta_ddot
            - m * l * sp.sin(theta) * theta_dot**2
            - force,
            m * l * sp.cos(theta) * x_ddot
            + m * l**2 * theta_ddot
            - m * g * l * sp.sin(theta),
        ]
    )
    for actual, wanted in zip(residuals, expected):
        assert sp.simplify(actual - wanted) == 0


def test_energy_is_constant_for_unforced_trajectory_derivative() -> None:
    model = make_model()
    state = np.array([0.2, 0.4, 0.7, -0.3])
    derivative = np.asarray(model.dynamics(state, [0])).reshape(-1)
    eps = 1e-6
    plus = np.asarray(model.energy(state + eps * derivative)).item()
    minus = np.asarray(model.energy(state - eps * derivative)).item()
    energy_rate = (plus - minus) / (2 * eps)
    np.testing.assert_allclose(energy_rate, 0.0, atol=1e-7)
