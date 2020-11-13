

class Ambient(object):

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name')
        self.theta = kwargs.get('theta', 10)

    def theta_t(self, time=0):
        """
        returns the air temperature theta for time
        :param time: time [s]
        :return: air temperature theta at the time
        """

        if hasattr(self.theta, 'current_value'):
            theta = self.theta.current_value(time)
        else:
            theta = self.theta

        return theta
