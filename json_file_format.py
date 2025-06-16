import datetime
import json
from typing import Iterable
from ionogram import Ionogram
from ionospheric_layer_trace import Modes


class JsonFileIO:

    def __init__(self):
        pass

    @staticmethod
    def save(filename: str, iono: Ionogram, traces: Iterable):

        date_ut = iono.date - datetime.timedelta(hours=iono.timezone)
        date_str = date_ut.isoformat()

        json_data = {
            date_str: {
                "station_name": iono.get_station_name(),
                "latitude": iono.lat,
                "longitude": iono.lon,
                "gyro": iono.gyro,
                "dip": iono.dip,
                "sunspot": iono.sunspot,
                "date": iono.date.isoformat(),
                "timezone": iono.timezone,
                "traces": [trace.to_dict() for trace in traces],
            }
        }

        try:
            with open(filename, "wt", encoding="utf-8") as file:
                json.dump(json_data, file, indent=4)
        except IOError:
            return False
        # print(date_str)
        return True

    @staticmethod
    def load(filename: str):
        try:
            with open(filename, "rt", encoding="utf-8") as file:
                loaded_data = json.load(file)
        except IOError:
            return

        return loaded_data

    @staticmethod
    def get_trace_points(trace_name: str, traces: Iterable):
        trace_points = []
        critical_frequency = None
        for trace in traces:
            if (
                trace["name"] == trace_name
                and trace["trace_type"] == Modes.ORDINARY
            ):
                critical_frequency = trace["critical_frequency"]
                for f, h in zip(trace["freqs"], trace["heights"]):
                    trace_points.append(f"{f} {h}")
        return critical_frequency, trace_points
