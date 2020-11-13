

class Ventilation(object):

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name', f'Ventilation')                  # ventilation

        self.t_ex = kwargs.get('t_ex', None)                              # exhaust air temperature [°C]
        self.t_in = kwargs.get('t_in', None)                              # supply air temperature [°C]

        if self.t_ex is None:
            self.t_ex = -5

        if self.t_in is None:
            self.t_in = self.t_ex

    def supply_air_density(self, theta=None, x=0, p=101300):
        """
        Calculates the density
        :param theta: temperature in °C
        :param x: humidity ratio [kg/kg]
        :param p: Absolute Pressure [Pa]
        :return: density wet air [kg / m³]
        """

        if theta is None:
            theta = self.t_in

        rho = (1 + x) / (x + 0.6222) * p / (461.40 * (theta + 273.15))    # Humid air density[kg / m³]
        return rho

    def c_p(self, x=0):
        return (925 * x + 503) / 500. * 1000


