
import numpy as np
from datetime import datetime
from os import path
from iono import Iono


class BazisIono(Iono):

    def __init__(self):
        super().__init__()

    def load(self, file_name):
        with open(file_name, 'rb') as file:
            header_size = 21
            date = file.read(header_size)[1:-1].decode("utf-8")
            self.date = datetime.strptime(date, '%d-%m-%Y %H:%M:%S')

            self.start_freq = 1.0
            self.n_rang = 250
            file_size = path.getsize(file_name)
            if file_size == 1200021:
                self.n_freq = 300
            elif file_size == 1600021:
                self.n_freq = 400
            else:
                return

            self.data = \
                [[0 for x in range(self.n_freq)] for y in range(self.n_rang)]

            buf = file.read(file_size - header_size)
            offset = 0

            for f in range(self.n_freq):
                for r in range(16):  # number of repeats
                    for h in range(self.n_rang):
                        z = self.n_rang - h - 1
                        self.data[z][f] += float(buf[offset]) ** 2  # -128.0
                        offset += 1

            for f in range(self.n_freq):
                for h in range(self.n_rang):
                    z = self.n_rang - h - 1
                    if self.data[h][f] <= 0 or self.get_altitude(z) < 100.0:
                        self.data[h][f] = 0

            self.data = np.array(self.data)

            n_freq = self.data.shape[1]
            for i in range(n_freq):
                avarage = np.average(self.data[:, i])
                self.data[:, i] -= avarage

            self.data[self.data < 0] = 0

            self.data[0][0] = -np.max(self.data)

    def get_altitude(self, h):
        # TODO check start and step values
        return 3 + h * 3

    def get_extent(self):
        left = self.start_freq
        right = left + self.n_freq * 0.025
        bottom = self.get_altitude(0)
        top = self.get_altitude(self.n_rang)
        return [left, right, bottom, top]

    def get_freq_tics(self):
        return [float(x) for x in self.get_freq_labels()]

    def get_freq_labels(self):
        return ['{:.1f}'.format(i) for i in range(
            int(self.start_freq), int(self.get_extent()[1]))]


if __name__ == '__main__':
    iono = BazisIono()
    iono.load('./examples/iion/NF190606.50')
    print(iono.date)
