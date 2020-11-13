import numpy as np
import pandas as pd
from pandasgui import show
from .tools import calc_air_density, calc_c_p
from progress.bar import Bar, ChargingBar
import multiprocessing as mp


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
                     name=self.name,
                     zone=self)

        res_entries = [{'name': 'n_persons', 'data': n_persons, 'df_name': 'Number of Persons'},
                       {'name': 'c_mg_m3', 'data': c_mg_m3, 'df_name': 'CO2 [mg/m³]'},
                       {'name': 'c_ppm', 'data': mg_m3_to_ppm(c_mg_m3), 'df_name': 'CO2 [ppm]'},
                       {'name': 'e', 'data': e, 'df_name': 'Total CO2 emission [mg/h]'},
                       {'name': 'internal_co2_source', 'data': internal_co2_source,
                        'df_name': 'Internal CO2 source [mg/h]'},
                       {'name': 'q', 'data': q, 'df_name': 'Total fresh air volume flow [m³/h]'},
                       {'name': 'air_change_rate', 'data': air_change_rate, 'df_name': 'Air change rate [1/h]'},
                       {'name': 'outdoor_temperature', 'data': outdoor_temperature,
                        'df_name': 'Outdoor temperature [°C]'},
                       {'name': 'indoor_temperature', 'data': indoor_temperature, 'df_name': 'Indoor temperature [°C]'}
                       ]

        for entry in res_entries:
            res.add_result(**entry)

        return res


class Solver(object):

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name', f'Unnamed Simulation')       # name of the simulation
        self.zone = kwargs.get('zone', None)                        # name of the simulation

        self.timestep = kwargs.get('timestep', 60)                  # timestep [s]
        self.t_end = kwargs.get('t_end', 26640)                     # End time [s]

    def calc_dtheta_dt(self, theta_room, time):

        # heat flows walls:
        phi_walls = 0
        for i, wall in enumerate(self.zone.walls):
            if wall.theta_s is None:
                f = wall.r_si * wall.alpha_k
                theta_out = wall.theta_out
                phi_wall = wall.area * wall.u * wall.r_si * wall.alpha_k
            else:
                f = 1
                theta_out = wall.theta_s
                phi_wall = wall.area * wall.alpha_k

            if hasattr(theta_out, 'current_value'):
                theta_out = theta_out.current_value(time)
            else:
                theta_out = theta_out

            phi_walls += phi_wall * (theta_out - theta_room)

        if hasattr(self.zone.air_change_rate, 'current_value'):
            air_change_rate = self.zone.air_change_rate.current_value(time)
        else:
            air_change_rate = self.zone.air_change_rate

        if hasattr(self.zone.ventilation.t_in, 'current_value'):
            t_supply_air = self.zone.ventilation.t_in.current_value(time)
        else:
            t_supply_air = self.zone.ventilation.t_in

        phi_ventilation = (air_change_rate * self.zone.volume / 3600) * self.zone.ventilation.c_p() * self.zone.ventilation.supply_air_density() * (t_supply_air - theta_room)

        # internal convective heat sources:
        phi_int_c = 0
        for i, int_c in enumerate(self.zone.phi_int_c):
            if hasattr(int_c, 'current_value'):
                int_c = int_c.current_value(time=0)
            else:
                int_c = int_c
            phi_int_c += int_c

        phi_hc_id = 0
        for i, hc_id in enumerate(self.zone.phi_hc_id):
            if hasattr(hc_id, 'current_value'):
                hc_id = hc_id.current_value(time=0)
            else:
                hc_id = hc_id
            phi_hc_id += hc_id

        air_density = calc_air_density(theta=theta_room, x=0, p=101300)
        c_p = calc_c_p(x=0)
        dtheta_dt = (phi_walls + phi_ventilation + phi_int_c + phi_hc_id) / (air_density * c_p * self.zone.volume)

        return dtheta_dt

    def calc_transient_room_temperature(self):

        n_steps = int(np.floor(self.t_end / self.timestep))
        time = np.arange(n_steps) * self.timestep
        theta = np.empty(n_steps+1)
        theta[0] = self.zone.theta_0

        for i in range(n_steps):
            print('-------------------------------------------------------------------')
            print(f'Calculating timestep {i}: time = {time[i]} s')
            dtheta_dt = self.calc_dtheta_dt(theta_room=theta[i], time=time[i])
            theta[i+1] = theta[i] + self.timestep * dtheta_dt
            print(f'dtheta_dt: {dtheta_dt} K/s')
            print(f'theta(time[i]+1): {theta[i+1]} °C')

        pass

    def calc_transient_co2_concentration(self):

        n_steps = int(np.floor(self.t_end / self.timestep))

        time = np.arange(n_steps) * self.timestep
        c_mg_m3 = np.empty(n_steps + 1)
        n_persons = np.empty(n_steps)
        e = np.empty(n_steps)
        air_change_rate = np.empty(n_steps)
        q = np.empty(n_steps)
        internal_co2_source = np.empty(n_steps)
        indoor_temperature = np.empty(n_steps)
        outdoor_temperature = np.empty(n_steps)

        c_mg_m3[0] = self.zone.c0i_mg_m3

        bar = Bar('Processing', max=n_steps)

        for i in range(n_steps):

            bar.next()

            # print(f'Calculating timestep {i}: time: {time[i]} s')

            t = time[i]

            #############################################################
            # calculate current boundary conditions
            #############################################################

            if hasattr(self.zone.n_persons, 'current_value'):
                n_persons[i] = self.zone.n_persons.current_value(t)
            else:
                n_persons[i] = self.zone.n_persons

            if hasattr(self.zone.air_change_rate, 'current_value'):
                air_change_rate[i] = self.zone.air_change_rate.current_value(t)
            else:
                air_change_rate[i] = self.zone.air_change_rate

            if hasattr(self.zone.internal_co2_source, 'current_value'):
                internal_co2_source[i] = self.zone.internal_co2_source.current_value(t)
            else:
                internal_co2_source[i] = self.zone.internal_co2_source

            if hasattr(self.zone.indoor_temperature, 'current_value'):
                indoor_temperature[i] = self.zone.indoor_temperature.current_value(t)
            else:
                indoor_temperature[i] = self.zone.indoor_temperature

            if hasattr(self.zone.outdoor_temperature, 'current_value'):
                outdoor_temperature[i] = self.zone.outdoor_temperature.current_value(t)
            else:
                outdoor_temperature[i] = self.zone.outdoor_temperature

            # -----------------------------------------------------------------------------
            # air change
            # -----------------------------------------------------------------------------

            q_win = 0
            for window in self.zone.windows:
                q_win_i = window.q(time=t,
                                   t_i=indoor_temperature[i],
                                   t_e=outdoor_temperature[i])
                q_win += q_win_i

            # air change windows:
            q_win = sum([x.q(time=t,
                             t_i=indoor_temperature[i],
                             t_e=outdoor_temperature[i]) for x in self.zone.windows])

            q_ven = self.zone.volume * air_change_rate[i]
            q[i] = q_ven + q_win

            # calculate co2 emission rate
            e[i] = calc_c02_emission(n_persons=n_persons[i],
                                     emission_rate=self.zone.co2_emission_rate,
                                     internal_source=internal_co2_source[i])

            # calculate derivative:
            dc_dt = calc_dc_dt(v=self.zone.volume,
                               q=q[i],
                               c_i=c_mg_m3[i],
                               c_e=self.zone.c0e_mg_m3,
                               e=e[i]
                               )

            c_mg_m3[i + 1] = integrate_euler_explicit(x_t=c_mg_m3[i],
                                                      dx_dt=dc_dt,
                                                      dt=self.timestep)

        bar.finish()

        res = Result(time=time,
                     name=self.name,
                     zone=self.zone)

        res_entries = [{'name': 'n_persons', 'data': n_persons, 'df_name': 'Number of Persons'},
                       {'name': 'c_mg_m3', 'data': c_mg_m3, 'df_name': 'CO2 [mg/m³]'},
                       {'name': 'c_ppm', 'data': mg_m3_to_ppm(c_mg_m3), 'df_name': 'CO2 [ppm]'},
                       {'name': 'e', 'data': e, 'df_name': 'Total CO2 emission [mg/h]'},
                       {'name': 'internal_co2_source', 'data': internal_co2_source, 'df_name': 'Internal CO2 source [mg/h]'},
                       {'name': 'q', 'data': q, 'df_name': 'Total fresh air volume flow [m³/h]'},
                       {'name': 'air_change_rate', 'data': air_change_rate, 'df_name': 'Air change rate [1/h]'},
                       {'name': 'outdoor_temperature', 'data': outdoor_temperature, 'df_name': 'Outdoor temperature [°C]'},
                       {'name': 'indoor_temperature', 'data': indoor_temperature, 'df_name': 'Indoor temperature [°C]'}
                       ]

        for entry in res_entries:
            res.add_result(**entry)

        return res

    def calc_transient_co2_temperature(self):

        n_steps = int(np.floor(self.t_end / self.timestep))
        time = np.arange(n_steps) * self.timestep

        c_mg_m3 = np.empty(n_steps + 1)
        n_persons = np.empty(n_steps)
        e = np.empty(n_steps)                           #
        air_change_rate = np.empty(n_steps)             # air change rate ventilation [1/h]
        q = np.empty(n_steps)                           # Total fresh air volume flow (ventilation + windows) [m³/h]
        internal_co2_source = np.empty(n_steps)         # internal co2 source [mg/h]
        indoor_temperature = np.empty(n_steps+1)        # zone temperature [K]
        outdoor_temperature = np.empty(n_steps)         # ambient temperature [K]
        t_supply_air = np.empty(n_steps)                # temperature of the ventilation supply air [K]
        phi = np.empty(n_steps)                         # sum heat flows for energy balance [W]
        dtheta_dt = np.empty(n_steps)                   # derivative of the room temperature [K/s]
        q_win = np.empty(n_steps)                       # air flow through windows [m³/h]

        #############################################################
        # calculate boundary conditions for calculated timesteps
        #############################################################

        timeseries = [self.zone.n_persons,
                      self.zone.air_change_rate,
                      self.zone.internal_co2_source,
                      self.zone.indoor_temperature,
                      self.zone.outdoor_temperature]

        parallel = False

        print('\nCalculating boundary conditions ...\n')
        if parallel:
            pool = mp.Pool(mp.cpu_count())
            results = [pool.apply(get_bc_for_times, args=(time, ts)) for ts in timeseries]
        else:
            results = []
            for ts in timeseries:
                results.append(get_bc_for_times(time, ts))
        print('\nFinished calculating boundary conditions ...\n')
        n_persons[:] = results[0]
        air_change_rate[:] = results[1]
        internal_co2_source[:] = results[2]
        indoor_temperature[:] = results[3]
        outdoor_temperature[:] = results[4]

        indoor_temperature[0] = self.zone.theta_0
        c_mg_m3[0] = self.zone.c0i_mg_m3

        with ChargingBar('Processing', max=n_steps) as bar:
            for i in range(n_steps):

                bar.next()

                # print(f'Calculating timestep {i}: time: {time[i]} s')

                t = time[i]

                ############################################################################################################
                #
                #   Air change and CO2 concentration
                #
                ############################################################################################################

                # air change windows:
                q_win[i] = sum([x.q(time=t,
                                    t_i=indoor_temperature[i],
                                    t_e=outdoor_temperature[i]) for x in self.zone.windows])

                q_ven = self.zone.volume * air_change_rate[i]
                q[i] = q_ven + q_win[i]

                # calculate co2 emission rate
                e[i] = calc_c02_emission(n_persons=n_persons[i],
                                         emission_rate=self.zone.co2_emission_rate,
                                         internal_source=internal_co2_source[i])

                # calculate derivative of co2 concentration:
                dc_dt = calc_dc_dt(v=self.zone.volume,
                                   q=q[i],
                                   c_i=c_mg_m3[i],
                                   c_e=self.zone.c0e_mg_m3,
                                   e=e[i]
                                   )

                c_mg_m3[i + 1] = integrate_euler_explicit(x_t=c_mg_m3[i],
                                                          dx_dt=dc_dt,
                                                          dt=self.timestep)

                # heat flows walls:
                phi_walls = 0
                for wall in self.zone.walls:
                    if wall.theta_s is None:
                        theta_out = wall.theta_out
                        phi_wall = wall.area * wall.u * wall.r_si * wall.alpha_k
                    else:
                        theta_out = wall.theta_s
                        phi_wall = wall.area * wall.alpha_k

                    if hasattr(theta_out, 'current_value'):
                        theta_out = theta_out.current_value(t)
                    else:
                        theta_out = theta_out

                    phi_walls += phi_wall * (theta_out - indoor_temperature[i])

                if hasattr(self.zone.ventilation.t_in, 'current_value'):
                    t_supply_air[i] = self.zone.ventilation.t_in.current_value(t)
                else:
                    t_supply_air[i] = self.zone.ventilation.t_in

                phi_ventilation = (q_ven / 3600) * self.zone.ventilation.c_p() * self.zone.ventilation.supply_air_density(theta=t_supply_air[i]) * (t_supply_air[i] - indoor_temperature[i])
                phi_windows = (q_win[i] / 3600) * calc_c_p(x=0) * calc_air_density(theta=outdoor_temperature[i]) * (outdoor_temperature[i] - indoor_temperature[i])

                # internal convective heat sources:
                phi_int_c = 0
                for int_c in self.zone.phi_int_c:
                    if hasattr(int_c, 'current_value'):
                        int_c = int_c.current_value(time=t)
                    else:
                        int_c = int_c
                    phi_int_c += int_c

                phi_hc_id = 0
                for hc_id in self.zone.phi_hc_id:
                    if hasattr(hc_id, 'current_value'):
                        hc_id = hc_id.current_value(time=t)
                    else:
                        hc_id = hc_id
                    phi_hc_id += hc_id

                air_density = calc_air_density(theta=indoor_temperature[i], x=0, p=101300)
                c_p = calc_c_p(x=0)
                phi[i] = phi_walls + phi_ventilation + phi_windows + phi_int_c + phi_hc_id
                dtheta_dt[i] = (phi[i]) / (air_density * c_p * self.zone.volume)

                indoor_temperature[i + 1] = indoor_temperature[i] + self.timestep * dtheta_dt[i]

                ############################################################################################################
                #
                #   create result
                #
                ############################################################################################################

        bar.finish()

        res = Result(time=time,
                     name=self.name,
                     zone=self.zone)

        res_entries = [{'name': 'n_persons', 'data': n_persons, 'df_name': 'Number of Persons'},
                       {'name': 'c_mg_m3', 'data': c_mg_m3, 'df_name': 'CO2 [mg/m³]'},
                       {'name': 'c_ppm', 'data': mg_m3_to_ppm(c_mg_m3), 'df_name': 'CO2 [ppm]'},
                       {'name': 'e', 'data': e, 'df_name': 'Total CO2 emission (persons + source) [mg/h]'},
                       {'name': 'internal_co2_source', 'data': internal_co2_source,
                        'df_name': 'Internal CO2 source [mg/h]'},
                       {'name': 'q', 'data': q, 'df_name': 'Total fresh air volume flow (ventilation + windows) [m³/h]'},
                       {'name': 'air_change_rate', 'data': air_change_rate, 'df_name': 'Air change rate [1/h]'},
                       {'name': 'outdoor_temperature', 'data': outdoor_temperature,
                        'df_name': 'Outdoor temperature [°C]'},
                       {'name': 'indoor_temperature', 'data': indoor_temperature,
                        'df_name': 'Indoor temperature [°C]'},
                       {'name': 'phi', 'data': phi, 'df_name': 'Sum heat flows [W]'},
                       {'name': 'dtheta_dt', 'data': dtheta_dt, 'df_name': 'd θ/dt [K/s]'},
                       {'name': 'q_win', 'data': q_win, 'df_name': 'Air flow over windows [m³/h]'},
                       ]

        for entry in res_entries:
            res.add_result(**entry)

        return res


class Result(object):

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name', '')                                      # name time
        self.time = kwargs.get('time', None)                                    # Simulation time

        self.zone = kwargs.get('zone', None)                                    # The zone to simulate

        self._df = None

    @property
    def df(self):
        if self._df is None:
            self._df = pd.DataFrame({'Time [s]': self.time})
        return self._df

    def add_result(self, name, data, df_name=None):
        if df_name is None:
            df_name = name
        setattr(self, name, data)
        self.df[df_name] = data[0:self.time.shape[0]]

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


def get_bc_for_times(times, timeseries):

    if hasattr(timeseries, 'current_value'):
        res = timeseries.current_value(times)
    else:
        res = timeseries

    return res
