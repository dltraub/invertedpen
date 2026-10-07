# Software architecture

The project models and controls continuous-time dynamical systems while allowing
simulation details and physical hardware interfaces to evolve independently.

## Core flow

```text
configuration
    -> plant model (f, h)
    -> simulator
    -> controller / estimator
    -> logger
    -> offline analysis and visualization
```

Every plant implements the common continuous-time contract:

```text
xdot = f(x, u, p)
y     = h(x, p)
```

`x` is the plant state, `u` is the ideal plant input, `p` is a validated parameter
set, and `y` is an ideal physical output. Models also expose state/input/output
metadata and, where meaningful, energy and linearization functions.

## Main boundaries

- **Models** contain symbolic energy descriptions and generated numerical functions.
  They do not know about controllers, plotting, serial transport, or experiment
  scripts.
- **Simulation** advances a plant and records state, input, output, time, and
  diagnostics. The initial simulator uses fixed-step RK4 and zero-order-held inputs.
- **Control** consumes a model contract and sampled state/output data. The first
  controller is discrete-time LQR around the upright cart-pole equilibrium.
- **Estimation** is a later layer. Ideal physical outputs remain distinct from
  noisy, quantized, filtered, or delayed sensor outputs.
- **Configuration** loads and validates SI-valued model and experiment parameters.
- **Logging** writes a stable, self-describing trajectory representation including
  resolved configuration and reproducibility metadata.
- **Visualization** reads logged results and is independent of model and simulator
  internals.
- **I/O** is a later boundary for connecting the same control concepts to serial or
  embedded hardware. It must not leak hardware-specific behavior into the ideal
  mechanical plant.

## Initial implementation

The first concrete model is a two-dimensional cart-pole with
`x_state = [x, theta, x_dot, theta_dot]`, upright `theta = 0`, positive cart
direction to the right, positive angle counter-clockwise, and ideal horizontal
force input. Controller, sensor, and actuator updates initially run at 100 Hz.
Actuator dynamics, friction, delays, quantization, constraints, and noise will be
added later as explicit model components.

The architecture favors small composable interfaces over a fully general
port-Hamiltonian framework in the first milestone. The energy formulation remains
the source of the mechanical equations, while composition boundaries leave room
for actuator and sensor subsystems later.