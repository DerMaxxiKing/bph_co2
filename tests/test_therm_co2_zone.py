from src.bph_co2.zone import ThermalCO2Zone
from src.bph_co2.wall import Wall
from src.bph_co2.ambient import Ambient
from src.bph_co2.ventilation import Ventilation
from src.bph_co2.timeseries import Timeseries
from src.bph_co2.solver import Solver
from src.bph_co2.window import Window
import multiprocessing as mp

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from src.bph_co2.resources import Input_Data as case_data


def create_case():

    with pkg_resources.path(case_data, 'persons.csv') as path:
        persons_filename = path.__str__()

    with pkg_resources.path(case_data, 'internal_co2_source.csv') as path:
        internal_co2_source_filename = path.__str__()

    with pkg_resources.path(case_data, 'air_change_rate.csv') as path:
        air_change_rate_filename = path.__str__()

    with pkg_resources.path(case_data, 'window_state.csv') as path:
        window_state_filename = path.__str__()

    with pkg_resources.path(case_data, 'outdoor_temperature.csv') as path:
        outdoor_temperature_filename = path.__str__()

    with pkg_resources.path(case_data, 'internal_heat_source.csv') as path:
        internal_heat_source_filename = path.__str__()

    with pkg_resources.path(case_data, 'room_heating.csv') as path:
        room_heating_filename = path.__str__()

    n_persons = Timeseries.from_csv(persons_filename, interpolation_scheme='previous')
    internal_co2_source = Timeseries.from_csv(internal_co2_source_filename, interpolation_scheme='linear')
    air_change_rate = Timeseries.from_csv(air_change_rate_filename, interpolation_scheme='linear')
    window_state = Timeseries.from_csv(window_state_filename, interpolation_scheme='previous')
    outdoor_temperature = Timeseries.from_csv(outdoor_temperature_filename, interpolation_scheme='linear')
    internal_heat_source = Timeseries.from_csv(internal_heat_source_filename, interpolation_scheme='linear')
    room_heating = Timeseries.from_csv(room_heating_filename, interpolation_scheme='linear')

    # create ambient

    ambient = Ambient(name='outside',
                      theta=outdoor_temperature)

    ventilation = Ventilation(t_ex=ambient.theta)

    # create walls:

    zone = ThermalCO2Zone(volume=6 * 6 * 2.6,
                          ventilation=ventilation,
                          phi_int_c=internal_heat_source,
                          phi_hc_id=room_heating,
                          n_persons=n_persons,
                          emission_rate=27000,
                          outdoor_temperature=outdoor_temperature,
                          internal_co2_source=internal_co2_source,
                          air_change_rate=air_change_rate,
                          ambient=ambient)

    window1 = Window(theta_in=None,
                     theta_out=ambient.theta,
                     r_si=0.13,
                     u=1,
                     r_se=0.04,
                     _orientation='vertical',
                     name='windows',
                     area=(1.6 * 1.3)*2,
                     alpha_k=2.5,
                     side1=zone,
                     hight=1.6,
                     state=window_state)

    outside_wall1 = Wall(theta_in=None,
                         theta_out=ambient.theta,
                         r_si=0.13,
                         u=0.35,
                         r_se=0.04,
                         _orientation='vertical',
                         name='outside walls',
                         area=6 * 2.6 * 2 - window1.area,
                         alpha_k=2.5,
                         side1=zone)

    inside_wall1 = Wall(theta_in=None,
                        theta_out=None,
                        theta_s=24,
                        r_si=0.13,
                        u=0.2,
                        r_se=0.04,
                        _orientation='vertical',
                        name='inside walls',
                        area=6*2.6*2,
                        alpha_k=2.5,
                        side1=zone)

    floor = Wall(theta_in=25,
                 theta_out=15,
                 u=0.35,
                 r_se=0.04,
                 orientation='floor',
                 name='floor',
                 area=5*5,
                 side1=zone)

    ceiling = Wall(theta_in=25,
                   theta_out=ambient.theta,
                   u=0.35,
                   r_se=0.04,
                   orientation='ceiling',
                   name='ceiling',
                   area=5*5,
                   side1=zone)

    # res = zone.calc_steady_state_result()
    # print(res)

    zone.theta_0 = 20

    return zone

# res.plot()


if __name__ == '__main__':
    mp.freeze_support()

    zone = create_case()

    solver = Solver(zone=zone,
                    timestep=60,
                    t_end=266400
                    )
    res = solver.calc_transient_co2_temperature()
    res.plot()
    pass