import numpy as np


class Modes:
    ORDINARY = "ordinary"
    EXTRAORDINARY = "extraordinary"


class IonosphericLayers:
    E_LAYER = "E"
    F1_LAYER = "F1"
    F2_LAYER = "F2"
    ES_LAYER = "Es"


class IonosphericLayerTrace:

    def __init__(
        self, name: str, freqs, heights, critical_frequency=None, trace_type=Modes.ORDINARY
    ):
        self.name = name
        self.freqs = np.array(freqs)
        self.heights = np.array(heights)
        self.critical_frequency = critical_frequency
        self.trace_type = trace_type

    def get_critical_frequency(self):
        return self.critical_frequency

    def to_dict(self):
        """Return trace data as a dictionary."""
        return {
            "name": self.name,
            "freqs": self.freqs.tolist(),
            "heights": self.heights.tolist(),
            "critical_frequency": self.critical_frequency,
            "trace_type": self.trace_type,
        }
