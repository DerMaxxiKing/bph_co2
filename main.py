from bph_co2.solver import CO2_Simulation, ppm_to_mg_m3, mg_m3_to_ppm
from bph_co2.timeseries import Timeseries
from bph_co2.window import Window

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from bph_co2.resources import Input_Data as case_data


if __name__ == '__main__':

    c0 = 1  # ppm
    c0_mg_m3 = ppm_to_mg_m3(c0)

    volume = 51.48
    emission_rate = 27000
    time = 0

    outdoor_temperature = 10
    indoor_temperature = 20

    # initial state:

    c0 = 400  # initial CO2-concentration in the room / zone
    t0 = 20  # initial temperature in the room / zone

    timestep = 60  # timestep [s]
    t_end = 10800  # End time [s]

    with pkg_resources.path(case_data, 'persons.csv') as path:
        persons_filename = path.__str__()

    with pkg_resources.path(case_data, 'internal_co2_source.csv') as path:
        internal_co2_source_filename = path.__str__()

    with pkg_resources.path(case_data, 'air_change_rate.csv') as path:
        air_change_rate_filename = path.__str__()

    with pkg_resources.path(case_data, 'window_state.csv') as path:
        window_state_filename = path.__str__()

    with pkg_resources.path(case_data, 'indoor_temperature.csv') as path:
        indoor_temperature_filename = path.__str__()

    with pkg_resources.path(case_data, 'outdoor_temperature.csv') as path:
        outdoor_temperature_filename = path.__str__()

    n_persons = Timeseries.from_csv(persons_filename, interpolation_scheme='previous')
    internal_co2_source = Timeseries.from_csv(internal_co2_source_filename, interpolation_scheme='linear')
    air_change_rate = Timeseries.from_csv(air_change_rate_filename, interpolation_scheme='linear')
    window_state = Timeseries.from_csv(window_state_filename, interpolation_scheme='previous')
    indoor_temperature = Timeseries.from_csv(indoor_temperature_filename, interpolation_scheme='linear')
    outdoor_temperature = Timeseries.from_csv(outdoor_temperature_filename, interpolation_scheme='linear')

    window = Window(hight=1,
                    area=1,
                    state=window_state)

    sim = CO2_Simulation(name='test_simulation',
                         volume=51.48,
                         n_persons=n_persons,
                         emission_rate=27000,
                         internal_co2_source=internal_co2_source,
                         indoor_temperature=indoor_temperature,
                         outdoor_temperature=outdoor_temperature,
                         windows=[window],
                         air_change_rate=air_change_rate,
                         timestep=60,
                         t_end=26640)

    res = sim.calculate()

    res.plot()
