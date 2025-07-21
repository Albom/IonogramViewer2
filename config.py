from configparser import ConfigParser, NoSectionError, NoOptionError
from dataclasses import dataclass


@dataclass
class Parameters:
    font_size: int
    f2_color: str
    f1_color: str
    e_color: str
    es_color: str


class Config:

    def __init__(self, filename: str):

        self.__set_default_values()

        config = ConfigParser()
        config.read(filename)

        try:
            self.__parameters.font_size = config.get("GUI", "font-size")
        except (NoSectionError, NoOptionError):
            pass

        try:
            self.__parameters.f2_color = "#" + config.get("GUI", "F2-layer-color")
        except (NoSectionError, NoOptionError):
            pass

        try:
            self.__parameters.f1_color = "#" + config.get("GUI", "F1-layer-color")
        except (NoSectionError, NoOptionError):
            pass

        try:
            self.__parameters.e_color = "#" + config.get("GUI", "E-layer-color")
        except (NoSectionError, NoOptionError):
            pass

        try:
            self.__parameters.es_color = "#" + config.get("GUI", "Es-layer-color")
        except (NoSectionError, NoOptionError):
            pass

    def __set_default_values(self):
        self.__parameters = Parameters(font_size=16, 
                                       f2_color="#F51020",
                                       f1_color="#10E0E0",
                                       e_color="#10C010",
                                       es_color="#F0B000"
                                       )

    def get_parameters(self):
        return self.__parameters
