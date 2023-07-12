from Traj_planning.traj_3ST.coupled_pol_interpolation import *
from Traj_planning.traj_3ST.diff_flat import *
from Traj_planning.traj_3ST.auxiliar_codes.plot_traj import *

from copy import deepcopy


def trajenerator_3ST(states, env_params, rocket_params, controller_params):
    """Function that takes the desired states and constraints and returns the trajectory parameters.

    Args:
        states (dict): Dictionary containing the desired states. The path points shall be in x, y and z lists, and the 
            time points shall be in t list. The lists shall have the same length and the time points shall be equally
            spaced. Currently, the initial and final velocities and accelerations are 0.
        env_params (dict): Dictionary containing the environment parameters. Currently g is used.
        rocket_params (dict): Dictionary containing the rocket parameters. Currently m, l_tvc and J_z are used.
        controller_params (dict): Dictionary containing the controller parameters. Currently dt, thrust and delta_tvc
            constraints are being used.

    Returns:
        trajectory_parameters (dict): Dictionary containing the trajectory parameters.
    """
    # interpolate polinomials for minimum snap trajectory
    Px_coeffs, Py_coeffs, Pz_coeffs, t = coupled_pol_interpolation(
        states, rocket_params, controller_params, env_params
    )

    # calculate gamma using differential flatness
    trajectory_params = diff_flat_traj(
        Px_coeffs, Py_coeffs, Pz_coeffs, t, env_params, rocket_params, controller_params
    )

    plot_trajectory(states, trajectory_params, controller_params, "Diff flat trajectory")

    return trajectory_params
