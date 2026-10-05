1. The starter kit won't get you there
Actuator: The kit's small DC motor and L293D H-bridge are too weak and have no feedback. Swing-up needs fast, repeatable acceleration of a cart or arm.
Angle sensor: The kit's potentiometer has a limited range and adds friction. A swing-up pendulum rotates continuously, so you need an incremental encoder or a magnetic encoder like the AS5600.
Multimeter: It's useful for debugging wiring, motor current and supply voltage. It can't measure anything dynamic. A cheap logic analyzer or just logging over serial is more useful.

A cheap setup that works:

Cart-pole: NEMA17 stepper with a TMC2209 or A4988 driver, a GT2 belt and a linear rail (3D-printer parts). The stepper gives you position and acceleration as a quasi-open-loop input, so you don't need a motor encoder. Add a ~600 PPR optical encoder or an AS5600 for the pendulum. The downside is track length and mechanical build effort.
Furuta (rotary) pendulum: A DC gearmotor with a built-in encoder plus a second encoder at the pendulum. It is mechanically more compact, but the nonlinear model is more involved.

Expect roughly 50–100 € in parts.

2. Can the Uno R4 run the MPC?

The R4 has a 48 MHz Cortex-M4 with FPU, 32 KB RAM and 256 KB flash. That is enough for a small linear MPC. It is not enough for real-time nonlinear MPC with a 1–2 s horizon.

Practical options:

PC-in-the-loop: The Arduino handles I/O (encoder, motor commands) and the MPC runs on your PC (CasADi, acados or similar), connected over USB serial. USB gives you roughly 1–2 ms latency. Avoid WiFi, because its latency jitter will hurt.
On-chip: Linear MPC for stabilization with an embedded QP solver such as TinyMPC or OSQP codegen, or explicit MPC. This is realistic for the balancing phase.

3. Swing-up itself

Swing-up is nonconvex, and NMPC from the hanging position has local minima. A short horizon can just rock the pendulum without ever reaching the top. Many practitioners use energy-based swing-up and switch to LQR or MPC near the top. Pure NMPC swing-up works with a long enough horizon, a good warm start and a terminal cost. The hybrid is a good fallback, and a comparison of the two is a nice learning exercise.

4. What bites people on hardware

Sim-to-real gap: Friction (Coulomb and viscous), backlash and unmodeled motor dynamics. Identify parameters from measured free-swing decay.
Actuator model: Decide early whether your input is force, acceleration, velocity or voltage. A stepper with an acceleration-limited step generator is easiest to model.
State estimation: Differentiating the encoder gives noisy velocity. Use an observer or Kalman filter.
Timing: Sampling jitter and computation delay matter. Fix the sample time (typically 5–20 ms) with a hardware timer, and compensate for the delay in the prediction model.
Constraints: Cart limits during swing-up are where MPC shines, and also where your hardware gets hit. Add end stops, software limits and a kill switch.
Encoder resolution and mechanics: Resolution, mounting play, wire drag and belt stretch all show up in the data.
Debugging: Log everything, and replay the data against your model offline.

5. Suggested path

Model the system and simulate it in Python (CasADi). Tune the MPC in simulation first.
Build the hardware, then identify parameters.
Stabilize at the top with LQR, then with linear MPC.
Run swing-up in simulation with NMPC and with the hybrid approach.
Move swing-up to hardware, initially with reduced limits, then loosen them.

If you tell me which mechanical variant you'd like (cart-pole or Furuta) and whether you want to run on the PC or on-chip, I can go deeper on the model or the solver setup.