
from struct import unpack


class UacIono:

    def __init__(self):
        self.data = None

    def load(self, file_name):
        with open(file_name, 'rb') as file:
            # head = file.read(64)
            data = file.read(512*576//8)

        data_tuple = unpack('H'*(len(data)//2), data)
        self.data = [[0 for x in range(576)] for y in range(512)]

        for f in range(576):
            for h in range(512//16):
                i = f*512//16+h
                for z in range(16):
                    self.data[511-(h*16+15-z)][f] = 1 if ((data_tuple[i]>>z) & 1) else 0

    def get_data(self):
        return self.data
