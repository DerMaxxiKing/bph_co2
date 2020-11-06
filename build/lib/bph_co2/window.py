import pandas as pd
import numpy as np


class Window(object):

    def __init__(self, *args, **kwargs):

        # siehe ÖNORM 8110-3

        self.hight = kwargs.get('hight', 1)                     # hight of the window [m]
        self.area = kwargs.get('hight', 1)                      # area of the window [m]
        self.state = kwargs.get('state', 0)                     # state of the window; 0: closed, 1: tilted; 2: opened
        self.c_ref = kwargs.get('c_ref', 100)                   # Austauschkoeffizient [m^0.5 / h * K^0.5]

        self._a_tilted = kwargs.get('a_tilted', None)           # effective ventilation area for tilted window [m²]
        self._a_opened = kwargs.get('a_opened', None)           # effective ventilation area for opened window [m²]

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
            state = self.state.current_value(time).values
        else:
            state = self.state

        if state == 0:
            return 0

        if state == 1:
            area = self.a_tilted
        elif state == 2:
            area = self.a_opened

        return 0.7 * self.c_ref * (area * np.sqrt(self.hight)) * np.sqrt(abs(t_i - t_e))