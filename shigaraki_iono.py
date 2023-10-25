
import numpy as np
from datetime import datetime
from os import path
from iono import Iono


class ShigarakiIono(Iono):

    def __init__(self):
        super().__init__()
        self.timezone = 9  # JST
        self.lat = 34.85
        self.lon = 136.1
        self.gyro = 1.16
        self.dip = 49.0

    def load(self, file_name):
        self.frequencies = []
        with open(file_name, 'r') as file:
            lines = [s.strip() for s in file.readlines()]

        self.station_name = lines[0].split()[0]
        date = lines[1].split(': ')[-1]
        self.date = datetime.strptime(date, '%Y-%m-%d %H:%M')
        self.fmin = float(lines[3].split(': ')[-1])
        self.fmax = float(lines[4].split(': ')[-1])
        self.hmin = float(lines[5].split(': ')[-1])
        self.hmax = float(lines[6].split(': ')[-1])
        self.frequencies = [float(f) for f in lines[9].split()]
        self.altitudes = []
        self.data = []
        m = float('-Inf')
        for i, line in enumerate(lines):
            if i > 9:
                tmp = [float(x)+90 for x in line.split()]
                self.altitudes.append(tmp[0])
                data = tmp[1:]
                self.data.append(data)
                _m = max(data)
                if _m > m:
                    m = _m
        self.data.reverse()
        # self.data[0][0] = -m

        self.data = np.array(self.data)

        n_freq = self.data.shape[1]
        for i in range(n_freq):
            avarage = np.average(self.data[:, i])
            self.data[:, i] -= avarage

        self.data[self.data < 0] = 0

        # self.data[0][0] = -np.max(self.data)

        self.load_sunspot()

    def get_altitude(self, h):
        return h

    def get_extent(self):
        left = self.fmin
        right = self.fmax
        bottom = self.hmin
        top = self.hmax
        return [left, right, bottom, top]

    def get_freq_tics(self):
        return [float(x) for x in self.get_freq_labels()]

    def get_freq_labels(self):
        return ['{:.1f}'.format(i) for i in range(
            int(self.get_extent()[0]), int(self.get_extent()[1]))]


if __name__ == '__main__':
    iono = ShigarakiIono()
    iono.load('./examples/shigaraki/201806071645_ionogram.txt')
    print(iono.date, iono.sunspot)
