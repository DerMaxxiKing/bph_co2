============================================================
bph2_co2: Educational tool for CO2 concentration simulations
============================================================

Python library for education with tools for CO2 concentration simulations

Usage
-----

Imports:
^^^^^^^^

.. code-block:: python

    from src.bph_co2.solver import CO2_Simulation, ppm_to_mg_m3, mg_m3_to_ppm
    from src.bph_co2.timeseries import Timeseries
    from src.bph_co2.window import Window

CO2_Simulation Objects:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- create a CO2_Simulation object. This is the base for running a simulation:

.. code-block:: python

    sim = CO2_Simulation(name='my_test_simulation')

The CO2_Simulation has the following parameters:
    - name:                         the name of the CO2_Simulation; default is 'Unnamed Simulation'
    - volume:                       the volume of the simulated zone [m³]; default is 75
    - n_persons:                    number of persons in the zone; default is 1
    - co2_emission_rate:            CO2 emission_rate of a person
    - a_tilted: effective ventilation area for tilted window [m²]; default is calculated from the window geometry
    - a_opened: effective ventilation area for opened window [m²]; default is calculated from the window geometry

All parameters can be set on initialization or afterwards.

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



Create a class:
^^^^^^^^^^^^^^^

The tracked class must have the metaclass=ObserverDBMeta. The tracked attributes are defined in the *_mapped_attributes*
dictionary. The keys of the dictionary are the names of the attributes to be tracked. The values of the dictionary are
the types of the attributes.

Valid types are all sqlalchemy types and the types in sqlalchemy.sql.sqltypes and all types in udbs.db_types.
The type Universal_DBType can handle all common data types. Unknown types are pickled.
Additional the types in udbs.db_types return a tracked mutable object when queried which can also be referenced.

Valid udbs.db_types:

* Bool_DBType
* Integer_DBType
* Float_DBType
* String_DBType
* Tuple_DBType
* List_DBType
* Pandas_DBType
* Numpy_DBType
* Dictionary_DBType
* Universal_DBType

The attribute *id* is automatically added to the class as the unique primary key in the database:
(Column(id_type, primary_key=True)).The primary key has to be a UUID.

.. code-block:: python

    class MyTest(metaclass=ObserverDBMeta):
        """
        Define which attributes should be saved in the database as a dictionary.

        The keys are the name of the attribute, the value the type of the value.
        In this Example the attribute 'pid', 'name', 'df' and 'unknown' are saved in the database.
        """

        # if true a new shadow_class an da table in the database is created
        # otherwise the super-class shadow_class is used and data is written in the super-class table
        _create_new_shadow_cls = True

        _mapped_attributes = {'pid': Integer,
                              'name': String,
                              'df': Pandas_DBType,
                              'unknown': Universal_DBType}

        new_id = count(0)

        def __init__(self, *args, **kwargs):

            # the attribute 'id' is automatically added to the class as the unique primary key in the database:
            # (Column(id_type, primary_key=True)).The primary key has to be a UUID.
            self.id = kwargs.get('id', uuid.uuid4())
            self.pid = kwargs.get('pid', next(self.new_id))
            self.name = kwargs.get('name', f'MyTest {self.pid}')

            self.df = kwargs.get('df', None)
            self.unknown = kwargs.get('unknown', [1, 2, 3])

* Other primary keys:

If another primary-key should be used, use *'_my_primary_key': PrimaryKey* entry in _mapped_attributes:

.. code-block:: python

    from udbs import PrimaryKey

    class NumpyClass(metaclass=ObserverDBMeta):

    _tracked = True

    _mapped_attributes = {'_my_primary_key': PrimaryKey,    # the attribute *_my_primary_key* will be the primary key
                          '_pid': Integer,
                          '_name': String,
                          '_color': Numpy_DBType,
                          '_is_visible': Boolean,
                          '_color_from_parent': Boolean,
                          'data': Numpy_DBType
                          }

    def __init__(self, *args, **kwargs):
        kwargs['_tracked'] = kwargs.get('_tracked', self.__class__._tracked)

        # if base_config.tracked:
        #     ConstructionBaseClass.__init__(self, *args, **kwargs)

        self._id = None
        self._pid = None
        self._name = None
        self._color = None
        self._is_visible = None
        self._color_from_parent = None

        self._pid = kwargs.get('_pid', kwargs.get('pid', next(self.new_id)))
        self._id = kwargs.get('_id', kwargs.get('id', str(uuid.uuid4())))
        self._is_visible = kwargs.get('_is_visible', kwargs.get('is_visible', True))
        self._color = kwargs.get('_color', kwargs.get('color', create_random_color()))
        self._color_from_parent = kwargs.get('_color_from_parent', kwargs.get('color_from_parent', False))
        self._name = kwargs.get('_name', kwargs.get('name', 'Base{}'.format(self.pid)))

        self.data = kwargs.get('_data', kwargs.get('data', None))

        # self._observer_notifications = []


* Untracked Classes:

To create a untracked class use *_tracked = False*. Class instances will not be written to the database.
While runtime the class can be changed to tracked with: *MyTest._tracked = True*:

.. code-block:: python

    class MyTest(metaclass=ObserverDBMeta):

            _tracked = False

            _mapped_attributes = {'pid': Integer,
                                  'name': String,
                                  'df': Pandas_DBType,
                                  'unknown': Universal_DBType}

            new_id = count(0)

            def __init__(self, *args, **kwargs):

                self.id = kwargs.get('id', uuid.uuid4())
                self.pid = kwargs.get('pid', next(self.new_id))
                self.name = kwargs.get('name', f'MyTest {self.pid}')

                self.df = kwargs.get('df', None)
                self.unknown = kwargs.get('unknown', [1, 2, 3])


Inheritance:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Inheritance is supported.

.. code-block:: python

    class MyTest2(MyTest):

        # if true a new shadow_class an da table in the database is created
        # otherwise the super-class shadow_class is used and data is written in the super-class table
        _create_new_shadow_cls = True

        _mapped_attributes = {'test_attr': Integer}

        def __init__(self, *args, **kwargs):

            MyTest.__init__(self, *args, **kwargs)
            self.test_attr = kwargs.get('test_attr', None)

    my_test2 = MyTest2(test_attr=7, df=df)
    print(MyTest.unknown)


create a sub-class with no new tracked attributes:

.. code-block:: python

    class MyTest3(MyTest2):

        # if true a new shadow_class an da table in the database is created
        # otherwise the super-class shadow_class is used and data is written in the super-class table
        _create_new_shadow_cls = True

        _mapped_attributes = {}

        def __init__(self, *args, **kwargs):

            MyTest2.__init__(self, *args, **kwargs)

    my_test3 = MyTest3(test_attr=7, df=df)
    print(MyTest.unknown)


* No new tracked attributes / Subclass which uses super-class shadow_class and database table

create a sub-class of *MyTest2* with no new tracked attributes which uses the shadow_class of *MyTest2*. In the database
no new table is created, instances are written in the table of *MyTest2*. Remember to set *_create_new_shadow_cls = True*
when creating a new subclass of *MyTest2*

.. code-block:: python

    class MyTest3(MyTest2):

        # if true a new shadow_class an da table in the database is created
        # otherwise the super-class shadow_class is used and data is written in the super-class table
        _create_new_shadow_cls = False

        _mapped_attributes = {}

        def __init__(self, *args, **kwargs):

            MyTest2.__init__(self, *args, **kwargs)

    my_test3 = MyTest3(test_attr=7, df=df)
    print(MyTest.unknown)


* Overrule loaded object type

By default when a class is created objects generated with this class will be loaded with this type.
The Type of a object is stored.

You can overrule this behaviour by defining *_overrule_registered_classes*:

.. code-block:: python

    class MyTest3(MyTest2):

        _overrule_registered_classes = [MyTest2]

        # if true a new shadow_class an da table in the database is created
        # otherwise the super-class shadow_class is used and data is written in the super-class table
        _create_new_shadow_cls = False

        _mapped_attributes = {}

        def __init__(self, *args, **kwargs):

            MyTest2.__init__(self, *args, **kwargs)


Objects in the database stored with the type *MyTest2* will no longer be loaded as *MyTest2* but with
the type *MyTest3*. Internally the registered classes entry of the db_handler will be changed when the
class is created:

.. code-block:: python

    if hasattr(cls, '_overrule_registered_classes'):
        for overruled_cls in cls._overrule_registered_classes:
            registered_classes[overruled_cls.__name__] = cls



Create class instances:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

create instances of *MyTest*:

.. code-block:: python

    fake = Faker()
    from faker import Faker

    def create_rows(num=100):
        output = [{"name": fake.name(),
                   "address": fake.address(),
                   "name": fake.name(),
                   "email": fake.email(),
                   "bs": fake.bs(),
                   "address": fake.address(),
                   "city": fake.city(),
                   "state": fake.state(),
                   "date_time": fake.date_time(),
                   "paragraph": fake.paragraph(),
                   "Conrad": fake.catch_phrase(),
                   "randomdata": random.randint(1000, 2000)} for x in range(num)]
        return output

    df = create_rows(20)

    my_new_test = MyTest(df=df, name='random_name', unknown=2.17)
    my_new_test2 = MyTest(df=df, name='some_test_name', unknown=[18, 28.15, {'some_key': np.random.rand(5, 5)}])

create a another instance of *MyTest*: notice: the database where the object should be stored is given. If None is given
the default database is taken.



.. code-block:: python

    my_new_test_3 = MyTest(df=df, db=db2)

* create untracked instance:

.. code-block:: python

    my_new_untracked_test = MyTest(df=df, name='random_name', unknown=2.17, _tracked = False)


* track untracked instance:
To track a untracked instance set *_tracked* to *True*. The instance will be added to the database
and further changes will be tracked:

.. code-block:: python

    my_new_untracked_test._tracked = True


* do not track tracked instance:
To untrack a tracked instance set *_tracked* to *False*:

.. code-block:: python

    # change to untracked:
    my_new_untracked_test._tracked = False
    # further changes are not written to rhe database:
    my_new_untracked_test.df = 'not_tracked'    # this change is not tracked in the database
    # change to tracked again:
    my_new_untracked_test._tracked = True
    # the instance is tracked and the database entry is updated in the database


Reference instances:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Once a object is created, the assigned values can be tracked.

.. code-block:: python

    my_new_test_4 = MyTest(df=my_new_test.df, name=my_new_test_2.name, db=db2)

In this case there is no new dataframe saved in the database as it already exists. Instead the reference to the existing
dataframe is stored in the database. So if Changes to my_new_test_4.df are made, these also affect my_new_test.df.


Load class instances:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The class instances can be loaded by:

.. code-block:: python

    my_new_tests = db.query_all(MyTest)
    my_new_tests_2 = db2.query_all(MyTest, return_type=list)

The default return type is a set with all instances. With the key return_type=list this can be changed to a list.

If only one instance with given id should be loaded use:

.. code-block:: python

    my_new_test = db.query_single_id(MyTest, id)


You can also do filtered queries:

.. code-block:: python

    my_new_test = db.query_filtered(MyTest, 'name', ['some_test_name', 5])




Requirements
------------

Python 3.7+.


Windows Support
---------------

Summary: On Windows, use ``py`` instead of ``python3`` for many of the examples in this
documentation.

This package fully supports Windows, along with Linux and macOS, but Python is typically
`installed differently on Windows <https://docs.python.org/3/using/windows.html>`_.
Windows users typically access Python through the
`py <https://www.python.org/dev/peps/pep-0397/>`_ launcher rather than a ``python3``
link in their ``PATH``. Within a virtual environment, all platforms operate the same and use a
``python`` link to access the Python version used in that virtual environment.

Dependencies
------------

Dependencies are defined in:

- ``requirements.in``

- ``requirements.txt``

- ``dev-requirements.in``

- ``dev-requirements.txt``

Virtual Environments
^^^^^^^^^^^^^^^^^^^^

It is best practice during development to create an isolated
`Python virtual environment <https://docs.python.org/3/library/venv.html>`_ using the
``venv`` standard library module. This will keep dependant Python packages from interfering
with other Python projects on your system.

On \*Nix:

.. code-block:: bash

    $ python3 -m venv venv
    $ source venv/bin/activate

On Windows ``cmd``:

.. code-block:: bash

    > py -m venv venv
    > venv\Scripts\activate.bat

Once activated, it is good practice to update core packaging tools (``pip``, ``setuptools``, and
``wheel``) to the latest versions.

.. code-block:: bash

    (venv) $ python -m pip install --upgrade pip setuptools wheel

Packaging
---------

This project is designed as a Python package, meaning that it can be bundled up and redistributed
as a single compressed file.

Packaging is configured by:

- ``pyproject.toml``

- ``setup.py``

- ``MANIFEST.in``

To package the project as both a
`source distribution <https://docs.python.org/3/distutils/sourcedist.html>`_ and a
`wheel <https://wheel.readthedocs.io/en/stable/>`_:

.. code-block:: bash

    (venv) $ python setup.py sdist bdist_wheel

This will generate ``dist/fact-1.0.0.tar.gz`` and ``dist/fact-1.0.0-py3-none-any.whl``.

Read more about the `advantages of wheels <https://pythonwheels.com/>`_ to understand why
generating wheel distributions are important.

Upload Distributions to PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Source and wheel redistributable packages can be
`uploaded to PyPI <https://packaging.python.org/tutorials/packaging-projects/>`_ or installed
directly from the filesystem using ``pip``.

To upload to PyPI:

.. code-block:: bash

    (venv) $ python -m pip install twine
    (venv) $ twine upload dist/*

Testing
-------

Automated testing is performed using `tox <https://tox.readthedocs.io/en/latest/index.html>`_.
tox will automatically create virtual environments based on ``tox.ini`` for unit testing,
PEP8 style guide checking, and documentation generation.

.. code-block:: bash

    # Run all environments.
    #   To only run a single environment, specify it like: -e pep8
    # Note: tox is installed into the virtual environment automatically by pip-sync command above.
    (venv) $ tox

Unit Testing
^^^^^^^^^^^^

Unit testing is performed with `pytest <https://pytest.org/>`_. pytest has become the defacto
Python unit testing framework. Some key advantages over the built in
`unittest <https://docs.python.org/3/library/unittest.html>`_ module are:

#. Significantly less boilerplate needed for tests.

#. PEP8 compliant names (e.g. ``pytest.raises()`` instead of ``self.assertRaises()``).

#. Vibrant ecosystem of plugins.

pytest will automatically discover and run tests by recursively searching for folders and ``.py``
files prefixed with ``test`` for any functions prefixed by ``test``.

The ``tests`` folder is created as a Python package (i.e. there is an ``__init__.py`` file
within it) because this helps ``pytest`` uniquely namespace the test files. Without this,
two test files cannot be named the same, even if they are in different sub-directories.

Code coverage is provided by the `pytest-cov <https://pytest-cov.readthedocs.io/en/latest/>`_
plugin.

When running a unit test tox environment (e.g. ``tox``, ``tox -e py37``, etc.), a data file
(e.g. ``.coverage.py37``) containing the coverage data is generated. This file is not readable on
its own, but when the ``coverage`` tox environment is run (e.g. ``tox`` or ``tox -e -coverage``),
coverage from all unit test environments is combined into a single data file and an HTML report is
generated in the ``htmlcov`` folder showing each source file and which lines were executed during
unit testing. Open ``htmlcov/index.html`` in a web browser to view the report. Code coverage 
reports help identify areas of the project that are currently not tested.

Code coverage is configured in ``pyproject.toml``.

To pass arguments to ``pytest`` through ``tox``:

.. code-block:: bash

    (venv) $ tox -e py37 -- -k invalid_factorial

Code Style Checking
^^^^^^^^^^^^^^^^^^^

`PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ is the universally accepted style
guide for Python code. PEP8 code compliance is verified using `flake8 <http://flake8.pycqa.org/>`_.
flake8 is configured in the ``[flake8]`` section of ``tox.ini``. Extra flake8 plugins
are also included:

- ``pep8-naming``: Ensure functions, classes, and variables are named with correct casing.

Automated Code Formatting
^^^^^^^^^^^^^^^^^^^^^^^^^

Code is automatically formatted using `black <https://github.com/psf/black>`_. Imports are
automatically sorted and grouped using `isort <https://github.com/timothycrosley/isort/>`_.

These tools are configured by:

- ``pyproject.toml``

To automatically format code, run:

.. code-block:: bash

    (venv) $ tox -e fmt

To verify code has been formatted, such as in a CI job:

.. code-block:: bash

    (venv) $ tox -e fmt-check

Generated Documentation
^^^^^^^^^^^^^^^^^^^^^^^

Documentation that includes the ``README.rst`` and the Python project modules is automatically
generated using a `Sphinx <http://sphinx-doc.org/>`_ tox environment. Sphinx is a documentation
generation tool that is the defacto tool for Python documentation. Sphinx uses the
`RST <https://www.sphinx-doc.org/en/latest/usage/restructuredtext/basics.html>`_ markup language.

This project uses the
`napoleon <http://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html>`_ plugin for
Sphinx, which renders Google-style docstrings. Google-style docstrings provide a good mix
of easy-to-read docstrings in code as well as nicely-rendered output.

.. code-block:: python

    """Computes the factorial through a recursive algorithm.

    Args:
        n: A positive input value.

    Raises:
        InvalidFactorialError: If n is less than 0.

    Returns:
        Computed factorial.
    """

The Sphinx project is configured in ``docs/conf.py``.

Build the docs using the ``docs`` tox environment (e.g. ``tox`` or ``tox -e docs``). Once built,
open ``docs/_build/index.html`` in a web browser.

Generate a New Sphinx Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To generate the Sphinx project shown in this project:

.. code-block:: bash

    # Note: Sphinx is installed into the virtual environment automatically by pip-sync command
    # above.
    (venv) $ mkdir docs
    (venv) $ cd docs
    (venv) $ sphinx-quickstart --no-makefile --no-batchfile --extensions sphinx.ext.napoleon
    # When prompted, select all defaults.

Modify ``conf.py`` appropriately:

.. code-block:: python

    # Add the project's Python package to the path so that autodoc can find it.
    import os
    import sys
    sys.path.insert(0, os.path.abspath('../src'))

    ...

    html_theme_options = {
        # Override the default alabaster line wrap, which wraps tightly at 940px.
        'page_width': 'auto',
    }

Modify ``index.rst`` appropriately:

::

    .. include:: ../README.rst

    apidoc/modules.rst

Project Structure
-----------------

Traditionally, Python projects place the source for their packages in the root of the project
structure, like:

.. code-block::

    fact
    ├── fact
    │   ├── __init__.py
    │   ├── cli.py
    │   └── lib.py
    ├── tests
    │   ├── __init__.py
    │   └── test_fact.py
    ├── tox.ini
    └── setup.py

However, this structure is `known
<https://docs.pytest.org/en/latest/goodpractices.html#tests-outside-application-code>`_ to have bad
interactions with ``pytest`` and ``tox``, two standard tools maintaining Python projects. The
fundamental issue is that tox creates an isolated virtual environment for testing. By installing
the distribution into the virtual environment, ``tox`` ensures that the tests pass even after the
distribution has been packaged and installed, thereby catching any errors in packaging and
installation scripts, which are common. Having the Python packages in the project root subverts
this isolation for two reasons:

#. Calling ``python`` in the project root (for example, ``python -m pytest tests/``) `causes Python
   to add the current working directory
   <https://docs.pytest.org/en/latest/pythonpath.html#invoking-pytest-versus-python-m-pytest>`_
   (the project root) to ``sys.path``, which Python uses to find modules. Because the source
   package ``fact`` is in the project root, it shadows the ``fact`` package installed in the tox
   environment.

#. Calling ``pytest`` directly anywhere that it can find the tests will also add the project root
   to ``sys.path`` if the ``tests`` folder is a a Python package (that is, it contains a
   ``__init__.py`` file). `pytest adds all folders containing packages
   <https://docs.pytest.org/en/latest/goodpractices.html#conventions-for-python-test-discovery>`_
   to ``sys.path`` because it imports the tests like regular Python modules.

In order to properly test the project, the source packages must not be on the Python path. To
prevent this, there are three possible solutions:

#. Remove the ``__init__.py`` file from ``tests`` and run ``pytest`` directly as a tox command.

#. Remove the ``__init__.py`` file from tests and change the working directory of
   ``python -m pytest`` to ``tests``.

#. Move the source packages to a dedicated ``src`` folder.

The dedicated ``src`` directory is the `recommended solution
<https://docs.pytest.org/en/latest/pythonpath.html#test-modules-conftest-py-files-inside-packages>`_
by ``pytest`` when using tox and the solution this blueprint promotes because it is the least
brittle even though it deviates from the traditional Python project structure. It results is a
directory structure like:

.. code-block::

    fact
    ├── src
    │   └── fact
    │       ├── __init__.py
    │       ├── cli.py
    │       └── lib.py
    ├── tests
    │   ├── __init__.py
    │   └── test_fact.py
    ├── tox.ini
    └── setup.py

Type Hinting
------------

`Type hinting <https://docs.python.org/3/library/typing.html>`_ allows developers to include
optional static typing information to Python source code. This allows static analyzers such
as `PyCharm <https://www.jetbrains.com/pycharm/>`_, `mypy <http://mypy-lang.org/>`_, or
`pytype <https://github.com/google/pytype>`_ to check that functions are used with the correct
types before runtime.

For
`PyCharm in particular <https://www.jetbrains.com/help/pycharm/type-hinting-in-product.html>`_,
the IDE is able to provide much richer auto-completion, refactoring, and type checking while
the user types, resulting in increased productivity and correctness.

This project uses the type hinting syntax introduced in Python 3:

.. code-block:: python

    def factorial(n: int) -> int:

Type checking is performed by mypy via ``tox -e mypy``. mypy is configured in ``setup.cfg``.

Licensing
---------

Licensing for the project is defined in:

- ``LICENSE.txt``

- ``setup.py``

This project uses a common permissive license, the MIT license.

You may also want to list the licenses of all of the packages that your Python project depends on.
To automatically list the licenses for all dependencies in ``requirements.txt`` (and their
transitive dependencies) using
`pip-licenses <https://github.com/raimon49/pip-licenses>`_:

.. code-block:: bash

    (venv) $ tox -e licenses
    ...
     Name        Version  License
     colorama    0.4.3    BSD License
     exitstatus  1.3.0    MIT License

PyCharm Configuration
---------------------

To configure PyCharm 2018.3 and newer to align to the code style used in this project:

- Settings | Search "Hard wrap at"

    - Editor | Code Style | General | Hard wrap at: 99

- Settings | Search "Optimize Imports"

    - Editor | Code Style | Python | Imports

        - ☑ Sort import statements

            - ☑ Sort imported names in "from" imports

            - ☐ Sort plain and "from" imports separately within a group

            - ☐ Sort case-insensitively

        - Structure of "from" imports
            
            - ◎ Leave as is
            
            - ◉ Join imports with the same source
            
            - ◎ Always split imports

- Settings | Search "Docstrings"

    - Tools | Python Integrated Tools | Docstrings | Docstring Format: Google

- Settings | Search "Force parentheses"

    - Editor | Code Style | Python | Wrapping and Braces | "From" Import Statements

        - ☑ Force parentheses if multiline

Integrate Code Formatters
^^^^^^^^^^^^^^^^^^^^^^^^^

To integrate automatic code formatters into PyCharm, reference the following instructions:

- `black integration <https://black.readthedocs.io/en/stable/editor_integration.html#pycharm-intellij-idea>`_

    - The File Watchers method (step 3) is recommended. This will run ``black`` on every save.

- `isort integration <https://github.com/timothycrosley/isort/wiki/isort-Plugins>`_

    - The File Watchers method (option 1) is recommended. This will run ``isort`` on every save.
