from src.bph_co2.zone import ThermalCO2Zone
from src.bph_co2.wall import Wall
from src.bph_co2.ambient import Ambient
from src.bph_co2.ventilation import Ventilation
from src.bph_co2.timeseries import Timeseries
from src.bph_co2.solver import Solver
from src.bph_co2.window import Window


def create_case():

    n_persons = Timeseries.from_csv(r'K:\ownCloud\Lehre\Bauphysik 2\Komfort\Python Cases\Aufgabe1\Timeseries\persons.csv', interpolation_scheme='previous')
    internal_co2_source = Timeseries.from_csv(r'K:\ownCloud\Lehre\Bauphysik 2\Komfort\Python Cases\Aufgabe1\Timeseries\internal_co2_source.csv', interpolation_scheme='linear')
    air_change_rate = Timeseries.from_csv(r'K:\ownCloud\Lehre\Bauphysik 2\Komfort\Python Cases\Aufgabe1\Timeseries\air_change_rate.csv', interpolation_scheme='linear')
    window_state = Timeseries.from_csv(r'K:\ownCloud\Lehre\Bauphysik 2\Komfort\Python Cases\Aufgabe1\Timeseries\window_state.csv', interpolation_scheme='previous')
    outdoor_temperature = Timeseries.from_csv(r'K:\ownCloud\Lehre\Bauphysik 2\Komfort\Python Cases\Aufgabe1\Timeseries\outdoor_temperature.csv', interpolation_scheme='linear')
    internal_heat_source = Timeseries.from_csv(r'K:\ownCloud\Lehre\Bauphysik 2\Komfort\Python Cases\Aufgabe1\Timeseries\internal_heat_source.csv', interpolation_scheme='linear')
    room_heating = Timeseries.from_csv(r'K:\ownCloud\Lehre\Bauphysik 2\Komfort\Python Cases\Aufgabe1\Timeseries\room_heating.csv', interpolation_scheme='linear')

    # create ambient

    ambient = Ambient(name='outside',
                      theta=-10)

    ventilation = Ventilation(t_ex=ambient.theta)

    # create walls:

    zone = ThermalCO2Zone(volume=6 * 6 * 2.6,
                          ventilation=ventilation,
                          phi_int_c=4 * (100 + 200),
                          phi_hc_id=500 * 0.7,
                          n_persons=0,
                          emission_rate=27000,
                          outdoor_temperature=-10,
                          internal_co2_source=0,
                          air_change_rate=0.5,
                          ambient=ambient)

    window1 = Window(theta_in=None,
                     theta_out=ambient.theta,
                     r_si=0.13,
                     u=1,
                     r_se=0.04,
                     _orientation='vertical',
                     name='windows',
                     area=(1.6 * 1.3)*4,
                     alpha_k=2.5,
                     side1=zone,
                     hight=1.6,
                     state=0)

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
                        theta_s=20,
                        r_si=0.13,
                        u=0.2,
                        r_se=0.04,
                        _orientation='vertical',
                        name='inside walls',
                        area=6 * 2.6 * 2,
                        alpha_k=2.5,
                        side1=zone)

    floor = Wall(theta_in=25,
                 theta_out=10,
                 u=0.35,
                 r_se=0.04,
                 orientation='floor',
                 name='floor',
                 area=6*6,
                 side1=zone)

    ceiling = Wall(theta_in=25,
                   theta_out=ambient.theta,
                   u=0.35,
                   r_se=0.04,
                   orientation='ceiling',
                   name='ceiling',
                   area=6*6,
                   side1=zone)

    # res = zone.calc_steady_state_result()
    # print(res)

    zone.theta_0 = 20

    return zone

# res.plot()

zone = create_case()

solver = Solver(zone=zone,
                timestep=60,
                t_end=26640
                )
res = solver.calc_transient_co2_temperature()
res.plot()