from src.representation import MusicAbstractor
from src.utils import midi_to_notes, notes_to_midi


import numpy as np

song_name = "/Users/trueshot/Documents/git/gimbop/data/output/MIDI-Unprocessed_01_R1_2008_01-04_ORIG_MID--AUDIO_01_R1_2008_wav--1.npy"
song = np.load(song_name)
np.savetxt("test.txt", song, fmt="%i")

abstractor = MusicAbstractor()
# music = abstractor.abstract()
notes = abstractor.deabstract("test.txt")

example_file = "new.mid"
example_pm = notes_to_midi(
    notes, out_file=example_file, instrument_name="Acoustic Grand Piano"
)
