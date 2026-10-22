import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from invertedpen.animate_pendulum import animate, save


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
