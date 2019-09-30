
from math import sqrt, log
from struct import unpack
from datetime import datetime, timedelta
from configparser import ConfigParser, NoSectionError, NoOptionError
from iono import Iono


class Ips42Iono(Iono):

    def __init__(self, debug_level=0):
        super().__init__(debug_level)
        self.ionosonde_model = 'IPS-42'

    def load(self, file_name):
        with open(file_name, 'rb') as file:
            head = file.read(64)
            data = file.read(512*576//8)

        data_tuple = unpack('H'*(len(data)//2), data)
        self.data = [[0 for x in range(576)] for y in range(512)]

        for f in range(576):
            for h in range(512//16):
                i = f*512//16+h
                for z in range(16):
                    alt = 511-(h*16+15-z)
                    bit = (data_tuple[i] >> z) & 1
                    self.data[alt][f] = 0 if bit else 1

        self.data[0][0] = -1

        self._extract_info()
        if self.date:
            self.load_sunspot()

    def _extract_info(self):

        try:
            s4 = self._img2digit(36, 0)
            s3 = self._img2digit(36, 16)
            s2 = self._img2digit(36, 32)
            s1 = self._img2digit(36, 48)
            station = s4*1000 + s3*100 + s2*10 + s1
        except ValueError:
            pass

        try:
            y2 = self._img2digit(36, 80)
            y1 = self._img2digit(36, 96)
            year = y2*10 + y1
            year += 1900 if year > 57 else 2000
        except ValueError:
            pass

        try:
            d3 = self._img2digit(36, 128)
            d2 = self._img2digit(36, 144)
            d1 = self._img2digit(36, 160)
            doy = d3*100+d2*10+d1
        except ValueError:
            pass

        try:
            h2 = self._img2digit(36, 192)
            h1 = self._img2digit(36, 208)
            hour = h2*10 + h1
        except ValueError:
            pass

        try:
            m2 = self._img2digit(36, 224)
            m1 = self._img2digit(36, 240)
            minute = m2*10 + m1
        except ValueError:
            pass

        names = vars()
        if ('year' in names) and ('hour' in names) and ('minute' in names):
            self.date = datetime(year, 1, 1, hour, minute, 0)
            self.date += timedelta(doy-1)

        if 'station' in names:
            config = ConfigParser()
            config_path = './data/IPS-42.ini'
            config.read(config_path)

            try:
                self.station_name = config.get(str(station), 'name')
            except (NoSectionError):
                pass

            try:
                self.lat = config.get(str(station), 'lat')
            except (NoSectionError):
                pass

            try:
                self.lon = config.get(str(station), 'lon')
            except (NoSectionError):
                pass

            try:
                self.gyro = config.get(str(station), 'gyro')
            except (NoSectionError):
                pass

            try:
                self.dip = config.get(str(station), 'dip')
            except (NoSectionError):
                pass

            try:
                self.timezone = int(config.get(str(station), 'timezone'))
            except (NoSectionError, ValueError):
                pass

    def _img2digit(self, offset_alt, offset_f):
        A = 1
        B = 1 << 1
        C = 1 << 2
        D = 1 << 3
        E = 1 << 4
        F = 1 << 5
        G = 1 << 6
        H = 1 << 7
        J = 1 << 8
        digits = [
                  A | B | C | D | E | F,  # 0
                  H | J,  # 1
                  A | B | G | E | D,  # 2
                  A | B | C | D | G,  # 3
                  F | G | H | J,  # 4
                  A | F | G | C | D,  # 5
                  F | E | D | C | G,  # 6
                  A | B | C,  # 7
                  A | B | C | D | E | F | G,  # 8
                  A | B | C | F | G  # 9
                 ]

        if self.debug_level > 0:
            for h in range(25):
                for f in range(13):
                    print(self.data[offset_alt+h][offset_f+f], end='')
                print()
            print()

        a = self.data[offset_alt][offset_f+7]
        b = self.data[offset_alt+6][offset_f+12]
        c = self.data[offset_alt+18][offset_f+12]
        d = self.data[offset_alt+24][offset_f+7]
        e = self.data[offset_alt+18][offset_f]
        f = self.data[offset_alt+6][offset_f]
        g = self.data[offset_alt+12][offset_f+7]
        h = self.data[offset_alt+6][offset_f+6]
        j = self.data[offset_alt+18][offset_f+6]
        array = [a, b, c, d, e, f, g, h, j]

        p = 0
        for i, e in enumerate(array):
            p |= e << i

        for i, d in enumerate(digits):
            if d == p:
                return i
        raise ValueError('Digit is not recognized')

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


if __name__ == '__main__':
    iono = Ips42Iono(debug_level=1)
    iono.load('./examples/ips42/01h00m.ion')
