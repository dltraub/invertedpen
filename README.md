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
```

The equivalent module entry point is useful when selecting an interpreter
explicitly or debugging:

```bash
python -m invertedpen --help
python -m invertedpen smoke-test
```

Both commands delegate to the same CLI implementation. Future simulation,
plotting, and experiment commands should be added as CLI subcommands rather
than as standalone source-file entry points.

`src/scripts/maintest.py` is retained as exploratory code. It is not the
project entry point; if run directly, it expects the package to have been
installed first.

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