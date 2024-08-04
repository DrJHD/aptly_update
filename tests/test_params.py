import unittest
import subprocess

class TestDebug(unittest.TestCase):
    def test_debug(self):
        cmds = ["python src/aptly_update/aptly_update.py --debug",
                "python src/aptly_update/aptly_update.py -d"]
        for cmd in cmds:
            test_cmd(self, cmd, "Debug mode")

class TestYaml(unittest.TestCase):
    def test_yaml(self):
        cmds = ["python src/aptly_update/aptly_update.py -d --yaml test.yaml",
                "python src/aptly_update/aptly_update.py -d -y     test.yaml",
                "python src/aptly_update/aptly_update.py -d --file test.yaml",
                "python src/aptly_update/aptly_update.py -d -f     test.yaml"]
        for cmd in cmds:
            test_cmd(self, cmd, "yaml=['test.yaml']")
 
class TestHelp(unittest.TestCase):
    def test_help(self):
        cmds = ["python src/aptly_update/aptly_update.py -h",
                "python src/aptly_update/aptly_update.py --help"]
        for cmd in cmds:
            test_cmd(self, cmd, "usage:")

def test_cmd(cls, cmd, expected):
    rtn = subprocess.run(cmd, stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                              text=True).stdout
    cls.assertIn(expected, rtn)

if __name__ == '__main__':
    unittest.main()