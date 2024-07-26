from math import log
from configparser import ConfigParser, NoSectionError, NoOptionError
from datetime import datetime
import numpy as np
from iono import Iono
from colormaps import cmap_two_comp


class RinanIono(Iono):

    def __init__(self):
        super().__init__()

    def load(self, file_name):
        with open(file_name, encoding="ascii") as file:
            lines = [s.strip() for s in file.readlines()]

        if file_name.lower().endswith('.pion'):
            self.cmap = cmap_two_comp
            self.ox_mode = True

        index_freq = lines.index('Frequency Set')
        index_end_of_header = lines.index('END')

        self.frequencies = []
        self.n_freq = index_end_of_header - index_freq - 1

        index_data = lines.index('DATA')
        index_end_of_data = lines[index_end_of_header +
                                  1:].index('END')+index_end_of_header+1

        data_temp = [0] * self.n_freq

        for i, line in enumerate(lines):
            if line.startswith('Observatory'):
                self.station_name = line.split(':')[-1].strip()
            elif line.startswith('Location'):
                location = line.split(':')[-1].strip().split(', ')

                def convert_to_decimal(coord):
                    d = float(coord[:2])
                    m = float(coord[3:5])
                    s = float(coord[6:8])
                    return d + m/60 + s/3600
                lat = convert_to_decimal(location[0][:-2])
                lon = convert_to_decimal(location[1][:-2])
                self.lat = lat * (1 if location[0][-1] == 'N' else -1)
                self.lon = lon * (1 if location[1][-1] == 'E' else -1)
            elif line.startswith('z0'):
                self.z0 = float(line.split('=')[-1].strip())
            elif line.startswith('dz'):
                self.dz = float(line.split('=')[-1].strip())
            elif line.startswith('Nstrob'):
                self.nstrob = int(line.split('=')[-1].strip())
            elif line.startswith('Nsound'):
                self.nsound = int(line.split('=')[-1].strip())
            elif line.startswith('TIME'):
                date = line.split('=')[-1].strip()
                if date.endswith(' UT') or date.endswith(' LT'):
                    date = date[:-3]
                self.date = datetime.strptime(date, '%d.%m.%Y %H:%M:%S')

            if i > index_freq and i < index_end_of_header:
                self.frequencies.append(float(line.split()[-1].strip()))

            if i > index_data and i < index_end_of_data:
                if file_name.lower().endswith('.pion'):
                    row = [-99999 if 49999<=float(x)<=50000 else float(x) for x in line.split()]
                else:
                    row = [log(abs(float(x))+1, 10) for x in line.split()]
                data_temp[i - index_data - 1] = row

        self.n_rang = len(data_temp[0])
        self.ranges = [self.z0 + self.dz * h for h in range(self.n_rang)]

        self.data = \
            [[0 for x in range(self.n_freq)] for y in range(self.n_rang)]

        for f in range(self.n_freq):
            for h in range(self.n_rang):
                self.data[h][f] = data_temp[f][self.n_rang - h - 1]

        self.data = np.array(self.data)

        n_freq = self.data.shape[1]

        if not file_name.lower().endswith('.pion'):
            for i in range(n_freq):
                avarage = np.average(self.data[:, i])
                self.data[:, i] -= avarage

            self.data[self.data < 0] = 0
        # self.data[0][0] = -np.max(self.data)

        self.load_sunspot()

        config = ConfigParser()
        config_path = './data/Rinan.ini'
        config.read(config_path)

        if self.lat > 0:
            station = 'IION'
        else:
            station = 'UAS'

        try:
            self.gyro = config.get(station, 'gyro')
        except (NoSectionError):
            pass

        try:
            self.dip = config.get(station, 'dip')
        except (NoSectionError):
            pass

        try:
            self.timezone = int(config.get(str(station), 'timezone'))
        except (NoSectionError, NoOptionError, ValueError):
            pass

    def get_extent(self):
        left = self.freq_to_coord(self.frequencies[0])
        right = self.freq_to_coord(self.frequencies[-1])
        bottom = self.ranges[0]
        top = self.ranges[-1]
        return [left, right, bottom, top]

    def get_freq_tics(self):
        return [self.freq_to_coord(x) for x in self.get_freq_labels()]

    def get_freq_labels(self):
        f_min = int(self.get_extent()[0])
        f_max = int(self.get_extent()[1])
        labels = ['{:.0f}'.format(self.coord_to_freq(float(x)))
                  for x in range(f_min, f_max)]
        labels = list(set(labels))
        return labels

    def freq_to_coord(self, freq):
        freq = float(freq)
        i = self.__find_closest_freq(freq)
        df = self.frequencies[i+1]-self.frequencies[i]
        return i + (freq - self.frequencies[i]) / df

    def coord_to_freq(self, coord):
        f1 = self.frequencies[int(coord)]
        f2 = self.frequencies[int(coord)+1]
        df = f2 - f1
        return f1 + (coord - int(coord)) * df

    def __find_closest_freq(self, freq):
        if freq <= self.frequencies[0]:
            return -1
        for i, f in enumerate(self.frequencies):
            if f - freq >= 0:
                return i-1
        return len(self.frequencies)-2


if __name__ == '__main__':
    iono = RinanIono()
    iono.load('./examples/rinan/20170620_1600_iono.ion')
    print(iono.coord_to_freq(iono.freq_to_coord(8.01)))
