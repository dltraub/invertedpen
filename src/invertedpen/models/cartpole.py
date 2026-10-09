"""Energy-based cart-pole model and symbolic equation derivation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import sympy as sp
import numpy as np
import casadi as ca


@dataclass(frozen=True)
class CartPoleParameters:
    """Physical parameters for the ideal, undamped cart-pole."""

    cart_mass: float
    pendulum_mass: float
    pendulum_length: float
    gravity: float = 9.81

    def __post_init__(self) -> None:
        for name in ("cart_mass", "pendulum_mass", "pendulum_length", "gravity"):
            value = getattr(self, name)
            if value <= 0:
                raise ValueError(f"{name} must be positive, got {value!r}")


def derive_euler_lagrange(
    kinetic_energy: sp.Expr,
    potential_energy: sp.Expr,
    dissipation: sp.Expr,
    generalized_forces: sp.Matrix,
    coordinates: sp.Matrix,
    velocities: sp.Matrix,
    accelerations: sp.Matrix,
) -> sp.Matrix:
    """Return Euler-Lagrange residuals for a supplied energy description.

    The returned vector is ``d/dt(dL/d(q_dot)) - dL/dq + dR/d(q_dot) - Q``.
    Time derivatives are expanded using the supplied coordinates, velocities,
    and accelerations, so the result is algebraic in the generalized
    accelerations.
    """

    lagrangian = kinetic_energy - potential_energy
    residuals = []
    for coordinate, velocity, acceleration, force in zip(
        coordinates, velocities, accelerations, generalized_forces
    ):
        momentum = sp.diff(lagrangian, velocity)
        total_derivative = sum(
            sp.diff(momentum, q) * q_dot
            + sp.diff(momentum, q_dot) * q_ddot
            for q, q_dot, q_ddot in zip(coordinates, velocities, accelerations)
        )
        residuals.append(
            total_derivative
            - sp.diff(lagrangian, coordinate)
            + sp.diff(dissipation, velocity)
            - force
        )
    return sp.Matrix(residuals)


class CartPoleModel:
    """Continuous-time ideal cart-pole with a horizontal force input.

    State ordering is ``[x, theta, x_dot, theta_dot]``.  The angle is zero
    when the pendulum is upright and positive counter-clockwise.
    """

    state_size = 4
    input_size = 1
    output_size = 4

    def __init__(self, parameters: CartPoleParameters) -> None:
        self.parameters = parameters
        self.q = sp.Matrix(sp.symbols("x theta"))
        self.q_dot = sp.Matrix(sp.symbols("x_dot theta_dot"))
        self.q_ddot = sp.Matrix(sp.symbols("x_ddot theta_ddot"))
        self.force = sp.Symbol("force")

        m_cart = sp.Float(parameters.cart_mass)
        m_pendulum = sp.Float(parameters.pendulum_mass)
        length = sp.Float(parameters.pendulum_length)
        gravity = sp.Float(parameters.gravity)
        x, theta = self.q
        x_dot, theta_dot = self.q_dot

        self.kinetic_energy = sp.expand(
            sp.Rational(1, 2) * (m_cart + m_pendulum) * x_dot**2
            + m_pendulum * length * sp.cos(theta) * x_dot * theta_dot
            + sp.Rational(1, 2) * m_pendulum * length**2 * theta_dot**2
        )
        self.potential_energy = m_pendulum * gravity * length * sp.cos(theta)
        self.dissipation = sp.Integer(0)
        self.generalized_forces = sp.Matrix([self.force, 0])
        self.euler_lagrange_equations = derive_euler_lagrange(
            self.kinetic_energy,
            self.potential_energy,
            self.dissipation,
            self.generalized_forces,
            self.q,
            self.q_dot,
            self.q_ddot,
        )

        self._build_casadi_functions(parameters)

    def _build_casadi_functions(self, parameters: CartPoleParameters) -> None:
        state = ca.SX.sym("state", self.state_size)
        control = ca.SX.sym("force", self.input_size)
        x, theta, x_dot, theta_dot = [state[i] for i in range(self.state_size)]
        force = control[0]
        mass = parameters.cart_mass + parameters.pendulum_mass
        pendulum_mass = parameters.pendulum_mass
        length = parameters.pendulum_length
        gravity = parameters.gravity
        cos_theta = ca.cos(theta)
        sin_theta = ca.sin(theta)
        determinant = pendulum_mass * length**2 * (
            parameters.cart_mass + pendulum_mass * sin_theta**2
        )
        rhs_x = force + pendulum_mass * length * sin_theta * theta_dot**2
        rhs_theta = pendulum_mass * gravity * length * sin_theta
        x_ddot = (
            pendulum_mass * length**2 * rhs_x
            - pendulum_mass * length * cos_theta * rhs_theta
        ) / determinant
        theta_ddot = (
            mass * rhs_theta - pendulum_mass * length * cos_theta * rhs_x
        ) / determinant
        self._dynamics = ca.Function(
            "cartpole_dynamics",
            [state, control],
            [ca.vertcat(x_dot, theta_dot, x_ddot, theta_ddot)],
        )
        self._output = ca.Function("cartpole_output", [state], [state])
        self._energy = ca.Function(
            "cartpole_energy",
            [state],
            [
                0.5 * mass * x_dot**2
                + pendulum_mass * length * cos_theta * x_dot * theta_dot
                + 0.5 * pendulum_mass * length**2 * theta_dot**2
                + pendulum_mass * gravity * length * cos_theta
            ],
        )

    def dynamics(self, state: Any, control: Any) -> Any:
        """Evaluate ``xdot = f(x, u, p)``."""

        return self._dynamics(state, control)

    def normalize_state(self, state: Any) -> np.ndarray:
        """Wrap the pendulum angle into the interval ``(-pi, pi]``."""

        normalized = np.asarray(state, dtype=float).copy()
        normalized[1] = (normalized[1] + np.pi) % (2 * np.pi) - np.pi
        return normalized

    def output(self, state: Any) -> Any:
        """Evaluate the ideal full-state output ``y = h(x, p)``."""

        return self._output(state)

    def energy(self, state: Any) -> Any:
        """Evaluate total mechanical energy ``T + V``."""

        return self._energy(state)
