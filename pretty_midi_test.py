import collections
from typing import Optional

import pretty_midi
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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


def plot_piano_roll(notes: pd.DataFrame, count: Optional[int] = None):
    if count:
        title = f"First {count} notes"
    else:
        title = f"Whole track"
        count = len(notes["pitch"])
    plt.figure(figsize=(20, 4))
    plot_pitch = np.stack([notes["pitch"], notes["pitch"]], axis=0)
    plot_start_stop = np.stack([notes["start"], notes["end"]], axis=0)
    plt.plot(plot_start_stop[:, :count], plot_pitch[:, :count], color="b", marker=".")
    plt.xlabel("Time [s]")
    plt.ylabel("Pitch")
    _ = plt.title(title)
    plt.show()


def main():
    fn = "test_song.mid"

    # Load MIDI file into PrettyMIDI object
    midi_data = pretty_midi.PrettyMIDI(fn)

    # Print an empirical estimate of its global tempo
    tempo = midi_data.estimate_tempo()

    # Get the beat locations
    beats = midi_data.get_beats()
    downbeats = midi_data.get_downbeats()

    # Get beat start estimate
    beat_start = midi_data.estimate_beat_start(candidates=10, tolerance=0.025)

    # Get piano roll
    piano_roll = midi_data.get_piano_roll()

    print(f"Tempo: {tempo},\nBeats: {beats},\nBeat Start: {beat_start}")
    print(f"Downbeats: {downbeats}")
    print(f"End time: {midi_data.get_end_time()}")
    # print(f"Piano Roll: {pd.DataFrame(piano_roll).head()}")

    # Compute the relative amount of each semitone across the entire song, a proxy for key
    # total_velocity = sum(sum(midi_data.get_chroma()))
    # print([sum(semitone) / total_velocity for semitone in midi_data.get_chroma()])

    # Shift all notes up by 5 semitones
    # for instrument in midi_data.instruments:
    #     # Don't want to shift drum notes
    #     if not instrument.is_drum:
    #         for note in instrument.notes:
    #             note.pitch += 5

    # Synthesize the resulting MIDI data using sine waves
    # audio_data = midi_data.synthesize()

    # Convert MIDI to notes
    raw_notes = midi_to_notes(fn, pm=midi_data)
    print(raw_notes.head())

    # Plot the piano roll
    plot_piano_roll(raw_notes, count=120)


def main2():
    fn = "test_song.mid"
    notes = midi_to_notes(fn)
    print(notes)

    all_notes = []
    all_notes.append(notes)

    all_notes = pd.concat(all_notes)
    print(all_notes)

    key_order = ["pitch", "step", "duration"]
    train_notes = np.stack([all_notes[key] for key in key_order], axis=1)
    print(train_notes)


if __name__ == "__main__":
    main()
