"""Plotting helpers for persisted simulation runs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from .simulation_logging import load_run

STATE_SPECS = (
    ("x", "Cart position", "x (m)", 0, False),
    ("theta", "Pendulum angle", "theta (deg)", 1, True),
    ("x_dot", "Cart velocity", "x_dot (m/s)", 2, False),
    ("theta_dot", "Pendulum angular velocity", "theta_dot (deg/s)", 3, False),
)
STATE_COLORS = ("tab:blue", "tab:orange", "tab:green", "tab:red")
INPUT_SPEC = ("input", "Control input", "u (N)", "tab:purple")


def _configuration_value(
    configuration: Mapping[str, Any], key: str, default: str = "unknown"
) -> str:
    value = configuration.get(key, default)
    if isinstance(value, Mapping):
        return ", ".join(f"{item}={item_value}" for item, item_value in value.items())
    return str(value)


def _configuration(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    configuration = metadata.get("configuration", {})
    return configuration if isinstance(configuration, Mapping) else {}


def _figure_title(metadata: Mapping[str, Any]) -> str:
    configuration = _configuration(metadata)
    simulation = configuration.get("simulation", {})
    simulation = simulation if isinstance(simulation, Mapping) else {}
    return (
        f"{metadata.get('tag', 'simulation')} | "
        f"{metadata.get('created_at_utc', 'unknown')} | "
        f"model={_configuration_value(configuration, 'model')} | "
        f"controller={_configuration_value(configuration, 'controller')} | "
        f"sample time={simulation.get('dt', 'unknown')} s"
    )


def _controller_name(metadata: Mapping[str, Any]) -> str:
    return _configuration_value(_configuration(metadata), "controller")


def _prepare_state(state: np.ndarray) -> np.ndarray:
    prepared = state.astype(float, copy=True)
    prepared[:, 1] = np.rad2deg(np.unwrap(prepared[:, 1]))
    prepared[:, 3] = np.rad2deg(prepared[:, 3])
    return prepared


def _add_series(
    axis: Any,
    time: np.ndarray,
    values: np.ndarray,
    label: str,
    color: str,
    *,
    target: float | None = None,
) -> list[Any]:
    handles = [axis.plot(time, values, color=color, label=label)[0]]
    if target is not None:
        handles.append(
            axis.axhline(
                target,
                color=color,
                linestyle="--",
                label=f"target ({target:g})",
            )
        )
    return handles


def plot_run(
    run_path: str | Path, *, separate_windows: bool = False
) -> list[Figure]:
    """Plot a persisted run and show all generated figures together."""
    metadata, arrays = load_run(run_path)
    if "time" not in arrays or "state" not in arrays:
        raise ValueError("run must contain 'time' and 'state' signals")
    time = np.asarray(arrays["time"])
    state = np.asarray(arrays["state"])
    if time.ndim != 1 or state.ndim != 2 or state.shape[1] != len(STATE_SPECS):
        raise ValueError("run must contain a time vector and a four-state trajectory")
    if len(time) != len(state):
        raise ValueError("time and state signals must have the same number of samples")

    state = _prepare_state(state)
    plot_input = _controller_name(metadata) != "zero_input"
    input_values = np.asarray(arrays["input"]).reshape(-1) if plot_input else None
    if input_values is not None and len(input_values) != len(time):
        raise ValueError("time and input signals must have the same number of samples")

    if separate_windows:
        figures: list[Figure] = []
        for index, (_, title, axis_label, _, is_angle) in enumerate(STATE_SPECS):
            figure, axis = plt.subplots(constrained_layout=True)
            _add_series(
                axis,
                time,
                state[:, index],
                axis_label,
                STATE_COLORS[index],
                target=0.0 if is_angle else None,
            )
            axis.set_title(f"{title}\n{_figure_title(metadata)}")
            axis.set_xlabel("Time (s)")
            axis.set_ylabel(axis_label)
            axis.grid(True)
            axis.legend()
            figures.append(figure)
        if input_values is not None:
            figure, axis = plt.subplots(constrained_layout=True)
            _add_series(axis, time, input_values, "u (N)", INPUT_SPEC[3])
            axis.set_title(f"{INPUT_SPEC[1]}\n{_figure_title(metadata)}")
            axis.set_xlabel("Time (s)")
            axis.set_ylabel(INPUT_SPEC[2])
            axis.grid(True)
            axis.legend()
            figures.append(figure)
    else:
        plot_count = len(STATE_SPECS) + (input_values is not None)
        figure, axes = plt.subplots(
            plot_count, 1, sharex=True, squeeze=False, constrained_layout=True
        )
        axes_flat = axes[:, 0]
        handles: list[Any] = []
        labels: list[str] = []
        for index, (_, title, axis_label, _, is_angle) in enumerate(STATE_SPECS):
            handles.extend(
                _add_series(
                    axes_flat[index],
                    time,
                    state[:, index],
                    axis_label,
                    STATE_COLORS[index],
                    target=0.0 if is_angle else None,
                )
            )
            axes_flat[index].set_title(title)
            axes_flat[index].set_ylabel(axis_label)
            axes_flat[index].grid(True)
        if input_values is not None:
            handles.extend(
                _add_series(
                    axes_flat[-1], time, input_values, "u (N)", INPUT_SPEC[3]
                )
            )
            axes_flat[-1].set_title(INPUT_SPEC[1])
            axes_flat[-1].set_ylabel(INPUT_SPEC[2])
            axes_flat[-1].grid(True)
        axes_flat[-1].set_xlabel("Time (s)")
        labels = [handle.get_label() for handle in handles]
        figure.suptitle(_figure_title(metadata))
        figure.legend(handles, labels)
        figures = [figure]

    plt.show()
    return figures
