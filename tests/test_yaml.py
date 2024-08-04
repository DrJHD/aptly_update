import unittest
import subprocess
import yaml
from os.path import exists
import os

yaml = """
- 
  name: bookworm
  mirrors:
    - bookworm-main
    - bookworm-security
"""

class TestYaml(unittest.TestCase):
    def test_yaml(self):
        with open("test.yaml", "w") as yaml_file:
            yaml_file.write(yaml) # type: ignore
        cmd = "python src/aptly_update/aptly_update.py -d --yaml test.yaml"
        rtn = subprocess.run(cmd, stdout=subprocess.PIPE, 
                                  stderr=subprocess.STDOUT,
                                  text=True).stdout
        os.remove("test.yaml") # The yaml file must be removed before
                               # the assertions, as failure will cause
                               # a premature exit and an orphaned file.
        self.assertIn("'name': 'bookworm'", rtn)
        self.assertIn("'mirrors': ['bookworm-main', 'bookworm-security']", rtn)

if __name__ == '__main__':
    if exists("test.yaml"):
        # Die if there is a danger of clobbering someone else's file.
        raise Exception("test.yaml already exists. Delete it manually before running this test. But be sure that won't cause problems for someone else.")
    else:
        unittest.main()

"""
Using a temporary file would be cleaner,
but it cannot be passed to the main programme.

YAML has been used, but other formats are possible. Patches welcome!
"""