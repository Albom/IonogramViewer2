
class KarazinIono:
    def load(self, file_name):
        with open(file_name, 'r') as file:
            lines = file.readlines()

        freq_set_section = False
        for line in lines:
            if line.startswith('Location'):
                self.location = line.split(':')[1].strip()
            if line.startswith('z0'):
                self.z0 = float(line.split('=')[1].strip())
            if line.startswith('dz'):
                self.dz = float(line.split('=')[1].strip())
            if line.startswith('Frep'):
                self.frep = float(line.split('=')[1].strip())
            if line.startswith('Nstrob'):
                self.nstrob = int(line.split('=')[1].strip())
            if line.startswith('Nsound'):
                self.nsound = int(line.split('=')[1].strip())
            if line.startswith('Frequency Set'):
                freq_set_section = True

        print(self.z0, self.dz, self.nsound, self.nstrob, self.frep)
