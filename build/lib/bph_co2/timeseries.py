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

        delimiter = kwargs.get('delimiter', ';')
        decimal = kwargs.get('delimiter', ',')

        data = pd.read_csv(filename, delimiter=delimiter, decimal=decimal)
        data.set_index('Time', inplace=True)
        return cls(*args, data=data, **kwargs)

    def __init__(self, *args, **kwargs):

        self.name = kwargs.get('name', None)
        self.data = kwargs.get('data')
        self.interpolation_scheme = kwargs.get('interpolation_scheme', 'linear')

    def current_value(self, time, columns=None):

        if type(self.data) in [int, float, str]:
            return self.data

        if not isinstance(time, np.ndarray):
            time = np.array([time])

        if isinstance(self.data, pd.DataFrame):
            data = self.data.reset_index().to_numpy()
        elif isinstance(self.data, np.ndarray):
            data = self.data
        else:
            return self.data

        values = np.empty([time.__len__(), data.shape[1] - 1])

        times, x_ind, y_ind = np.intersect1d(data[:, 0], time, return_indices=True)

        values[y_ind, :] = data[x_ind, 1:]

        mask = np.ones(time.shape, bool)
        mask[y_ind] = False
        timesteps_to_interp = time[mask]

        interpolated_values = np.empty([timesteps_to_interp.__len__(), data.shape[1] - 1])

        index = None
        for i in range(timesteps_to_interp.__len__()):
            index = bisection(data[:, 0], timesteps_to_interp[i], index)

            if index >= data.shape[0]-1:
                interpolated_values[i, :] = data[-1, 1:]
            else:
                interpolated_values[i, :] = interp_values(x0=data[index, 0],
                                                          x1=data[index+1, 0],
                                                          y0=data[index, 1:],
                                                          y1=data[index + 1, 1:],
                                                          time=timesteps_to_interp[i],
                                                          scheme=self.interpolation_scheme)
        values[mask, :] = interpolated_values

        if values.shape == (1, 1):
            return values[0, 0]
        elif values.shape[0] == 1:
            return values[0, :]
        elif values.shape[1] == 1:
            return values[:, 0]
        return values

        # if type(self.data) in [int, float, str]:
        #     return self.data
        # if isinstance(self.data, pd.DataFrame):
        #     try:
        #
        #         values = self.data.loc[time].values
        #         if values.shape.__len__() == 1:
        #             return values[0]
        #         else:
        #             return values
        #     except KeyError:
        #         # interpolate
        #         index = bisection(self.data.index.values, time)
        #         vals = self.data.iloc[[index, index+1]]
        #
        #         x0 = vals.index[0]
        #         x1 = vals.index[1]
        #         y0 = vals.iloc[0]
        #         y1 = vals.iloc[1]
        #
        #         values = interp_values(x0, x1, y0, y1, time, scheme=self.interpolation_scheme).values
        #
        #         if values.shape.__len__() == 1:
        #             return values[0]
        #         else:
        #             return values
        #
        # elif isinstance(self.data, np.ndarray):
        #     index = bisection(self.data[0, :], time)
        #
        #     x0 = self.data[0, index]
        #     x1 = self.data[0, index+1]
        #     y0 = self.data[1:, index]
        #     y1 = self.data[1:, index+1]
        #
        #     values = interp_values(x0, x1, y0, y1, time, scheme=self.interpolation_scheme)
        #     if values.shape.__len__() == 1:
        #         return values[0]
        #     else:
        #         return values
        # else:
        #     return self.data

def bisection(array, value, ind=None):
    '''Given an ``array`` , and given a ``value`` , returns an index j such that ``value`` is between array[j]
    and array[j+1]. ``array`` must be monotonic increasing. j=-1 or j=len(array) is returned
    to indicate that ``value`` is out of range below and above respectively.'''
    n = len(array)
    if (value < array[0]):
        return -1
    elif (value > array[n - 1]):
        return n

    if ind is None:
        jl = 0  # Initialize lower
        ju = n-1    # and upper limits.
    else:
        jl = ind  # Initialize lower
        ju = n - 1  # and upper limits.

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