from os import path
from datetime import datetime
from fnmatch import fnmatch


class IonoTester:
    def __init__(self):
        self.FILE_FORMATS = {
            'Unknown': {
                'class_name': 'Unknown'},
            'IPS42': {
                'class_name': 'Ips42Iono',
                'sizes': [36928],
                'patterns': ['??h??m.ion']},
            'DPS_AMP': {
                'class_name': 'DpsAmpIono'},
            'KARAZIN': {
                'class_name': 'KarazinIono',
                'patterns': ['??-??.dat']},
            'RINAN': {
                'class_name': 'RinanIono',
                'patterns': ['????????_????_iono.ion', '????????_????_c?_iono.ion', '????????_????_iono.pion']},
            'IION': {
                'class_name': 'BazisIono',
                'patterns': ['NF??????.??', 'B1??????.??', 'B2??????.??'],
                'sizes': [1200021, 1600021]},
            'Shigaraki': {
                'class_name': 'ShigarakiIono',
                'patterns': ['????????????_ionogram.txt']},
            'VISRC2T': {
                'class_name': 'Visrc2tIono',
                'patterns': ['??????????????.rad', '??????????????.rad.bz2', '??????????????.ig', '??????????????.ig.bz2']
            }
        }
        self.class_name = ''
        self.probability = 0
        self.points = {x: 0 for x in self.FILE_FORMATS.keys()}

    def examine(self, filename):
        self.__init__()

        file_size = path.getsize(filename)

        try:
            with open(filename) as f:
                first_line = f.readline()
        except UnicodeDecodeError:
            first_line = ''

        keys = self.FILE_FORMATS.keys()
        for key in keys:
            if 'sizes' in self.FILE_FORMATS[key]:
                for size in self.FILE_FORMATS[key]['sizes']:
                    if file_size == size:
                        self.points[key] += 1
            if 'patterns' in self.FILE_FORMATS[key]:
                for pattern in self.FILE_FORMATS[key]['patterns']:
                    (_, name) = path.split(filename)
                    if fnmatch(name, pattern):
                        self.points[key] += 1

        try:
            datetime.strptime(
                first_line[:-1],
                '%Y.%m.%d (%j) %H:%M:%S.%f')
        except ValueError:
            pass
        else:
            self.points['DPS_AMP'] += 1

        max_points = 0
        all_points = 0
        file_format = 'Unknown'
        for key in keys:
            all_points += self.points[key]
            if self.points[key] > max_points:
                max_points = self.points[key]
                file_format = key

        self.class_name = self.FILE_FORMATS[file_format]['class_name']
        if all_points != 0:
            self.probability = max_points/all_points

        p = 1.0 if self.class_name == 'Unknown' else self.probability
        return {
            'class_name': self.class_name,
            'probability': p}


if __name__ == '__main__':
    tester = IonoTester()
    ips = tester.examine('./examples/ips42/00h30m.ion')
    dps = tester.examine('./examples/dps_amp/00_00.txt')
    karazin = tester.examine('./examples/karazin/12-00.dat')
    iion = tester.examine('./examples/iion/NF190606.50')
    py = tester.examine('./iono_tester.py')
    print(ips, dps, karazin, iion, py, sep='\n')
