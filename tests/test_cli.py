import argparse
import subprocess
import sys

import numpy as np

from invertedpen.cli import _build_initial_state, main


def test_cli_help_without_command(capsys) -> None:
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "usage:" in output
    assert "--initial-state" in output
    assert "--initial-theta-dot" in output


def test_cli_smoke_test(capsys) -> None:
    assert main(["smoke-test"]) == 0
    assert "cart-pole ready" in capsys.readouterr().out


def test_cli_simulate(capsys) -> None:
    assert main(["simulate", "--steps", "3", "--no-log"]) == 0
    output = capsys.readouterr().out
    assert "simulation complete; steps=3" in output


def test_cli_simulate_no_plot_skips_plotting(tmp_path, monkeypatch) -> None:
    from invertedpen import plotting

    calls = []
    monkeypatch.setattr(plotting, "plot_run", lambda path: calls.append(path))

    assert (
        main(
            [
                "simulate",
                "--steps",
                "1",
                "--log-dir",
                str(tmp_path),
                "--no-plot",
            ]
        )
        == 0
    )

    assert calls == []


def test_cli_simulate_plots_new_log_by_default(tmp_path, monkeypatch) -> None:
    from invertedpen import plotting

    calls = []
    monkeypatch.setattr(
        plotting, "plot_run", lambda path, separate_windows=False: calls.append(
            (path, separate_windows)
        )
    )

    assert (
        main(
            [
                "simulate",
                "--steps",
                "1",
                "--log-dir",
                str(tmp_path),
            ]
        )
        == 0
    )

    assert len(calls) == 1
    assert calls[0][0].parent == tmp_path
    assert calls[0][0].joinpath("trajectory.npz").is_file()
    assert calls[0][1] is False


def test_cli_separate_windows_is_forwarded_to_plotting(tmp_path, monkeypatch) -> None:
    from invertedpen import plotting

    calls = []
    monkeypatch.setattr(
        plotting, "plot_run", lambda path, separate_windows=False: calls.append(
            separate_windows
        )
    )

    assert (
        main(
            [
                "simulate",
                "--steps",
                "1",
                "--log-dir",
                str(tmp_path),
                "--separate-windows",
            ]
        )
        == 0
    )

    assert calls == [True]


def test_full_initial_state_option(capsys) -> None:
    assert main(
        [
            "simulate",
            "--steps",
            "0",
            "--no-log",
            "--initial-state",
            "1",
            "2",
            "3",
            "4",
        ]
    ) == 0

    assert "final_state=[1. 2. 3. 4.]" in capsys.readouterr().out


def test_individual_initial_state_options_leave_other_values_at_zero(capsys) -> None:
    assert (
        main(["simulate", "--steps", "0", "--no-log", "--initial-theta", "0.25"])
        == 0
    )

    assert "final_state=[0.   0.25 0.   0.  ]" in capsys.readouterr().out


def test_individual_initial_state_options_override_full_state() -> None:
    args = argparse.Namespace(
        initial_state=[1.0, 2.0, 3.0, 4.0],
        initial_x=None,
        initial_theta=20.0,
        initial_x_dot=None,
        initial_theta_dot=None,
    )

    np.testing.assert_allclose(_build_initial_state(args), [1.0, 20.0, 3.0, 4.0])


def test_module_entry_point() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "invertedpen", "smoke-test"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "cart-pole ready" in result.stdout
