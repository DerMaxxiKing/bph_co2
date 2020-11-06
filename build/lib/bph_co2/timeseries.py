import pandas as pd
import numpy as np


class Timeseries(object):
    """
    Interpolation schemes:

    'linear':       linear interpolation
    'previous':     take the value from the nearest previous entry
    """

    @classmethod
    def from_csv(cls, filename, *args, **kwargs):
        data = pd.read_csv(filename, delimiter=';')
        data.set_index('Time', inplace=True)
        return cls(*args, data=data, **kwargs)

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name', None)
        self.data = kwargs.get('data')
        self.interpolation_scheme = kwargs.get('interpolation_scheme', 'linear')

    def current_value(self, time, columns=None):

        if type(self.data) in [int, float, str]:
            return self.data
        if isinstance(self.data, pd.DataFrame):
            try:
                return self.data.loc[time]
            except KeyError:
                # interpolate
                index = bisection(self.data.index.values, time)
                vals = self.data.iloc[[index, index+1]]

                x0 = vals.index[0]
                x1 = vals.index[1]
                y0 = vals.iloc[0]
                y1 = vals.iloc[1]

                return interp_values(x0, x1, y0, y1, time, scheme=self.interpolation_scheme)

        elif isinstance(self.data, np.ndarray):
            index = bisection(self.data[0, :], time)

            x0 = self.data[0, index]
            x1 = self.data[0, index+1]
            y0 = self.data[1:, index]
            y1 = self.data[1:, index+1]

            return interp_values(x0, x1, y0, y1, time, scheme=self.interpolation_scheme)
        else:
            return self.data


def bisection(array, value):
    '''Given an ``array`` , and given a ``value`` , returns an index j such that ``value`` is between array[j]
    and array[j+1]. ``array`` must be monotonic increasing. j=-1 or j=len(array) is returned
    to indicate that ``value`` is out of range below and above respectively.'''
    n = len(array)
    if (value < array[0]):
        return -1
    elif (value > array[n-1]):
        return n
    jl = 0  # Initialize lower
    ju = n-1    # and upper limits.
    while (ju-jl > 1):  # If we are not yet done,
        jm=(ju+jl) >> 1 # compute a midpoint with a bitshift
        if (value >= array[jm]):
            jl = jm   # and replace either the lower limit
        else:
            ju = jm     # or the upper limit, as appropriate.
        # Repeat until the test condition is satisfied.
    if (value == array[0]): # edge cases at bottom
        return 0
    elif (value == array[n-1]): # and top
        return n-1
    else:
        return jl


def interp_values(x0, x1, y0, y1, time, scheme='linear'):

    if scheme == 'linear':
        return y0 + (y1-y0) / (x1 - x0) * (time - x0)
    elif scheme == 'previous':
        return y0