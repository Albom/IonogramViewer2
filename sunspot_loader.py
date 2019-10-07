
from datetime import datetime


class SunspotLoader:

    def __init__(self, filename='./data/SN_d_tot_V2.0.txt'):
        with open(filename) as file:
            self.lines = [s.split() for s in file.readlines()]

    def get(self, date):
        year = date.year
        month = date.month
        day = date.day
        number = -1
        for line in self.lines:
            if (int(line[0]) == year
                and int(line[1]) == month
                    and int(line[2]) == day):
                    number = int(line[4])
                    break
        return number

Sunspots = SunspotLoader()
