from math import log
from struct import unpack
from datetime import datetime, timedelta
from configparser import ConfigParser, NoSectionError, NoOptionError
from ionogram import Ionogram


class IonogramIps42(Ionogram):

    def __init__(self, debug_level=0):
        super().__init__(debug_level)
        self.ionosonde_model = "IPS-42"

    def load(self, file_name):
        with open(file_name, "rb") as file:
            head = file.read(64)
            data = file.read(512 * 576 // 8)

        data_tuple = unpack("H" * (len(data) // 2), data)
        self.data = [[0 for x in range(576)] for y in range(512)]

        for f in range(576):
            for h in range(512 // 16):
                i = f * 512 // 16 + h
                for z in range(16):
                    alt = 511 - (h * 16 + 15 - z)
                    bit = (data_tuple[i] >> z) & 1
                    self.data[alt][f] = 0 if bit else 1

        # self.data[0][0] = -1

        self._extract_info()
        if self.date:
            self.load_sunspot()

    def _digit_recognize(self, offset_f):
        offset_alt = 36
        digit = None
        for da in range(-1, 2):
            for df in range(-1, 2):
                try:
                    digit = self._img2digit(offset_alt + da, offset_f + df)
                except ValueError:
                    pass
                else:
                    return digit
        if self.debug_level == 0:
            self._print_digit(offset_alt, offset_f)
        raise ValueError("Digit is not recognized")

    def _extract_info(self):

        try:
            y2 = self._digit_recognize(80)
            y1 = self._digit_recognize(96)
            year = y2 * 10 + y1
            year += 1900 if year > 57 else 2000

            d3 = self._digit_recognize(128)
            d2 = self._digit_recognize(144)
            d1 = self._digit_recognize(160)
            doy = d3 * 100 + d2 * 10 + d1

            h2 = self._digit_recognize(192)
            h1 = self._digit_recognize(208)
            hour = h2 * 10 + h1

            m2 = self._digit_recognize(224)
            m1 = self._digit_recognize(240)
            minute = m2 * 10 + m1

            self.date = datetime(year, 1, 1, hour, minute, 0)
            self.date += timedelta(doy - 1)
        except ValueError:
            self.date = datetime.now()
            print("Date is not recognized. Current date is used.")

        try:
            s4 = self._digit_recognize(0)
            s3 = self._digit_recognize(16)
            s2 = self._digit_recognize(32)
            s1 = self._digit_recognize(48)
            station = s4 * 1000 + s3 * 100 + s2 * 10 + s1
            is_station = True
        except ValueError:
            is_station = False
            print("Station is not recognized. Default parameters are used.")

        if is_station:
            config = ConfigParser()
            config_path = "./data/IPS-42.ini"
            config.read(config_path)

            try:
                self.station_name = config.get(str(station), "name")
            except (NoSectionError, NoOptionError):
                pass

            try:
                self.lat = config.get(str(station), "lat")
            except (NoSectionError, NoOptionError):
                pass

            try:
                self.lon = config.get(str(station), "lon")
            except (NoSectionError, NoOptionError):
                pass

            try:
                self.gyro = config.get(str(station), "gyro")
            except (NoSectionError, NoOptionError):
                pass

            try:
                self.dip = config.get(str(station), "dip")
            except (NoSectionError, NoOptionError):
                pass

            try:
                self.timezone = int(config.get(str(station), "timezone"))
            except (NoSectionError, NoOptionError, ValueError):
                pass

    def _print_digit(self, offset_alt, offset_f):
        for h in range(25):
            print()
            for f in range(13):
                print(self.data[offset_alt + h][offset_f + f], end="")
        print()

    def _img2digit(self, offset_alt, offset_f):
        LEVEL = 8
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
            A | B | C | F | G,  # 9
        ]

        if self.debug_level > 0:
            self._print_digit(offset_alt, offset_f)
            print(offset_alt, offset_f, sep=", ")

        """
        aaaaaaaaaaaaa
        f     h     b
        f     h     b
        f     h     b
        f     h     b
        f     h     b
        ggggggggggggg
        e     j     c
        e     j     c
        e     j     c
        e     j     c
        e     j     c
        ddddddddddddd
        """
        a = sum(self.data[offset_alt][offset_f : offset_f + 13]) + sum(
            self.data[offset_alt + 1][offset_f : offset_f + 13]
        )
        b = sum(self.data[offset_alt + i][offset_f + 12] for i in range(13))
        c = sum(self.data[offset_alt + i + 13][offset_f + 12] for i in range(13))
        d = sum(self.data[offset_alt + 23][offset_f : offset_f + 13]) + sum(
            self.data[offset_alt + 24][offset_f : offset_f + 13]
        )
        e = sum(self.data[offset_alt + i + 13][offset_f] for i in range(13))

        f = sum(self.data[offset_alt + i][offset_f] for i in range(13))
        g = sum(self.data[offset_alt + 12][offset_f : offset_f + 13]) + sum(
            self.data[offset_alt + 13][offset_f : offset_f + 13]
        )

        h = sum(self.data[offset_alt + i][offset_f + 6] for i in range(13))
        j = sum(self.data[offset_alt + i + 13][offset_f + 6] for i in range(13))

        array = [a, b, c, d, e, f, g, h, j]

        if self.debug_level > 0:
            print(array)

        if self.debug_level > 0:
            print([i > LEVEL for i in array])

        p = 0
        for i, e in enumerate(array):
            p |= (e > LEVEL) << i

        for i, d in enumerate(digits):
            if d == p:
                return i

        raise ValueError("Digit is not recognized")

    def get_extent(self):
        left = self.freq_to_coord(1)
        right = self.freq_to_coord(22.6)
        bottom = -2
        top = 796
        return [left, right, bottom, top]

    def get_freq_tics(self):
        return [self.freq_to_coord(x) for x in self.get_freq_labels()]

    def get_freq_labels(self):
        return [1.0, 1.4, 2.0, 2.8, 4.0, 5.6, 8.0, 11.4, 16.0, 22.6]

    def freq_to_coord(self, freq):
        return log(float(freq), 22.6) * 575

    def coord_to_freq(self, coord):
        return 22.6 ** (coord / 575)
