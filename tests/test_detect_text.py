# THIS IS AN ABANDONED TEMPLATE, WOULD NOT DO ANYTHING UNTIL FUTURE UPDATES

import unittest
import numpy as np

import detect_text

class TestCropFrame(unittest.TestCase):

    def test_cases(self):
        cases = [
                # ordinary
                (frame,
                 top,
                 left,
                 bottom,
                 right,
                 expected),
                ]

        for a, b, c, d, e, expected in cases:
            with self.subTest(a=a, b=b, c=c, d=d, e=e):
                self.assertEqual(detect_text.crop_frame(a, b, c, d, e), expected)

if __name__ == '__main__':
    unittest.main()
