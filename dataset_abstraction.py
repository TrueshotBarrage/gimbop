import os
import glob
import pathlib
import logging

from src.representation import MusicAbstractor

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

filenames = glob.glob(str(data_dir / "**/*.mid*"))
logger.info(f"Number of files: {len(filenames)}")

# For each file, run the abstraction method to convert each MIDI file to a
# music representation suitable for Gimbop
for filename in filenames:
    # Parse filename base and extension
    filename_path, filename_ext = os.path.splitext(filename)
    filename_base = os.path.basename(filename_path)
    logger.info(f"-- Processing => {filename_base}{filename_ext}")

    # Set output path of the music representation
    output_path = os.path.join(os.getcwd(), "data", "output", f"{filename_base}.npy")
    logger.info(f"Saving to => {output_path}")

    # Convert the MIDI file into numpy data arrays
    abstractor = MusicAbstractor(filename)
    music = abstractor.abstract(fn=output_path, format="numpy")
    # notes = abstractor.deabstract()
