import unittest
from src.aptly_update.aptly_update import get_timestamp, get_logfile


class TestTimeStamp(unittest.TestCase):
    def test_timestamp(self):
        timestamp = get_timestamp()
        self.assertRegex(timestamp, r'^\d{8}T\d{2}:\d{2}:\d{2}$')

class TestLogFile(unittest.TestCase):
    def test_logfile(self):
        logfile = get_logfile()
        self.assertRegex(logfile, r'-run-\d{8}T\d{2}:\d{2}:\d{2}$')
        self.assertGreater(len(logfile), 22)
        # The actual file name cannot be used because it may come from the test
        # file, the test runner or elsewhere. But the length of the calling file
        # must be non-zero.

if __name__ == '__main__':
    unittest.main()