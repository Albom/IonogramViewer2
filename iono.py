
class Iono:

    def __init__(self):
        self.data = None
        self.date = None
        self.timezone = 0
        self.station_name = ''
        self.ionosonde_model = ''

    def get_data(self):
        return self.data

    def freq_to_coord(self, freq):
        return float(freq)

    def coord_to_freq(self, coord):
        return float(coord)

    def get_station_name(self):
        return self.station_name

    def get_date(self):
        return self.date

    def get_timezone(self):
        return self.timezone
