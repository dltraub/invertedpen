# invertedpen

`invertedpen` is a Python project for deriving, simulating, and controlling an
inverted pendulum, starting with an energy-based cart-pole model.

## Getting started

Use the project’s `invpen` conda environment, then install the repository in
editable mode:

```bash
conda activate invpen
python -m pip install -e ".[dev]"
```

Editable installation makes the local `src/invertedpen` package available to
both the console command and `python -m` while developing.

## Running the project

The primary entry point is the installed console script:

```bash
invertedpen --help
invertedpen smoke-test
invertedpen simulate --steps 100 --dt 0.01
```

The equivalent module entry point is useful when selecting an interpreter
explicitly or debugging:

```bash
python -m invertedpen --help
python -m invertedpen smoke-test
python -m invertedpen simulate --steps 100 --dt 0.01
```

Both commands delegate to the same CLI implementation. Future simulation,
plotting, and experiment commands should be added as CLI subcommands rather
than as standalone source-file entry points.

The `simulate` command constructs the model and application, then runs a
bounded deterministic loop. The loop uses explicit `INIT`, `BALANCE`, `STOP`,
and `ERROR` states. The CLI is only responsible for parsing options and
starting the application; orchestration belongs under `src/invertedpen/app/`.

The initial state can be supplied as four values in the project state order
`[x, theta, x_dot, theta_dot]`:

```bash
python -m invertedpen simulate \
  --steps 100 \
  --initial-state 0.0 0.1 0.0 0.0
```

Alternatively, set only selected components; unspecified components remain
zero:

```bash
python -m invertedpen simulate \
  --steps 100 \
  --initial-theta 0.1 \
  --initial-x-dot 0.2
```

The individual options are `--initial-x`, `--initial-theta`,
`--initial-x-dot`, and `--initial-theta-dot`. If both forms are used, the
individual options override the corresponding values from `--initial-state`.

Simulations log by default to a timestamped directory under
`artifacts/runs/`. Each run contains a `trajectory.npz` file with named NumPy
arrays and a `metadata.json` manifest containing the resolved configuration,
signal units, random seeds, and Git/runtime provenance:

```bash
python -m invertedpen simulate --steps 100 --tag balance-test
```

Use `--log-dir` to select another output directory or `--no-log` for a
non-persistent run. Completed logged simulations show four state plots by
default in one figure with vertically stacked, shared-x subplots. Angles are
shown in unwrapped degrees. Use `--separate-windows` for one window per signal,
or `--no-plot` to suppress plotting. A control-input subplot is included when
the saved controller is not `zero_input`. Logged input samples follow the
zero-order-hold convention:
`input[k]` is held over the interval from `time[k]` to `time[k+1]`; the final
sample repeats the last held input.

Previously saved runs can be plotted without starting a simulation. By default,
`plot` selects the most recent run:

```bash
python -m invertedpen plot
```

Select a tag and log directory explicitly, and optionally use separate windows:

```bash
python -m invertedpen plot \
  --tag balance-test \
  --log-dir artifacts/runs \
  --separate-windows
```


## Testing

```bash
python -m pytest
```

## Project structure

- `src/invertedpen/`: installable Python package.
- `src/invertedpen/models/`: physical plant models and symbolic derivations.
- `src/scripts/`: exploratory scripts, not public entry points.
- `src/tools/`: supporting numerical tools.
- `tests/`: automated model and CLI tests.
- `docs/`: requirements and architecture decisions.

## Conventions
q = [x, theta]
x_state = [x, theta, x_dot, theta_dot]
theta = 0 means upright
positive x is to the right
positive theta is counter-clockwise

## Contributing
Development conventions and contribution process.