"""
Contains the following atmospheric functions:

 - alt = get_alt_for_density(density, density_units='slug/ft^3', alt_units='ft',
             nmax=20, tol=5.)
 - alt = get_alt_for_eas_with_constant_mach(equivalent_airspeed, mach,
             velocity_units='ft/s', alt_units='ft',
             nmax=20, tol=5.)
 - alt = get_alt_for_q_with_constant_mach(q, mach, pressure_units='psf', alt_units='ft',
             nmax=20, tol=5.)
 - alt = get_alt_for_pressure(pressure, pressure_units='psf', alt_units='ft',
             nmax=20, tol=5.)

All the default units are in English units because the source equations
are in English units.

"""
from __future__ import print_function, absolute_import
import numpy as np
from .atmosphere import atm_temperature, atm_pressure, atm_density
from .unit_conversion import convert_altitude, convert_velocity, convert_pressure


def get_alt_for_density(density, density_units='slug/ft^3', alt_units='ft', nmax=20, tol=5.):
    # type : (float, str, str, int) -> float
    """
    Gets the altitude associated with a given air density.

    Parameters
    ----------
    density : float
        the air density in slug/ft^3
    density_units : str; default='slug/ft^3'
        the density units; slug/ft^3, slinch/in^3, kg/m^3
    alt_units : str; default='ft'
        sets the units for the output altitude; ft, m, kft
    nmax : int; default=20
        max number of iterations for convergence
    tol : float; default=5.
        tolerance in alt_units

    Returns
    -------
    alt : float
        the altitude in feet

    """
    tol = convert_altitude(tol, alt_units, 'ft')
    dalt = tol  # ft
    alt_old = 0.
    alt_final = 5000.
    n = 0
    #density_scale = _density_factor(density_units, "slug/ft^3")

    # Newton's method
    while abs(alt_final - alt_old) > tol and n < nmax:
        alt_old = alt_final
        alt1 = alt_old
        alt2 = alt_old + dalt
        rho1 = atm_density(alt1, density_units=density_units)
        rho2 = atm_density(alt2, density_units=density_units)
        m = dalt / (rho2 - rho1)
        alt_final = m * (density - rho1) + alt1
        n += 1
    if abs(alt_final - alt_old) > tol:
        raise RuntimeError('Did not converge; Check your units; n=nmax=%s\n'
                           'target alt=%s alt_current=%s (ft)' % (nmax, alt_final, alt1))
    alt_out = convert_altitude(alt_final, 'ft', alt_units)
    return alt_out


def get_alt_for_eas_with_constant_mach(equivalent_airspeed, mach,
                                       velocity_units='ft/s', alt_units='ft', nmax=20, tol=5.):
    # type : (float, float, str, str, int, float) -> float
    """
    Gets the altitude associated with a equivalent airspeed.

    Parameters
    ----------
    equivalent_airspeed : float
        the equivalent airspeed in velocity_units
    mach : float
        the mach to hold constant
    alt_units : str; default='ft'
        the altitude units; ft, kft, m
    nmax : int; default=20
        max number of iterations for convergence
    tol : float; default=5.
        tolerance in alt_units

    Returns
    -------
    alt : float
        the altitude in alt units

    """
    equivalent_airspeed = convert_velocity(equivalent_airspeed, velocity_units, 'ft/s')
    tol = convert_altitude(tol, alt_units, 'ft')
    dalt = tol  # ft
    alt_old = 0.
    alt_final = 5000.
    n = 0

    gamma = 1.4
    R = 1716.
    z0 = 0.
    T0 = atm_temperature(z0)
    p0 = atm_pressure(z0)

    #eas = a * mach * sqrt((p * T0) / (T * p0))
    #    = sqrt(gamma * R * T) * mach * sqrt(T0 / p0) * sqrt(p / T)
    #    = sqrt(gamma * R) * mach * sqrt(T0 / p0) * sqrt(T) * sqrt(p / T)
    #    = sqrt(gamma * R * T0 / p0) * mach * sqrt(p)
    #    = k * sqrt(p)
    # rho0 = p0 / (R * T0)
    # k = sqrt(gamma / rho0) * mach
    k = np.sqrt(gamma * R * T0 / p0) * mach

    # Newton's method
    while abs(alt_final - alt_old) > tol and n < nmax:
        alt_old = alt_final
        alt1 = alt_old
        alt2 = alt_old + dalt
        press1 = atm_pressure(alt1)
        press2 = atm_pressure(alt2)
        eas1 = k * np.sqrt(press1)
        eas2 = k * np.sqrt(press2)
        m = dalt / (eas2 - eas1)
        alt_final = m * (equivalent_airspeed - eas1) + alt1
        n += 1

    if n > nmax - 1:
        print('n = %s' % n)
    alt_final = convert_altitude(alt_final, 'ft', alt_units)
    return alt_final


def get_alt_for_q_with_constant_mach(q, mach, pressure_units='psf', alt_units='ft',
                                     nmax=20, tol=5.):
    # type : (float, float, str, str, int, float) -> float
    """
    Gets the altitude associated with a dynamic pressure.

    Parameters
    ----------
    q : float
        the dynamic pressure lb/ft^2 (SI=Pa)
    mach : float
        the mach to hold constant
    pressure_units : str; default='psf'
        the pressure units; psf, psi, Pa, kPa, MPa
    alt_units : str; default='ft'
        the altitude units; ft, kft, m
    nmax : int; default=20
        max number of iterations for convergence
    tol : float; default=5.
        tolerance in alt_units

    Returns
    -------
    alt : float
        the altitude in alt_units

    """
    pressure = 2 * q / (1.4 * mach ** 2) # gamma = 1.4
    alt = get_alt_for_pressure(
        pressure, pressure_units=pressure_units, alt_units=alt_units, nmax=nmax, tol=tol)
    return alt


def get_alt_for_pressure(pressure, pressure_units='psf', alt_units='ft', nmax=20, tol=5.):
    # type : (float, str, str, int, float) -> float
    """
    Gets the altitude associated with a pressure.

    Parameters
    ----------
    pressure : float
        the pressure lb/ft^2 (SI=Pa)
    pressure_units : str; default='psf'
        the pressure units; psf, psi, Pa, kPa, MPa
    alt_units : str; default='ft'
        the altitude units; ft, kft, m
    nmax : int; default=20
        max number of iterations for convergence
    tol : float; default=5.
        tolerance in alt_units

    Returns
    -------
    alt : float
        the altitude in alt_units

    """
    pressure = convert_pressure(pressure, pressure_units, 'psf')
    tol = convert_altitude(tol, alt_units, 'ft')
    dalt = tol  # ft
    alt_old = 0.
    alt_final = 5000.
    n = 0

    # Newton's method
    while abs(alt_final - alt_old) > tol and n < nmax:
        alt_old = alt_final
        alt1 = alt_old
        alt2 = alt_old + dalt
        press1 = atm_pressure(alt1)
        press2 = atm_pressure(alt2)
        m = dalt / (press2 - press1)
        alt_final = m * (pressure - press1) + alt1
        n += 1

    if n > nmax - 1:
        print('n = %s' % n)
    #if abs(alt_final - alt_old) > tol:
        #raise RuntimeError('Did not converge; Check your units; n=nmax=%s\n'
                           #'target alt=%s alt_current=%s (ft)' % (nmax, alt_final, alt1))

    alt_final = convert_altitude(alt_final, 'ft', alt_units)
    return alt_final
