"""Display the four state plots for one persisted simulation run."""

from __future__ import annotations

import argparse

from invertedpen.plotting import plot_run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_path")
    args = parser.parse_args()
    plot_run(args.run_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())