"""This module contains the brains behind music generation."""
import tensorflow as tf
from src.representation import MusicAbstractor


def create_model():
    # Hyperparameters
    batch_size = 64
    label_size = 16
    vocab_size = 88
    seq_length = 16 * 4  # 10 measures since each quantum = sixteenth note
    batch_input_shape = (batch_size, seq_length, vocab_size)
    learning_rate = 0.01

    model = tf.keras.Sequential()
    # model.add(tf.keras.Input(batch_input_shape=batch_input_shape))
    # model.add(tf.keras.layers.LSTM(vocab_size))
    model.add(
        tf.keras.layers.LSTM(
            units=label_size * vocab_size,
            batch_input_shape=batch_input_shape,
            stateful=False,
            return_sequences=False,
        )
    )
    # model.add(tf.keras.layers.Dense(label_size * vocab_size, name="quantum"))
    model.add(tf.keras.layers.Activation(tf.keras.activations.relu))

    # Make sure the output shape is correct
    model.add(tf.keras.layers.Reshape((label_size, vocab_size)))
    # model.add(tf.keras.layers.Flatten())

    # loss = {
    #     "quantum": tf.keras.losses.CategoricalCrossentropy(from_logits=True),
    # }
    loss = tf.keras.losses.Poisson()
    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate, clipvalue=1.0)

    model.compile(loss=loss, optimizer=optimizer)

    return model


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


class GimbopAPI:
    def __init__(self, checkpoint_filepath="./training_checkpoints/ckpt_7"):
        self.model = create_model()
        self.retrieve_model(checkpoint_filepath)

    def retrieve_model(self, checkpoint_filepath="./training_checkpoints/ckpt_7"):
        self.model.load_weights(checkpoint_filepath)

    def generate_notes_test(self, midi_file):
        abstractor = MusicAbstractor(midi_file)
        music = abstractor.abstract()

        # Generate notes to the right input size for the model, which is (64, 88)
        print(music.shape)
        assert music.shape[1] == 88, "Music representation has wrong number of features"
        num_quantums = music.shape[0]  # Much bigger than 64

        batch_size = 64
        seq_length = 16 * 4  # 10 measures since each quantum = sixteenth note
        shift_size = 4
        label_size = 16

        notes_ds = tf.data.Dataset.from_tensor_slices(music)
        seq_ds = create_sequences(notes_ds, seq_length, shift_size, label_size)
        seq_ds.batch(batch_size, drop_remainder=True)

        for i in range(10):
            input_seq = music[i : i + 64, :]
            # input_seq = tf.expand_dims(input_seq, 0)
            print(f"Input {i+1}: {input_seq}")
            print(f"Input {i+1} shape: {input_seq.shape}")

            # Predict the next 16 notes
            predictions = self.model.predict(input_seq)
            print(f"Prediction {i+1}: {predictions}")
            assert predictions.shape == (1, 16, 88), "Predictions have wrong shape"

            # Save the predictions to a numpy array
            # Reshape the predictions to (16, 88)
            predictions = tf.reshape(predictions, (16, 88))
