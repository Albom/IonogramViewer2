import datetime
from typing import Iterable
from ionogram import Ionogram
from ionospheric_layer_trace import IonosphericLayerTrace, IonosphericLayers, Modes


class STDFileIO:

    def __init__(self):
        pass

    @staticmethod
    def get_trace_points(trace_name: str, traces: Iterable):
        trace_points = []
        critical_frequency = None
        for trace in traces:
            trace_dict = trace.to_dict()
            if (
                trace_dict["name"] == trace_name
                and trace_dict["trace_type"] == Modes.ORDINARY
            ):
                critical_frequency = trace_dict["critical_frequency"]
                for f, h in zip(trace_dict["freqs"], trace_dict["heights"]):
                    trace_points.append(f"{f} {h}")
        return critical_frequency, trace_points

    @staticmethod
    def save(filename: str, iono: Ionogram, traces: Iterable):
        first_line = f"{iono.station_name}//{iono.timezone}"
        second_line = f"{iono.lat} {iono.lon} {iono.gyro} {iono.dip} {iono.sunspot}"
        date = iono.date - datetime.timedelta(hours=iono.timezone)
        third_line = date.strftime("%Y %m %d %H %M 00\n")

        foe, e_layer_points = STDFileIO.get_trace_points(
            IonosphericLayers.E_LAYER, traces
        )
        fof1, f1_layer_points = STDFileIO.get_trace_points(
            IonosphericLayers.F1_LAYER, traces
        )
        fof2, f2_layer_points = STDFileIO.get_trace_points(
            IonosphericLayers.F2_LAYER, traces
        )

        try:
            with open(filename, "wt", encoding="ascii") as file:

                file.write("\n".join([first_line, second_line, third_line]))

                def write_layer(critical_frequency, layer_points):
                    print(layer_points)

                    file.write(f"{critical_frequency}\n" if critical_frequency else "99.0\n")
                    file.write("\n".join(layer_points + [""]) if layer_points else "")
                    file.write("END\n")

                write_layer(foe, e_layer_points)
                write_layer(fof1, f1_layer_points)
                write_layer(fof2, f2_layer_points)
        except IOError:
            return False

        return True

    @staticmethod
    def load(filename: str):
        try:
            with open(filename, "r", encoding="ascii") as file:
                lines = file.readlines()
        except IOError:
            return

        if "//" in lines[0]:
            station_name, timezone = lines[0].strip().split("//")
            timezone = int(timezone)
        else:
            station_name = lines[0].strip()
            timezone = 0

        lat, lon, gyro, dip, sunspot = lines[1].strip().split()
        date = datetime.datetime.strptime(lines[2].strip(), "%Y %m %d %H %M 00")
        date += datetime.timedelta(hours=timezone)  # Convert from UT

        traces = []

        freqs = []
        heights = []
        critical_frequency = 0
        current_layer = IonosphericLayers.E_LAYER
        for line in lines[3:]:
            values = line.split()
            if len(values) == 2:
                freqs.append(float(values[0]))
                heights.append(float(values[1]))
            else:
                if values[0].strip().upper() == "END":
                    # save layer trace
                    if int(critical_frequency) != 99:
                        trace = IonosphericLayerTrace(
                            current_layer, freqs, heights, critical_frequency
                        )
                        traces.append(trace)

                    # go to the next layer
                    if current_layer == IonosphericLayers.E_LAYER:
                        current_layer = IonosphericLayers.F1_LAYER
                    elif current_layer == IonosphericLayers.F1_LAYER:
                        current_layer = IonosphericLayers.F2_LAYER

                    freqs = []
                    heights = []
                else:
                    critical_frequency = float(values[0])

        return {
            "station_name": station_name,
            "latitude": lat,
            "longitude": lon,
            "gyro": gyro,
            "dip": dip,
            "sunspot": sunspot,
            "date": date,
            "timezone": timezone,
            "traces": traces,
        }
