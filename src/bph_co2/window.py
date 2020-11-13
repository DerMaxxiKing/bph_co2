import numpy as np
from .zone import BaseZone
from .wall import Wall


class Window(Wall):

    def __init__(self, *args, **kwargs):

        Wall.__init__(self, *args, **kwargs)

        # siehe ÖNORM 8110-3

        self.hight = kwargs.get('hight', 1)                     # hight of the window [m]
        self.state = kwargs.get('state', 0)                     # state of the window; 0: closed, 1: tilted; 2: opened
        self.c_ref = kwargs.get('c_ref', 100)                   # Austauschkoeffizient [m^0.5 / h * K^0.5]

        self._a_tilted = kwargs.get('a_tilted', None)           # effective ventilation area for tilted window [m²]
        self._a_opened = kwargs.get('a_opened', None)           # effective ventilation area for opened window [m²]

    @property
    def side1(self):
        return self._side_1

    @side1.setter
    def side1(self, value):
        self._side_1 = value

        if isinstance(self._side_1, BaseZone):
            self._side_1.add_window(self)

    @property
    def side2(self):
        return self._side_2

    @side2.setter
    def side2(self, value):
        self._side_2 = value

        if isinstance(self._side_2, BaseZone):
            self._side_2.add_window(self)

    @property
    def a_tilted(self):
        if self._a_tilted is None:
            self._a_tilted = 0.15 * (self.hight + (self.area / self.hight))
        return self._a_tilted

    @property
    def a_opened(self):
        if self._a_opened is None:
            self._a_opened = self.area
        return self._a_opened

    def q(self, t_i=20, t_e=10, time=0):

        if hasattr(self.state, 'current_value'):
            state = self.state.current_value(time)
        else:
            state = self.state

        if state == 0:
            return 0

        if state == 1:
            area = self.a_tilted
        elif state == 2:
            area = self.a_opened

        return 0.7 * self.c_ref * (area * np.sqrt(self.hight)) * np.sqrt(abs(t_i - t_e))