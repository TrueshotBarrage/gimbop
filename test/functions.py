"""This module contains unit tests for the main functionalities of GIMBOP."""

import unittest

from src.setup import Key


class TestKeyInitialization(unittest.TestCase):
    def test_get_key_num(self):
        """Test that the get_key_num method returns the correct key number."""
        c_key = Key("C")
        self.assertEqual(int(repr(c_key)), 0)

    def test_key_attribute(self):
        """Test that the key attribute is set correctly."""
        b_key = Key("B")
        self.assertEqual(b_key.key, 5)


if __name__ == "__main__":
    unittest.main()
