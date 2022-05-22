from unittest import TestCase

from ycl.tools import youtube


class YCLTestCases(TestCase):
    """Class for YCL test cases
    """

    def test_is_connected(self):
        """Test if the device is connected
        """
        self.assertTrue(youtube.is_connected())

    def test_is_valid_URL(self):
        """Test if the URL is valid
        """
        self.assertTrue(youtube.isValidURL("https://www.youtube.com/watch?v=dQw4w9WgXcQ")[0])
        self.assertFalse(youtube.isValidURL("https://www.youtube.com/watch?v=dQw4w9WgXcQs")[0])
