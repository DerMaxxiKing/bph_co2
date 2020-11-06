============================================================
bph2_co2: Educational tool for CO2 concentration simulations
============================================================

Python library for education with tools for CO2 concentration simulations

.. image:: https://raw.githubusercontent.com/bph-tuwien/bph_co2/master/docs/screenshot_1.PNG?sanitize=true

Installation:
^^^^^^^^^^^^^
pip install bph2-co2==1.0.0


Example:
--------

see also main.py

.. code-block:: python

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

        # load .csv files
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

        # create a window:
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

Usage
-----

Imports:
^^^^^^^^

.. code-block:: python

    from src.bph_co2.solver import CO2_Simulation
    from src.bph_co2.timeseries import Timeseries
    from src.bph_co2.window import Window


CO2_Simulation:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- create a CO2_Simulation object. This is the base for running a simulation:

.. code-block:: python

    sim = CO2_Simulation(name='my_test_simulation')

The CO2_Simulation has the following parameters:

    - *name*:                         the name of the CO2_Simulation; default is 'Unnamed Simulation'
    - *volume*:                       the volume of the simulated zone [m³]; default is 75
    - *n_persons*:                    number of persons in the zone; default is 1 *
    - *emission_rate*:                CO2 emission_rate of a person in mg/h; default is 27000 mg/h;
    - *internal_co2_source*:          co2 emission rate of internal sources in mg/h; default is 0 *
    - *outdoor_temperature*:          outdoor temperature in °C; default is 10 °C *
    - *indoor_temperature*:           indoor temperature in °C; default is 20 °C *
    - *windows*:                      windows of the zone; list of *window*-objects; default is []
    - *air_change_rate*:              air change rate in 1/h; default is 0.5 *
    - *c0i*:                          initial CO2-concentration in the room/zone in ppm; default is 400
    - *c0e*:                          initial outdoor CO2-concentration in ppm; default is 400
    - *timestep*:                     simulation timestep [s]; default is 360
    - *t_end*:                        end time of the simulation

All parameters can be set on initialization or afterwards.
* Parameters can be Timeseries objects

- run a simulation:

.. code-block:: python

    res = sim.calculate()

- display simulation results:
    res.plot()


Timeseries Objects:
^^^^^^^^^^^^^^^^^^^^^^^^^^

- A Timeseries handles data and returns a value / values for a time [s]. A Timeseries can handle static values (int, float, etc..), numpy arrays (first column has to be the time in [s]) or pd.Dataframes (index must be the time).

- Timeseries objects can interpolate Data in different ways. To specify interpolation scheme pass keyword *interpolation_scheme* with:
    - 'linear': linear interpolation
    - 'previous': closest previous value (for example for persons)

- Create a timeseries object with static value (integer):

.. code-block:: python

    n_persons = Timeseries(data=1)


- Create a timeseries object with np.array:

.. code-block:: python

    array = array = np.empty((2,100))
    array[0,:] = np.arange(array.shape[1])
    array[1,:] = np.random.rand(array.shape[1])
    n_persons = Timeseries(data=array)


- Create a timeseries object with pd.Dataframe:

.. code-block:: python

    array = array = np.empty((2,100))
    array[0,:] = np.arange(array.shape[1])
    array[1,:] = np.random.rand(array.shape[1])

    df = pd.DataFrame({'Time': array[0,:],
                       'n_persons': array[1,:]})
    df.set_index('Time', inplace=True)

    n_persons = Timeseries(data=array, interpolation_scheme='linear')

- Create a timeseries object from .csv file:

.. code-block:: python

    n_persons = Timeseries.from_csv('test.csv', interpolation_scheme='previous')


Windows:
^^^^^^^^^^^^^^^^^^^^^^^^^^

In the Simulation windows can be added. Windows create additional air change in the zone dependent of the indoor- and outdoor-temperatures, the opening state and the geometry.

The window can have three states:
    - 0: closed
    - 1: tilted
    - 2: opened

The window has the following parameters:
    - hight:    the hight of the window [m]; default is 1
    - area:     the area of the window [m²]; default is 1
    - state:    state of the window; 0: closed, 1: tilted; 2: opened; default is 0 (closed)
    - c_ref:    Austauschkoeffizient [m^0.5 / h * K^0.5], default is 100
    - a_tilted: effective ventilation area for tilted window [m²]; default is calculated from the window geometry
    - a_opened: effective ventilation area for opened window [m²]; default is calculated from the window geometry

- Create a window:


.. code-block:: python

    from src.bph_co2.window import Window

    window_state = Timeseries.from_csv('window_state.csv', interpolation_scheme='previous')

    window = Window(hight=1,
                    area=1,
                    state=window_state)

- Add window to the simulation:

The windows are specified as a list of window objects:

.. code-block:: python

    sim.windows = [window]






