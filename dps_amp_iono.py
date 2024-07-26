from datetime import datetime
from math import sin
from iono import Iono
from colormaps import cmap_two_comp


class DpsAmpIono(Iono):

    def __init__(self):
        super().__init__()
        self.ursi_code = None
        self.cmap = cmap_two_comp
        self.ox_mode = True

    def load(self, file_name):

        with open(file_name, "r", encoding="ascii") as file:
            lines = [line[:-1] for line in file.readlines()]

        self.date = datetime.strptime(lines[0], "%Y.%m.%d (%j) %H:%M:%S.%f")

        for line in lines[1:4]:
            if line.startswith("Station name"):
                self.station_name = line.split(":")[-1].strip()
            elif line.startswith("URSI code"):
                self.ursi_code = line.split(":")[-1].strip()
            elif line.startswith("Ionosonde model"):
                self.ionosonde_model = line.split(":")[-1].strip()

        self.columns = [line.strip() for line in lines[4].split()]

        data = {x: [] for x in self.columns}
        for line in lines[5:]:
            values = line.split()
            for n_col, value in enumerate(values):
                data[self.columns[n_col]].append(value)

        self.frequencies = sorted([float(x) for x in set(data["Freq"])])
        self.ranges = sorted([float(x) for x in set(data["Range"])])

        self.n_freq = len(self.frequencies)
        self.n_rang = len(self.ranges)

        self.data = [[0 for x in range(self.n_freq)] for y in range(self.n_rang)]

        for i, amp in enumerate(data["Amp"]):
            freq = float(data["Freq"][i])
            rang = float(data["Range"][i])
            pol = int(data["Pol"][i])
            az = float(data["Az"][i])
            zn = float(data["Zn"][i])
            i_freq = self.frequencies.index(freq)
            i_rang = self.ranges.index(rang)

            if az == 0 and zn == 0:
                self.data[self.n_rang - i_rang - 1][i_freq] = float(amp) * sin(pol)

        self.load_sunspot()

    def get_extent(self):
        left = self.frequencies[0]
        right = self.frequencies[-1]
        bottom = self.ranges[0]
        top = self.ranges[-1]
        return [left, right, bottom, top]

    def get_freq_tics(self):
        return [float(x) for x in self.get_freq_labels()]

    def get_freq_labels(self):
        return [
            "{:.1f}".format(i)
            for i in range(int(self.frequencies[0]), int(self.frequencies[-1]) + 1)
        ]

    def get_ursi_code(self):
        return self.ursi_code


if __name__ == "__main__":
    iono = DpsAmpIono()
    iono.load("./examples/dps_amp/00_00.txt")
    print(iono.get_extent())
