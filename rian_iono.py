from math import log
from datetime import datetime
from iono import Iono


class RianIono(Iono):

    def __init__(self):
        super().__init__()

    def load(self, file_name):
        with open(file_name) as file:
            lines = [s.strip() for s in file.readlines()]

        index_freq = lines.index('Frequency Set')
        index_end_of_header = lines.index('END')

        self.frequencies = []
        self.n_freq = index_end_of_header - index_freq - 1

        index_data = lines.index('DATA')
        index_end_of_data = lines[index_end_of_header+1:].index('END')+index_end_of_header+1

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
                self.date = datetime.strptime(date, '%d.%m.%Y %H:%M:%S')

            if i > index_freq and i < index_end_of_header:
                self.frequencies.append(float(line.split()[-1].strip()))

            if i > index_data and i < index_end_of_data:
                row = [log(float(x), 10) for x in line.split()]
                data_temp[i - index_data - 1] = row

        self.n_rang = len(data_temp[0])
        self.ranges = [self.z0 + self.dz * h for h in range(self.n_rang)]

        self.data = \
            [[0 for x in range(self.n_freq)] for y in range(self.n_rang)]

        max_val = float('-inf')
        for f in range(self.n_freq):
            for h in range(self.n_rang):
                self.data[h][f] = data_temp[f][self.n_rang - h - 1]
                if self.data[h][f] > max_val:
                    max_val = self.data[h][f]
        self.data[0][0] = -max_val

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
        labels = ['{:.0f}'.format(self.coord_to_freq(float(x))) for x in range(f_min, f_max)]
        labels = list(set(labels))
        return labels

    def freq_to_coord(self, freq):
        step = self.frequencies[1] / self.frequencies[0]
        return log(float(freq), step)

    def coord_to_freq(self, coord):
        step = self.frequencies[1] / self.frequencies[0]
        return step ** coord


if __name__ == '__main__':
    iono = RianIono()
    iono.load('./examples/rian/20170620_1600_iono.ion')
