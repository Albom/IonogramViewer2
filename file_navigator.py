import os
from glob import glob
from ionogram_tester import IonogramTester


class FileNavigator:

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.directory = os.path.dirname(file_name)
        full_file_list = glob(f"{self.directory}/*.*")
        tester = IonogramTester()
        self.file_list = [file for file in full_file_list if tester.examine(file)]

    def next(self):
        index = [os.path.basename(file) for file in self.file_list].index(
            os.path.basename(self.file_name)
        )
        if index + 1 < len(self.file_list):
            self.file_name = self.file_list[index + 1]
        return self.file_name

    def previous(self):
        index = [os.path.basename(file) for file in self.file_list].index(
            os.path.basename(self.file_name)
        )
        if index > 0:
            self.file_name = self.file_list[index - 1]
        return self.file_name

    def first(self):
        self.file_name = self.file_list[0]
        return self.file_name

    def last(self):
        self.file_name = self.file_list[-1]
        return self.file_name
