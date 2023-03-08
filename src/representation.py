"""This module contains the high-level representation wrapper for Gimbop."""
import numpy as np

# A note requires a pitch, a duration, and a time


class MusicAbstractor:
    """This class abstracts the music representation for Gimbop."""

    def __init__(self):
        self.time = 0
        self.channel = 0

    def abstract(self):
        return None

    def deabstract(self):
        return None


# TODO: Figure out the exact encoding of the music representation - most likely
# will be a multi-hot encoding of note played and note rest for every time step
# Time step is probably 1/16th note


class Note:
    """This class represents a single note."""

    def __init__(self, pitch, duration):
        self.pitch = pitch
        self.duration = duration

    def __repr__(self):
        return f"Note(pitch={self.pitch}, duration={self.duration})"

    def __eq__(self, other):
        return self.pitch == other.pitch and self.duration == other.duration

    def __hash__(self):
        return hash((self.pitch, self.duration))
