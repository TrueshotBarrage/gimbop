import os
import glob
import pathlib
import logging
import numpy as np
import tensorflow as tf

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s: %(message)s", "%H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Get path of dataset
path = os.path.join(os.getcwd(), "data", "output")
data_dir = pathlib.Path(path)
logger.info(f"Looking in {data_dir}")

filenames = glob.glob(str(data_dir / "*.npy"))
logger.info(f"Number of files: {len(filenames)}")

# Process a select number of files to mock train the model
num_files = 5
all_notes = []
for f in filenames[:num_files]:
    notes = np.load(f)
    # logger.info(notes.shape)
    all_notes.append(notes)

# Concatenate all the notes into a single numpy array with shape (num_notes, 88)
all_notes = np.concatenate(all_notes, axis=0)
n_notes = all_notes.shape[0]
logger.info(f"Shape of all_notes: {all_notes.shape}")

# Convert numpy data into tensorflow dataset
notes_ds = tf.data.Dataset.from_tensor_slices(all_notes)
logger.info(f"Notes element spec: {notes_ds.element_spec}")


# Define a helper function to generate RNN input sequences
def create_sequences(
    dataset: tf.data.Dataset,
    seq_length: int,
    shift_size=4,
) -> tf.data.Dataset:
    """Returns TF Dataset of sequence and label examples."""

    # Take 1 extra for the labels
    seq_length = seq_length + 1
    windows = dataset.window(
        seq_length, shift=shift_size, stride=1, drop_remainder=True
    )

    # `flat_map` flattens the" dataset of datasets" into a dataset of tensors
    flatten = lambda x: x.batch(seq_length, drop_remainder=True)
    sequences = windows.flat_map(flatten)

    # Split the labels
    def split_labels(sequences):
        inputs = sequences[:-1]
        labels = sequences[-1]

        return inputs, labels

    return sequences.map(split_labels, num_parallel_calls=tf.data.AUTOTUNE)


# Parameters for training the RNN
vocab_size = 88
seq_length = 16 * 100  # 100 measures since each quantum = sixteenth note
shift_size = 4
batch_size = 64

# Generate RNN sequences
seq_ds = create_sequences(notes_ds, seq_length, shift_size)
logger.info(f"Sequence element spec: {seq_ds.element_spec}")

for seq, target in seq_ds.take(1):
    logger.info(f"Sequence shape: {seq.shape}")
    logger.info(f"Sequence elements (first 10): {seq[0:10]}")
    logger.info()
    logger.info(f"Target: {target}")

# Buffer size is the number of items in the dataset; e.g.:
# 64 notes & seq = 4 & stride = 1 => buffer = 60
# 64 notes & seq = 4 & stride = 4 => buffer = 15
buffer_size = (n_notes - seq_length) // shift_size
train_ds = (
    seq_ds.shuffle(buffer_size)
    .batch(batch_size, drop_remainder=True)
    .cache()
    .prefetch(tf.data.experimental.AUTOTUNE)
)
logger.info(train_ds.element_spec)

# Train the model
input_shape = (seq_length, 88)
learning_rate = 0.005

inputs = tf.keras.Input(input_shape)
x = tf.keras.layers.LSTM(128)(inputs)

outputs = {
    "quantum": tf.keras.layers.Dense(88, name="quantum")(x),
}

model = tf.keras.Model(inputs, outputs)

loss = {
    "quantum": tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
}

optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)

model.compile(loss=loss, optimizer=optimizer)

model.summary()

# Evaluate losses
losses = model.evaluate(train_ds, return_dict=True)
logger.info(f"Losses: {losses}")

# Train the model
callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        filepath='./training_checkpoints/ckpt_{epoch}',
        save_weights_only=True),
    tf.keras.callbacks.EarlyStopping(
        monitor='loss',
        patience=5,
        verbose=1,
        restore_best_weights=True),
]
epochs = 50
history = model.fit(
    train_ds,
    epochs=epochs,
    callbacks=callbacks,
)