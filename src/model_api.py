"""This module contains the brains behind music generation."""
import tensorflow as tf


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


class GimbopAPI:
    def __init__(self, checkpoint_filepath="./training_checkpoints/ckpt_7"):
        self.model = create_model()
        self.retrieve_model(checkpoint_filepath)

    def retrieve_model(self, checkpoint_filepath="./training_checkpoints/ckpt_7"):
        self.model.load_weights(checkpoint_filepath)
