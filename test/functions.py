"""This module contains unit tests for the main functionalities of Gimbop."""

import unittest
import os

from src.setup import Key, SongWriter

# Increase the maximum length of strings to be printed in the console
unittest.util._MAX_LENGTH = 2000


class TestKeyInitialization(unittest.TestCase):
    def test_get_num_accidentals(self):
        """Test that the Key returns the correct number of accidentals."""
        c_key = Key("C")
        self.assertEqual(int(repr(c_key)), 0)

    def test_key_attribute(self):
        """Test that the num_accidentals attribute is set correctly."""
        b_key = Key("B")
        self.assertEqual(b_key.num_accidentals, 5)


class TestSongWriter(unittest.TestCase):
    def setUp(self):
        self.writer = SongWriter()
        self.filename_base = os.path.join(os.getcwd(), "test", "test_song")

    def tearDown(self):
        if os.path.isfile(self.filename_base + ".csv"):
            os.remove(self.filename_base + ".csv")
            os.remove(self.filename_base + ".mid")

    def assertIsFile(self, path):
        if not os.path.isfile(path):
            raise AssertionError("File does not exist: %s" % str(path))

    def test_write_to_file(self):
        """Test that the SongWriter writes to a file correctly."""
        self.writer.write(self.filename_base)

        # Check that the files were created properly
        self.assertIsFile(self.filename_base + ".csv")
        self.assertIsFile(self.filename_base + ".mid")

    def test_write_header(self):
        """Test that the SongWriter writes the header correctly."""
        self.writer._write_header()

        # Generate the header string
        header_exp = ""
        for line in self.writer.lines:
            self.assertIsInstance(line, list)
            line = [str(x) for x in line]
            header_exp += ",".join(line) + "\n"
        header_exp += f"1,{self.writer.total_time},End_track\n0,0,End_of_file\n"
        self.writer._finish(self.filename_base)

        # Check that the header was written properly
        with open(self.filename_base + ".csv", "r") as f:
            header = f.readlines()
        header = "".join(header)

        # Check equivalence
        self.assertEqual(header, header_exp)


if __name__ == "__main__":
    unittest.main()
