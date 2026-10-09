import subprocess
import sys

from invertedpen.cli import main


def test_cli_help_without_command(capsys) -> None:
    assert main([]) == 0
    assert "usage:" in capsys.readouterr().out


def test_cli_smoke_test(capsys) -> None:
    assert main(["smoke-test"]) == 0
    assert "cart-pole ready" in capsys.readouterr().out


def test_module_entry_point() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "invertedpen", "smoke-test"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "cart-pole ready" in result.stdout
