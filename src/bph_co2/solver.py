import numpy as np
import pandas as pd
from pandasgui import show


class CO2_Simulation(object):

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name', f'Unnamed Simulation')               # zone volume in m³

        self.volume = kwargs.get('volume', 5 * 5 * 3)                       # zone volume in m³

        self.n_persons = kwargs.get('n_persons', 1)                         # number of persons in the room
        self.co2_emission_rate = kwargs.get('emission_rate', 27000)         # co2 emission rate per person in mg/h

        self.internal_co2_source = kwargs.get('internal_co2_source', 0)     # co2 emission rate of internal sources in mg/h

        self.time = kwargs.get('time', 0)

        self.outdoor_temperature = kwargs.get('outdoor_temperature', 10)    # outdoor temperature in °C
        self.indoor_temperature = kwargs.get('indoor_temperature', 20)      # indoor temperature in °C

        self.windows = kwargs.get('windows', [])

        # air change
        self.air_change_rate = kwargs.get('air_change_rate', 0.5)            # air change rate in m³/h

        # initial state:

        self.c0i_ppm = kwargs.get('c0i', 400)                  # initial CO2-concentration in the room/zone in ppm
        self.c0i_mg_m3 = ppm_to_mg_m3(self.c0i_ppm)

        self.c0e_ppm = kwargs.get('c0e', 400)                  # initial outdoor CO2-concentration in ppm
        self.c0e_mg_m3 = ppm_to_mg_m3(self.c0e_ppm)

        # simulation parameters:

        self.timestep = kwargs.get('timestep', 360)                     # timestep [s]
        self.t_end = kwargs.get('t_end', 26640)                         # End time [s]
        self.write_interval = kwargs.get('write_interval', 5)           # Write results each write_interval timestep

    def calculate(self):

        n_steps = int(np.floor(self.t_end / self.timestep))

        time = np.arange(n_steps) * self.timestep
        c_mg_m3 = np.empty(n_steps+1)
        n_persons = np.empty(n_steps)
        e = np.empty(n_steps)
        air_change_rate = np.empty(n_steps)
        q = np.empty(n_steps)
        internal_co2_source = np.empty(n_steps)
        indoor_temperature = np.empty(n_steps)
        outdoor_temperature = np.empty(n_steps)

        c_mg_m3[0] = self.c0i_mg_m3

        for i in range(n_steps):

            print(f'Calculating timestep {i}: time: {time[i]} s')

            t = time[i]

            #############################################################
            # calculate current boundary conditions
            #############################################################

            if hasattr(self.n_persons, 'current_value'):
                n_persons[i] = self.n_persons.current_value(t)
            else:
                n_persons[i] = self.n_persons

            if hasattr(self.air_change_rate, 'current_value'):
                air_change_rate[i] = self.air_change_rate.current_value(t)
            else:
                air_change_rate[i] = self.air_change_rate

            if hasattr(self.internal_co2_source, 'current_value'):
                internal_co2_source[i] = self.internal_co2_source.current_value(t)
            else:
                internal_co2_source[i] = self.internal_co2_source

            if hasattr(self.indoor_temperature, 'current_value'):
                indoor_temperature[i] = self.indoor_temperature.current_value(t)
            else:
                indoor_temperature[i] = self.indoor_temperature

            if hasattr(self.outdoor_temperature, 'current_value'):
                outdoor_temperature[i] = self.outdoor_temperature.current_value(t)
            else:
                outdoor_temperature[i] = self.outdoor_temperature


            # -----------------------------------------------------------------------------
            # air change
            # -----------------------------------------------------------------------------

            q_win = 0
            for window in self.windows:
                q_win_i = window.q(time=t,
                                   t_i=indoor_temperature[i],
                                   t_e=outdoor_temperature[i])
                q_win += q_win_i

            # air change windows:
            q_win = sum([x.q(time=t,
                             t_i=indoor_temperature[i],
                             t_e=outdoor_temperature[i]) for x in self.windows])

            q_ven = self.volume * air_change_rate[i]
            q[i] = q_ven + q_win

            # calculate co2 emission rate
            e[i] = calc_c02_emission(n_persons=n_persons[i],
                                     emission_rate=self.co2_emission_rate,
                                     internal_source=internal_co2_source[i])

            # calculate derivative:
            dc_dt = calc_dc_dt(v=self.volume,
                               q=q[i],
                               c_i=c_mg_m3[i],
                               c_e=self.c0e_mg_m3,
                               e=e[i]
                               )

            c_mg_m3[i+1] = integrate_euler_explicit(x_t=c_mg_m3[i],
                                                    dx_dt=dc_dt,
                                                    dt=self.timestep)

        res = Result(time=time,
                     n_persons=n_persons,
                     ci_mg_m3=c_mg_m3,
                     e=e,
                     internal_co2_source=internal_co2_source,
                     q=q,
                     air_change_rate=air_change_rate)

        return res


class Result(object):

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name', '')                                      # name time
        self.time = kwargs.get('time', None)                                    # Simulation time
        self.n_persons = kwargs.get('n_persons', None)                          # number of persons in the room
        self._ci_ppm = kwargs.get('ci_ppm', None)                               # CO2-concentration in the room/zone in ppm
        self._ci_mg_m3 = kwargs.get('ci_mg_m3', None)                           # CO2-concentration in the room/zone in ppm
        self.internal_co2_source = kwargs.get('internal_co2_source', None)      # internal_co2_source in mg/h
        self.e = kwargs.get('e', None)                                          # CO2 emission in the room/zone in ppm
        self.q = kwargs.get('q', None)                                          # fresh air volume flow
        self.air_change_rate = kwargs.get('air_change_rate', None)              # air_change_rate

        self._df = None

    @property
    def df(self):
        if self._df is None:

            self._df = pd.DataFrame({'Time': self.time,
                                     'n_persons': self.n_persons[0:self.time.shape[0]],
                                     'CO2_ppm': self.ci_ppm[0:self.time.shape[0]],
                                     'CO2_mg_m3': self.ci_mg_m3[0:self.time.shape[0]],
                                     'e': self.e[0:self.time.shape[0]],
                                     'internal CO2 source': self.internal_co2_source[0:self.time.shape[0]],
                                     'fresh air volume flow': self.q[0:self.time.shape[0]],
                                     'air change rate': self.air_change_rate[0:self.time.shape[0]]}
                                    )

        return self._df

    @property
    def ci_mg_m3(self):
        if self._ci_mg_m3 is not None:
            return self._ci_mg_m3
        elif self.ci_ppm is not None:
            self._ci_mg_m3 = ppm_to_mg_m3(self.ci_ppm)

    @ci_mg_m3.setter
    def ci_mg_m3(self, value):
        self._ci_mg_m3 = value

    @property
    def ci_ppm(self):
        if self._ci_ppm is not None:
            return self._ci_ppm
        elif self._ci_mg_m3 is not None:
            self._ci_ppm = mg_m3_to_ppm(self._ci_mg_m3)
            return self._ci_ppm

    @ci_ppm.setter
    def ci_ppm(self, value):
        self._ci_ppm = value

    def plot(self):

        show(self.df, settings={'block': True})


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
        mol_mass=44.01

    c_ppm = c_mg_m3 * mol_vol / mol_mass

    return c_ppm
