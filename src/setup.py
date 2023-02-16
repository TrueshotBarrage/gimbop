import csv
import random
import operator
import subprocess
import numpy as np

from typing import NamedTuple


class Key:
    def __init__(self, key_string):
        self.key_string = key_string
        self.key = self.get_key_num(key_string)

    def __repr__(self):
        return str(self.key)

    def get_key_num(self, key_string):
        key_dict = {
            # Key signature is the number of sharps or flats in the key
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


class SongWriter:
    def __init__(
        self,
        key,
    ):
        pass


class Music:
    def __init__(self, key):
        self.midi_type = 1
        self.num_tracks = 1
        self.quarter_note = 480
        self.ts_num = 4
        self.ts_denom = 2  # negative power of two, e.g. eighth note = 3
        self.key_signature = key  # -7 to 7 inclusive; flats (-) & sharps (+)
        self.major = "major"
        # 500000 = 120 quarter notes (beats) per minute; also 60,000,000 / bpm
        self.bpm = 120
        self.tempo = 60000000 / self.bpm

        self.LH_instrument = 0
        self.RH_instrument = 0
        self.misc_instrument1 = 0
        self.misc_instrument2 = 26  # Electric Guitar (jazz)

        self.LH_time = 0
        self.RH_time = 0
        self.misc_time1 = 0
        self.misc_time2 = 0
        self.lines = []

    # Song setup
    def start(self):
        self.lines.append(
            [0, 0, "Header", self.midi_type, self.num_tracks, self.quarter_note]
        )
        self.lines.append([1, 0, "Start_track"])
        self.lines.append([1, 0, "Time_signature", self.ts_num, self.ts_denom, 24, 8])
        self.lines.append([1, 0, "Key_signature", self.key_signature, self.major])
        self.lines.append([1, 0, "Tempo", self.tempo])

        # These remain to be seen what they do exactly...
        self.lines.append([1, 0, "Control_c", 0, 121, 0])
        self.lines.append([1, 0, "Program_c", 0, self.LH_instrument])  # 0 = piano
        self.lines.append([1, 0, "MIDI_port", 0])

        self.lines.append([1, 0, "Control_c", 1, 121, 0])
        self.lines.append([1, 0, "Program_c", 1, self.RH_instrument])
        self.lines.append([1, 0, "MIDI_port", 1])

        self.lines.append([1, 0, "Control_c", 2, 121, 0])
        self.lines.append([1, 0, "Program_c", 2, self.misc_instrument1])
        self.lines.append([1, 0, "MIDI_port", 2])

        self.lines.append([1, 0, "Control_c", 3, 121, 0])
        self.lines.append([1, 0, "Program_c", 3, self.misc_instrument2])
        self.lines.append([1, 0, "MIDI_port", 3])

    # Song wrap-up
    def finish(self, filename):
        self.lines = sorted(self.lines, key=operator.itemgetter(1))
        total_time = self.LH_time if self.LH_time > self.RH_time else self.RH_time
        total_time = self.misc_time1 if self.misc_time1 > total_time else total_time
        total_time = self.misc_time2 if self.misc_time2 > total_time else total_time

        self.lines.append([1, total_time, "End_track"])
        self.lines.append([0, 0, "End_of_file"])

        with open(filename + ".csv", "w") as writeFile:
            writer = csv.writer(writeFile)
            writer.writerows(self.lines)

        writeFile.close()
        subprocess.run(["./csvmidi", filename + ".csv", filename + ".mid"])

    # Wrapper for repeating any method indefinitely
    def repeat(self, func, args, n):
        for _ in range(n):
            x = func(*args)
        return

    # Plays a note at a given time for the specified duration, with optional args.
    def play_note(self, note, time, length, d=0.875, ch=0, track=1):
        self.lines.append([track, time, "Note_on_c", ch, note, 80])
        self.lines.append([track, time + (length * d), "Note_off_c", ch, note, 0])
