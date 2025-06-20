import numpy as np
from scipy import signal
from datetime import datetime
from struct import unpack
import bz2
import cv2
from ionogram import Ionogram
from colormaps import cmap_two_comp


class IonogramVisrc2t(Ionogram):

    def __init__(self, debug_level=0):
        super().__init__()
        self.station_name = "IION"
        self.ionosonde_model = "VISRC2-t"
        self.lat = 49.6766
        self.lon = 36.2952
        self.gyro = 1.4
        self.dip = 66.7
        self.debug_level = debug_level
        self.cmap = cmap_two_comp
        self.ox_mode = True

    def __read_raw_data(self, file_name):
        open_proc = bz2.open if file_name.endswith(".bz2") else open
        with open_proc(file_name, "rb") as file:
            magic = unpack("4s", file.read(4))[0]
            buffer = file.read(4 + 8 + 4 + 4 + 8 + 8)
            (version, date, self.n_height, n_scan, self.rx_rate, rx_bandwidth) = unpack(
                "<iQiidd", buffer
            )

            self.date = datetime.utcfromtimestamp(date)
            self.ranges = [
                h * 3e8 / self.rx_rate / 2 / 1000 for h in range(self.n_height)
            ]

            reserved = file.read(1024 - 8)

            if self.debug_level > 0:
                print(
                    f"Version: {version}\n"
                    f"Date: {date} ({self.date})\n"
                    f"Number of heights: {self.n_height}\n"
                    f"Number of scans: {n_scan}\n"
                    f"RX rate: {self.rx_rate}\n"
                    f"RX bandwidth: {rx_bandwidth}\n"
                )

            raw_data = []
            for _ in range(n_scan):
                freq, amp, bittime, code_length = unpack("fffi", file.read(16))

                buffer = file.read(4 * code_length)
                code_real = unpack("f" * code_length, buffer)
                code_real = [x for i, x in enumerate(code_real) if i < code_length]
                buffer = file.read(4 * code_length)
                code_image = unpack("f" * code_length, buffer)
                code_image = [x for i, x in enumerate(code_image) if i < code_length]

                if self.debug_level > 1:
                    print(
                        f"Freq: {freq}\n"
                        f"Amp: {amp}\n"
                        f"Bittime: {bittime}\n"
                        f"Code length: {code_length}\n"
                        f"Code (Real part): {code_real}\n"
                        f"Code (Image part): {code_image}\n"
                        f"\n"
                    )

                sa = unpack("f" * 2 * self.n_height, file.read(4 * 2 * self.n_height))
                sa = [complex(sa[i], sa[i + 1]) for i in range(0, len(sa), 2)]
                sb = unpack("f" * 2 * self.n_height, file.read(4 * 2 * self.n_height))
                sb = [complex(sb[i], sb[i + 1]) for i in range(0, len(sb), 2)]
                raw_data.append(
                    {
                        "freq": freq,
                        "amp": amp,
                        "bittime": bittime,
                        "code_real": code_real,
                        "code_image": code_image,
                        "sa": sa,
                        "sb": sb,
                    }
                )
            return raw_data

    def __calc_code_complementary(self, code, bittime):
        dt = 1 / self.rx_rate
        code = list(reversed(code))
        cc_length = int(bittime * len(code) / dt)
        cc = [complex(0, code[int(dt * t / bittime)]) for t in range(cc_length)]
        n_height_new = len(signal.convolve(np.zeros(self.n_height), cc, mode="valid"))
        return cc, n_height_new

    def load(self, file_name):

        if file_name.endswith("rad.bz2") or file_name.endswith("rad"):
            self.__make_iono_from_raw(file_name)
        elif file_name.endswith("ig.bz2") or file_name.endswith("ig"):
            self.__load_ionogram(file_name)

        self.load_sunspot()

    def __load_ionogram(self, file_name):
        open_proc = bz2.open if file_name.endswith(".bz2") else open
        with open_proc(file_name, "rt") as file:
            header = [
                s.replace("#", "").strip()
                for s in file.readlines()
                if s.startswith("#")
            ]

        parameters = dict()
        for line in header:
            if line.startswith("datetime: "):
                d = line[line.index(":") + 2 :]
                self.date = datetime.fromisoformat(d)
            elif ":" in line:
                key = line.split(":")[0].strip()
                value = line.split(":")[1].strip()
                parameters[key] = value

        self.frequencies = [float(f) for f in parameters["freqs"].split()]
        self.ranges = [float(h) for h in parameters["heights"].split()]
        self.n_freq = float(parameters["n_freq"])

        self.data = np.loadtxt(file_name)

        min_h_index = 0
        for r in self.ranges:
            if r > 100:
                break
            min_h_index += 1

        self.ranges = self.ranges[min_h_index:]
        self.n_height = len(self.ranges)

        self.data = np.delete(self.data, [h for h in range(min_h_index)], axis=0)

        self.data = np.flip(self.data, 0)

        min_val = np.min(self.data)
        max_val = np.max(self.data)

        max_abs = max(abs(min_val), abs(max_val))

        if abs(min_val / max_abs) < 0.95:
            self.data[self.data < 0] *= -max_abs / min_val

        if abs(max_val / max_abs) < 0.95:
            self.data[self.data < 0] *= max_abs / max_val

        # self.data[0][0] = -max_abs
        # self.data[-1][-1] = max_abs

        # hist = np.histogram(self.data, bins=50)
        # np.savetxt('out_y.txt', hist[0])
        # np.savetxt('out_x.txt', hist[1])

    def __make_iono_from_raw(self, file_name):

        raw_data = self.__read_raw_data(file_name)

        frequencies_hz = list(set([d["freq"] for d in raw_data]))
        frequencies_hz.sort()

        self.n_freq = len(frequencies_hz)
        self.frequencies = np.array(frequencies_hz) / 1e6

        amplitudes_a = np.zeros((self.n_freq, self.n_height), dtype=complex)

        amplitudes_b = np.zeros((self.n_freq, self.n_height), dtype=complex)

        Is = np.zeros((self.n_freq, self.n_height), dtype=complex)

        dt = 1 / self.rx_rate

        for d in raw_data:
            if d["amp"] < 1e-6:
                continue

            current_code = d["code_real"]
            bittime = d["bittime"]
            code_complementary, n_height_new = self.__calc_code_complementary(
                current_code, bittime
            )

            if amplitudes_a.shape != (self.n_freq, n_height_new):
                amplitudes_a.resize((self.n_freq, n_height_new))

            if amplitudes_b.shape != (self.n_freq, n_height_new):
                amplitudes_b.resize((self.n_freq, n_height_new))

            if Is.shape != (self.n_freq, n_height_new):
                Is.resize((self.n_freq, n_height_new))

            sa = signal.convolve(d["sa"], code_complementary, mode="valid")
            sb = signal.convolve(d["sb"], code_complementary, mode="valid")

            pos = frequencies_hz.index(d["freq"])
            amplitudes_a[pos] += np.array(sa)
            amplitudes_b[pos] += np.array(sb)

            Is[pos] += np.array(sa) * np.conj(np.array(sa)) + np.array(sb) * np.conj(
                np.array(sb)
            )

        Vs = [None] * len(frequencies_hz)
        IIs = [None] * len(frequencies_hz)

        for f, freq in enumerate(frequencies_hz):
            Vs[f] = [
                1 if x < 0 else -1
                for x in 2 * (amplitudes_a[f] * np.conj(amplitudes_b[f])).real
            ]

            IIs[f] = [z.real**1e-2 for z in Is[f]]

            average = np.average(IIs[f])
            IIs[f] = [x - average for x in IIs[f]]

            IIs[f] = [x * v for (x, v) in zip(IIs[f], Vs[f])]

        self.data = np.flip(np.array(IIs).T, 0)

        self.data[0][0] = np.min(IIs)
        self.data[-1][-1] = np.max(IIs)

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
        labels = [
            "{:.0f}".format(self.coord_to_freq(float(x))) for x in range(f_min, f_max)
        ]
        labels = list(set(labels))
        return labels

    def freq_to_coord(self, freq):
        freq = float(freq)
        i = self.__find_closest_freq(freq)
        df = self.frequencies[i + 1] - self.frequencies[i]
        return i + (freq - self.frequencies[i]) / df

    def coord_to_freq(self, coord):
        f1 = self.frequencies[int(coord)]
        f2 = self.frequencies[int(coord) + 1]
        df = f2 - f1
        return f1 + (coord - int(coord)) * df

    def __find_closest_freq(self, freq):
        if freq <= self.frequencies[0]:
            return -1
        for i, f in enumerate(self.frequencies):
            if f - freq >= 0:
                return i - 1
        return len(self.frequencies) - 2

    def clean_ionogram(self):
        sign_vals = np.sign(self.data)
        abs_vals = np.fabs(self.data)
        abs_vals /= np.max(abs_vals)
        abs_vals *= 255

        abs_vals = cv2.fastNlMeansDenoising(abs_vals.astype("uint8"), None, 7, 7, 7)

        self.data = abs_vals * sign_vals

        min_val = np.min(self.data)
        max_val = np.max(self.data)

        max_abs = max(abs(min_val), abs(max_val))

        self.data[0][0] = -max_abs
        self.data[-1][-1] = max_abs
