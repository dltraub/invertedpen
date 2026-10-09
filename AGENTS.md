
# Project Goal
In this project I want to simulate an inverted pendulum on a cart with the goal of playing with and testing control systems. I want to set up a running simulation and based thereon decide on mechanical system architecture to build the system in real and run it on a microcontroller.

## Software Design
The main programming language is Python. Selected interpreter should be in the local conda env 'invpen', which contains all packages specified in requirements.txt.
I want to derive the equations of motion symbolically with SymPy (sympy.physics.mechanics, Lagrange or Kane). For numerics, automatic differentiation, integrators, NLP, eventual C code generation for the real system I want to use CasADI. Linearization, LQR and analysis can be done with SciPy.
Define every plant as a continuous-time system

ẋ = f(x, u, p), y = h(x, p)

and make everything else (simulation, controller, estimator) depend only on that interface. I want physical models to be easily interchangable. 

Here is a suggested architecture:
src/
  models/        # symbolic derivation → CasADi Functions, one file per system
    cartpole.py, furuta.py
    actuators.py   # force / accel / dc_motor / stepper
    friction.py
  params/        # YAML per hardware variant (masses, lengths, motor constants)
  sim/           # integrator (RK4 or CVODES), sensor noise, quantization, delay
  estimation/    # observer / Kalman filter
  control/       # lqr.py, energy_swingup.py, mpc_linear.py, mpc_nonlinear.py
  io/            # SimInterface and SerialInterface (Arduino) with the same API
  experiments/   # scripts + logging

I want to use unit tests from the start, for example to check energy conservation without damping and compare linearizations against the nonlinear model.
I want to parameterize everything through config files.
I want a logger to track outputs into a universal format every simulation so that I can compare them easily.

## Mechanical Design
To start, I want a classical pendulum-on-a-cart system with a sliding cart. The pendulum has one DoF, a revolute joint which connects with the cart. The whole system is modeled in 2D. 
Along the road I want to model friction but it is not necessary initially. Other models like Furata pendulum I want to test later on.

## Modeling
Use two models: a detailed "truth" plant in the simulator (friction, delay, quantization, noise) and a simpler design model inside the controller to test robustness before touching hardware.
Write each system as an energy description and derive the dynamics generically:

- generalized coordinates q
- kinetic energy T(q, q̇) and potential energy V(q)
- dissipation (Rayleigh function) and generalized forces from the actuator

One function turns (T, V, R, Q) into the Euler–Lagrange equations. A new mechanical variant then only needs a new energy expression.
Model the actuator as a separate subsystem and connect it to the mechanics, in the spirit of a port-Hamiltonian interconnection.

## Control System
The first control subproblem is to perform balance control around an upright equilibrium of the pendulum via LQR control. Afterwards come swing-up control with iLQR and MPC and a state estimator (kalman filter or observer).


## Animation
I want a way to view animated simulation runs offline. Matplotlib FuncAnimation could be useful. Visualization should be a stand-alone module independent from dynamics.

## Planning

Don't implement anything yet. Help me identify missing requirements and ambiguities.

## Testing

- Every new feature must have tests.
- Run the relevant tests after making changes.
- Run the full test suite before declaring a task complete.

## Scope

- Don't modify unrelated files.
- If a requirement is ambiguous, ask before making
  a significant architectural decision.
- Don't change the project's architecture without
  discussing it first.

## Agreed MVP conventions

The first implementation is a balance-control simulation for a classical cart-pole.
The first physical reference target is a stepper-driven cart, but actuator-specific
behavior is deliberately deferred.

### Coordinates and state

- The model is two-dimensional with generalized coordinates `q = [x, theta]`.
- `x` is cart position; positive `x` points to the right.
- `theta` is the pendulum angle; `theta = 0` is upright and positive rotation is
  counter-clockwise.
- The continuous state is ordered as
  `x_state = [x, theta, x_dot, theta_dot]`.
- Angles are represented in radians and positions in meters. SI units are used
  throughout the project.
- The initial plant has ideal horizontal force input `u`, with force in newtons.
- The initial plant state contains only mechanical states; actuator states are not
  included.

### Plant and simulation boundary

Every plant exposes continuous-time dynamics:

```text
xdot = f(x, u, p)
y     = h(x, p)
```

For the MVP, `u` is an ideal force, `y` is the ideal physical output, and the
simulator uses a fixed 100 Hz controller/sensor/actuator update rate with
zero-order-held input. A fixed-step RK4 integrator is the initial numerical
method. The integration step is a configurable subdivision of the control period.

Sensor noise, quantization, delays, actuator dynamics, friction, track limits, and
stepper-specific behavior are not part of the MVP. They will be added as explicit
composition layers rather than hidden in the mechanical model. In particular,
ideal outputs and later sensor outputs must remain separate quantities.

### MVP scope and acceptance criteria

The first milestone includes:

- a symbolic cart-pole derivation from kinetic energy, potential energy, dissipation,
  and generalized force;
- a numerical plant interface usable by a simulator and controller;
- configurable physical parameters;
- fixed-step simulation and universal trajectory logging;
- upright-equilibrium linearization and discrete-time LQR;
- offline state/input/energy plots;
- tests for equilibrium correctness, energy conservation without damping, numerical
  linearization agreement, LQR stabilization, and deterministic replay.

The MVP is complete when a reproducible simulation can stabilize the pendulum from
an explicitly documented neighborhood of the upright equilibrium and all targeted
tests pass.

## Deferred decisions

The following are intentionally unsolved because they are not required for the MVP:

- truth-model actuator input semantics such as motor current, target velocity, or
  step frequency;
- actuator state augmentation, motor dynamics, missed steps, backlash, and belt
  compliance;
- friction laws beyond the initial ideal/no-damping model;
- sensor noise, encoder quantization, filtering, and measurement delay;
- cart track limits, collision/event handling, and constrained MPC;
- energy swing-up, iLQR, nonlinear MPC, and hybrid mode-switching policy;
- state estimators and their sensor/covariance interfaces;
- embedded deployment, C code generation, and on-device MPC;
- Furuta and other mechanical variants;
- parameter identification and sim-to-real calibration;
- the final persistent log file format;
- adaptive/stiff integration and real-time execution;
- hardware watchdog, emergency-stop, homing, and safe-failure procedures.