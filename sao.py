
class GeophysicalConstants:
    GYROFREQUENCY = 0
    DIP_ANGLE = 1
    GEOGRAPHIC_LATITUDE = 2
    GEOGRAPHIC_LONGITUDE = 3
    SUNSPOT_NUMBER = 4


class PrefaceAA:
    def __init__(self, line):
        self.version = ''.join(line[0:2])
        self.year = ''.join(line[2:6])
        self.day_of_year = ''.join(line[6:9])
        self.month = ''.join(line[9:11])
        self.day_of_month = ''.join(line[11:13])
        self.hour = ''.join(line[13:15])
        self.minutes = ''.join(line[15:17])
        self.seconds = ''.join(line[17:19])


class PrefaceFF(PrefaceAA):
    def __init__(self, line):
        super().__init__(line)
        self.receiver_id = ''.join(line[19:22])
        self.transmitter_id = ''.join(line[22:25])
        self.dps_schedule = line[25]
        self.dps_program = line[26]
        self.start_frequency = ''.join(line[27:32])
        self.coarse_frequency = ''.join(line[32:36])
        self.stop_frequency = ''.join(line[36:41])
        self.dps_frequency = ''.join(line[41:45])
        self.multiplexing_disabled = line[45] == '1'
        self.number_of_small_steps = line[46]
        self.dps_phase_code = line[47]
        self.alternative_antenna_setup = line[48] == '1'
        self.dps_antenna_options = line[49]
        self.fft_samples = line[50]
        self.silent_mode = line[51] == '1'
        self.pulse_repetation_rate = ''.join(line[52:55])
        self.start_range = ''.join(line[55:59])
        if line[59] == '2':
            self.range_increment = 2.5
        elif line[59] == '5':
            self.range_increment = 5
        elif line[59] == 'A':
            self.range_increment = 10
        self.number_of_ranges = ''.join(line[60:64])
        self.scan_delay = ''.join(line[64:68])
        self.gain = line[68]
        self.frequency_search_enabled = line[69] == '1'
        self.operating_mode = line[70]
        self.artist_enabled = line[71] == '1'
        self.data_format = line[72]
        if line[73] == '0':
            self.online_printer = 'no printer'
        elif line[73] == '1':
            self.online_printer = 'b/w'
        elif line[73] == '2':
            self.online_printer = 'color'
        self.thresholded = ''.join(line[74:76])
        self.extra_attenuation = line[76] == '1'


class PrefaceFE(PrefaceAA):
    def __init__(self, line):
        super().__init__(line)
        self.timestamp = ''.join(line[19:30])
        # TODO add another Digisonde 256 System Preface Parameters


class ScaledCharacteristics:
    FoF2 = 0
    FoF1 = 1
    M_D = 2
    MUF_D = 3
    F_MIN = 4
    FoEs = 5
    F_MIN_F = 6
    F_MIN_E = 7
    FoE = 8
    FxI = 9
    H_F = 10
    H_F2 = 11
    H_E = 12
    H_Es = 13
    ZM_E = 14
    Y_E = 15
    Q_F = 16
    Q_E = 17
    DOWN_F = 18
    DOWN_E = 19
    DOWN_Es = 20
    FF = 21
    FE = 22
    D = 23
    F_MUF = 24
    H_FMUF = 25
    DELTA_FoF2 = 26
    FoEp = 27
    F_H_F = 28
    F_H_F2 = 29
    FoF1p = 30
    PH_F2 = 31
    PH_F1 = 32
    Z_HALF_Nm = 33
    FoF2p = 34
    F_MIN_Es = 35
    Y_F2 = 36
    Y_F1 = 37
    TEC = 38
    SH_F2 = 39
    B0 = 40
    B1 = 41
    D1 = 42
    FoEa = 43
    H_Ea = 44
    FoP = 45
    H_P = 46
    FbEs = 47
    TYPE_Es = 48


class Sao():
    def __init__(self):
        self.sao_version = ''
        self.data_file_index = [0]*80
        self.geophysical_constants = []
        self.system_description = ''
        self.timestamp_and_settings = ''
        self.scaled_characteristics = []
        self.analysis_flags = []
        self.doppler = []
        self.f2_o_heights_virtual = []
        self.f2_o_heights_true = []
        self.f2_o_amplitudes = []
        self.f2_o_doppler_numbers = []
        self.f2_o_frequencies = []
        self.f1_o_heights_virtual = []
        self.f1_o_heights_true = []
        self.f1_o_amplitudes = []
        self.f1_o_doppler_numbers = []
        self.f1_o_frequencies = []
        self.e_o_heights_virtual = []
        self.e_o_heights_true = []
        self.e_o_amplitudes = []
        self.e_o_doppler_numbers = []
        self.e_o_frequencies = []
        self.f2_x_heights_virtual = []
        self.f2_x_amplitudes = []
        self.f2_x_doppler_numbers = []
        self.f2_x_frequencies = []
        self.f1_x_heights_virtual = []
        self.f1_x_amplitudes = []
        self.f1_x_doppler_numbers = []
        self.f1_x_frequencies = []
        self.e_x_heights_virtual = []
        self.e_x_amplitudes = []
        self.e_x_doppler_numbers = []
        self.e_x_frequencies = []
        self.median_amplitudes_f = []
        self.median_amplitudes_e = []
        self.median_amplitudes_es = []
        self.true_height_coeff_f2 = []
        self.true_height_coeff_f1 = []
        self.true_height_coeff_e = []
        self.quazi_parabolic_segments = []
        self.edit_flags = []
        self.valley_description = []
        self.es_o_heights_virtual = []
        self.es_o_amplitudes = []
        self.es_o_doppler_numbers = []
        self.es_o_frequencies = []
        self.ea_o_heights_virtual = []
        self.ea_o_amplitudes = []
        self.ea_o_doppler_numbers = []
        self.ea_o_frequencies = []
        self.true_heights = []
        self.plasma_frequencies = []
        self.electron_densities = []
        self.qualifying_letters = []
        self.descriptive_letters = []

    def load(self, filename):
        with open(filename) as file:
            data = [line.replace('\n', '') for line in file.readlines()]

        row = 0
        for i in range(40):
            self.data_file_index[i] = int(data[row][3*i:3*i+3])
            self.data_file_index[i+40] = int(data[row+1][3*i:3*i+3])

        self.sao_version = Sao.get_sao_version(self.data_file_index[79])

        # group 1 (req.)
        row += 2
        num = self.data_file_index[0]
        self.geophysical_constants = [0] * num
        for i in range(num):
            self.geophysical_constants[i] = float(data[row][7*i:7*i+7])

        # group 2
        if self.data_file_index[1] > 0:
            row += 1
            self.system_description = data[row].strip()

        # group 3 (req.)
        row += 1
        chars = list(data[row])
        if chars[0] == 'A' and chars[1] == 'A':
            preface = PrefaceAA(chars)
        elif chars[0] == 'F' and chars[1] == 'F':
            preface = PrefaceFF(chars)
        elif chars[0] == 'F' and chars[1] == 'E':
            preface = PrefaceFE(chars)
        else:
            return None

        self.timestamp_and_settings = preface

        # group 4 (req.)
        row += 1
        num = self.data_file_index[3]
        self.scaled_characteristics = [0] * num
        col = 0
        for i in range(num):
            self.scaled_characteristics[i] = float(data[row][8*col:8*col+8])
            if col > 13 and i != num-1:
                col = 0
                row += 1
            else:
                col += 1

        # group 5
        num = self.data_file_index[4]
        if num > 0:
            row += 1
            self.analysis_flags = [0] * num
            for i in range(num):
                self.analysis_flags[i] = int(data[row][2*i:2*i+2])

        # group 6
        num = self.data_file_index[5]
        if num > 0:
            row += 1
            self.doppler = [0] * num
            for i in range(num):
                self.doppler[i] = float(data[row][7*i:7*i+7])

        # groups 7, 8, 9, 10, 11
        (row,
         self.f2_o_heights_virtual,
         self.f2_o_heights_true,
         self.f2_o_amplitudes,
         self.f2_o_doppler_numbers,
         self.f2_o_frequencies) = Sao.read_layer(
             data,
             row,
             self.data_file_index[6:11])

        # groups 12, 13, 14, 15, 16
        (row,
         self.f1_o_heights_virtual,
         self.f1_o_heights_true,
         self.f1_o_amplitudes,
         self.f1_o_doppler_numbers,
         self.f1_o_frequencies) = Sao.read_layer(
             data,
             row,
             self.data_file_index[11:16])

        # groups 17, 18, 19, 20, 21
        (row,
         self.e_o_heights_virtual,
         self.e_o_heights_true,
         self.e_o_amplitudes,
         self.e_o_doppler_numbers,
         self.e_o_frequencies) = Sao.read_layer(
             data,
             row,
             self.data_file_index[16:21])

        # groups 22, 23, 24, 25
        (row,
         self.f2_x_heights_virtual,
         self.f2_x_amplitudes,
         self.f2_x_doppler_numbers,
         self.f2_x_frequencies) = Sao.read_layer(
             data,
             row,
             self.data_file_index[21:25],
             False)

        # groups 26, 27, 28, 29
        (row,
         self.f1_x_heights_virtual,
         self.f1_x_amplitudes,
         self.f1_x_doppler_numbers,
         self.f1_x_frequencies) = Sao.read_layer(
             data,
             row,
             self.data_file_index[25:29],
             False)

        # groups 30, 31, 32, 33
        (row,
         self.e_x_heights_virtual,
         self.e_x_amplitudes,
         self.e_x_doppler_numbers,
         self.e_x_frequencies) = Sao.read_layer(
             data,
             row,
             self.data_file_index[29:34],
             False)

        # group 34
        num = self.data_file_index[33]
        if num > 0:
            row += 1
            self.median_amplitudes_f = [0] * num
            for i in range(num):
                self.median_amplitudes_f[i] = int(data[row][3*i:3*i+3])

        # group 35
        num = self.data_file_index[34]
        if num > 0:
            row += 1
            self.median_amplitudes_e = [0] * num
            for i in range(num):
                self.median_amplitudes_e[i] = int(data[row][3*i:3*i+3])

        # group 36
        num = self.data_file_index[35]
        if num > 0:
            row += 1
            self.median_amplitudes_es = [0] * num
            for i in range(num):
                self.median_amplitudes_es[i] = int(data[row][3*i:3*i+3])

        # group 37
        num = self.data_file_index[36]
        if num > 0:
            row += 1
            self.true_height_coeff_f2 = [0] * num
            for i in range(num):
                self.true_height_coeff_f2[i] = float(data[row][11*i:11*i+11])

        # group 38
        num = self.data_file_index[37]
        if num > 0:
            row += 1
            self.true_height_coeff_f1 = [0] * num
            for i in range(num):
                self.true_height_coeff_f1[i] = float(data[row][11*i:11*i+11])

        # group 39
        num = self.data_file_index[38]
        if num > 0:
            row += 1
            self.true_height_coeff_e = [0] * num
            for i in range(num):
                self.true_height_coeff_e[i] = float(data[row][11*i:11*i+11])

        # group 40
        num = self.data_file_index[39]
        if num > 0:
            row += 1
            self.quazi_parabolic_segments = [0] * num
            col = 0
            for i in range(num):
                temp = data[row][20*col:20*col+20]
                self.quazi_parabolic_segments[i] = float(temp)
                if col > 4 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1


        # group 41
        num = self.data_file_index[40]
        if num > 0:
            row += 1
            self.edit_flags = [0] * num
            for i in range(num):
                self.edit_flags[i] = int(data[row][i:i+1])

        # group 42
        num = self.data_file_index[41]
        if num > 0:
            row += 1
            self.valley_description = [0] * num
            for i in range(num):
                self.valley_description[i] = float(data[row][11*i:11*i+11])

        # groups 43, 44, 45, 46
        (row,
         self.es_o_heights_virtual,
         self.es_o_amplitudes,
         self.es_o_doppler_numbers,
         self.es_o_frequencies) = Sao.read_layer(
             data,
             row,
             self.data_file_index[42:46],
             False)

        # groups 47, 48, 49, 50
        (row,
         self.ea_o_heights_virtual,
         self.ea_o_amplitudes,
         self.ea_o_doppler_numbers,
         self.ea_o_frequencies) = Sao.read_layer(
             data,
             row,
             self.data_file_index[46:50],
             False)

        # group 51
        num = self.data_file_index[50]
        if num > 0:
            row += 1
            self.true_heights = [0] * num
            col = 0
            for i in range(num):
                self.true_heights[i] = float(data[row][col*8:col*8+8])
                if col > 13 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        # group 52
        num = self.data_file_index[51]
        if num > 0:
            row += 1
            self.plasma_frequencies = [0] * num
            col = 0
            for i in range(num):
                self.plasma_frequencies[i] = float(data[row][col*8:col*8+8])
                if col > 13 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        # group 53
        num = self.data_file_index[52]
        if num > 0:
            row += 1
            self.electron_densities = [0] * num
            col = 0
            for i in range(num):
                self.electron_densities[i] = float(data[row][col*8:col*8+8])
                if col > 13 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        # group 54
        num = self.data_file_index[53]
        if num > 0:
            row += 1
            self.qualifying_letters = [0] * num
            col = 0
            for i in range(num):
                self.qualifying_letters[i] = data[row][col:col+1]
                if col > 119 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        # group 55
        num = self.data_file_index[54]
        if num > 0:
            row += 1
            self.descriptive_letters = [0] * num
            col = 0
            for i in range(num):
                self.descriptive_letters[i] = data[row][col:col+1]
                if col > 119 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        # group 56
        num = self.data_file_index[55]
        if num > 0:
            row += 1
            self.edit_flags = [0] * num
            col = 0
            for i in range(num):
                self.edit_flags[i] = data[row][col:col+1]
                if col > 119 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        # TODO add groups 57-60 (AURORAL E_LAYER PROFILE DATA)

    def __str__(self):
        preface = str(vars(self.timestamp_and_settings))
        string_format = (
            'sao_version: {}\n'
            'geophysical_constants: {}\n'
            'system_description: {}\n'
            'timestamp_and_settings: {}\n'
            'scaled_characteristics: {}\n'
            'analysis_flags: {}\n'
            'doppler: {}\n'
            'f2_o_heights_virtual: {}\n'
            'f2_o_heights_true: {}\n'
            'f2_o_amplitudes: {}\n'
            'f2_o_doppler_numbers: {}\n'
            'f2_o_frequencies: {}\n'
            'f1_o_heights_virtual: {}\n'
            'f1_o_heights_true: {}\n'
            'f1_o_amplitudes: {}\n'
            'f1_o_doppler_numbers: {}\n'
            'f1_o_frequencies: {}\n'
            'e_o_heights_virtual: {}\n'
            'e_o_heights_true: {}\n'
            'e_o_amplitudes: {}\n'
            'e_o_doppler_numbers: {}\n'
            'e_o_frequencies: {}\n'
            'f2_x_heights_virtual: {}\n'
            'f2_x_amplitudes: {}\n'
            'f2_x_doppler_numbers: {}\n'
            'f2_x_frequencies: {}\n'
            'f1_x_heights_virtual: {}\n'
            'f1_x_amplitudes: {}\n'
            'f1_x_doppler_numbers: {}\n'
            'f1_x_frequencies: {}\n'
            'e_x_heights_virtual: {}\n'
            'e_x_amplitudes: {}\n'
            'e_x_doppler_numbers: {}\n'
            'e_x_frequencies: {}\n'
            'median_amplitudes_f: {}\n'
            'median_amplitudes_e: {}\n'
            'median_amplitudes_es: {}\n'
            'true_height_coeff_f2: {}\n'
            'true_height_coeff_f1: {}\n'
            'true_height_coeff_e: {}\n'
            'quazi_parabolic_segments: {}\n'
            'edit_flags: {}\n'
            'valley_description: {}\n'
            'es_o_heights_virtual: {}\n'
            'es_o_amplitudes: {}\n'
            'es_o_doppler_numbers: {}\n'
            'es_o_frequencies: {}\n'
            'ea_o_heights_virtual: {}\n'
            'ea_o_amplitudes: {}\n'
            'ea_o_doppler_numbers: {}\n'
            'ea_o_frequencies: {}\n'
            'true_heights: {}\n'
            'plasma_frequencies: {}\n'
            'electron_densities: {}\n'
            'qualifying_letters: {}\n'
            'descriptive_letters: {}'
            )

        result = string_format.format(
            self.sao_version,
            self.geophysical_constants,
            self.system_description,
            preface,
            self.scaled_characteristics,
            self.analysis_flags,
            self.doppler,
            self.f2_o_heights_virtual,
            self.f2_o_heights_true,
            self.f2_o_amplitudes,
            self.f2_o_doppler_numbers,
            self.f2_o_frequencies,
            self.f1_o_heights_virtual,
            self.f1_o_heights_true,
            self.f1_o_amplitudes,
            self.f1_o_doppler_numbers,
            self.f1_o_frequencies,
            self.e_o_heights_virtual,
            self.e_o_heights_true,
            self.e_o_amplitudes,
            self.e_o_doppler_numbers,
            self.e_o_frequencies,
            self.f2_x_heights_virtual,
            self.f2_x_amplitudes,
            self.f2_x_doppler_numbers,
            self.f2_x_frequencies,
            self.f1_x_heights_virtual,
            self.f1_x_amplitudes,
            self.f1_x_doppler_numbers,
            self.f1_x_frequencies,
            self.e_x_heights_virtual,
            self.e_x_amplitudes,
            self.e_x_doppler_numbers,
            self.e_x_frequencies,
            self.median_amplitudes_f,
            self.median_amplitudes_e,
            self.median_amplitudes_es,
            self.true_height_coeff_f2,
            self.true_height_coeff_f1,
            self.true_height_coeff_e,
            self.quazi_parabolic_segments,
            self.edit_flags,
            self.valley_description,
            self.es_o_heights_virtual,
            self.es_o_amplitudes,
            self.es_o_doppler_numbers,
            self.es_o_frequencies,
            self.ea_o_heights_virtual,
            self.ea_o_amplitudes,
            self.ea_o_doppler_numbers,
            self.ea_o_frequencies,
            self.true_heights,
            self.plasma_frequencies,
            self.electron_densities,
            self.qualifying_letters,
            self.descriptive_letters)
        return result

    @staticmethod
    def get_sao_version(num):
        names = {0: '3', 1: '3.1', 2: '4.0', 3: '4.1', 4: '4.2', 5: '4.3'}
        return names[num] if num in names else 'Unknown'

    @staticmethod
    def read_layer(data, row, indices, with_true_heights=True):

        heights_virtual = []
        heights_true = []
        amplitudes = []
        doppler_numbers = []
        frequencies = []

        index = 0
        num = indices[index]
        if num > 0:
            row += 1
            heights_virtual = [0] * num
            col = 0
            for i in range(num):
                heights_virtual[i] = float(data[row][8*col:8*col+8])
                if col > 13 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        if with_true_heights:
            index += 1
            num = indices[index]
            if num > 0:
                row += 1
                heights_true = [0] * num
                col = 0
                for i in range(num):
                    heights_true[i] = float(data[row][8*col:8*col+8])
                    if col > 13 and i != num-1:
                        col = 0
                        row += 1
                    else:
                        col += 1

        index += 1
        num = indices[index]
        if num > 0:
            row += 1
            amplitudes = [0] * num
            col = 0
            for i in range(num):
                amplitudes[i] = int(data[row][3*col:3*col+3])
                if col > 38 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        index += 1
        num = indices[index]
        if num > 0:
            row += 1
            doppler_numbers = [0] * num
            col = 0
            for i in range(num):
                doppler_numbers[i] = int(data[row][col:col+1])
                if col > 119 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        index += 1
        num = indices[index]
        if num > 0:
            row += 1
            frequencies = [0] * num
            col = 0
            for i in range(num):
                frequencies[i] = float(data[row][8*col:8*col+8])
                if col > 13 and i != num-1:
                    col = 0
                    row += 1
                else:
                    col += 1

        return (
            row,
            heights_virtual,
            heights_true,
            amplitudes,
            doppler_numbers,
            frequencies) if with_true_heights else (
                row,
                heights_virtual,
                amplitudes,
                doppler_numbers,
                frequencies)


if __name__ == '__main__':
    sao = Sao()
    sao.load('./examples/sao/test.sao')
    print(sao)
    # with open('out.txt', 'w') as f:
    #     f.write(str(sao))
