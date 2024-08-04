import unittest
import subprocess
from os.path import exists
import os
import re
from src.aptly_update.aptly_update import import_module

def get_parse_output(yaml):
    cmd = "python src/aptly_update/aptly_update.py -d --yaml test.yaml"
    with open("test.yaml", "w") as yaml_file:
        yaml_file.write(yaml)
    rtn = subprocess.run(cmd, stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                                text=True).stdout
    os.remove("test.yaml")
    # The yaml file must be removed before the assertions, as failure will
    # lead to a premature exit and an orphaned file.
    timematch = re.search(r'Timestamp:\s+(\d{8}T\d{2}:\d{2}:\d{2})', rtn)
    timestamp = timematch.group(1) # type: ignore
    logmatch = re.search(r'Logfile:\s+(.+\d{8}T\d{2}:\d{2}:\d{2})', rtn)
    logfile = logmatch.group(1) # type: ignore
    # The timestamp and logfile must be parsed rather than queried from the
    # code, as the two runs would be at different times.
    return (timestamp, logfile, rtn)

yaml_simplest = """
- 
  name: bookworm
  mirrors:
    - bookworm-main
"""

class TestPublishSimplest(unittest.TestCase):
    def test_yaml(self):
        (timestamp, logfile, rtn) = get_parse_output(yaml_simplest)
        self.assertIn("aptly mirror update bookworm-main >> " + logfile, rtn)
        self.assertIn("aptly snapshot create bookworm-main-" + timestamp + 
                      " from mirror bookworm-main >> " + logfile , rtn)
        self.assertIn("aptly publish drop bookworm >> " + logfile, rtn)
        self.assertIn("aptly publish snapshot -distribution=bookworm bookworm-main-"
                       + timestamp + " >> " + logfile + "", rtn)

yaml_2_mirrors = """
- 
  name: bookworm
  mirrors:
    - bookworm-main
    - bookworm-security
"""

class TestPublish2Mirrors(unittest.TestCase):
    def test_yaml(self):
        (timestamp, logfile, rtn) = get_parse_output(yaml_2_mirrors)
        self.assertIn("aptly mirror update bookworm-main >> " + logfile, rtn)
        self.assertIn("aptly snapshot create bookworm-main-" + timestamp + 
                      " from mirror bookworm-main >> " + logfile , rtn)
        self.assertIn("aptly mirror update bookworm-security >> " + logfile, rtn)
        self.assertIn("aptly snapshot create bookworm-security-" + timestamp + 
                      " from mirror bookworm-security >> " + logfile , rtn)
        self.assertIn("aptly snapshot merge -latest bookworm-" + timestamp 
                      + " bookworm-main-" + timestamp + " bookworm-security-"
                      + timestamp + " >> " + logfile, rtn)
        self.assertIn("aptly publish drop bookworm >> " + logfile, rtn)
        self.assertIn("aptly publish snapshot -distribution=bookworm bookworm-"
                       + timestamp + " >> " + logfile + "", rtn)

yaml_2_repos = """
- 
  name: bookworm
  mirrors:
    - bookworm-main
- 
  name: raspbian
  mirrors:
    - raspbian-main
"""

class TestPublish2Repos(unittest.TestCase):
    def test_yaml(self):
        (timestamp, logfile, rtn) = get_parse_output(yaml_2_repos)
        self.assertIn("aptly mirror update bookworm-main >> " + logfile, rtn)
        self.assertIn("aptly snapshot create bookworm-main-" + timestamp + 
                      " from mirror bookworm-main >> " + logfile , rtn)
        self.assertIn("aptly publish drop bookworm >> " + logfile, rtn)
        self.assertIn("aptly publish snapshot -distribution=bookworm bookworm-main-"
                       + timestamp + " >> " + logfile + "", rtn)
        self.assertIn("aptly mirror update raspbian-main >> " + logfile, rtn)
        self.assertIn("aptly snapshot create raspbian-main-" + timestamp + 
                      " from mirror raspbian-main >> " + logfile , rtn)
        self.assertIn("aptly publish drop raspbian >> " + logfile, rtn)
        self.assertIn("aptly publish snapshot -distribution=raspbian raspbian-main-"
                       + timestamp + " >> " + logfile + "", rtn)

yaml_2_repos_2_mirrors = """
- 
  name: bookworm # bookworm is a publication
  mirrors:       # mirrors will be updated & snapshotted
    - bookworm-main
    - bookworm-security
                                                           
-
  name: raspbian
  mirrors:
    - raspbian-main
"""

class TestPublish2Repos2Mirrors(unittest.TestCase):
    def test_yaml(self):
        (timestamp, logfile, rtn) = get_parse_output(yaml_2_repos_2_mirrors)
        self.assertIn("aptly mirror update bookworm-main >> " + logfile, rtn)
        self.assertIn("aptly snapshot create bookworm-main-" + timestamp + 
                      " from mirror bookworm-main >> " + logfile , rtn)
        self.assertIn("aptly mirror update bookworm-security >> " + logfile, rtn)
        self.assertIn("aptly snapshot create bookworm-security-" + timestamp + 
                      " from mirror bookworm-security >> " + logfile , rtn)
        self.assertIn("aptly snapshot merge -latest bookworm-" + timestamp 
                      + " bookworm-main-" + timestamp + " bookworm-security-"
                      + timestamp + " >> " + logfile, rtn)
        self.assertIn("aptly publish drop bookworm >> " + logfile, rtn)
        self.assertIn("aptly publish snapshot -distribution=bookworm bookworm-"
                       + timestamp + " >> " + logfile + "", rtn)
        self.assertIn("aptly mirror update raspbian-main >> " + logfile, rtn)
        self.assertIn("aptly snapshot create raspbian-main-" + timestamp + 
                      " from mirror raspbian-main >> " + logfile , rtn)
        self.assertIn("aptly publish drop raspbian >> " + logfile, rtn)
        self.assertIn("aptly publish snapshot -distribution=raspbian raspbian-main-"
                       + timestamp + " >> " + logfile + "", rtn)

if __name__ == '__main__':
    if exists("test.yaml"):
        # Die if there is a danger of clobbering someone else's file.
        raise Exception("test.yaml already exists. Delete it manually before running this test. But be sure that won't cause problems for someone else.")
    else:
        unittest.main()
