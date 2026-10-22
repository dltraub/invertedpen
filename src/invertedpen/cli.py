"""Command-line interface for the invertedpen project."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from . import __version__
from .app import SimulationApplication, SimulationConfig
from .models.cartpole import CartPoleModel, CartPoleParameters
from . import plotting
from .simulation_logging import SimulationLogger


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
    simulate.add_argument("--tag", default="simulation")
    simulate.add_argument("--log-dir", default="artifacts/runs")
    simulate.add_argument("--no-log", action="store_true")
    simulate.add_argument(
        "--no-plot",
        action="store_true",
        help="do not show state plots after saving the simulation log",
    )
    simulate.add_argument(
        "--separate-windows",
        action="store_true",
        help="show each plotted signal in its own window",
    )
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
    animate = subparsers.add_parser("animate", help="animate a persisted simulation run")
    animate.add_argument("--tag", help="run tag; defaults to the most recent run")
    animate.add_argument("--log-dir", default="artifacts/runs")
    animate.add_argument("--fps", type=float, default=30.0)
    animate.add_argument("--speed", type=float, default=1.0)
    animate.add_argument("--camera", choices=("fixed", "follow"), default="fixed")
    plot = subparsers.add_parser(
        "plot",
        help="plot trajectories from a persisted simulation run",
    )
    plot.add_argument("--tag", help="run tag; defaults to the most recent run")
    plot.add_argument("--log-dir", default="artifacts/runs")
    plot.add_argument(
        "--separate-windows",
        action="store_true",
        help="show each plotted signal in its own window",
    )
    return parser


def _find_run(log_dir: str | Path, tag: str | None) -> Path:
    candidates = []
    for path in Path(log_dir).iterdir():
        if not path.is_dir() or not (path / "metadata.json").is_file():
            continue
        if tag is not None:
            try:
                with (path / "metadata.json").open(encoding="utf-8") as file:
                    metadata = json.load(file)
            except (OSError, json.JSONDecodeError):
                continue
            if metadata.get("tag") != tag:
                continue
        candidates.append(path)
    if not candidates:
        description = f" with tag {tag!r}" if tag is not None else ""
        raise FileNotFoundError(f"no simulation runs found{description} in {log_dir}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _run_animation(args: argparse.Namespace) -> int:
    from .animate_pendulum import animate
    from .simulation_logging import load_run
    import matplotlib.pyplot as plt

    run_path = _find_run(args.log_dir, args.tag)
    _metadata, arrays = load_run(run_path)
    if "time" not in arrays or "state" not in arrays:
        raise ValueError("run must contain 'time' and 'state' signals")
    parameters = _metadata.get("configuration", {}).get("parameters", {})
    length = parameters.get("pendulum_length", 0.5)
    animation = animate(
        arrays["time"],
        arrays["state"],
        float(length),
        fps=args.fps,
        speed=args.speed,
        camera=args.camera,
    )
    print(f"animating run={run_path}")
    plt.show()
    return 0


def _run_plot(args: argparse.Namespace) -> int:
    run_path = _find_run(args.log_dir, args.tag)
    plotting.plot_run(run_path, separate_windows=args.separate_windows)
    print(f"plotted run={run_path}")
    return 0


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
    model = _make_default_model()
    logger = None
    if not args.no_log:
        logger = SimulationLogger(
            args.log_dir,
            tag=args.tag,
            metadata={
                "model": "cartpole",
                "controller": "zero_input",
                "parameters": vars(model.parameters),
                "simulation": {"dt": args.dt, "steps": args.steps},
                "initial_state": _build_initial_state(args),
            },
            signal_metadata={
                "time": {"unit": "s", "description": "simulation time"},
                "state": {
                    "unit": "SI",
                    "description": "[x, theta, x_dot, theta_dot]",
                },
                "input": {"unit": "N", "description": "ideal horizontal force"},
                "output": {"unit": "SI", "description": "ideal plant output"},
                "energy.total": {"unit": "J", "description": "total mechanical energy"},
            },
        )
    application = SimulationApplication(
        model,
        SimulationConfig(
            initial_state=_build_initial_state(args),
            steps=args.steps,
            dt=args.dt,
        ),
        logger=logger,
    )
    trajectory = application.run()
    print(
        f"simulation complete; steps={args.steps}, dt={args.dt:g}, "
        f"final_state={trajectory[-1]}"
    )
    if logger is not None:
        print(f"log={logger.run_path}")
        if not args.no_plot:
            plotting.plot_run(logger.run_path, separate_windows=args.separate_windows)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit status."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "smoke-test":
        return _run_smoke_test()
    if args.command == "simulate":
        return _run_simulation(args)
    if args.command == "animate":
        return _run_animation(args)
    if args.command == "plot":
        return _run_plot(args)
    parser.print_help()
    return 0
