"""This module contains the high-level representation wrapper for Gimbop."""
import numpy as np
import pandas as pd
import pretty_midi

from src.utils import midi_to_notes

# A note requires a pitch, a duration, and a time


class MusicAbstractor:
    """This class abstracts the music representation for Gimbop."""

    def __init__(self, fn="test_song.mid"):
        self.fn = fn
        self.midi = pretty_midi.PrettyMIDI(fn)
        self.bpm = self.midi.estimate_tempo()

        # The quantum is the smallest unit of time (sec) in the song, which is a
        # 16th note. This assumes that the quarter note gets one beat.
        self.quantum = 15 / self.bpm
        self.time = 0
        self.channel = 0

    def abstract(self, fn=None, format="numpy"):
        # Get the notes from the MIDI file
        notes = midi_to_notes(self.fn)

        # Assign each note to a time step to the nearest quantum
        num_quantums = int(notes["end"].max() / self.quantum) + 4

        # Notes on the piano have a range of 21 to 108, so for many-hot encoding
        # purposes, we will have 88 notes and 1 rest per note, for a total of
        # 176 features per quantum.
        # Each pitch will alternate between a note and a rest, so the first
        # feature will be the note corresponding to the pitch 21, and the
        # second feature will be the rest corresponding to the pitch 21, and so
        # on.

        # Actually, new plan: each pitch will have a single feature, whose value
        # will represent the number of quantums that the note is held for.
        num_features = 88

        # Initialize the music representation using numpy
        music = np.zeros((num_quantums, num_features))
        print(f"Shape of song array: {music.shape}")

        # Iterate through the notes and assign them to the music representation
        for i, note in notes.iterrows():
            # Get the start and end times of the note
            start = note["start"]
            end = note["end"]
            duration = note["duration"]

            # Get the pitch of the note
            pitch = int(note["pitch"])

            # Verify that the pitch is within the range of the piano
            if pitch < 21 or pitch > 108:
                print(f"Note {pitch} is out of piano range. Skipping note...")
                continue

            # Get the time step of the note, rounded to the nearest quantum
            start_quantum = round(start / self.quantum)
            end_quantum = round(end / self.quantum)
            duration_quantum = round(duration / self.quantum)

            # Assign the note to the music representation
            music[start_quantum, pitch - 21] = duration_quantum

        if fn is not None:
            # Save the music representation to a file
            if format == "numpy":
                np.save(fn, music)
            else:
                np.savetxt(fn, music, fmt="%d")

        # from matplotlib import pyplot as plt

        # plt.imshow(music, interpolation="nearest")
        # plt.show()

        return music

    def deabstract(self, fn="music.txt"):
        """This method deabstracts the music representation from the encoder
        to a pandas DataFrame with the following columns:
        - pitch
        - start
        - end
        - step
        - duration"""

        # Load the music representation from a file
        music = np.loadtxt(fn, dtype=int)

        # Initialize the notes DataFrame
        notes = []

        note_locs = np.nonzero(music)
        note_vals = music[note_locs]

        prev_start = note_locs[0][0] * self.quantum
        for i in range(len(note_vals)):
            pitch = note_locs[1][i] + 21
            start = note_locs[0][i] * self.quantum
            duration = note_vals[i] * self.quantum
            # note = Note(pitch, start, duration)
            # notes.append(note)
            end = start + duration
            step = start - prev_start
            prev_start = start
            notes.append([pitch, start, end, step, duration])

        # Convert the notes DataFrame to a pandas DataFrame
        notes = pd.DataFrame(
            notes, columns=["pitch", "start", "end", "step", "duration"]
        )

        return notes


class Note:
    """This class represents a single note."""

    def __init__(self, pitch, start, duration):
        self.pitch = pitch
        self.start = start
        self.end = start + duration
        self.duration = duration

    def __repr__(self):
        return (
            f"Note(pitch={self.pitch}, start={self.start}, end={self.end}, "
            f"duration={self.duration})"
        )

    def __eq__(self, other):
        return (
            self.pitch == other.pitch
            and self.start == other.start
            and self.duration == other.duration
        )

    def __hash__(self):
        return hash((self.pitch, self.start, self.duration))
