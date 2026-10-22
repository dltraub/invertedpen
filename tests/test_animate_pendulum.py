import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.backend_bases import KeyEvent
import numpy as np
import pytest

from invertedpen.animate_pendulum import _resample, animate, save


def test_resample_unwraps_theta_before_interpolation() -> None:
    time = np.array([0.0, 0.01, 0.02])
    states = np.zeros((3, 4))
    states[:, 1] = np.array([np.deg2rad(170), np.deg2rad(179), np.deg2rad(-172)])

    frame_time, frame_states = _resample(time, states, fps=200, speed=1)

    crossing = np.flatnonzero(np.isclose(frame_time, 0.015))[0]
    assert np.rad2deg(frame_states[crossing, 1]) == pytest.approx(183.5)


def test_animate_resamples_nonuniform_trajectory_and_returns_animation() -> None:
    time = np.array([0.0, 0.2, 0.7, 1.0])
    states = np.column_stack(
        (time, np.zeros(4), np.ones(4), np.zeros(4))
    )
    animation = animate(time, states, 0.5, fps=10, speed=2)

    assert len(list(animation.new_frame_seq())) == 6
    assert animation._interval == 100
    plt.close(animation._fig)


def test_follow_camera_updates_ticks_and_overlay() -> None:
    time = np.linspace(0.0, 1.0, 4)
    states = np.zeros((4, 4))
    states[:, 0] = np.arange(4)
    animation = animate(time, states, 0.5, camera="follow", trail=False)

    initial_width = np.diff(animation._fig.axes[0].get_xlim())[0]
    animation._func(2)
    axis = animation._fig.axes[0]
    assert np.diff(axis.get_xlim())[0] == pytest.approx(initial_width)
    assert "theta =" in axis.texts[0].get_text()
    plt.close(animation._fig)


def test_spacebar_toggles_pause_and_button_can_resume() -> None:
    animation = animate([0.0, 1.0], np.zeros((2, 4)), 0.5)
    button = animation.pause_button
    axis = animation._fig.axes[0]
    animation._func(1)
    animation._fig.canvas.draw()
    text_before_pause = axis.texts[0].get_text()
    assert button.label.get_text() == "Pause"

    animation._fig.canvas.callbacks.process(
        "key_press_event", KeyEvent("key_press_event", animation._fig.canvas, key=" ")
    )
    assert button.label.get_text() == "Resume"
    assert axis.texts[0].get_text() == text_before_pause

    animation.toggle_pause()
    assert button.label.get_text() == "Pause"
    assert axis.texts[0].get_text() == text_before_pause
    plt.close(animation._fig)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fps": 0},
        {"speed": 0},
        {"camera": "invalid"},
    ],
)
def test_animate_rejects_invalid_options(kwargs) -> None:
    with pytest.raises(ValueError):
        animate([0.0, 1.0], np.zeros((2, 4)), 0.5, **kwargs)


def test_save_rejects_unknown_format() -> None:
    animation = animate([0.0, 1.0], np.zeros((2, 4)), 0.5)
    with pytest.raises(ValueError, match="must end"):
        save(animation, "animation.webm")
    plt.close(animation._fig)
