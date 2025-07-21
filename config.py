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

        def safe_load(section_name, parameter_name):
            try:
                return config.get(section_name, parameter_name)
            except (NoSectionError, NoOptionError):
                return None

        if value := safe_load("GUI", "font-size"):
            self.__parameters.font_size = value

        if value := safe_load("GUI", "F2-layer-color"):
            self.__parameters.f2_color = "#" + value

        if value := safe_load("GUI", "F1-layer-color"):
            self.__parameters.f1_color = "#" + value

        if value := safe_load("GUI", "E-layer-color"):
            self.__parameters.e_color = "#" + value

        if value := safe_load("GUI", "Es-layer-color"):
            self.__parameters.es_color = "#" + value

    def __set_default_values(self):
        self.__parameters = Parameters(
            font_size=16,
            f2_color="#F51020",
            f1_color="#10E0E0",
            e_color="#10C010",
            es_color="#F0B000",
        )

    def get_parameters(self):
        return self.__parameters
