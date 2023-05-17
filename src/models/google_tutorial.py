import os
import glob
import pathlib
import logging
import numpy as np
import pandas as pd
import pretty_midi
import tensorflow as tf
import collections

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s: %(message)s", "%H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Get path of dataset
path = os.path.join(os.getcwd(), "data", "maestro-v3.0.0")
data_dir = pathlib.Path(path)
logger.info(f"Looking in {data_dir}")

filenames = glob.glob(str(data_dir/'**/*.mid*'))
logger.info(f"Number of files: {len(filenames)}")


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

# Process a select number of files to mock train the model
num_files = 10  # 1276 total, we can do a rough 60:30:10 split -- nvm, too big
all_notes = []
for f in filenames[:num_files]:
    notes = midi_to_notes(f)
    all_notes.append(notes)

all_notes = pd.concat(all_notes)
n_notes = len(all_notes)
logger.info(f"Shape of all_notes: {all_notes.shape}")

key_order = ["pitch", "step", "duration"]
train_notes = np.stack([all_notes[key] for key in key_order], axis=1)

notes_ds = tf.data.Dataset.from_tensor_slices(train_notes)


def create_sequences(
    dataset: tf.data.Dataset,
    seq_length: int,
    vocab_size=128,
) -> tf.data.Dataset:
    """Returns TF Dataset of sequence and label examples."""
    seq_length = seq_length + 1

    # Take 1 extra for the labels
    windows = dataset.window(seq_length, shift=1, stride=1, drop_remainder=True)

    # `flat_map` flattens the" dataset of datasets" into a dataset of tensors
    flatten = lambda x: x.batch(seq_length, drop_remainder=True)
    sequences = windows.flat_map(flatten)

    # Normalize note pitch
    def scale_pitch(x):
        x = x / [vocab_size, 1.0, 1.0]
        return x

    # Split the labels
    def split_labels(sequences):
        inputs = sequences[:-1]
        labels_dense = sequences[-1]
        labels = {key: labels_dense[i] for i, key in enumerate(key_order)}

        return scale_pitch(inputs), labels

    return sequences.map(split_labels, num_parallel_calls=tf.data.AUTOTUNE)


seq_length = 25
vocab_size = 128
seq_ds = create_sequences(notes_ds, seq_length, vocab_size)

batch_size = 64
buffer_size = n_notes - seq_length  # the number of items in the dataset
train_ds = (
    seq_ds.shuffle(buffer_size)
    .batch(batch_size, drop_remainder=True)
    .cache()
    .prefetch(tf.data.experimental.AUTOTUNE)
)


def mse_with_positive_pressure(y_true: tf.Tensor, y_pred: tf.Tensor):
    mse = (y_true - y_pred) ** 2
    positive_pressure = 10 * tf.maximum(-y_pred, 0.0)
    return tf.reduce_mean(mse + positive_pressure)


input_shape = (seq_length, 3)
learning_rate = 0.005

inputs = tf.keras.Input(input_shape)
x = tf.keras.layers.LSTM(128)(inputs)

outputs = {
    "pitch": tf.keras.layers.Dense(128, name="pitch")(x),
    "step": tf.keras.layers.Dense(1, name="step")(x),
    "duration": tf.keras.layers.Dense(1, name="duration")(x),
}

model = tf.keras.Model(inputs, outputs)

loss = {
    "pitch": tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    "step": mse_with_positive_pressure,
    "duration": mse_with_positive_pressure,
}

optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)

# model.compile(loss=loss, optimizer=optimizer)

# model.summary()

# losses = model.evaluate(train_ds, return_dict=True)

model.compile(
    loss=loss,
    loss_weights={
        "pitch": 0.05,
        "step": 1.0,
        "duration": 1.0,
    },
    optimizer=optimizer,
)

model.evaluate(train_ds, return_dict=True)

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        filepath="./training_checkpoints/ckpt_{epoch}", save_weights_only=True
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor="loss", patience=5, verbose=1, restore_best_weights=True
    ),
]

epochs = 50

history = model.fit(
    train_ds,
    epochs=epochs,
    callbacks=callbacks,
)


def predict_next_note(
    notes: np.ndarray, keras_model: tf.keras.Model, temperature: float = 1.0
) -> int:
    """Generates a note IDs using a trained sequence model."""

    assert temperature > 0

    # Add batch dimension
    inputs = tf.expand_dims(notes, 0)

    predictions = model.predict(inputs)
    pitch_logits = predictions["pitch"]
    step = predictions["step"]
    duration = predictions["duration"]

    pitch_logits /= temperature
    pitch = tf.random.categorical(pitch_logits, num_samples=1)
    pitch = tf.squeeze(pitch, axis=-1)
    duration = tf.squeeze(duration, axis=-1)
    step = tf.squeeze(step, axis=-1)

    # `step` and `duration` values should be non-negative
    step = tf.maximum(0, step)
    duration = tf.maximum(0, duration)

    return int(pitch), float(step), float(duration)


temperature = 2.0
num_predictions = 120


raw_notes = midi_to_notes(
    "data/maestro-v3.0.0/2018/MIDI-Unprocessed_Chamber2_MID--AUDIO_09_R3_2018_wav--1.midi"
)
sample_notes = np.stack([raw_notes[key] for key in key_order], axis=1)

# The initial sequence of notes; pitch is normalized similar to training
# sequences
input_notes = sample_notes[:seq_length] / np.array([vocab_size, 1, 1])

generated_notes = []
prev_start = 0
for _ in range(num_predictions):
    pitch, step, duration = predict_next_note(input_notes, model, temperature)
    start = prev_start + step
    end = start + duration
    input_note = (pitch, step, duration)
    generated_notes.append((*input_note, start, end))
    input_notes = np.delete(input_notes, 0, axis=0)
    input_notes = np.append(input_notes, np.expand_dims(input_note, 0), axis=0)
    prev_start = start

generated_notes = pd.DataFrame(generated_notes, columns=(*key_order, "start", "end"))


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


out_file = "output.mid"
out_pm = notes_to_midi(
    generated_notes, out_file=out_file, instrument_name="Acoustic Grand Piano"
)


# Load the MIDI file using Pretty MIDI
# get_note_names = np.vectorize(pretty_midi.note_number_to_name)
# note_names = get_note_names(all_notes["pitch"])
