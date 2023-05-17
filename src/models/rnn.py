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

# Verify that the GPU is available
logger.info(f"GPU list: {tf.config.list_physical_devices('GPU')}")

# Get path of dataset
path = os.path.join(os.getcwd(), "data", "output")
data_dir = pathlib.Path(path)
logger.info(f"Looking in {data_dir}")

filenames = glob.glob(str(data_dir / "*.npy"))
logger.info(f"Number of files: {len(filenames)}")

# Process a select number of files to mock train the model
num_files = 10  # 1276 total, we can do a rough 60:30:10 split -- nvm, too big
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
    label_size=16,
) -> tf.data.Dataset:
    """Returns TF Dataset of sequence and label examples."""

    # Take extra "label_size" length for the labels
    seq_length = seq_length + label_size
    windows = dataset.window(
        seq_length, shift=shift_size, stride=1, drop_remainder=True
    )

    # `flat_map` flattens the" dataset of datasets" into a dataset of tensors
    flatten = lambda x: x.batch(seq_length, drop_remainder=True)
    sequences = windows.flat_map(flatten)

    # Split the labels
    def split_labels(sequences):
        inputs = sequences[:-label_size]
        labels = sequences[-label_size:]

        return inputs, labels

    return sequences.map(split_labels, num_parallel_calls=tf.data.AUTOTUNE)


# Parameters for training the RNN
vocab_size = 88
seq_length = 16 * 4  # 10 measures since each quantum = sixteenth note
shift_size = 4
label_size = 16

# Generate RNN sequences
seq_ds = create_sequences(notes_ds, seq_length, shift_size, label_size)
logger.info(f"Sequence element spec: {seq_ds.element_spec}")

for seq, target in seq_ds.take(1):
    logger.info(f"Sequence shape: {seq.shape}")
    logger.info(f"Sequence elements (first 10): {seq[0:10]}")
    logger.info("")
    logger.info(f"Target: {target}")

# Buffer size is the number of items in the dataset; e.g.:
# 64 notes & seq = 4 & stride = 1 => buffer = 60
# 64 notes & seq = 4 & stride = 4 => buffer = 15
batch_size = 64
buffer_size = (n_notes - seq_length) // shift_size
train_ds = (
    seq_ds.shuffle(buffer_size)
    .batch(batch_size, drop_remainder=True)
    .cache()
    .prefetch(tf.data.experimental.AUTOTUNE)
)
logger.info(train_ds.element_spec)

# Train the model
input_shape = (seq_length, vocab_size)
# batch_input_shape = (batch_size, seq_length, vocab_size)
learning_rate = 0.005

inputs = tf.keras.Input(input_shape)
x = tf.keras.layers.LSTM(vocab_size)(inputs)

outputs = {
    "quantum": tf.keras.layers.Dense(label_size * vocab_size, name="quantum")(x),
}

model = tf.keras.Model(inputs, outputs)

# logger.info("===== MODEL SUMMARY =====")
# # logger.info(f"batch_size: {batch_size}")
# logger.info(f"seq_length: {seq_length}")
# logger.info(f"vocab_size: {vocab_size}")
# logger.info(f"input_shape: {input_shape}")
# # logger.info(f"batch_input_shape: {batch_input_shape}")
# logger.info(f"learning_rate: {learning_rate}")
# logger.info("===== MODEL SUMMARY =====")

# model = tf.keras.Sequential()
# # model.add(tf.keras.Input(batch_input_shape=batch_input_shape))
# # model.add(tf.keras.layers.LSTM(vocab_size))
# model.add(
#     tf.keras.layers.LSTM(
#         units=label_size * vocab_size,
#         # batch_input_shape=batch_input_shape,
#         # stateful=False,
#         return_sequences=False,
#     )
# )
# model.add(tf.keras.layers.Dense(label_size * vocab_size, name="quantum"))
# model.add(tf.keras.layers.Activation(tf.keras.activations.relu))

# Make sure the output shape is correct
# model.add(tf.keras.layers.Reshape((label_size, vocab_size)))
# model.add(tf.keras.layers.Flatten())

# loss = {
#     "quantum": tf.keras.losses.CategoricalCrossentropy(from_logits=True),
# }
loss = tf.keras.losses.MeanSquaredError()
optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)

model.compile(loss=loss, optimizer=optimizer)
# model.build(input_shape)

model.summary()

# Evaluate losses
# losses = model.evaluate(train_ds, return_dict=True)
# logger.info(f"Losses: {losses}")

# Train the model
callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        filepath="./training_checkpoints_simple/ckpt_{epoch}", save_weights_only=True
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor="loss", patience=5, verbose=1, restore_best_weights=True
    ),
]
epochs = 10
history = model.fit(
    train_ds,
    epochs=epochs,
    callbacks=callbacks,
)
