"""Command-line interface for the invertedpen project."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import __version__
from .models.cartpole import CartPoleModel, CartPoleParameters


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="invertedpen",
        description="Run inverted-pendulum simulation and control experiments.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "smoke-test",
        help="instantiate the default cart-pole and check its upright equilibrium",
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


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit status."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "smoke-test":
        return _run_smoke_test()
    parser.print_help()
    return 0
