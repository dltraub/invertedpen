# Design decisions

This document records decisions that affect the project architecture. Decisions
marked **MVP** are resolved for the first implementation. Items marked **unsolved**
are deliberately deferred and must be revisited before the related feature is
implemented.

## Resolved for the MVP

| Topic | Decision | Rationale |
|---|---|---|
| First system | Classical two-dimensional cart-pole | Smallest useful model for underactuated balance control |
| First hardware reference | Stepper-driven cart | Concrete future target without coupling the MVP to motor details |
| Coordinates | `q = [x, theta]`; `theta = 0` upright; positive `x` right; positive `theta` counter-clockwise | Fixed convention prevents sign and equilibrium ambiguity |
| State | `[x, theta, x_dot, theta_dot]` | Simple, documented mechanical state for initial controller work |
| Units | SI units; radians for angles | Consistent numerical and configuration conventions |
| Initial input | Ideal horizontal force in newtons | Keeps the first plant and LQR focused on mechanics |
| Actuator state | Not included initially | Ideal input is sufficient for the MVP |
| Plant output | Ideal physical output, separate from sensor output | Preserves a clean path to observers and realistic sensors |
| Timing | Controller, sensor, and actuator updates at 100 Hz | Matches the initial fixed sampled-data design |
| Input hold | Zero-order hold between updates | Natural representation of a digital controller command |
| Integrator | Fixed-step RK4 | Predictable and adequate for the initial non-stiff model |
| Mechanical derivation | Energy-based SymPy derivation | Supports validation and future mechanical variants |
| First controller | Discrete-time LQR around upright equilibrium | Provides a focused, testable balance-control milestone |
| Configuration | Validated configuration files using SI units | Makes experiments reproducible and parameters explicit |
| Visualization | Offline plots/animation from logged results | Keeps visualization independent from dynamics |

## Unsolved and intentionally deferred

These decisions are not needed to implement the MVP:

- truth-model command semantics: motor current, target velocity, step rate, or
  another actuator-level input;
- whether and when actuator states are added to the plant;
- motor torque limits, acceleration limits, missed-step behavior, backlash, and
  belt compliance;
- viscous, Coulomb, static, and track friction models;
- encoder model, sensor noise, quantization, filtering, and measurement delay;
- event handling for track limits and end stops;
- exact persistent log format and long-term schema versioning;
- adaptive or stiff numerical integration;
- energy-based swing-up versus iLQR versus nonlinear MPC;
- hybrid swing-up/balance switching conditions and recovery behavior;
- estimator API, covariance representation, initialization, and missing-data policy;
- embedded target, generated C code, and on-device MPC solver;
- parameter identification and sim-to-real calibration procedure;
- Furuta pendulum and other plant variants;
- hardware watchdog, emergency stop, homing, and safe-failure behavior.

Each deferred item should receive a new decision and corresponding tests when its
feature is brought into scope.