from datetime import datetime
from iono import Iono


class DpsAmpIono(Iono):

    def __init__(self):
        super().__init__()
        self.ursi_code = None

    def load(self, file_name):

        with open(file_name, 'r') as file:
            lines = [line[:-1] for line in file.readlines()]

        self.date = datetime.strptime(lines[0], '%Y.%m.%d (%j) %H:%M:%S.%f')

        for line in lines[1:4]:
            if line.startswith('Station name'):
                self.station_name = line.split(':')[-1].strip()
            elif line.startswith('URSI code'):
                self.ursi_code = line.split(':')[-1].strip()
            elif line.startswith('Ionosonde model'):
                self.ionosonde_model = line.split(':')[-1].strip()

        self.columns = [line.strip() for line in lines[4].split()]

        data = {x: [] for x in self.columns}
        for line in lines[5:]:
            values = line.split()
            for n_col, value in enumerate(values):
                data[self.columns[n_col]].append(value)

        self.frequencies = sorted([float(x) for x in set(data['Freq'])])
        self.ranges = sorted([float(x) for x in set(data['Range'])])

        self.n_freq = len(self.frequencies)
        self.n_rang = len(self.ranges)

        self.data = \
            [[0 for x in range(self.n_freq)] for y in range(self.n_rang)]

        for i, amp in enumerate(data['Amp']):
            freq = float(data['Freq'][i])
            rang = float(data['Range'][i])
            i_freq = self.frequencies.index(freq)
            i_rang = self.ranges.index(rang)
            sign = -1 if float(data['Pol'][i]) > 0 else 1
            self.data[self.n_rang-i_rang-1][i_freq] = float(amp)*sign

    def get_extent(self):
        left = self.frequencies[0]
        right = self.frequencies[-1]
        bottom = self.ranges[0]
        top = self.ranges[-1]
        return [left, right, bottom, top]

    def get_freq_tics(self):
        return [float(x) for x in self.get_freq_labels()]

    def get_freq_labels(self):
        return ['{:.1f}'.format(i) for i in range(int(self.frequencies[0]),
                                                  int(self.frequencies[-1])+1)]

    def get_ursi_code(self):
        return self.ursi_code

if __name__ == '__main__':
    iono = DpsAmpIono()
    iono.load('./examples/dps_amp/00_00.txt')
    print(iono.get_extent())
