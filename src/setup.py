"""This module contains the main framework for representing music in GIMBOP."""
import csv
import operator
import subprocess


class Key:
    """Class for representing a key signature."""

    def __init__(self, key_string):
        self.key_string = key_string
        self.num_accidentals = self.get_num_accidentals(key_string)

    def __repr__(self):
        return str(self.num_accidentals)

    def get_num_accidentals(self, key_string):
        key_dict = {
            "C": 0,
            "G": 1,
            "D": 2,
            "A": 3,
            "E": 4,
            "B": 5,
            "F#": 6,
            "C#": 7,
            "F": -1,
            "Bb": -2,
            "Eb": -3,
            "Ab": -4,
            "Db": -5,
            "Gb": -6,
            "Cb": -7,
            # Also include enharmonic equivalents
            "B#": 0,
            "E#": -1,
            "A#": -2,
            "D#": -3,
            "G#": -4,
            "Fb": 4,
        }
        return key_dict[key_string]


class SongMetadata:
    """Class to store fixed metadata about every generated song."""

    def __init__(self):
        self.midi_type = 1
        self.num_tracks = 1
        self.quarter_note = 480
        self.ts_num = 4
        self.ts_denom = 2  # negative power of two, e.g. eighth note = 3
        self.major = "major"


# Dictionary of MIDI-standard instrument types
instrument_types = {
    "grand_piano": 0,
    "bright_acoustic_piano": 1,
    "electric_piano_1": 4,
    "electric_piano_2": 5,
    "acoustic_guitar": 24,
    "electric_guitar_jazz": 26,
}


class SongWriter:
    """Class to generate and write a song to a MIDI file."""

    def __init__(
        self,
        key=Key("C"),
        bpm=120,
    ):
        # Initialize the metadata that we (probably) won't change
        self.meta = SongMetadata()

        # Initialize the key signature
        self.key_signature = key
        self.num_accidentals = key.num_accidentals

        # 500000 = 120 quarter notes (beats) per minute; also 60,000,000 / bpm
        self.bpm = bpm
        self.tempo = 60000000 / self.bpm

        # Initialize the instruments
        self.instruments = [
            instrument_types["grand_piano"],
            instrument_types["grand_piano"],
        ]

        # Initialize the actual contents of the song
        self.lines = []
        self.total_time = 100000  # TODO: Hardcoded for now, change this

    def _initialize_instruments(self):
        """Initialize the instruments for the song in csvmidi format."""
        for i in range(len(self.instruments)):
            self.lines.append([1, 0, "Control_c", i, 121, 0])
            self.lines.append([1, 0, "Program_c", i, self.instruments[i]])
            self.lines.append([1, 0, "MIDI_port", i])

    def write(self, filename):
        """Write the song to a MIDI file."""
        self._write_header()
        # self._initialize_instruments()
        # self._write_content()
        self._finish(filename)

    def _write_header(self):
        self.lines.append(
            [
                0,
                0,
                "Header",
                self.meta.midi_type,
                self.meta.num_tracks,
                self.meta.quarter_note,
            ]
        )
        self.lines.append([1, 0, "Start_track"])
        self.lines.append(
            [1, 0, "Time_signature", self.meta.ts_num, self.meta.ts_denom, 24, 8]
        )
        self.lines.append(
            [1, 0, "Key_signature", self.num_accidentals, self.meta.major]
        )
        self.lines.append([1, 0, "Tempo", self.tempo])

    def _write_content(self):
        # TODO: Figure out how to keep track of each track with its own time
        pass

    def _finish(self, filename):
        self.lines = sorted(self.lines, key=operator.itemgetter(1))
        # total_time = self.LH_time if self.LH_time > self.RH_time else self.RH_time
        # total_time = self.misc_time1 if self.misc_time1 > total_time else total_time
        # total_time = self.misc_time2 if self.misc_time2 > total_time else total_time
        self.total_time = 100000  # TODO: Hardcoded for now, change this

        self.lines.append([1, self.total_time, "End_track"])
        self.lines.append([0, 0, "End_of_file"])

        with open(filename + ".csv", "w") as f:
            writer = csv.writer(f)
            writer.writerows(self.lines)

        f.close()
        subprocess.run(["./csvmidi", filename + ".csv", filename + ".mid"])
