"""This module contains unit tests for the main functionalities of GIMBOP."""

import unittest

from src.setup import Key


class TestKeyInitialization(unittest.TestCase):
    def test_get_num_accidentals(self):
        """Test that the Key returns the correct number of accidentals."""
        c_key = Key("C")
        self.assertEqual(int(repr(c_key)), 0)

    def test_key_attribute(self):
        """Test that the num_accidentals attribute is set correctly."""
        b_key = Key("B")
        self.assertEqual(b_key.num_accidentals, 5)


if __name__ == "__main__":
    unittest.main()
