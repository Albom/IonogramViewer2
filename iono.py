
class Iono:

    def __init__(self):
        self.data = None
        self.date = None
        self.station_name = None
        self.ionosonde_model = None

    def get_data(self):
        return self.data

    def freq_to_coord(self, freq):
        return float(freq)

    def coord_to_freq(self, coord):
        return float(coord)
