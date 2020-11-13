import numpy as np
import pandas as pd
from pandasgui import show
from .tools import calc_air_density, calc_c_p, ppm_to_mg_m3, mg_m3_to_ppm


class BaseZone(object):

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name', f'Unnamed Simulation')       # zone volume in m³
        self.volume = kwargs.get('volume', 5 * 5 * 3)               # zone volume in m³
        self.air_change_rate = kwargs.get('air_change_rate', 0.5)   # air change rate in m³/h

        self.walls = kwargs.get('walls', set())                     # walls of the zone
        self.windows = kwargs.get('windows', [])                    # windows of the zone
        self.ambient = kwargs.get('ambient', None)                  # windows of the zone


class ThermalZone(BaseZone):

    def __init__(self, *args, **kwargs):

        BaseZone.__init__(self, *args, **kwargs)

        self._phi_int_c = set()                                          # convective internal heat sources [W]
        self._phi_hc_id = set()                                          # convective heat flow from room heating or cooling [W]

        self.ventilation = kwargs.get('ventilation', None)

        self.phi_int_c = kwargs.get('phi_int_c', set())                 # convective internal heat sources [W]
        self.phi_hc_id = kwargs.get('phi_hc_id', set())                 # convective heat flow from room heating or cooling [W]

        # simulation parameters:

        self.theta_0 = kwargs.get('theta_0', 20)                        # initial room temperature [°C]

        self.timestep = kwargs.get('timestep', 60)  # timestep [s]
        self.t_end = kwargs.get('t_end', 26640)  # End time [s]

    @property
    def phi_int_c(self):
        return self._phi_int_c

    @phi_int_c.setter
    def phi_int_c(self, value):
        if value is None:
            self._phi_int_c = set()

        elif isinstance(value, set):
            self._phi_int_c = value
        else:
            try:
                self._phi_int_c = set(value)
            except TypeError:
                self._phi_int_c = {value}

    @property
    def phi_hc_id(self):
        return self._phi_hc_id

    @phi_hc_id.setter
    def phi_hc_id(self, value):
        if value is None:
            self._phi_hc_id = set()

        elif isinstance(value, set):
            self._phi_hc_id = value
        else:
            try:
                self._phi_hc_id = set(value)
            except TypeError:
                self._phi_hc_id = {value}

    def q(self, air_change_rate=None, time=0):

        if air_change_rate is None:
            air_change_rate = self.air_change_rate

        if hasattr(air_change_rate, 'current_value'):
            air_change_rate = air_change_rate.current_value(time)
        else:
            air_change_rate = air_change_rate

        if air_change_rate is not None:
            return air_change_rate * self.volume / 3600
        else:
            return 0

    def phi(self, q=None, time=0, theta_in=None, theta_out=None):
        """
        calculates the ventilation heat flow [W]
        :param q: supply air flow [m^3/s]
        :param time: simulation time [s]
        :param theta_in: room air temperature [°C]
        :param theta_out: supply air temperature [°C]
        :return: ventilation heat flow [W]
        """

        if theta_in is None:
            theta_in = self.theta_in

        if theta_out is None:
            if self.ventilation is not None:
                theta_out = self.ventilation.theta_out(time)
            else:
                theta_out = self.theta_out

        if hasattr(theta_out, 'current_value'):
            theta_out = theta_out.current_value(time)
        else:
            theta_out = theta_out

        if q is None:
            q = self.q(time=time)

        if hasattr(q, 'current_value'):
            q = q.current_value(time)
        else:
            q = q

        if self.ventilation is None:
            c_p = 1.0064
            rho = 1.3266
        else:
            c_p = self.ventilation.c_p
            rho = self.ventilation.air_density

        phi = c_p * rho * q * (theta_in - theta_out)

        return phi

    def add_window(self, element):
        self.windows.add(element)
        self.add_wall(element)

    def add_wall(self, element):
        self.walls.add(element)

    def calc_steady_state_result(self, time=0):

        # heat flows walls:
        phi_walls = np.zeros(self.walls.__len__())
        phi_walls_out = np.zeros(self.walls.__len__())
        for i, wall in enumerate(self.walls):
            if wall.theta_s is None:
                f = wall.r_si * wall.alpha_k
                phi_walls[i] = wall.area * wall.u * wall.r_si * wall.alpha_k
                theta_out = wall.theta_out

                phi_walls_out[i] = phi_walls[i] * wall.theta_out
            else:
                f = 1
                theta_out = wall.theta_s
                phi_walls[i] = wall.area * wall.alpha_k

            if hasattr(theta_out, 'current_value'):
                theta_out = theta_out.current_value(time)
            else:
                theta_out = theta_out

            phi_walls_out[i] = phi_walls[i] * theta_out

            print('----------------------------------------')
            print(f'{wall.name:}')
            print(f'Area: {wall.area}')
            print(f'Convective proportion: {f}')
            print(f'specific heat loss: {phi_walls[i]} W/K')
            print(f'phi_wall * t_out: {phi_walls_out[i]} W')
            print('\n')

        print('----------------------------------------')
        print(f'convective heat flow over parts:')
        print(f'phi: {sum(phi_walls)}')
        print(f'phi out: {sum(phi_walls_out)}')
        print('\n')

        if hasattr(self.air_change_rate, 'current_value'):
            air_change_rate = self.air_change_rate.current_value(time)
        else:
            air_change_rate = self.air_change_rate

        if hasattr(self.ventilation.t_in, 'current_value'):
            t_supply_air = self.ventilation.t_in.current_value(time)
        else:
            t_supply_air = self.ventilation.t_in

        phi_ventilation = (air_change_rate * self.volume / 3600) * self.ventilation.c_p() * self.ventilation.supply_air_density()
        phi_ventilation_out = phi_ventilation * t_supply_air
        print('----------------------------------------')
        print('ventilation:')
        print(f'air change rate: {air_change_rate} 1/h')
        print(f'zone volume: {self.volume} m^3')
        print(f'Volume flow: {air_change_rate * self.volume / 3600} m^3/s')
        print(f'cp: {self.ventilation.c_p()} J/kg K')
        print(f'rho: {self.ventilation.supply_air_density()} kg/m^3')
        print(f'phi_ventilation: {phi_ventilation} W/K')
        print(f'phi ventilation supply air ({t_supply_air}): {phi_ventilation_out} W')
        print('\n')

        # internal convective heat sources:
        phi_int_c = 0
        for i, int_c in enumerate(self.phi_int_c):
            if hasattr(int_c, 'current_value'):
                int_c = int_c.current_value(time=0)
            else:
                int_c = int_c
            phi_int_c += int_c

        phi_hc_id = 0
        for i, hc_id in enumerate(self.phi_hc_id):
            if hasattr(hc_id, 'current_value'):
                hc_id = hc_id.current_value(time=0)
            else:
                hc_id = hc_id
            phi_hc_id += hc_id

        print('----------------------------------------')
        print('Equation:')
        print(f'static: {sum(phi_walls_out)} + {(phi_int_c + phi_hc_id)} + {phi_ventilation_out} = {(sum(phi_walls_out) + (phi_int_c + phi_hc_id) + phi_ventilation_out)} W')
        print(f'dynamic static: {sum(phi_walls)} + {phi_ventilation} W = {(sum(phi_walls) + phi_ventilation)}')
        print('\n')

        theta = (sum(phi_walls_out) + (phi_int_c + phi_hc_id) + phi_ventilation_out) / (sum(phi_walls) + phi_ventilation)

        print('----------------------------------------')
        print('static room temperature: {theta}')

        return theta

    def calc_dtheta_dt(self, theta_room, time):

        # heat flows walls:
        phi_walls = 0
        for i, wall in enumerate(self.walls):
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

        if hasattr(self.air_change_rate, 'current_value'):
            air_change_rate = self.air_change_rate.current_value(time)
        else:
            air_change_rate = self.air_change_rate

        if hasattr(self.ventilation.t_in, 'current_value'):
            t_supply_air = self.ventilation.t_in.current_value(time)
        else:
            t_supply_air = self.ventilation.t_in

        phi_ventilation = (air_change_rate * self.volume / 3600) * self.ventilation.c_p() * self.ventilation.supply_air_density() * (t_supply_air - theta_room)

        # internal convective heat sources:
        phi_int_c = 0
        for i, int_c in enumerate(self.phi_int_c):
            if hasattr(int_c, 'current_value'):
                int_c = int_c.current_value(time=0)
            else:
                int_c = int_c
            phi_int_c += int_c

        phi_hc_id = 0
        for i, hc_id in enumerate(self.phi_hc_id):
            if hasattr(hc_id, 'current_value'):
                hc_id = hc_id.current_value(time=0)
            else:
                hc_id = hc_id
            phi_hc_id += hc_id

        air_density = calc_air_density(theta=theta_room, x=0, p=101300)
        c_p = calc_c_p(x=0)
        dtheta_dt = (phi_walls + phi_ventilation + phi_int_c + phi_hc_id) / (air_density * c_p * self.volume)

        return dtheta_dt


class CO2Zone(BaseZone):

    def __init__(self, *args, **kwargs):

        BaseZone.__init__(self, *args, **kwargs)

        self.n_persons = kwargs.get('n_persons', 1)  # number of persons in the room
        self.co2_emission_rate = kwargs.get('emission_rate', 27000)  # co2 emission rate per person in mg/h
        self.internal_co2_source = kwargs.get('internal_co2_source', 0)  # co2 emission rate of internal sources in mg/h

        self.outdoor_temperature = kwargs.get('outdoor_temperature', None)  # outdoor temperature in °C
        self.indoor_temperature = kwargs.get('indoor_temperature', None)  # indoor temperature in °C

        self.windows = kwargs.get('windows', set())

        # air change
        self.ventilation = kwargs.get('ventilation', None)

        # initial state:
        self.c0i_ppm = kwargs.get('c0i', 400)  # initial CO2-concentration in the room/zone in ppm
        self.c0i_mg_m3 = ppm_to_mg_m3(self.c0i_ppm)
        self.c0e_ppm = kwargs.get('c0e', 400)  # initial outdoor CO2-concentration in ppm
        self.c0e_mg_m3 = ppm_to_mg_m3(self.c0e_ppm)

        # simulation parameters:

        self.timestep = kwargs.get('timestep', 360)  # timestep [s]
        self.t_end = kwargs.get('t_end', 26640)  # End time [s]
        self.write_interval = kwargs.get('write_interval', 5)  # Write results each write_interval timestep


class ThermalCO2Zone(ThermalZone, CO2Zone):

    def __init__(self, *args, **kwargs):

        ThermalZone.__init__(self, *args, **kwargs)
        CO2Zone.__init__(self, *args, **kwargs)


class Result(object):

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name', '')                                      # name time
        self.time = kwargs.get('time', None)                                    # Simulation time
        self.q = kwargs.get('q', None)                                          # fresh air volume flow
        self.air_change_rate = kwargs.get('air_change_rate', None)              # air_change_rate
        self.outdoor_temperature = kwargs.get('outdoor_temperature', None)      # outdoor_temperature [°C]
        self.indoor_temperature = kwargs.get('indoor_temperature', None)        # indoor_temperature [°C]

        self._df = None

    @property
    def df(self):
        if self._df is None:

            self._df = pd.DataFrame({'Time [s]': self.time,
                                     'Total fresh air volume flow [m³/h]': self.q[0:self.time.shape[0]],
                                     'Air change rate [1/h]': self.air_change_rate[0:self.time.shape[0]],
                                     'Outdoor temperature [°C]': self.outdoor_temperature[0:self.time.shape[0]],
                                     'Indoor temperature [°C]': self.indoor_temperature[0:self.time.shape[0]]}
                                    )

        return self._df

    def plot(self):

        show(self.df, settings={'block': True})







