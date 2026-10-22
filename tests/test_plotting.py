import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from invertedpen.plotting import plot_run
from invertedpen.simulation_logging import SimulationLogger


def make_run(tmp_path, *, controller="zero_input"):
    logger = SimulationLogger(
        tmp_path,
        tag="plot-test",
        metadata={
            "model": "cartpole",
            "controller": controller,
            "simulation": {"dt": 0.01},
        },
    )
    for step in range(3):
        logger.log(
            step,
            time=step * 0.01,
            state=np.array([step, 3.0 * step, step + 2, step + 3], dtype=float),
            input=np.array([step], dtype=float),
        )
    return logger.finalize()


def test_plot_run_creates_stacked_state_subplots(tmp_path, monkeypatch) -> None:
    run_path = make_run(tmp_path)
    monkeypatch.setattr(plt, "show", lambda: None)

    figures = plot_run(run_path)

    assert len(figures) == 1
    axes = figures[0].axes
    assert len(axes) == 4
    assert [axis.get_xlabel() for axis in axes] == ["", "", "", "Time (s)"]
    assert axes[0].get_ylabel() == "x (m)"
    assert axes[1].get_ylabel() == "theta (deg)"
    assert len(figures[0].legends) == 1
    assert len(figures[0].legends[0].legend_handles) == 5
    assert "model=cartpole" in figures[0]._suptitle.get_text()
    plt.close("all")


def test_plot_run_adds_input_subplot_for_nonzero_controller(
    tmp_path, monkeypatch
) -> None:
    run_path = make_run(tmp_path, controller="lqr")
    monkeypatch.setattr(plt, "show", lambda: None)

    figures = plot_run(run_path)

    assert len(figures[0].axes) == 5
    assert figures[0].axes[-1].get_ylabel() == "u (N)"
    plt.close("all")


def test_plot_run_can_use_separate_windows(tmp_path, monkeypatch) -> None:
    run_path = make_run(tmp_path)
    monkeypatch.setattr(plt, "show", lambda: None)

    figures = plot_run(run_path, separate_windows=True)

    assert len(figures) == 4
    assert [figure.axes[0].get_xlabel() for figure in figures] == ["Time (s)"] * 4
    plt.close("all")
