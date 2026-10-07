# Software requirements

## Purpose

The software shall provide a reproducible environment for deriving, simulating,
testing, and comparing control systems for an inverted pendulum. The initial
application is balance control of a classical pendulum mounted on a sliding cart,
with later support for more realistic actuators, sensors, hardware, and mechanical
variants.

## Initial functional requirements

The MVP shall:

1. Represent the cart-pole as a continuous-time plant
   `xdot = f(x, u, p), y = h(x, p)`.
2. Use the state ordering `[x, theta, x_dot, theta_dot]`, with `theta = 0` upright.
3. Use SI units, an ideal horizontal force input, and configurable physical
   parameters.
4. Derive the mechanical equations from energy expressions using SymPy and expose
   numerical functions usable by the simulator and controller.
5. Simulate the plant with a fixed-step RK4 integrator and zero-order-held input.
6. Run controller, sensor, and actuator updates at a common initial rate of 100 Hz.
7. Linearize the plant around the upright equilibrium and provide discrete-time LQR.
8. Log time, state, input, output, energy, resolved configuration, and run metadata.
9. Provide offline plots or animation from logged simulation data.
10. Include automated tests for model physics, linearization, simulation
    reproducibility, and closed-loop stabilization.

## Quality requirements

- Invalid physical parameters and incompatible dimensions must fail explicitly.
- Simulations with the same configuration and random seed must be reproducible.
- Ideal physical outputs must be separate from future sensor outputs.
- Model code must not depend on controller, visualization, or experiment scripts.
- Controllers must depend on the plant contract rather than a specific model
  implementation.
- Numerical tolerances, integration settings, and test scenarios must be explicit.
- Every feature must have focused tests; the full test suite must pass before a
  change is considered complete.

## MVP acceptance

A documented cart-pole configuration shall stabilize the pendulum from a defined
neighborhood of the upright equilibrium using discrete-time LQR. The run shall
produce a reproducible log and diagnostic plots, and the model tests shall verify
the upright equilibrium, energy conservation in the undamped unforced case, and
agreement between the nonlinear model and its local linearization.

## Future requirements

The following are intentionally outside the MVP: friction and detailed truth
models, stepper dynamics, sensor imperfections, delays, track constraints, state
estimation, swing-up, iLQR, nonlinear MPC, embedded deployment, code generation,
hardware safety integration, parameter identification, and additional mechanical
systems. They must be introduced through explicit requirements and tests when
their implementation is prioritized.