"""unused"""
import casadi as ca


def make_step(dynamics, dt):
    """Perfrom RK4 integration step"""
    
    x = ca.SX.sym("x", 4)
    u = ca.SX.sym("u", 1)
    k1 = dynamics(x, u)
    k2 = dynamics(x + dt/2 * k1, u)
    k3 = dynamics(x + dt/2 * k2, u)
    k4 = dynamics(x + dt * k3, u)
    x_next = x + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
    return ca.Function("step", [x, u], [x_next])