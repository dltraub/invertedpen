"""Command-line interface for the invertedpen project."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import numpy as np

from . import __version__
from .app import SimulationApplication, SimulationConfig
from .models.cartpole import CartPoleModel, CartPoleParameters


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="invertedpen",
        description="Run inverted-pendulum simulation and control experiments.",
        epilog=(
            "Simulation options: --steps, --dt, --initial-state X THETA X_DOT "
            "THETA_DOT, --initial-x, --initial-theta, --initial-x-dot, and "
            "--initial-theta-dot. Use 'invertedpen simulate --help' for "
            "descriptions and examples."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "smoke-test",
        help="instantiate the default cart-pole and check its upright equilibrium",
    )
    simulate = subparsers.add_parser(
        "simulate",
        help="run a bounded deterministic cart-pole simulation",
    )
    simulate.add_argument("--steps", type=int, default=100)
    simulate.add_argument("--dt", type=float, default=0.01)
    simulate.add_argument(
        "--initial-state",
        nargs=4,
        type=float,
        metavar=("X", "THETA", "X_DOT", "THETA_DOT"),
        help="set the complete initial state",
    )
    simulate.add_argument("--initial-x", type=float, help="set initial cart position")
    simulate.add_argument(
        "--initial-theta", type=float, help="set initial pendulum angle"
    )
    simulate.add_argument(
        "--initial-x-dot", type=float, help="set initial cart velocity"
    )
    simulate.add_argument(
        "--initial-theta-dot", type=float, help="set initial pendulum angular velocity"
    )
    return parser


def _run_smoke_test() -> int:
    model = CartPoleModel(
        CartPoleParameters(
            cart_mass=1.0,
            pendulum_mass=0.2,
            pendulum_length=0.5,
        )
    )
    derivative = model.dynamics([0.0, 0.0, 0.0, 0.0], [0.0])
    print(f"cart-pole ready; upright derivative={derivative}")
    return 0


def _make_default_model() -> CartPoleModel:
    return CartPoleModel(
        CartPoleParameters(
            cart_mass=1.0,
            pendulum_mass=0.2,
            pendulum_length=0.5,
        )
    )


def _build_initial_state(args: argparse.Namespace) -> np.ndarray:
    """Build the initial state, applying individual options as overrides."""

    if args.initial_state is None:
        initial_state = np.zeros(4, dtype=float)
    else:
        initial_state = np.asarray(args.initial_state, dtype=float)

    overrides = (
        (0, args.initial_x),
        (1, args.initial_theta),
        (2, args.initial_x_dot),
        (3, args.initial_theta_dot),
    )
    for index, value in overrides:
        if value is not None:
            initial_state[index] = value
    if not np.all(np.isfinite(initial_state)):
        raise ValueError("initial state values must be finite")
    return initial_state


def _run_simulation(args: argparse.Namespace) -> int:
    application = SimulationApplication(
        _make_default_model(),
        SimulationConfig(
            initial_state=_build_initial_state(args),
            steps=args.steps,
            dt=args.dt,
        ),
    )
    trajectory = application.run()
    print(
        f"simulation complete; steps={args.steps}, dt={args.dt:g}, "
        f"final_state={trajectory[-1]}"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit status."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "smoke-test":
        return _run_smoke_test()
    if args.command == "simulate":
        return _run_simulation(args)
    parser.print_help()
    return 0
