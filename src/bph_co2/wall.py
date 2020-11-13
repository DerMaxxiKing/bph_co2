from .zone import BaseZone


class Wall(object):

    def __init__(self, *args, **kwargs):

        self._side_1 = None             # inside (Rsi)
        self._side_2 = None             # outside (Rse)

        self.theta_in = kwargs.get('theta_in', 20)
        self.theta_out = kwargs.get('theta_out', -10)
        self.theta_s = kwargs.get('theta_s', None)

        self.r_si = kwargs.get('r_si', 0.13)
        self.u = kwargs.get('u', 1)  # U-Value of the element
        self.r_se = kwargs.get('r_se', 0.04)
        self.alpha_k = kwargs.get('alpha_k', 2.5)

        self.orientation = kwargs.get('orientation', None)

        self.name = kwargs.get('name', '')
        self.area = kwargs.get('area', 0)

        self.side1 = kwargs.get('side1', None)
        self.side2 = kwargs.get('side2', None)

    @property
    def side1(self):
        return self._side_1

    @side1.setter
    def side1(self, value):
        self._side_1 = value

        if isinstance(self._side_1, BaseZone):
            self._side_1.add_wall(self)

    @property
    def side2(self):
        return self._side_2

    @side2.setter
    def side2(self, value):
        self._side_2 = value

        if isinstance(self._side_2, BaseZone):
            self._side_2.add_wall(self)

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        self._orientation = value

        if value is None:
            return

        if self._orientation == 'vertical':
            self.r_si = 0.13
            self.alpha_k = 2.5

        if (self.theta_in is None) or (self.theta_out is None):
            return

        if hasattr(self.theta_in, 'current_value'):
            theta_in = self.theta_in.current_value(0)
        else:
            theta_in = self.theta_in

        if hasattr(self.theta_out, 'current_value'):
            theta_out = self.theta_out.current_value(0)
        else:
            theta_out = self.theta_out

        if self._orientation == 'floor':
            if theta_in > theta_out:  # downwards
                self.r_si = 0.17
                self.alpha_k = 0.7
            else:
                self.r_si = 0.10
                self.alpha_k = 5

        elif self._orientation == 'ceiling':
            if theta_in > theta_out:  # upwards
                self.r_si = 0.10
                self.alpha_k = 5
            else:
                self.r_si = 0.17
                self.alpha_k = 0.7

    @property
    def f_konv(self, ):
        return self.r_si * self.alpha_k

    def calc_surface_temp(self, theta_in, theta_out):
        if self.theta_s is not None:
            return self.theta_s

        theta_s = theta_in - self.r_si * self.u * (theta_in - theta_out)
        return theta_s

    def calc_heat_flow(self, theta_in, theta_out):

        q = self.area * self.u * (theta_in - theta_out)
        return q



