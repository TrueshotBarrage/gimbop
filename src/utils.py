"""This module contains utilities for music generation."""
import collections

import numpy as np
import pandas as pd
import pretty_midi


# Wrapper for repeating any void method indefinitely
def repeat(func, args, n):
    for _ in range(n):
        _ = func(*args)
    return


# Plays a note at a given time for the specified duration, with optional args.
def play_note(lines, note, time, length, d=0.875, ch=0, track=1):
    lines.append([track, time, "Note_on_c", ch, note, 80])
    lines.append([track, time + (length * d), "Note_off_c", ch, note, 0])

    return lines


def midi_to_notes(midi_file: str, pm=None) -> pd.DataFrame:
    # Initialize PrettyMIDI for parsing MIDI file
    if pm is None:
        pm = pretty_midi.PrettyMIDI(midi_file)
    instrument = pm.instruments[0]
    notes = collections.defaultdict(list)

    # Sort the notes by start time
    sorted_notes = sorted(instrument.notes, key=lambda note: note.start)
    prev_start = sorted_notes[0].start

    for note in sorted_notes:
        start = note.start
        end = note.end
        notes["pitch"].append(note.pitch)
        notes["start"].append(start)
        notes["end"].append(end)
        notes["step"].append(start - prev_start)
        notes["duration"].append(end - start)
        prev_start = start

    return pd.DataFrame({name: np.array(value) for name, value in notes.items()})


def notes_to_midi(
    notes: pd.DataFrame,
    out_file: str,
    instrument_name: str,
    velocity: int = 100,  # note loudness
) -> pretty_midi.PrettyMIDI:
    pm = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(
        program=pretty_midi.instrument_name_to_program(instrument_name)
    )

    prev_start = 0
    for i, note in notes.iterrows():
        start = float(prev_start + note["step"])
        end = float(start + note["duration"])
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=int(note["pitch"]),
            start=start,
            end=end,
        )
        instrument.notes.append(note)
        prev_start = start

    pm.instruments.append(instrument)
    pm.write(out_file)

    return pm
