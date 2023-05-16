from src.model_api import GimbopAPI

api = GimbopAPI()
api.generate_notes_test(
    "data/maestro-v3.0.0/2018/MIDI-Unprocessed_Chamber2_MID--AUDIO_09_R3_2018_wav--1.midi"
)
