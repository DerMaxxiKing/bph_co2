

def calc_air_density(theta, x=0, p=101300):
    """
    Calculates the density
    :param theta: temperature in °C
    :param x: humidity ratio [kg/kg]
    :param p: Absolute Pressure [Pa]
    :return: density wet air [kg / m³]
    """
    rho = (1 + x) / (x + 0.6222) * p / (461.40 * (theta + 273.15))  # Humid air density[kg / m³]
    return rho


def calc_c_p(x=0):
    return (925 * x + 503) / 500. * 1000


def calc_c02_emission(n_persons=0, emission_rate=0, internal_source=0, time=0):
    """

    :param n_persons:           # number of persons in the zone
    :param emission_rate:       # CO2 emission rate per person [mg/h]
    :param internal_source:     # emission rate of interal sources [mg/h]
    :param time:                # simulation time
    :return:
    """

    e = n_persons * emission_rate + internal_source
    return e


def calc_air_change_rate(time=None, room_volume=10, air_change_rate=0.5):
    """

    :param time: optional
    :param room_volume: [m³]
    :param air_change_rate: [1/h]
    :return: q [m³/h]
    """

    return room_volume * air_change_rate


def integrate_euler_explicit(x_t, dx_dt, dt):
    """
    Explicit euler integration

    x(t+1) = x(t) + dx/dt * dt

    :param x_t:         known value at timestep t
    :param dx_dt:       derivative dx/dt
    :param dt:          timestep
    :return:            x(t+1); solution for the time t+1
    """

    x_tp1 = x_t + dx_dt * dt

    return x_tp1


def calc_dc_dt(v, q, c_i, c_e, e):
    """
    calculates the derivative of the co2 concentration

    :param v:       room (or zone) volume (m3)
    :param q:       flow rate of outdoor or replacement air (m³/h)
    :param c_i:     CO2 concentration in the room (mg/m³);
    :param c_e:     CO2 concentration in outdoor air or replacement air (mg/m³);
    :param e:       CO2 emission rate of indoor sources (mg/h)
    :return:        derivative d c_i / dt
    """

    return (e - (c_i - c_e) * q) / v / 3600


def ppm_to_mg_m3(c_ppm, mol_mass=None, mol_vol=None):
    """
    converts concentration in ppm to concentration in mg/m³

    :param c_ppm:       concentration in ppm (parts per million)
    :param mol_mass:    molar mass of the component; default is 44.01 g/mol for CO2
    :param mol_vol:     molar volume of the component; default is 24.471 L/mol for CO2
    :return c_mg_m3:    concentration in mg/m³
    """

    # molar volume of 24,471 if None is given
    if mol_vol is None:
        mol_vol = 24.471

    # Molar mass of CO2 if None is given
    if mol_mass is None:
        mol_mass = 44.01

    c_mg_m3 = c_ppm * mol_mass / mol_vol

    return c_mg_m3


def mg_m3_to_ppm(c_mg_m3,  mol_mass=None, mol_vol=None):
    """
    converts concentration in ppm to concentration in mg/m³

    :param c_mg_m3:     concentration in mg/m³
    :param mol_mass:    molar mass of the component; default is 44.01 g/mol for CO2
    :param mol_vol:     molar volume of the component; default is 24.471 L/mol for CO2
    :return c_ppm:      concentration in ppm (parts per million)
    """

    # molar volume of 24,471 if None is given
    if mol_vol is None:
        mol_vol = 24.471

    # Molar mass of CO2 if None is given
    if mol_mass is None:
        mol_mass = 44.01

    c_ppm = c_mg_m3 * mol_vol / mol_mass

    return c_ppm

