
from math import sqrt, log
from struct import unpack
from iono import Iono


class Ips42Iono(Iono):

    def __init__(self):
        super().__init__()

    def load(self, file_name):
        with open(file_name, 'rb') as file:
            #  should be read but image is not proper
            #  head = file.read(64)
            data = file.read(512*576//8)

        data_tuple = unpack('H'*(len(data)//2), data)
        self.data = [[0 for x in range(576)] for y in range(512)]

        for f in range(576):
            for h in range(512//16):
                i = f*512//16+h
                for z in range(16):
                    alt = 511-(h*16+15-z)
                    bit = (data_tuple[i] >> z) & 1
                    self.data[alt][f] = 0 if bit else -1

        self.data[0][0] = 1

    def get_extent(self):
        left = 0
        right = 22.5
        bottom = -2
        top = 796
        return [left, right, bottom, top]

    def get_freq_tics(self):
        return [self.freq_to_coord(x) for x in self.get_freq_labels()]

    def get_freq_labels(self):
        # [1, 1.4, 2, 2.8, 4, 5.6, 8, 11.4, 16, 22.4]
        return ['{:.1f}'.format(sqrt(2) ** i) for i in range(10)]

    def freq_to_coord(self, freq):
        return log(float(freq), sqrt(2)) * 2.5

    def coord_to_freq(self, coord):
        return sqrt(2) ** (coord / 2.5)
