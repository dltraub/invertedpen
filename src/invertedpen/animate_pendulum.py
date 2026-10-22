"""Matplotlib animation of logged cart-pole trajectories.

The angle convention is ``theta = 0`` for an upright pendulum and positive
angles counter-clockwise.  ``PENDULUM_X_SIGN`` is the single convention
constant used by the drawing code, making it easy to adapt the visualization
if a logged model uses the opposite horizontal sign.
"""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle
from matplotlib.lines import Line2D

PENDULUM_X_SIGN = -1.0


def _validate_inputs(t: np.ndarray, X: np.ndarray, L: float) -> None:
    if t.ndim != 1 or X.ndim != 2 or X.shape[1] != 4:
        raise ValueError("t must have shape (N,) and X must have shape (N, 4)")
    if len(t) != len(X) or len(t) < 2:
        raise ValueError("t and X must have the same length of at least two")
    if not np.all(np.isfinite(t)) or not np.all(np.isfinite(X)):
        raise ValueError("t and X must contain only finite values")
    if np.any(np.diff(t) <= 0):
        raise ValueError("t must be strictly increasing")
    if not np.isfinite(L) or L <= 0:
        raise ValueError("L must be a positive finite number")


def _resample(
    t: np.ndarray, X: np.ndarray, fps: float, speed: float
) -> tuple[np.ndarray, np.ndarray]:
    duration = float(t[-1] - t[0])
    frame_count = max(2, int(np.ceil(duration * fps / speed)) + 1)
    frame_time = np.linspace(t[0], t[-1], frame_count)
    sampled = np.column_stack(
        [np.interp(frame_time, t, X[:, column]) for column in range(X.shape[1])]
    )
    return frame_time, sampled


def animate(
    t: Sequence[float] | np.ndarray,
    X: Sequence[Sequence[float]] | np.ndarray,
    L: float,
    *,
    cart_width: float = 0.2,
    cart_height: float = 0.1,
    fps: float = 30.0,
    speed: float = 1.0,
    camera: str = "fixed",
    x_limits: tuple[float, float] | None = None,
    trail: bool = True,
    figure: Figure | None = None,
) -> FuncAnimation:
    """Create an animation from a four-state cart-pole trajectory.

    ``speed`` is the playback multiplier: ``2`` plays twice as fast.  The
    optional ``x_limits`` provides fixed limits (and the follow-camera width)
    and leaves room for future end-stop rendering.
    """
    time = np.asarray(t, dtype=float)
    states = np.asarray(X, dtype=float)
    _validate_inputs(time, states, L)
    if not np.isfinite(cart_width) or cart_width <= 0:
        raise ValueError("cart_width must be positive and finite")
    if not np.isfinite(cart_height) or cart_height <= 0:
        raise ValueError("cart_height must be positive and finite")
    if not np.isfinite(fps) or fps <= 0 or not np.isfinite(speed) or speed <= 0:
        raise ValueError("fps and speed must be positive and finite")
    if camera not in {"fixed", "follow"}:
        raise ValueError("camera must be 'fixed' or 'follow'")
    if x_limits is not None and (
        len(x_limits) != 2
        or not np.all(np.isfinite(x_limits))
        or x_limits[1] <= x_limits[0]
    ):
        raise ValueError("x_limits must contain two finite increasing values")

    frame_time, frame_states = _resample(time, states, fps, speed)
    figure = figure if figure is not None else plt.figure()
    axis = figure.add_subplot(111)
    margin = max(0.2, 0.1 * L)
    if x_limits is None:
        x_min = float(np.min(states[:, 0]) - max(L, cart_width / 2))
        x_max = float(np.max(states[:, 0]) + max(L, cart_width / 2))
        fixed_limits = (x_min - margin, x_max + margin)
    else:
        fixed_limits = x_limits
    follow_width = fixed_limits[1] - fixed_limits[0]
    if follow_width <= 0:
        raise ValueError("x_limits must have positive width")

    axis.set_ylim(-cart_height, L + margin)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x (m)")
    axis.set_ylabel("height (m)")
    axis.grid(True, alpha=0.2)
    track = axis.axhline(0.0, color="black", linewidth=1.0)
    cart = Rectangle((0.0, 0.0), cart_width, cart_height, color="tab:blue")
    rod = Line2D([], [], color="tab:orange", linewidth=2.0)
    bob = Circle((0.0, L), radius=max(0.025, 0.04 * L), color="tab:red")
    axis.add_patch(cart)
    axis.add_line(rod)
    axis.add_patch(bob)
    overlay = axis.text(
        0.02, 0.98, "", transform=axis.transAxes, va="top", family="monospace"
    )
    trail_line = Line2D([], [], color="tab:red", alpha=0.25, linewidth=1.0)
    axis.add_line(trail_line)
    tick_lines = [
        Line2D([], [], color="0.35", linewidth=0.8) for _ in range(11)
    ]
    for tick_line in tick_lines:
        axis.add_line(tick_line)

    def positions(index: int) -> tuple[float, float, float]:
        x, theta = frame_states[index, :2]
        return x, x + PENDULUM_X_SIGN * L * np.sin(theta), L * np.cos(theta)

    def update_ticks(center: float) -> None:
        spacing = max(0.1, follow_width / 10)
        first = np.floor((center - follow_width / 2) / spacing) * spacing
        for number, tick_line in enumerate(tick_lines):
            tick_x = first + number * spacing
            tick_line.set_data([tick_x, tick_x], [-0.018, 0.018])

    def update(index: int) -> tuple[Any, ...]:
        x, bob_x, bob_y = positions(index)
        theta = frame_states[index, 1]
        cart.set_xy((x - cart_width / 2, 0.0))
        rod.set_data([x, bob_x], [cart_height, bob_y])
        bob.center = (bob_x, bob_y)
        if trail:
            first = max(0, index - int(round(fps / speed)))
            trail_points = np.array([positions(i)[1:] for i in range(first, index + 1)])
            trail_line.set_data(trail_points[:, 0], trail_points[:, 1])
        else:
            trail_line.set_data([], [])
        if camera == "follow":
            axis.set_xlim(x - follow_width / 2, x + follow_width / 2)
            update_ticks(x)
        overlay.set_text(
            f"t = {frame_time[index]:6.2f} s\n"
            f"x = {x: .3f} m   theta = {np.rad2deg(theta): .2f} deg\n"
            f"x_dot = {frame_states[index, 2]: .3f} m/s\n"
            f"theta_dot = {np.rad2deg(frame_states[index, 3]): .2f} deg/s"
        )
        return (track, cart, rod, bob, overlay, trail_line, *tick_lines)

    def init() -> tuple[Any, ...]:
        if camera == "fixed":
            axis.set_xlim(*fixed_limits)
        else:
            axis.set_xlim(
                frame_states[0, 0] - follow_width / 2,
                frame_states[0, 0] + follow_width / 2,
            )
            update_ticks(float(frame_states[0, 0]))
        return update(0)

    return FuncAnimation(
        figure,
        update,
        frames=len(frame_time),
        init_func=init,
        interval=1000.0 / fps,
        blit=True,
    )


def save(anim: FuncAnimation, path: str | Path) -> None:
    """Save an animation as GIF or MP4, selecting the matching writer."""
    output = Path(path)
    suffix = output.suffix.lower()
    interval = getattr(anim.event_source, "interval", 1000.0 / 30.0)
    writer_fps = max(1, round(1000.0 / interval))
    if suffix == ".gif":
        anim.save(output, writer=PillowWriter(fps=writer_fps))
    elif suffix in {".mp4", ".m4v"}:
        if shutil.which("ffmpeg") is None:
            raise RuntimeError(
                "Saving MP4 requires ffmpeg on PATH; install ffmpeg and try again"
            )
        anim.save(output, writer=FFMpegWriter(fps=writer_fps))
    else:
        raise ValueError("animation path must end in .gif, .mp4, or .m4v")
